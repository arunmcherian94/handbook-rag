"""Cost estimate (AC-8) and stored chunk provenance (AC-6) for the eval runner (spec 0004)."""

import pytest

from handbook_rag.constants import EST_ANSWER_USD_PER_ROW
from handbook_rag.evaluation.evalset import Fact, Row
from handbook_rag.evaluation.run import estimate, stored_chunk_params, to_run

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
