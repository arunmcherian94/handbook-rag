"""Cost estimate (AC-8), stored chunk provenance (AC-6) and retrieved tokens (AC-3) for the
eval runner (spec 0004)."""

import uuid

import pytest

from handbook_rag import ask
from handbook_rag.constants import EST_ANSWER_USD_PER_ROW
from handbook_rag.evaluation.evalset import Fact, Row
from handbook_rag.evaluation.evidence import Evidence
from handbook_rag.evaluation.run import (
    baseline_mismatch,
    estimate,
    metadata,
    record,
    stored_chunk_params,
    to_run,
)

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
    """execute() returns successive scripted result sets; each is served by fetchone/fetchall."""

    def __init__(self, *results):
        self.results = list(results)
        self.current = []

    def execute(self, *_):
        self.current = self.results.pop(0)
        return self

    def fetchall(self):
        return self.current

    def fetchone(self):
        return self.current[0] if self.current else None


CFG = [("fixed", {"size": 512, "overlap": 64}, "tok")]


def test_stored_chunk_params_from_db():
    """AC-4, AC-6: the config row and corpus SHA are the stored values, not constants."""
    params, sha = stored_chunk_params(FakeConn(CFG, [("abc",)]), "abc", "fixed-512-64")
    assert params == {
        "config_id": "fixed-512-64",
        "strategy": "fixed",
        "params": {"size": 512, "overlap": 64},
        "tokenizer": "tok",
    }
    assert sha == "abc"


def test_stored_chunk_params_unknown_config():
    """AC-4: a config with no chunk_configs row fails."""
    with pytest.raises(SystemExit, match="unknown config"):
        stored_chunk_params(FakeConn([]), "abc", "nope")


def test_stored_chunk_params_no_chunks():
    """AC-4: a registered config without chunks fails."""
    with pytest.raises(SystemExit, match="has no chunks"):
        stored_chunk_params(FakeConn(CFG, []), "abc", "x")


@pytest.mark.parametrize("shas", [[("old",)], [("abc",), ("old",)]])
def test_stored_chunk_params_stale(shas):
    """AC-6: chunks from any other commit than the pin fail."""
    with pytest.raises(SystemExit, match="chunks are stale vs CORPUS.md"):
        stored_chunk_params(FakeConn(CFG, shas), "abc", "x")


def test_metadata_records_config():
    """AC-12: run metadata has config_id and the config's params, strategy and tokenizer."""
    cfg = {"config_id": "c", "strategy": "s", "params": {"a": 1}, "tokenizer": "t"}
    meta = metadata("v", b"e", "sha", cfg, "m", None, 1, None)
    assert meta["config_id"] == "c"
    assert meta["chunk_params"] == {"strategy": "s", "a": 1, "tokenizer": "t"}


def test_baseline_mismatch_allows_only_the_chunk_config():
    """AC-11: a baseline that differs in more than the chunk config is reported; answer keys
    count only when both runs answered."""
    base = {"eval_sha256": "e", "corpus_sha": "c", "embed_model": "m", "k": 5, "limit": None,
            "answer_model": "a", "system_prompt_sha256": "p", "config_id": "x"}  # fmt: skip
    assert baseline_mismatch(base, base | {"config_id": "y", "chunk_params": {}}) == []
    assert baseline_mismatch(base, base | {"limit": 10}) == ["limit: baseline None, this run 10"]
    assert baseline_mismatch(base, base | {"answer_model": None, "system_prompt_sha256": "q"}) == []
    assert len(baseline_mismatch(base, base | {"system_prompt_sha256": "q"})) == 1


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
        [
            (ids[1], 400, doc, "content/handbook/a.md", ["A", "B"]),
            (ids[0], 7, doc, "content/handbook/a.md", None),
        ]
    )
    ev = Evidence(relevant={(1, "F1"): frozenset({ids[1]})}, warnings=[])
    rec = record(conn, ROWS[0], ev, chunks, None)
    assert [c["tokens"] for c in rec["retrieved"]] == [7, 400]
    assert [c["heading_path"] for c in rec["retrieved"]] == [None, ["A", "B"]]  # AC-4
    assert rec["metrics"]["retrieved_tokens@1"] == 7
    assert rec["metrics"]["retrieved_tokens@5"] == 407
