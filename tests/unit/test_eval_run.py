"""Cost estimate for the eval cost guard (spec 0004, AC-8)."""

import pytest

from handbook_rag.constants import EST_ANSWER_USD_PER_ROW
from handbook_rag.evaluation.evalset import Fact, Row
from handbook_rag.evaluation.run import estimate, to_run

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
