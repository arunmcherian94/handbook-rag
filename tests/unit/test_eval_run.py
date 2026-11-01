"""Cost estimate (AC-8), stored chunk provenance (AC-6) and retrieved tokens (AC-3) for the
eval runner (spec 0004)."""

import uuid

import pytest

from handbook_rag import ask
from handbook_rag.constants import (
    EST_ANSWER_USD_PER_ROW,
    EVAL_DEPTH,
    FUSION_DEPTH,
    RERANK_DEPTH,
    RRF_K,
)
from handbook_rag.evaluation.evalset import Fact, Row
from handbook_rag.evaluation.evidence import Evidence
from handbook_rag.evaluation.run import (
    baseline_change,
    baseline_mismatch,
    estimate,
    main,
    metadata,
    new_run_dir,
    parser,
    record,
    stored_chunk_params,
    to_run,
)
from handbook_rag.hybrid import FTS_SETTINGS
from handbook_rag.models import InputTooLong, describe_embedder

ROWS = [
    Row(1, "lookup", "hello world", ("a.md",), (Fact("F1", True, {"a.md": (1,)}),)),
    Row(2, "ooc-off-topic", "hello", expected="Sorry"),
]


def test_estimate_full_and_retrieval_only():
    """AC-8: answers cost per row in full mode, nothing in retrieval-only mode."""
    full = estimate(ROWS, retrieval_only=False, usd_per_1m=0.02)
    # Answerable "hello world" (2 tokens) is embedded twice, ooc "hello" (1) once.
    assert full["embed_tokens"] == 5
    assert full["answer_usd"] == pytest.approx(2 * EST_ANSWER_USD_PER_ROW)
    assert full["total_usd"] == pytest.approx(full["embed_usd"] + full["answer_usd"])
    assert estimate(ROWS, retrieval_only=True, usd_per_1m=0.02)["answer_usd"] == 0.0


def test_estimate_uses_the_price_passed():
    """Spec 0008 AC-5: embed cost is tokens x the given USD per 1M, not a constant."""
    assert estimate(ROWS, True, 0.13)["embed_usd"] == pytest.approx(5 * 0.13 / 1_000_000)
    assert estimate(ROWS, True, 0.0)["total_usd"] == 0.0


def test_estimate_counts_queries_as_sent():
    """Spec 0008 AC-3, AC-5: the estimate counts each question as sent, with Qwen's query
    instruction, and a query over the limit fails before anything is spent (AC-4)."""
    qwen = describe_embedder("deepinfra:Qwen/Qwen3-Embedding-8B@1536", kind="query")
    plain = estimate(ROWS, True, 0.01)["embed_tokens"]
    sent = estimate(ROWS, True, 0.01, lambda q: qwen.prepare([q])[0])["embed_tokens"]
    assert sent > plain + 2 * 15  # the instruction is ~20 tokens, twice for the answerable row
    with pytest.raises(InputTooLong, match="query 'word word"):
        qwen.prepare(["fine", "word " * 20_000])


def test_estimate_counts_two_query_embeds_per_answerable_row():
    """Spec 0006 AC-10: k=5 and depth-20 queries for answerable rows, one for ooc rows."""
    assert estimate(ROWS[:1], True, 0.02)["embed_tokens"] == 4
    assert estimate(ROWS[1:], False, 0.02)["embed_tokens"] == 1


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


def test_baseline_mismatch_allows_one_change():
    """Spec 0008 AC-6: the chunk config OR the embed model may change, not both; other keys
    must match, and answer keys count only when both runs answered."""
    base = {"eval_sha256": "e", "corpus_sha": "c", "embed_model": "m", "k": 5, "limit": None,
            "answer_model": "a", "system_prompt_sha256": "p", "config_id": "x"}  # fmt: skip
    assert baseline_mismatch(base, base | {"config_id": "y", "chunk_params": {}}) == []
    assert baseline_mismatch(base, base | {"embed_model": "n"}) == []
    assert baseline_mismatch(base, base | {"limit": 10}) == ["limit: baseline None, this run 10"]
    assert baseline_mismatch(base, base | {"answer_model": None, "system_prompt_sha256": "q"}) == []
    assert len(baseline_mismatch(base, base | {"system_prompt_sha256": "q"})) == 1
    both = baseline_mismatch(base, base | {"config_id": "y", "embed_model": "n"})
    assert both == [
        "config_id and embed_model changed together: baseline (x, m), this run (y, n); "
        "change one at a time (spec 0008 AC-6, spec 0011 AC-10)"
    ]


def test_baseline_change_names_the_one_change():
    """Spec 0008 AC-6: baseline_change reports chunk config, embed model, or None."""
    base = {"config_id": "x", "embed_model": "m"}
    assert baseline_change(base, base | {"config_id": "y"}) == "chunk config"
    assert baseline_change(base, base | {"embed_model": "n"}) == "embed model"
    assert baseline_change(base, base) is None
    assert baseline_change(base, {"config_id": "y", "embed_model": "n"}) is None


def test_baseline_mismatch_on_eval_depth():
    """Spec 0006 AC-6: a baseline with another (or no) eval_depth fails the compatibility check."""
    base = {"eval_sha256": "e", "corpus_sha": "c", "embed_model": "m", "k": 5, "limit": None,
            "eval_depth": EVAL_DEPTH}  # fmt: skip
    assert baseline_mismatch(base, base) == []
    assert baseline_mismatch(base, base | {"eval_depth": 10}) == [
        f"eval_depth: baseline {EVAL_DEPTH!r}, this run 10"
    ]
    old = {k: v for k, v in base.items() if k != "eval_depth"}
    assert len(baseline_mismatch(old, base)) == 1


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
    rec = record(conn, ROWS[0], ev, chunks, [], None)
    assert [c["tokens"] for c in rec["retrieved"]] == [7, 400]
    assert [c["heading_path"] for c in rec["retrieved"]] == [None, ["A", "B"]]  # AC-4
    assert rec["metrics"]["retrieved_tokens@1"] == 7
    assert rec["metrics"]["retrieved_tokens@5"] == 407


def _deep_setup(order):
    """Eight chunks on one page, chunk 0 relevant to F1; deep is the chunks in `order`."""
    doc = uuid.uuid4()
    ids = [uuid.uuid4() for _ in range(8)]
    chunks = [
        ask.Retrieved(n, ids[i], doc, "a", "H", "t", 0.1, 512, 64, "t", "sha")
        for n, i in enumerate(order, start=1)
    ]
    stored = [(cid, 10 + i, doc, "content/handbook/a.md", None) for i, cid in enumerate(ids)]
    ev = Evidence(relevant={(1, "F1"): frozenset({ids[0]})}, warnings=[])
    return stored, ev, chunks


def test_record_deep_agrees_with_k5_when_not_near_tie():
    """Spec 0006 AC-6: when the deep top-5 is the k=5 list, the k<=5 metrics from either list are
    equal, and the deep entries and required facts are recorded."""
    stored, ev, deep = _deep_setup([3, 0, 1, 2, 4, 5, 6, 7])
    rec = record(FakeConn(stored, stored), ROWS[0], ev, deep[:5], deep, None)
    assert rec["near_tie"] is False
    assert rec["required_facts"] == ["F1"]
    assert [d["rank"] for d in rec["deep"]] == list(range(1, 9))
    assert rec["deep"][1]["facts"] == ["F1"] and rec["deep"][1]["page_relevant"]
    assert rec["deep"][0]["tokens"] == 10 + 3
    assert rec["metrics"]["chunk_mrr"] == 0.5
    assert "chunk_hit@20" in rec["metrics"] and "chunk_hit@10" in rec["metrics"]
    ref = record(FakeConn(stored, stored), ROWS[0], ev, deep[:5], deep[:5], None)["metrics"]
    for key, value in ref.items():
        if not key.endswith(("@10", "@20")):
            assert rec["metrics"][key] == value, key


def test_record_flags_near_tie_and_scores_k5_list_for_low_ks():
    """Spec 0006 AC-6: a deep top-5 that differs from the retrieved list sets near_tie; the k<=5
    metrics still come from the k=5 list the model saw."""
    stored, ev, deep = _deep_setup([3, 0, 1, 2, 4, 5, 6, 7])
    seen = [deep[1], deep[0], deep[2], deep[3], deep[4]]
    rec = record(FakeConn(stored, stored), ROWS[0], ev, seen, deep, None)
    assert rec["near_tie"] is True
    assert rec["metrics"]["chunk_mrr"] == 1.0  # the k=5 list has the relevant chunk first
    assert rec["metrics"]["chunk_hit@1"] == 1


def test_record_ooc_has_no_deep():
    """Spec 0006 AC-6: an ooc row has no deep retrieval and is not a near tie."""
    stored, ev, chunks = _deep_setup([0, 1, 2, 3, 4])
    rec = record(FakeConn(stored), ROWS[1], ev, chunks, [], None)
    assert rec["deep"] == [] and rec["near_tie"] is False and rec["metrics"] == {}


def test_run_dir_is_created_dated_and_never_shared(tmp_path, monkeypatch):
    """Spec 0009, AC-3: the paid mains create the run folder before spending, as <date>-<8 hex>;
    a name that already exists raises rather than reusing another run's folder."""
    meta = {"timestamp": "2026-10-24T15:00:00+00:00"}
    out = new_run_dir(tmp_path, meta)
    assert out.is_dir() and out.parent == tmp_path
    assert out.name.startswith("2026-10-24-") and len(out.name) == len("2026-10-24-") + 8
    fixed = uuid.UUID(int=0)
    monkeypatch.setattr(uuid, "uuid4", lambda: fixed)
    new_run_dir(tmp_path, meta)
    with pytest.raises(FileExistsError):
        new_run_dir(tmp_path, meta)


def test_retriever_flag_defaults_to_dense_and_rejects_unknown():
    """Spec 0011 AC-8: --retriever is dense unless given; an unknown mode is a usage error."""
    assert parser().parse_args([]).retriever == "dense"
    assert parser().parse_args(["--retriever", "hybrid"]).retriever == "hybrid"
    with pytest.raises(SystemExit):
        parser().parse_args(["--retriever", "bm25"])


@pytest.mark.parametrize("retriever", ["fts", "hybrid"])
def test_full_mode_refused_for_non_dense_retriever(retriever):
    """Spec 0011 AC-8: hybrid enters the answer path only by ADR, so a non-dense retriever needs
    --retrieval-only; refused before any DB or model work."""
    with pytest.raises(SystemExit, match="needs --retrieval-only"):
        main(["--retriever", retriever])


def test_estimate_fts_embeds_nothing():
    """Spec 0011 AC-9: fts mode costs $0 to embed; dense and hybrid are unchanged."""
    fts = estimate(ROWS, True, 0.02, embeds=False)
    assert fts["embed_tokens"] == 0 and fts["embed_usd"] == 0.0 and fts["total_usd"] == 0.0
    assert estimate(ROWS, True, 0.02)["embed_tokens"] == 5


def test_metadata_records_retriever_per_mode():
    """Spec 0011 AC-9: dense records only the retriever; fts adds the FTS settings; hybrid adds
    the fusion settings too."""
    cfg = {"config_id": "c", "strategy": "s", "params": {"a": 1}, "tokenizer": "t"}
    dense = metadata("v", b"e", "sha", cfg, "m", None, 1, None)
    assert dense["retriever"] == "dense"
    assert not {"fts", "rrf_k", "fusion_depth"} & set(dense)
    fts = metadata("v", b"e", "sha", cfg, "m", None, 1, None, retriever="fts")
    assert fts["retriever"] == "fts" and fts["fts"] == FTS_SETTINGS
    assert "rrf_k" not in fts
    hyb = metadata("v", b"e", "sha", cfg, "m", None, 1, None, retriever="hybrid")
    assert hyb["retriever"] == "hybrid" and hyb["fts"] == FTS_SETTINGS
    assert hyb["rrf_k"] == RRF_K and hyb["fusion_depth"] == FUSION_DEPTH


def test_baseline_accepts_a_retriever_only_change():
    """Spec 0011 AC-10: a run differing only in retriever is accepted and named; a baseline
    without the key reads as dense."""
    base = {"eval_sha256": "e", "corpus_sha": "c", "embed_model": "m", "k": 5, "limit": None,
            "config_id": "x"}  # fmt: skip
    hybrid_run = base | {"retriever": "hybrid"}
    assert baseline_mismatch(base, hybrid_run) == []
    assert baseline_change(base, hybrid_run) == "retriever"
    assert baseline_mismatch(base, base | {"retriever": "dense"}) == []
    assert baseline_change(base, base | {"retriever": "dense"}) is None
    assert baseline_change(base | {"retriever": "fts"}, hybrid_run) == "retriever"


@pytest.mark.parametrize("other", [{"config_id": "y"}, {"embed_model": "n"}])
def test_baseline_refuses_retriever_with_another_change(other):
    """Spec 0011 AC-10: retriever plus the chunk config or the embed model is two changes."""
    base = {"eval_sha256": "e", "corpus_sha": "c", "embed_model": "m", "k": 5, "limit": None,
            "config_id": "x"}  # fmt: skip
    diff = baseline_mismatch(base, base | other | {"retriever": "hybrid"})
    assert len(diff) == 1
    assert "retriever" in diff[0] and "dense" in diff[0] and "hybrid" in diff[0]
    assert "spec 0011 AC-10" in diff[0]
    assert baseline_change(base, base | other | {"retriever": "hybrid"}) is None


def test_embed_model_is_not_an_axis_for_fts():
    """Spec 0011 AC-10: fts never uses the embedding model, so differing embed specs are not a
    change when either run is fts."""
    base = {"eval_sha256": "e", "corpus_sha": "c", "embed_model": "m", "k": 5, "limit": None,
            "config_id": "x"}  # fmt: skip
    fts = base | {"retriever": "fts", "embed_model": "n"}
    assert baseline_mismatch(base, fts) == []
    assert baseline_change(base, fts) == "retriever"
    assert baseline_change(fts, base) == "retriever"
    assert baseline_change(fts, fts | {"embed_model": "o"}) is None
    hyb = base | {"retriever": "hybrid", "embed_model": "n"}
    assert baseline_change(base, hyb) is None  # hybrid does embed: two changes


def test_keyless_baseline_is_dense_whatever_the_default(monkeypatch):
    """Spec 0011 AC-10: a baseline without the retriever key is dense, not DEFAULT_RETRIEVER."""
    import handbook_rag.evaluation.run as run_mod

    monkeypatch.setattr(run_mod, "DEFAULT_RETRIEVER", "hybrid", raising=False)
    base = {"embed_model": "m", "config_id": "x"}
    assert baseline_change(base, base | {"retriever": "hybrid"}) == "retriever"
    assert baseline_change(base, base | {"retriever": "dense"}) is None


def test_estimate_without_embeds_never_tokenizes():
    """Spec 0011 AC-9: embeds=False does not call sent or the tokenizer."""

    def boom(_):
        raise AssertionError("sent called")

    assert estimate(ROWS, True, 0.02, sent=boom, embeds=False)["embed_tokens"] == 0


RERANK = {
    "model": "deepinfra:Qwen/Qwen3-Reranker-4B",
    "endpoint": "https://example.invalid",
    "instruction": "Given a web search query, retrieve relevant passages that answer the query",
    "max_input_tokens": 32768,
    "template_tokens": 80,
    "usd_per_1m": 0.025,
    "price_source": "test",
}


def test_estimate_rerank_prices_depth_pairs_and_embeds_once():
    """Spec 0012 AC-9: rerank embeds each answerable question once (one vector serves the top 5
    and the deep list) and prices RERANK_DEPTH pairs per row at question + longest chunk +
    template tokens."""
    rows = [ROWS[0]]
    plain = estimate(rows, True, 0.02)
    cost = estimate(rows, True, 0.02, rerank=RERANK, chunk_tokens=512)
    assert cost["embed_tokens"] == plain["embed_tokens"] // 2
    q = plain["embed_tokens"] // 2
    assert cost["rerank_tokens"] == RERANK_DEPTH * (q + 512 + 80)
    assert cost["rerank_usd"] == pytest.approx(cost["rerank_tokens"] * 0.025 / 1_000_000)
    assert cost["total_usd"] == pytest.approx(cost["embed_usd"] + cost["rerank_usd"])
    assert plain["rerank_tokens"] == 0 and plain["rerank_usd"] == 0.0


def test_metadata_records_reranker_settings_and_no_fts():
    """Spec 0012 AC-9: a rerank run records the model, depth, instruction, limit and truncation
    handling, and no FTS settings; dense and hybrid metadata are unchanged."""
    cfg = {"config_id": "c", "strategy": "s", "params": {}, "tokenizer": "t"}
    m = metadata("v", b"e", "sha", cfg, "m", None, 1, None, retriever="rerank", rerank=RERANK)
    assert m["retriever"] == "rerank" and "fts" not in m and "rrf_k" not in m
    r = m["rerank"]
    assert r["model"] == RERANK["model"] and r["depth"] == RERANK_DEPTH
    assert r["instruction"] == RERANK["instruction"] and r["max_input_tokens"] == 32768
    assert r["truncation"] == "none; refuse over limit"
    assert "endpoint" not in r and "api_key" not in r
    assert "rerank" not in metadata("v", b"e", "sha", cfg, "m", None, 1, None)
    hyb = metadata("v", b"e", "sha", cfg, "m", None, 1, None, retriever="hybrid")
    assert "rerank" not in hyb and hyb["fts"] == FTS_SETTINGS
    with pytest.raises(ValueError, match="settings"):
        metadata("v", b"e", "sha", cfg, "m", None, 1, None, retriever="rerank")


def test_rerank_is_a_retriever_choice_and_needs_retrieval_only():
    """Spec 0012 AC-8: rerank is a --retriever choice, dense stays the default, and full mode
    refuses it."""
    assert parser().parse_args([]).retriever == "dense"
    assert parser().parse_args(["--retriever", "rerank"]).retriever == "rerank"
    with pytest.raises(SystemExit, match="needs --retrieval-only"):
        main(["--retriever", "rerank"])


def test_baseline_accepts_a_rerank_only_change():
    """Spec 0012 AC-9, AC-12: a dense baseline (d83f3edc has no retriever key) against a rerank
    run is the one retriever change; rerank with a new embed model is two changes."""
    base = {"config_id": "c", "embed_model": "m"}
    run = base | {"retriever": "rerank"}
    assert baseline_mismatch(base, run) == [] and baseline_change(base, run) == "retriever"
    assert baseline_change(base, run | {"embed_model": "n"}) is None


def test_record_rerank_keeps_every_candidate_with_both_ranks():
    """Spec 0012 AC-9, AC-11: a rerank row records all candidates in dense order with their
    dense and rerank ranks, scores and facts, plus latencies and the reranker's tokens; the
    retrieved entries carry rerank_score."""
    from handbook_rag import hybrid

    stored, ev, plain = _deep_setup([0, 1, 2, 3, 4, 5, 6, 7])
    dense = [hybrid.Ranked(**vars(c), dense_rank=c.n, rerank_score=float(c.n)) for c in plain]
    order = sorted(dense, key=lambda c: -c.rerank_score)
    reranked = [hybrid.Ranked(**(vars(c) | {"n": n})) for n, c in enumerate(order, 1)]
    lists = hybrid.RerankLists(dense, reranked, 3.0, 400.0, 4800, 0)
    rec = record(FakeConn(stored, stored), ROWS[0], ev, reranked[:5], reranked, None, rerank=lists)
    cands = rec["candidates"]
    assert [c["dense_rank"] for c in cands] == list(range(1, 9))
    assert [c["rerank_rank"] for c in cands] == list(range(8, 0, -1))
    assert cands[0]["facts"] == ["F1"] and cands[0]["rerank_score"] == 1.0
    assert rec["latency_ms"] == {"dense": 3.0, "rerank": 400.0}
    assert rec["rerank"] == {"input_tokens": 4800, "pairs": 8, "pairs_over": 0}
    assert all("rerank_score" in e for e in rec["retrieved"] + rec["deep"])
    assert rec["metrics"]["chunk_fact_recall@5"] == 0.0  # F1's chunk fell to rerank rank 8


def test_run_rerank_without_a_reranker_fails_before_embedding(tmp_path):
    """Spec 0012 AC-1, AC-3 (review fix): run() in rerank mode with no reranker raises before
    anything is embedded or written."""
    from fakes import FakeEmbedder

    from handbook_rag.evaluation import run as run_mod

    emb = FakeEmbedder()
    with pytest.raises(ValueError, match="needs a reranker"):
        run_mod.run(
            None, ROWS, Evidence({}, []), emb, None, principal=None, meta={},
            out=tmp_path, retriever="rerank",
        )  # fmt: skip
    assert emb.calls == []
