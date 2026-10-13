from pathlib import Path

import psycopg
import pytest

from handbook_rag.chunk import CHUNK_OVERLAP, CHUNK_SIZE, TOKENIZER, run
from handbook_rag.corpus import CHECKOUT, read_manifest
from handbook_rag.db import connect

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
MODEL = "fake:chunk-test"
FINGERPRINT = "SELECT md5(string_agg(chunk_id::text || content, '|' ORDER BY chunk_id)) FROM chunks"


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


def count(conn) -> int:
    return conn.execute("SELECT count(*) FROM chunks").fetchone()[0]


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
    before = conn.execute(FINGERPRINT).fetchone()[0]
    skipped = run(conn)
    assert skipped.skipped and skipped.chunks == first and count(conn) == first
    forced = run(conn, force=True)
    assert not forced.skipped and forced.chunks == first
    assert forced.changed == 0 and forced.deleted == 0
    assert conn.execute(FINGERPRINT).fetchone()[0] == before


def test_every_document_chunked_with_parameters(conn):
    """AC-1: non-empty docs have chunks; rows carry the parameters and the manifest SHA."""
    (uncovered,) = conn.execute(
        """SELECT count(*) FROM documents d WHERE d.body ~ '\\S'
           AND NOT EXISTS (SELECT 1 FROM chunks c WHERE c.doc_id = d.doc_id)"""
    ).fetchone()
    assert uncovered == 0
    bad = conn.execute(
        """SELECT count(*) FROM chunks WHERE token_count > %s OR token_count < 1
           OR chunk_size <> %s OR chunk_overlap <> %s OR tokenizer <> %s OR commit_sha <> %s""",
        (CHUNK_SIZE, CHUNK_SIZE, CHUNK_OVERLAP, TOKENIZER, read_manifest(ROOT / "CORPUS.md").sha),
    ).fetchone()[0]
    assert bad == 0


def test_deleting_document_cascades_to_chunks_and_embeddings(conn):
    """AC-2: removing a document removes its chunks and their embeddings."""
    before = count(conn)
    with conn.transaction(force_rollback=True):
        doc_id, chunk_id = conn.execute(
            "SELECT doc_id, chunk_id FROM chunks ORDER BY chunk_id LIMIT 1"
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
                      (SELECT chunk_id FROM chunks WHERE doc_id = c.doc_id AND chunk_index = 0),
                      c.chunk_id
               FROM chunks c
               JOIN (SELECT doc_id, max(chunk_index) m FROM chunks GROUP BY doc_id) l
                 ON l.doc_id = c.doc_id AND l.m = c.chunk_index
               WHERE c.chunk_index >= 2 AND c.token_count <= 400
               ORDER BY c.doc_id LIMIT 1"""
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
