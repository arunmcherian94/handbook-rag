"""Cost estimate (AC-8), stored chunk provenance (AC-6) and retrieved tokens (AC-3) for the
eval runner (spec 0004)."""

import uuid

import pytest

from handbook_rag import ask
from handbook_rag.constants import EST_ANSWER_USD_PER_ROW
from handbook_rag.evaluation.evalset import Fact, Row
from handbook_rag.evaluation.evidence import Evidence
from handbook_rag.evaluation.run import estimate, record, stored_chunk_params, to_run

ROWS = [
    Row(1, "lookup", "hello world", ("a.md",), (Fact("F1", True, {"a.md": (1,)}),)),
    Row(2, "ooc-off-topic", "hello", expected="Sorry"),
]


def test_estimate_full_and_retrieval_only():
    """AC-8: answers cost per row in full mode, nothing in retrieval-only mode."""
    full = estimate(ROWS, retrieval_only=False)
    assert full["embed_tokens"] == 3  # "hello", " world", "hello" in cl100k
    assert full["answer_usd"] == pytest.approx(2 * EST_ANSWER_USD_PER_ROW)
    assert full["total_usd"] == pytest.approx(full["embed_usd"] + full["answer_usd"])
    assert estimate(ROWS, retrieval_only=True)["answer_usd"] == 0.0


def test_retrieval_only_skips_ooc_rows():
    """AC-8: retrieval-only mode runs answerable rows only."""
    assert [r.id for r in to_run(ROWS, True)] == [1]
    assert [r.id for r in to_run(ROWS, False)] == [1, 2]


class FakeConn:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, *_):
        return self

    def fetchall(self):
        return self.rows


def test_stored_chunk_params_from_db():
    """AC-6: chunk params and corpus SHA are the stored values, not constants."""
    params, sha = stored_chunk_params(FakeConn([(512, 64, "tok", "abc")]), "abc")
    assert params == {"chunk_size": 512, "chunk_overlap": 64, "tokenizer": "tok"}
    assert sha == "abc"


@pytest.mark.parametrize("rows", [[], [(512, 64, "tok", "abc"), (256, 64, "tok", "abc")]])
def test_stored_chunk_params_not_exactly_one_set(rows):
    """AC-6: zero or several stored parameter sets fail."""
    with pytest.raises(SystemExit, match=f"holds {len(rows)} parameter sets"):
        stored_chunk_params(FakeConn(rows), "abc")


def test_stored_chunk_params_stale():
    """AC-6: chunks from another commit than the pin fail."""
    with pytest.raises(SystemExit, match="chunks are stale vs CORPUS.md"):
        stored_chunk_params(FakeConn([(512, 64, "tok", "old")]), "abc")


def test_record_uses_stored_token_counts():
    """AC-3: retrieved tokens are the stored chunks.token_count, in rank order, not a
    re-encoding of the content."""
    doc = uuid.uuid4()
    ids = [uuid.uuid4(), uuid.uuid4()]
    chunks = [
        ask.Retrieved(n, cid, doc, "a", "H", "one two three", 0.1, 512, 64, "t", "sha")
        for n, cid in enumerate(ids, start=1)
    ]
    # DB rows in a different order from the ranks.
    conn = FakeConn(
        [(ids[1], 400, doc, "content/handbook/a.md"), (ids[0], 7, doc, "content/handbook/a.md")]
    )
    ev = Evidence(relevant={(1, "F1"): frozenset({ids[1]})}, warnings=[])
    rec = record(conn, ROWS[0], ev, chunks, None)
    assert [c["tokens"] for c in rec["retrieved"]] == [7, 400]
    assert rec["metrics"]["retrieved_tokens@1"] == 7
    assert rec["metrics"]["retrieved_tokens@5"] == 407
