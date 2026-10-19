from pathlib import Path

import psycopg
import pytest

from handbook_rag import chunk
from handbook_rag.chunk import register_config, run
from handbook_rag.constants import (
    BASELINE_CONFIG,
    CHECKOUT,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHUNKS_SCHEMA,
    TOKENIZER,
)
from handbook_rag.corpus import read_manifest
from handbook_rag.db import connect

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
MODEL = "fake:chunk-test"
STRUCTURAL = "structural-v1"
FINGERPRINT = """SELECT count(*), md5(string_agg(chunk_id::text || content, '|' ORDER BY chunk_id))
                 FROM chunks WHERE config_id = %s"""
# The baseline as embedded for run 2026-10-17-3748df5b (spec 0005, AC-3).
BASELINE_FINGERPRINT = (22378, "a74cd0329fbcd326128f12b6fb46d6de")
# Every stored column, and the embeddings present, for a config (spec 0006, AC-2).
ROWS = """SELECT count(*), md5(string_agg(concat_ws('|', chunk_id, doc_id, chunk_index, content,
                 token_count, heading, chunk_size, chunk_overlap, tokenizer, commit_sha,
                 heading_path::text, line_start, line_end), '#' ORDER BY chunk_id))
          FROM chunks WHERE config_id = %s"""
EMBEDDINGS = """SELECT count(*), md5(string_agg(e.chunk_id::text || e.model, '|'
                 ORDER BY e.chunk_id, e.model))
                FROM chunk_embeddings e JOIN chunks c USING (chunk_id) WHERE c.config_id = %s"""
NEW_CONFIGS = ("structural-v2", "structural-v3", "fixed-512-64-prefixed")
BASELINE_EMBEDDINGS = """SELECT count(*) FROM chunk_embeddings e JOIN chunks c USING (chunk_id)
                         WHERE c.config_id = %s"""


@pytest.fixture(scope="module")
def conn():
    """Real DB connection; chunk the ingested corpus (forced) so tests see a full table."""
    mp = pytest.MonkeyPatch()
    mp.chdir(ROOT)
    if not (CHECKOUT / ".git").exists():
        pytest.fail("Corpus checkout missing. Run `make corpus` first.")
    try:
        conn = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    with conn:
        run(conn, force=True)
        conn.commit()
        yield conn
    mp.undo()


def count(conn, config_id: str = BASELINE_CONFIG) -> int:
    return conn.execute(
        "SELECT count(*) FROM chunks WHERE config_id = %s", (config_id,)
    ).fetchone()[0]


def fingerprint(conn, config_id: str = BASELINE_CONFIG) -> tuple[int, str]:
    return conn.execute(FINGERPRINT, (config_id,)).fetchone()


def embed(conn, chunk_id) -> None:
    conn.execute(
        "INSERT INTO chunk_embeddings (chunk_id, model, embedding) VALUES (%s, %s, %s::vector)",
        (chunk_id, MODEL, "[1,0,0]"),
    )


def has_embedding(conn, chunk_id) -> bool:
    return conn.execute(
        "SELECT EXISTS (SELECT 1 FROM chunk_embeddings WHERE chunk_id = %s AND model = %s)",
        (chunk_id, MODEL),
    ).fetchone()[0]


def test_early_exit_then_force_is_identical(conn):
    """AC-2: a re-run skips; a forced re-run reproduces the same ids and content."""
    first = count(conn)
    print(f"chunks: {first}")
    assert 22_000 <= first <= 22_800
    before = fingerprint(conn)
    assert before == BASELINE_FINGERPRINT  # spec 0005, AC-3: the rewrite left the baseline as is
    skipped = run(conn)
    assert skipped.skipped and skipped.chunks == first and count(conn) == first
    forced = run(conn, force=True)
    assert not forced.skipped and forced.chunks == first
    assert forced.changed == 0 and forced.deleted == 0
    assert fingerprint(conn) == before


def test_every_document_chunked_with_parameters(conn):
    """AC-1: non-empty docs have chunks; rows carry the parameters and the manifest SHA."""
    (uncovered,) = conn.execute(
        """SELECT count(*) FROM documents d WHERE d.body ~ '\\S' AND NOT EXISTS
           (SELECT 1 FROM chunks c WHERE c.doc_id = d.doc_id AND c.config_id = %s)""",
        (BASELINE_CONFIG,),
    ).fetchone()
    assert uncovered == 0
    bad = conn.execute(
        """SELECT count(*) FROM chunks WHERE config_id = %s AND (token_count > %s OR token_count < 1
           OR chunk_size <> %s OR chunk_overlap <> %s OR tokenizer <> %s OR commit_sha <> %s
           OR heading_path IS NOT NULL OR line_start IS NOT NULL OR line_end IS NOT NULL)""",
        (BASELINE_CONFIG, CHUNK_SIZE, CHUNK_SIZE, CHUNK_OVERLAP, TOKENIZER,
         read_manifest(ROOT / "CORPUS.md").sha),
    ).fetchone()[0]  # fmt: skip
    assert bad == 0


def test_deleting_document_cascades_to_chunks_and_embeddings(conn):
    """AC-2: removing a document removes its chunks and their embeddings."""
    before = count(conn)
    with conn.transaction(force_rollback=True):
        doc_id, chunk_id = conn.execute(
            "SELECT doc_id, chunk_id FROM chunks WHERE config_id = %s ORDER BY chunk_id LIMIT 1",
            (BASELINE_CONFIG,),
        ).fetchone()
        embed(conn, chunk_id)
        conn.execute("DELETE FROM documents WHERE doc_id = %s", (doc_id,))
        assert (
            conn.execute("SELECT count(*) FROM chunks WHERE doc_id = %s", (doc_id,)).fetchone()[0]
            == 0
        )
        assert not has_embedding(conn, chunk_id)
    assert count(conn) == before
    assert (
        conn.execute("SELECT count(*) FROM chunks WHERE doc_id = %s", (doc_id,)).fetchone()[0] > 0
    )


def test_changed_content_drops_only_its_embedding(conn):
    """AC-2: a chunk whose text changed loses its embedding; unchanged chunks keep theirs."""
    with conn.transaction(force_rollback=True):
        doc_id, first_id, last_id = conn.execute(
            """SELECT c.doc_id,
                      (SELECT chunk_id FROM chunks
                       WHERE doc_id = c.doc_id AND chunk_index = 0 AND config_id = %(cfg)s),
                      c.chunk_id
               FROM chunks c
               JOIN (SELECT doc_id, max(chunk_index) m FROM chunks WHERE config_id = %(cfg)s
                     GROUP BY doc_id) l
                 ON l.doc_id = c.doc_id AND l.m = c.chunk_index
               WHERE c.config_id = %(cfg)s AND c.chunk_index >= 2 AND c.token_count <= 400
               ORDER BY c.doc_id LIMIT 1""",
            {"cfg": BASELINE_CONFIG},
        ).fetchone()
        embed(conn, first_id)
        embed(conn, last_id)
        conn.execute(
            "UPDATE documents SET body = body || E'\\n\\nappended tail text' WHERE doc_id = %s",
            (doc_id,),
        )
        result = run(conn, force=True)
        assert result.changed == 1
        assert has_embedding(conn, first_id)
        assert not has_embedding(conn, last_id)


def test_stale_documents_are_refused(conn):
    """AC-2: documents whose SHA differs from CORPUS.md stop the run and point at ingest."""
    with conn.transaction(force_rollback=True):
        conn.execute(
            "UPDATE documents SET commit_sha = 'deadbeef' WHERE doc_id = "
            "(SELECT doc_id FROM documents ORDER BY doc_id LIMIT 1)"
        )
        with pytest.raises(SystemExit, match="make ingest"):
            run(conn)


def test_migration_is_idempotent(conn):
    """Spec 0005, AC-2: the chunks DDL re-runs cleanly; every row has a config."""
    with conn.transaction(force_rollback=True):
        conn.execute(CHUNKS_SCHEMA.read_text())
        conn.execute(CHUNKS_SCHEMA.read_text())
        (nulls,) = conn.execute("SELECT count(*) FROM chunks WHERE config_id IS NULL").fetchone()
        assert nulls == 0
        assert conn.execute(
            "SELECT strategy, params FROM chunk_configs WHERE config_id = %s", (BASELINE_CONFIG,)
        ).fetchone() == ("fixed", {"size": CHUNK_SIZE, "overlap": CHUNK_OVERLAP})


def test_structural_run_leaves_baseline_untouched(conn):
    """Spec 0005, AC-1, AC-3, AC-9: chunking structural-v1 keeps every baseline row and
    embedding; a re-run early-exits; structural rows carry paths and line ranges."""
    before = fingerprint(conn)
    (embedded,) = conn.execute(BASELINE_EMBEDDINGS, (BASELINE_CONFIG,)).fetchone()
    first = run(conn, config_id=STRUCTURAL, force=True)
    conn.commit()
    assert not first.skipped and first.chunks == count(conn, STRUCTURAL)
    again = run(conn, config_id=STRUCTURAL)
    assert again.skipped and again.chunks == first.chunks
    assert fingerprint(conn) == before == BASELINE_FINGERPRINT
    assert conn.execute(BASELINE_EMBEDDINGS, (BASELINE_CONFIG,)).fetchone()[0] == embedded
    print(f"baseline embeddings: {embedded}")
    assert conn.execute(
        "SELECT strategy, params, tokenizer FROM chunk_configs WHERE config_id = %s",
        (STRUCTURAL,),
    ).fetchone() == ("structural", chunk.CHUNK_CONFIGS[STRUCTURAL]["params"], TOKENIZER)
    (bad,) = conn.execute(
        """SELECT count(*) FROM chunks WHERE config_id = %s AND (heading_path IS NULL
           OR line_start IS NULL OR line_end < line_start OR token_count > 512 OR token_count < 1
           OR chunk_size <> 512 OR chunk_overlap <> 64 OR tokenizer <> %s)""",
        (STRUCTURAL, TOKENIZER),
    ).fetchone()
    assert bad == 0
    (uncovered,) = conn.execute(
        """SELECT count(*) FROM documents d WHERE d.body ~ '\\S' AND NOT EXISTS
           (SELECT 1 FROM chunks c WHERE c.doc_id = d.doc_id AND c.config_id = %s)""",
        (STRUCTURAL,),
    ).fetchone()
    assert uncovered == 0
    n, p50, p90, top = conn.execute(
        """SELECT count(*), percentile_disc(0.5) WITHIN GROUP (ORDER BY token_count),
                  percentile_disc(0.9) WITHIN GROUP (ORDER BY token_count), max(token_count)
           FROM chunks WHERE config_id = %s""",
        (STRUCTURAL,),
    ).fetchone()
    print(f"{STRUCTURAL}: {n} chunks; tokens p50 {p50}, p90 {p90}, max {top}")


def snapshot(conn) -> dict:
    return {
        cfg: (conn.execute(ROWS, (cfg,)).fetchone(), conn.execute(EMBEDDINGS, (cfg,)).fetchone())
        for cfg in (BASELINE_CONFIG, STRUCTURAL)
    }


def test_packed_and_prefixed_runs_leave_existing_configs_untouched(conn):
    """Spec 0006, AC-1, AC-2, AC-4: chunking the three new configs keeps every fixed-512-64 and
    structural-v1 row, chunk_id and embedding; structural-v3 rows equal structural-v2 rows on
    content and line ranges, and fixed-512-64-prefixed rows equal the baseline's content.
    Rolled back, so the new configs' rows in the dev DB are as they were before the test."""
    if not count(conn, STRUCTURAL):
        run(conn, config_id=STRUCTURAL)
        conn.commit()
    before = snapshot(conn)
    new_before = [count(conn, cfg) for cfg in NEW_CONFIGS]
    with conn.transaction(force_rollback=True):
        for cfg in NEW_CONFIGS:
            r = run(conn, config_id=cfg, force=True)
            assert not r.skipped and r.chunks == count(conn, cfg) > 0
        assert snapshot(conn) == before
        assert fingerprint(conn) == BASELINE_FINGERPRINT
        (diff,) = conn.execute(
            """SELECT count(*)
               FROM (SELECT * FROM chunks WHERE config_id = 'structural-v2') a
               FULL JOIN (SELECT * FROM chunks WHERE config_id = 'structural-v3') b
                 USING (doc_id, chunk_index)
               WHERE (a.content, a.line_start, a.line_end, a.heading, a.heading_path)
                     IS DISTINCT FROM (b.content, b.line_start, b.line_end, b.heading,
                                       b.heading_path)"""
        ).fetchone()
        assert diff == 0
        assert count(conn, "structural-v3") == count(conn, "structural-v2")
        (diff,) = conn.execute(
            """SELECT count(*) FROM chunks a JOIN chunks b USING (doc_id, chunk_index)
               WHERE a.config_id = %s AND b.config_id = 'fixed-512-64-prefixed'
                 AND (a.content, a.token_count, a.heading)
                     IS DISTINCT FROM (b.content, b.token_count, b.heading)""",
            (BASELINE_CONFIG,),
        ).fetchone()
        assert diff == 0 and count(conn, "fixed-512-64-prefixed") == count(conn)
        (bad,) = conn.execute(
            """SELECT count(*) FROM chunks WHERE config_id = 'fixed-512-64-prefixed'
               AND (heading_path IS NULL OR line_start IS NOT NULL OR line_end IS NOT NULL
                    OR heading IS DISTINCT FROM heading_path[cardinality(heading_path)])"""
        ).fetchone()
        assert bad == 0
        (bad,) = conn.execute(
            """SELECT count(*) FROM chunks WHERE config_id = 'structural-v2' AND (
               heading_path IS NULL OR line_start IS NULL OR line_end < line_start
               OR token_count > 512 OR token_count < 1 OR chunk_size <> 512 OR chunk_overlap <> 64
               OR heading IS DISTINCT FROM heading_path[cardinality(heading_path)])"""
        ).fetchone()
        assert bad == 0
        n, p50, p90 = conn.execute(
            """SELECT count(*), percentile_disc(0.5) WITHIN GROUP (ORDER BY token_count),
                      percentile_disc(0.9) WITHIN GROUP (ORDER BY token_count)
               FROM chunks WHERE config_id = 'structural-v2'"""
        ).fetchone()
        print(f"structural-v2: {n} chunks; tokens p50 {p50}, p90 {p90}")
    assert snapshot(conn) == before
    assert [count(conn, cfg) for cfg in NEW_CONFIGS] == new_before


def test_register_config_rejects_drift_and_unknown(conn, monkeypatch):
    """Spec 0005, AC-1: a config's first registration records it; changed params under the same
    id fail; an unknown id fails."""
    cfg = {"strategy": "structural", "params": {"max_tokens": 256, "overlap": 0, "min_tokens": 0}}
    monkeypatch.setattr(chunk, "CHUNK_CONFIGS", {"test-drift": cfg})
    try:
        assert register_config(conn, "test-drift") == cfg
        conn.commit()
        assert register_config(conn, "test-drift") == cfg  # unchanged: passes
        drifted = {**cfg, "params": {**cfg["params"], "overlap": 32}}
        monkeypatch.setattr(chunk, "CHUNK_CONFIGS", {"test-drift": drifted})
        with pytest.raises(SystemExit, match="drifted"):
            register_config(conn, "test-drift")
        with pytest.raises(SystemExit, match="unknown chunk config"):
            register_config(conn, "no-such-config")
    finally:
        conn.rollback()
        conn.execute("DELETE FROM chunk_configs WHERE config_id = 'test-drift'")
        conn.commit()
