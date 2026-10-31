import inspect
import uuid

import pytest
from fakes import FakeReranker, make_principal

from handbook_rag import ask, hybrid
from handbook_rag.constants import FUSION_DEPTH, RERANK_DEPTH, RERANK_TOKEN_MARGIN, RRF_K
from handbook_rag.models import RerankResult


def cid(i: int) -> uuid.UUID:
    return uuid.UUID(int=i)


def dense_row(i: int, n: int, distance: float = 0.1, content: str = "d") -> ask.Retrieved:
    return ask.Retrieved(
        n, cid(i), cid(900), "/handbook/x/", "H", content, distance, 512, 64, "t", "sha"
    )


def fts_row(i: int, n: int, score: float = 1.5) -> hybrid.Ranked:
    return hybrid.Ranked(
        n, cid(i), cid(900), "/handbook/x/", "H", "f", None, 512, 64, "t", "sha",
        fts_rank=n, fts_score=score,
    )  # fmt: skip


def ids(rows) -> list[uuid.UUID]:
    return [r.chunk_id for r in rows]


def test_fuse_rrf_arithmetic():
    """Spec 0011, AC-5: score is the sum of 1/(RRF_K + rank) over the lists a chunk is in."""
    dense = [dense_row(1, 1), dense_row(2, 2), dense_row(3, 3)]
    fts = [fts_row(3, 1), fts_row(1, 2), fts_row(4, 3)]
    got = {r.chunk_id: r for r in hybrid.fuse(dense, fts, 10)}
    assert got[cid(1)].rrf_score == pytest.approx(1 / (RRF_K + 1) + 1 / (RRF_K + 2))
    assert got[cid(3)].rrf_score == pytest.approx(1 / (RRF_K + 3) + 1 / (RRF_K + 1))
    assert got[cid(2)].rrf_score == pytest.approx(1 / (RRF_K + 2))
    assert got[cid(4)].rrf_score == pytest.approx(1 / (RRF_K + 3))
    assert RRF_K == 60


def test_fuse_orders_by_score_and_numbers_from_one():
    """Spec 0011, AC-5: output is by descending score, n is the 1-based fused rank."""
    dense = [dense_row(1, 1), dense_row(2, 2), dense_row(3, 3)]
    fts = [fts_row(3, 1), fts_row(1, 2), fts_row(4, 3)]
    got = hybrid.fuse(dense, fts, 10)
    assert [r.n for r in got] == [1, 2, 3, 4]
    scores = [r.rrf_score for r in got]
    assert scores == sorted(scores, reverse=True)
    assert ids(got)[:2] == [cid(1), cid(3)]


def test_fuse_tie_goes_to_better_dense_rank():
    """Spec 0011, AC-5: a dense-only and an fts-only chunk at the same rank tie on score; the
    dense one comes first, whichever list is built first."""
    got = hybrid.fuse([dense_row(7, 2)], [fts_row(1, 1), fts_row(2, 2)], 10)
    assert got[1].rrf_score == got[2].rrf_score
    assert ids(got) == [cid(1), cid(7), cid(2)]


def test_fuse_dense_absent_sorts_after_dense_found():
    """Spec 0011, AC-5: on equal score, a chunk the dense list lacks sorts after any dense one,
    even with a smaller chunk_id."""
    got = hybrid.fuse([dense_row(50, 3)], [fts_row(1, 3)], 10)
    assert ids(got) == [cid(50), cid(1)]
    assert got[1].dense_rank is None


def test_fuse_final_tie_is_str_chunk_id():
    """Spec 0011, AC-5: both dense-absent with equal scores, the order is by str(chunk_id)."""
    fts = [fts_row(9, 1), fts_row(2, 1), fts_row(5, 1)]
    got = hybrid.fuse([], fts, 10)
    assert ids(got) == sorted((cid(9), cid(2), cid(5)), key=str)


def test_fuse_single_list_chunks_carry_none_for_the_other():
    """Spec 0011, AC-5: a chunk in one list has None for the other list's rank."""
    got = {r.chunk_id: r for r in hybrid.fuse([dense_row(1, 1)], [fts_row(2, 1)], 10)}
    assert (got[cid(1)].dense_rank, got[cid(1)].fts_rank) == (1, None)
    assert (got[cid(2)].dense_rank, got[cid(2)].fts_rank) == (None, 1)
    assert got[cid(1)].fts_score is None
    assert got[cid(2)].fts_score == 1.5


def test_fuse_empty_fts_equals_dense_order():
    """Spec 0011, AC-5: with no FTS hits the fused order is the dense order, dense_rank == n."""
    dense = [dense_row(i, n) for n, i in enumerate((5, 3, 8, 1), 1)]
    got = hybrid.fuse(dense, [], 10)
    assert ids(got) == ids(dense)
    assert [r.dense_rank for r in got] == [r.n for r in got] == [1, 2, 3, 4]
    assert all(r.fts_rank is None for r in got)


def test_fuse_cuts_to_k():
    """Spec 0011, AC-5: only the top k fused rows are returned."""
    dense = [dense_row(i, i) for i in range(1, 8)]
    got = hybrid.fuse(dense, [fts_row(20, 1)], 3)
    assert len(got) == 3
    assert [r.n for r in got] == [1, 2, 3]


def test_fuse_dense_row_wins_fields_and_fts_score_carried():
    """Spec 0011, AC-5: for a chunk in both lists the dense row's distance and fields win, and
    the FTS list's score is carried."""
    got = hybrid.fuse(
        [dense_row(1, 2, distance=0.25, content="dense text")], [fts_row(1, 1, 3.5)], 5
    )
    (r,) = got
    assert r.distance == 0.25
    assert r.content == "dense text"
    assert (r.dense_rank, r.fts_rank, r.fts_score) == (2, 1, 3.5)


def test_sql_has_no_tsquery_parsers():
    """Spec 0011, AC-2 (text pin; behaviour is in the integration test): the query is built
    from quoted lexemes, never parsed from user text by a tsquery parser."""
    for sql in (hybrid.FTS_SEARCH, hybrid.QUERY):
        for bad in ("websearch_to_tsquery", "plainto_tsquery", "phraseto_tsquery", "to_tsquery("):
            assert bad not in sql
        for good in ("quote_literal", "tsvector_to_array", "to_tsvector('english'", "' | '"):
            assert good in sql


def test_fts_search_sql_ordering_and_config_scope():
    """Spec 0011, AC-3: ranked by ts_rank_cd, chunk_id breaks ties, scoped to one config."""
    assert "ts_rank_cd(c.fts, q.query) DESC, c.chunk_id" in hybrid.FTS_SEARCH
    assert "c.config_id = %(config_id)s" in hybrid.FTS_SEARCH


@pytest.mark.parametrize("fn", [hybrid.search_fts, hybrid.search, hybrid.retrieve])
def test_principal_is_required_without_default(fn):
    """Spec 0011, AC-3/AC-4: no retrieval entry point has a default principal."""
    p = inspect.signature(fn).parameters["principal"]
    assert p.default is inspect.Parameter.empty


def test_retrieve_fts_never_embeds(monkeypatch):
    """Spec 0011, AC-9: fts mode embeds nothing, so embedder may be None."""
    seen = {}

    def fake_fts(conn, question, principal, k, config_id):
        seen.update(question=question, k=k, config_id=config_id)
        return ["row"]

    def boom(*a, **kw):
        raise AssertionError("embedded in fts mode")

    monkeypatch.setattr(hybrid, "search_fts", fake_fts)
    monkeypatch.setattr(hybrid, "embed_with_retry", boom)
    got = hybrid.retrieve(None, "fts", None, "pto policy", make_principal("staff"), 4, "cfg")
    assert got == ["row"]
    assert seen == {"question": "pto policy", "k": 4, "config_id": "cfg"}


def test_retrieve_dense_delegates_to_ask_retrieve(monkeypatch):
    """Spec 0011, AC-7: dense mode is ask.retrieve itself."""
    calls = []

    def fake(conn, embedder, question, principal, k, sleep, rand, config_id):
        calls.append((embedder, question, k, config_id))
        return ["dense"]

    monkeypatch.setattr(ask, "retrieve", fake)
    got = hybrid.retrieve(None, "dense", "E", "q?", make_principal("staff"), 7, "cfg")
    assert got == ["dense"]
    assert calls == [("E", "q?", 7, "cfg")]


def test_search_unknown_retriever_raises():
    """Spec 0011, AC-9: an unknown retriever is a ValueError naming the choices."""
    with pytest.raises(ValueError, match="dense, fts, hybrid"):
        hybrid.search(None, "bm25", None, "q", "m", make_principal("staff"), 5)


@pytest.mark.parametrize("k", [5, FUSION_DEPTH + 10])
def test_hybrid_search_retrieves_both_lists_to_fusion_depth(monkeypatch, k):
    """Spec 0011, AC-5: both lists are retrieved to max(k, FUSION_DEPTH) before fusing."""
    depths = {}

    def fake_dense(conn, q, model, principal, depth, config_id):
        depths["dense"] = depth
        return [dense_row(1, 1)]

    def fake_fts(conn, question, principal, depth, config_id):
        depths["fts"] = depth
        return [fts_row(2, 1)]

    monkeypatch.setattr(ask, "search", fake_dense)
    monkeypatch.setattr(hybrid, "search_fts", fake_fts)
    got = hybrid.search(None, "hybrid", "[0]", "q", "m", make_principal("staff"), k)
    assert depths == {"dense": max(k, FUSION_DEPTH), "fts": max(k, FUSION_DEPTH)}
    assert set(ids(got)) == {cid(1), cid(2)}


def _dense_list(contents):
    return [dense_row(i, i, content=c) for i, c in enumerate(contents, 1)]


def _rerank(monkeypatch, contents, reranker, clock=None, question="q"):
    monkeypatch.setattr(ask, "search", lambda *a: _dense_list(contents))
    kw = {"clock": clock} if clock else {}
    return hybrid.rerank_lists(None, reranker, "[1]", question, "m", make_principal("staff"), **kw)


def test_rerank_sorts_by_score_and_keeps_dense_rank(monkeypatch):
    """Spec 0012, AC-3: reranked is by score descending, n is the new rank, dense_rank is kept
    and every result carries rerank_score."""
    fake = FakeReranker(score=lambda q, d: {"a": 1, "b": 3, "c": 2}[d])
    got = _rerank(monkeypatch, ["a", "b", "c"], fake).reranked
    assert ids(got) == [cid(2), cid(3), cid(1)]
    assert [r.n for r in got] == [1, 2, 3]
    assert [r.dense_rank for r in got] == [2, 3, 1]
    assert [r.rerank_score for r in got] == [3.0, 2.0, 1.0]


def test_rerank_equal_scores_break_by_dense_rank(monkeypatch):
    """Spec 0012, AC-3: equal scores keep dense order."""
    got = _rerank(monkeypatch, ["a", "b", "c"], FakeReranker(score=lambda q, d: 1)).reranked
    assert ids(got) == [cid(1), cid(2), cid(3)]


def test_rerank_search_cuts_to_k(monkeypatch):
    """Spec 0012, AC-3: search() returns the reranked top k."""
    monkeypatch.setattr(ask, "search", lambda *a: _dense_list(["a", "b", "c"]))
    fake = FakeReranker(score=lambda q, d: {"a": 1, "b": 3, "c": 2}[d])
    got = hybrid.search(None, "rerank", "[1]", "q", "m", make_principal("s"), 2, reranker=fake)
    assert ids(got) == [cid(2), cid(3)]


def test_rerank_dense_list_keeps_dense_order_with_scores(monkeypatch):
    """Spec 0012, AC-3: the dense list is in dense order, n = dense rank, scored; it is fetched
    once to RERANK_DEPTH."""
    depths = []

    def fake_dense(conn, q, model, principal, depth, config_id):
        depths.append(depth)
        return _dense_list(["a", "b"])

    monkeypatch.setattr(ask, "search", fake_dense)
    fake = FakeReranker(score=lambda q, d: {"a": 1, "b": 3}[d])
    lists = hybrid.rerank_lists(None, fake, "[1]", "q", "m", make_principal("s"))
    assert depths == [RERANK_DEPTH]
    assert ids(lists.dense) == [cid(1), cid(2)]
    assert [(r.n, r.dense_rank, r.rerank_score) for r in lists.dense] == [(1, 1, 1.0), (2, 2, 3.0)]
    assert lists.input_tokens == 42 and lists.pairs_over == 0


def test_rerank_empty_dense_makes_no_call(monkeypatch):
    """Spec 0012, AC-3: no candidates, no rerank call."""
    fake = FakeReranker()
    lists = _rerank(monkeypatch, [], fake)
    assert (lists.dense, lists.reranked, lists.input_tokens, lists.pairs_over) == ([], [], 0, 0)
    assert fake.calls == []


def test_rerank_pair_too_long_raises_before_any_call(monkeypatch):
    """Spec 0012, AC-4: an oversized pair raises PairTooLong naming the chunk; nothing is sent
    and nothing is truncated."""
    fake = FakeReranker()
    fake.max_input_tokens = 200
    with pytest.raises(hybrid.PairTooLong) as e:
        _rerank(monkeypatch, ["short", "word " * 400], fake)
    assert e.value.chunk_id == cid(2)
    assert fake.calls == []


def test_rerank_estimate_applies_template_and_margin(monkeypatch):
    """Spec 0012, AC-4: (question + content + template) tokens x margin against the limit."""
    fake = FakeReranker()
    q_and_doc = 1 + 1  # "q" and "d" are one cl100k token each
    fake.max_input_tokens = (q_and_doc + fake.template_tokens) * RERANK_TOKEN_MARGIN
    assert len(_rerank(monkeypatch, ["d"], fake).reranked) == 1
    fake.max_input_tokens -= 1
    with pytest.raises(hybrid.PairTooLong):
        _rerank(monkeypatch, ["d"], fake)


def test_rerank_failure_propagates_without_fallback(monkeypatch):
    """Spec 0012, AC-3: a reranker error is raised, never replaced by the dense order."""
    fake = FakeReranker(fail=RuntimeError("provider down"))
    with pytest.raises(RuntimeError, match="provider down"):
        _rerank(monkeypatch, ["a", "b"], fake)


def test_rerank_score_count_mismatch_raises(monkeypatch):
    """Spec 0012, AC-3: a score list of the wrong length is an error, not a partial order."""
    fake = FakeReranker()
    fake.rerank = lambda q, docs: RerankResult([1.0], None)
    with pytest.raises(ValueError, match="1 scores for 2"):
        _rerank(monkeypatch, ["a", "b"], fake)


def test_rerank_search_needs_a_reranker():
    """Spec 0012, AC-3: the rerank mode without a reranker is a ValueError."""
    with pytest.raises(ValueError, match="needs a reranker"):
        hybrid.search(None, "rerank", "[1]", "q", "m", make_principal("s"), 5)


def test_rerank_timings_come_from_the_clock(monkeypatch):
    """Spec 0012, AC-3: dense_ms and rerank_ms are the clock's deltas in milliseconds."""
    ticks = iter([0.0, 0.25, 1.0, 3.0])
    got = _rerank(monkeypatch, ["a"], FakeReranker(), clock=lambda: next(ticks))
    assert (got.dense_ms, got.rerank_ms) == (250.0, 2000.0)


def test_other_modes_ignore_the_reranker(monkeypatch):
    """Spec 0012, AC-7: dense, fts and hybrid dispatch as before and never call the reranker."""
    fake = FakeReranker()
    monkeypatch.setattr(ask, "search", lambda *a: _dense_list(["a", "b"]))
    monkeypatch.setattr(hybrid, "search_fts", lambda *a: [fts_row(2, 1)])
    p = make_principal("s")
    dense = hybrid.search(None, "dense", "[1]", "q", "m", p, 2, reranker=fake)
    assert ids(dense) == [cid(1), cid(2)]
    assert ids(hybrid.search(None, "fts", None, "q", "m", p, 2, reranker=fake)) == [cid(2)]
    assert ids(hybrid.search(None, "hybrid", "[1]", "q", "m", p, 2, reranker=fake))[0] == cid(2)
    assert fake.calls == []


def test_worst_pair_bounds_the_longest_question_with_the_longest_chunk():
    """Spec 0012 AC-4 (review fix): the dry-run bound is (longest question + longest chunk +
    template) x RERANK_TOKEN_MARGIN, in cl100k tokens."""
    from handbook_rag.constants import RERANK_TOKEN_MARGIN

    short, long = "a", "one two three four five"
    assert hybrid.worst_pair([short, long], 512, 80) == (5 + 512 + 80) * RERANK_TOKEN_MARGIN
    assert hybrid.worst_pair([], 512, 80) == (512 + 80) * RERANK_TOKEN_MARGIN


def test_rerank_tokens_counts_depth_pairs_per_search():
    """Spec 0012 AC-9 (review fix: one helper for both runners): each search scores RERANK_DEPTH
    pairs at question + longest chunk + template tokens."""
    from handbook_rag.constants import RERANK_DEPTH

    assert hybrid.rerank_tokens({"a": 1, "one two": 2}, 512, 80) == RERANK_DEPTH * (
        (1 + 512 + 80) + 2 * (2 + 512 + 80)
    )
    assert hybrid.rerank_tokens({}, 512, 80) == 0


def test_rerank_preflight_exits_over_the_limit_and_reports_under_it():
    """Spec 0012 AC-4, AC-9 (review fix): the dry-run line names the model, depth, tokens, cost and
    longest pair; a pair over the limit exits before any spend."""
    rerank = {"model": "m", "template_tokens": 80, "max_input_tokens": 1000, "usd_per_1m": 0.025}
    rerank |= {"price_source": "test"}
    line = hybrid.rerank_preflight(["a"], rerank, 512, 1_000_000)
    assert "m, depth 50" in line and "$0.0250" in line and "of 1000 tokens" in line
    with pytest.raises(SystemExit, match="over the reranker's 1000"):
        hybrid.rerank_preflight(["a"], rerank, 700, 0)
