"""Eval runner against the real DB with fake models (spec 0004, AC-2, AC-4..AC-8).

Real chunks, fake embeddings under a test-only model name (cleaned up), and a tmp checkout whose
page files are built from those chunks' text, so the evidence lines match by construction. Each
page ends with its chunk's stored heading, so the AC-5 heading check passes by construction.
"""

import json

import psycopg
import pytest
from fakes import FakeAnswerer, FakeEmbedder, bow_vector

from handbook_rag.constants import CORPUS_PREFIX, EVAL_RUNS
from handbook_rag.db import connect, vector_literal
from handbook_rag.evaluation import evidence
from handbook_rag.evaluation import run as run_mod
from handbook_rag.evaluation.evalset import Fact, Row
from handbook_rag.prompts import NOT_FOUND

pytestmark = pytest.mark.integration

INSERT = "INSERT INTO chunk_embeddings (chunk_id, model, embedding) VALUES (%s, %s, %s::vector)"
MODEL = "fake:eval-run-test"
META_KEYS = {
    "eval_version", "eval_sha256", "harness_sha", "harness_dirty", "corpus_sha", "chunk_params",
    "embed_model", "answer_model", "system_prompt_sha256", "k", "timestamp", "rows", "mode",
    "limit",
}  # fmt: skip
MISSING = "zzqx this line is in no stored chunk qxzz"


def _clean(conn):
    conn.execute("DELETE FROM chunk_embeddings WHERE model = %s", (MODEL,))
    conn.commit()


def _longest_line(content: str) -> str:
    return max(content.split("\n"), key=lambda s: len(s.strip())).strip()


@pytest.fixture
def setup(tmp_path):
    """Seeds 30 chunks; writes pages A and B (L1 from chunk A / B, L2 matches nothing, L3 the
    chunk's stored heading).

    Yields (conn, checkout, path_a, path_b, question)."""
    try:
        conn = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    with conn:
        _clean(conn)
        rows = conn.execute(
            "SELECT c.chunk_id, c.content, d.path, COALESCE(c.heading, d.title) "
            "FROM chunks c JOIN documents d USING (doc_id) "
            "WHERE d.path LIKE %s ORDER BY c.chunk_id LIMIT 30",
            (CORPUS_PREFIX + "%",),
        ).fetchall()
        if len(rows) < 30:
            pytest.fail("chunks table is empty or too small. Run `make chunk` first.")
        a = max(rows, key=lambda r: len(r[1].split()))
        b = next(r for r in rows if r[2] != a[2])
        checkout = tmp_path / "checkout"
        for _, content, path, heading in (a, b):
            page = checkout / path
            page.parent.mkdir(parents=True, exist_ok=True)
            lines = [_longest_line(content), MISSING, f"# {heading}"]
            page.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with conn.cursor() as cur:
            cur.executemany(
                INSERT, [(cid, MODEL, vector_literal(bow_vector(c))) for cid, c, *_ in rows]
            )
        conn.commit()
        try:
            path_a, path_b = (r[2].removeprefix(CORPUS_PREFIX) for r in (a, b))
            yield conn, checkout, path_a, path_b, " ".join(a[1].split()[:40])
        finally:
            conn.rollback()
            _clean(conn)


def _rows(path_a, path_b, question, optional_line=1):
    lookup = Row(
        1,
        "lookup",
        question,
        expected_docs=(path_a,),
        facts=(
            Fact("F1", True, {path_a: (1,)}),
            Fact("F2", False, {path_b: (optional_line,)}),
            Fact("F3", False),  # answer-only
        ),
    )
    answer_only = Row(2, "lookup", question, (path_a,), (Fact("F1", True),))
    ooc = Row(3, "ooc-in-scope", "What is the airspeed of a swallow?", expected=NOT_FOUND)
    return [lookup, answer_only, ooc]


def _meta(answer_model, rows):
    params = {"chunk_size": 1, "chunk_overlap": 0, "tokenizer": "t"}
    return run_mod.metadata("v0.0", b"eval", "sha", params, MODEL, answer_model, rows, None)


def _read(out):
    records = [json.loads(line) for line in (out / "rows.jsonl").read_text().splitlines()]
    return {r["row"]: r for r in records}, json.loads((out / "summary.json").read_text())


def test_unmatchable_required_fact_raises(setup):
    """AC-2: a required fact whose cited line is in no stored chunk fails before any spend."""
    conn, checkout, path_a, _, question = setup
    row = Row(9, "lookup", question, (path_a,), (Fact("F1", True, {path_a: (2,)}),))
    with pytest.raises(evidence.EvidenceError, match="row 9 F1"):
        evidence.check([row], conn, checkout)


def test_unmatchable_optional_fact_warns(setup):
    """AC-2: the same failure on an optional fact is a warning only."""
    conn, checkout, path_a, path_b, question = setup
    ev = evidence.check(_rows(path_a, path_b, question, optional_line=2), conn, checkout)
    assert ev.relevant[(1, "F1")]
    assert ev.warnings == [
        f"row 1 F2 (optional): no stored chunk contains a cited line of {path_b}"
    ]


def test_retrieval_only_writes_outputs(setup, tmp_path):
    """AC-6, AC-7: no answerer call, ooc rows skipped, all three files and every meta key."""
    conn, checkout, path_a, path_b, question = setup
    rows = _rows(path_a, path_b, question)
    ev = evidence.check(rows, conn, checkout)
    answerer = FakeAnswerer("never [1]")
    embedder = FakeEmbedder(name=MODEL)
    out = run_mod.run(
        conn, rows, ev, embedder, None, meta=_meta(None, 2), out_root=tmp_path, checkout=checkout
    )
    assert answerer.calls == []
    assert len(embedder.calls) == 2
    assert out.parent == tmp_path
    assert {p.name for p in out.iterdir()} == {"rows.jsonl", "summary.json", "summary.md"}
    records, summary = _read(out)
    assert set(records) == {1, 2}
    r = records[1]
    assert r["metrics"]["chunk_fact_recall@5"] == 1.0
    assert r["retrieved"][0]["facts"] == ["F1"]  # chunk A ranks first; optional F2 not scored
    assert r["retrieved"][0]["path"] == path_a and r["retrieved"][0]["page_relevant"]
    assert r["page_hit_no_chunk"] is False
    assert r["answer"] is None and r["abstention"] is None and r["checks"] is None
    # Row 2: its only required fact is answer-only, so retrieval is recorded but not scored.
    assert records[2]["metrics"] == {} and records[2]["page_hit_no_chunk"] is False
    assert len(records[2]["retrieved"]) == 5
    assert set(summary["meta"]) == META_KEYS
    assert summary["meta"]["mode"] == "retrieval-only"
    assert summary["notes"]["no_retrieval_facts"] == [2]
    assert summary["notes"]["answer_only_facts"] == ["row 1 F3", "row 2 F1"]
    assert summary["groups"]["overall"]["chunk_fact_recall@5"]["n"] == 1
    assert (out / "summary.md").read_text().startswith("# Eval summary")


def test_full_mode_writes_abstention_and_checks(setup, tmp_path):
    """AC-4, AC-5, AC-7: answered rows get abstention; answerable non-abstentions get checks."""
    conn, checkout, path_a, path_b, question = setup
    lookup, _, ooc = _rows(path_a, path_b, question)
    ev = evidence.check([lookup, ooc], conn, checkout)
    embedder = FakeEmbedder(name=MODEL)
    answerer = FakeAnswerer("The handbook says so [1].")
    out = run_mod.run(
        conn,
        [lookup],
        ev,
        embedder,
        answerer,
        meta=_meta("fake:answer", 1),
        out_root=tmp_path,
        checkout=checkout,
    )
    r = _read(out)[0][1]
    assert len(answerer.calls) == 1
    assert r["answer"] == "The handbook says so [1]."
    assert r["citations"][0]["n"] == 1
    assert r["abstention"]["abstained"] is False and r["abstention"]["false_abstention"] is False
    assert r["checks"]["has_citation"] and r["checks"]["headings_exist"]
    assert r["checks"]["passed"] is True and r["truncated"] is False

    out = run_mod.run(
        conn,
        [ooc],
        ev,
        embedder,
        FakeAnswerer(NOT_FOUND),
        meta=_meta("fake:answer", 1),
        out_root=tmp_path,
        checkout=checkout,
    )
    records, summary = _read(out)
    r = records[3]
    assert r["metrics"] == {} and r["checks"] is None
    assert r["abstention"] == {
        "abstained": True, "passed": True, "false_abstention": None, "label": None
    }  # fmt: skip
    assert summary["meta"]["mode"] == "full"
    assert summary["groups"]["overall"]["ooc_pass"]["mean"] == 1.0


def test_heading_checked_against_pinned_file(setup, tmp_path):
    """AC-5: a stored heading absent from the pinned file fails headings_exist (not DB vs DB)."""
    conn, checkout, path_a, path_b, question = setup
    lookup = _rows(path_a, path_b, question)[0]
    ev = evidence.check([lookup], conn, checkout)
    page = checkout / CORPUS_PREFIX / path_a
    page.write_text("\n".join(page.read_text().split("\n")[:2]) + "\n", encoding="utf-8")
    out = run_mod.run(
        conn,
        [lookup],
        ev,
        FakeEmbedder(name=MODEL),
        FakeAnswerer("The handbook says so [1]."),
        meta=_meta("fake:answer", 1),
        out_root=tmp_path,
        checkout=checkout,
    )
    r = _read(out)[0][1]
    heading = r["retrieved"][0]["heading"]
    assert r["retrieved"][0]["path"] == path_a
    assert r["checks"]["headings_exist"] is False and r["checks"]["passed"] is False
    assert r["checks"]["missing_headings"] == [[r["citations"][0]["url_path"], heading]]


def test_stored_chunk_params_match_db():
    """AC-6: provenance read from the stored chunks; a wrong pin is reported as stale."""
    with connect() as conn:
        (want,) = conn.execute(
            "SELECT DISTINCT chunk_size, chunk_overlap, tokenizer, commit_sha FROM chunks"
        ).fetchall()
        params, sha = run_mod.stored_chunk_params(conn, want[3])
        assert (params["chunk_size"], params["chunk_overlap"], params["tokenizer"], sha) == want
        with pytest.raises(SystemExit, match="chunks are stale vs CORPUS.md"):
            run_mod.stored_chunk_params(conn, "0" * 40)


def test_dry_run_spends_nothing(monkeypatch, capsys):
    """AC-8: without --confirm, no model is built, nothing is run and no folder is written."""

    def boom(*_, **__):
        raise AssertionError("dry run must not build a model or run")

    monkeypatch.setattr(run_mod, "make_embedder", boom)
    monkeypatch.setattr(run_mod, "make_answerer", boom)
    monkeypatch.setattr(run_mod, "run", boom)
    before = set(EVAL_RUNS.iterdir()) if EVAL_RUNS.exists() else set()
    assert run_mod.main(["--limit", "2"]) == 0
    after = set(EVAL_RUNS.iterdir()) if EVAL_RUNS.exists() else set()
    assert after == before
    out = capsys.readouterr().out
    assert "2 rows" in out and "mode full" in out and "estimated cost" in out
    assert "Dry run: add CONFIRM=1 to spend." in out
