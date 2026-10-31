import math

import pytest

from handbook_rag.evaluation.metrics import (
    Stat,
    all_required_at,
    best_top_k,
    fact_recall_at,
    first_page_hits,
    hit_at,
    mean_se,
    mrr,
    ndcg_at,
    row_metrics,
)

T, F = True, False


def test_hit_at():
    """AC-3: hit@k is 1.0 when any of the top k is relevant."""
    rel = [F, F, T]
    assert hit_at(rel, 1) == 0.0
    assert hit_at(rel, 2) == 0.0
    assert hit_at(rel, 3) == 1.0


def test_hit_at_k_beyond_list_and_no_relevant():
    """AC-3: k past the list end uses the whole list; nothing relevant gives 0.0."""
    assert hit_at([F, T], 5) == 1.0
    assert hit_at([F, F, F], 5) == 0.0
    assert hit_at([], 5) == 0.0


def test_mrr():
    """AC-3: MRR is 1 / rank of the first relevant item, 0.0 if none."""
    assert mrr([T, T]) == 1.0
    assert mrr([F, F, T, T]) == pytest.approx(1 / 3)
    assert mrr([F, F]) == 0.0
    assert mrr([]) == 0.0


def test_ndcg_hand_worked_rank_3():
    """AC-3, AC-9: one relevant item at rank 3 of one, k=5 -> 0.50."""
    assert round(ndcg_at([F, F, T, F, F], 5, 1), 2) == 0.50


def test_ndcg_hand_worked_ranks_1_and_4():
    """AC-3, AC-9: relevant at ranks 1 and 4 of two, k=5 -> 0.88."""
    assert round(ndcg_at([T, F, F, T, F], 5, 2), 2) == 0.88


def test_ndcg_edges():
    """AC-3: perfect ranking is 1.0; nothing relevant or n_relevant 0 gives 0.0; ideal is capped
    at k; ranks past k don't count."""
    assert ndcg_at([T, T, F], 5, 2) == pytest.approx(1.0)
    assert ndcg_at([F, F, F], 5, 2) == 0.0
    assert ndcg_at([T, F], 5, 0) == 0.0
    assert ndcg_at([T, T], 2, 10) == pytest.approx(1.0)  # ideal = min(10, 2) ones
    assert ndcg_at([F, F, T], 2, 1) == 0.0


def test_fact_recall_counts_a_fact_once():
    """AC-3: a fact covered by two chunks counts once."""
    chunk_facts = [{"f1"}, {"f1"}, set()]
    assert fact_recall_at(chunk_facts, {"f1", "f2"}, 3) == 0.5


def test_fact_recall_at_k():
    """AC-3: only the top k count; k past the list end uses the whole list."""
    chunk_facts = [set(), {"f1"}, {"f2", "f1"}]
    req = {"f1", "f2"}
    assert fact_recall_at(chunk_facts, req, 1) == 0.0
    assert fact_recall_at(chunk_facts, req, 2) == 0.5
    assert fact_recall_at(chunk_facts, req, 3) == 1.0
    assert fact_recall_at(chunk_facts, req, 10) == 1.0


def test_fact_recall_ignores_non_required_facts():
    """AC-3: facts outside required don't raise recall."""
    assert fact_recall_at([{"opt"}, {"f1"}], {"f1", "f2"}, 5) == 0.5


def test_fact_recall_empty_required_raises():
    """AC-3: an answerable row always has a required fact; empty is a bug."""
    with pytest.raises(ValueError):
        fact_recall_at([{"f1"}], set(), 5)


def test_all_required_at():
    """AC-3: 1.0 only when every required fact is covered in the top k."""
    chunk_facts = [{"f1"}, set(), {"f2"}]
    req = {"f1", "f2"}
    assert all_required_at(chunk_facts, req, 2) == 0.0
    assert all_required_at(chunk_facts, req, 3) == 1.0
    assert all_required_at(chunk_facts, req, 10) == 1.0
    assert all_required_at([set(), set()], req, 5) == 0.0


def test_first_page_hits_duplicate_page():
    """AC-3: a page counts once, at its best rank; non-targets are False."""
    pages = ["x", "a", "a", "b", "x", "b"]
    assert first_page_hits(pages, {"a", "b"}) == [F, T, F, T, F, F]
    assert first_page_hits([], {"a"}) == []


def test_row_metrics_hand_worked():
    """AC-3: every key of one row, worked by hand.

    ranks:   1      2      3      4      5
    facts:   -      f1     f1     f2     -
    page:    x      a      a      c      b
    f1 cites a; f2 cites b OR c. expected_docs = {a, b}; 3 relevant chunks in the corpus.
    """
    lg = lambda i: 1 / math.log2(i + 1)  # noqa: E731
    got = row_metrics(
        chunk_facts=[set(), {"f1"}, {"f1"}, {"f2"}, set()],
        pages=["x", "a", "a", "c", "b"],
        required={"f1": {"a"}, "f2": {"b", "c"}},
        expected_docs={"a", "b"},
        n_relevant_chunks=3,
        token_counts=[100, 200, 300, 400, 500],
        ks=(1, 3, 5),
    )
    expected = {
        "chunk_fact_recall@1": 0.0,
        "chunk_fact_recall@3": 0.5,
        "chunk_fact_recall@5": 1.0,
        "chunk_all_required@1": 0.0,
        "chunk_all_required@3": 0.0,
        "chunk_all_required@5": 1.0,
        "chunk_hit@1": 0.0,
        "chunk_hit@3": 1.0,
        "chunk_hit@5": 1.0,
        "chunk_mrr": 0.5,
        # rel at 2, 3, 4; ideal 3 ones first
        "chunk_ndcg@5": (lg(2) + lg(3) + lg(4)) / (lg(1) + lg(2) + lg(3)),  # 0.7328
        "page_fact_recall@1": 0.0,
        "page_fact_recall@3": 0.5,
        "page_fact_recall@5": 1.0,  # f2 via c (or b)
        "page_hit@1": 0.0,
        "page_hit@3": 1.0,
        "page_hit@5": 1.0,
        "page_mrr": 0.5,
        # a at 2 (dup at 3 ignored), b at 5; ideal 2 ones first
        "page_ndcg@5": (lg(2) + lg(5)) / (lg(1) + lg(2)),  # 0.6241
        "retrieved_tokens@1": 100,
        "retrieved_tokens@3": 600,
        "retrieved_tokens@5": 1500,
    }
    assert set(got) == set(expected)
    for key, value in expected.items():
        assert got[key] == pytest.approx(value), key
    assert round(got["chunk_ndcg@5"], 4) == 0.7328
    assert round(got["page_ndcg@5"], 4) == 0.6241


def test_row_metrics_alternative_pages_either_satisfies():
    """AC-3: a fact citing two pages is covered at page level by either one."""
    for page in ("b", "c"):
        got = row_metrics(
            chunk_facts=[set()],
            pages=[page],
            required={"f": {"b", "c"}},
            expected_docs={"b"},
            n_relevant_chunks=1,
            token_counts=[10],
        )
        assert got["page_fact_recall@1"] == 1.0
        assert got["chunk_fact_recall@1"] == 0.0


def test_row_metrics_nothing_relevant():
    """AC-3: no relevant chunk or page gives zeros everywhere but tokens."""
    got = row_metrics(
        chunk_facts=[set(), set()],
        pages=["x", "y"],
        required={"f": {"a"}},
        expected_docs={"a"},
        n_relevant_chunks=2,
        token_counts=[5, 7],
        ks=(1, 5),
    )
    for key, value in got.items():
        if key.startswith("retrieved_tokens"):
            continue
        assert value == 0.0, key
    assert got["retrieved_tokens@1"] == 5
    assert got["retrieved_tokens@5"] == 12  # k past the list end


def test_mean_se_binary():
    """AC-7: a binary metric uses sqrt(p(1-p)/n)."""
    s = mean_se([1, 0, 1, 1], binary=True)
    assert s == Stat(mean=0.75, se=pytest.approx(math.sqrt(0.75 * 0.25 / 4)), n=4)
    assert mean_se([1.0, 1.0], binary=True).se == 0.0


def test_mean_se_continuous():
    """AC-7: a continuous metric uses sample sd (ddof=1) / sqrt(n)."""
    s = mean_se([1.0, 2.0, 4.0], binary=False)
    assert s.mean == pytest.approx(7 / 3)
    assert s.se == pytest.approx(0.881917, abs=1e-6)
    assert s.n == 3


def test_mean_se_continuous_with_only_0_1_values():
    """AC-7: the kind is explicit, not inferred; all-0/1 continuous values still use the sd."""
    s = mean_se([1, 0, 1, 1], binary=False)
    assert s.se == pytest.approx(0.5 / math.sqrt(4))  # sd(ddof=1) = 0.5
    assert s.se != pytest.approx(math.sqrt(0.75 * 0.25 / 4))


@pytest.mark.parametrize("binary", [True, False])
def test_mean_se_empty_and_single(binary):
    """AC-7: None for no values; se 0.0 for one value."""
    assert mean_se([], binary=binary) is None
    assert mean_se([0.4], binary=binary) == Stat(mean=0.4, se=0.0, n=1)


def test_row_metrics_k10_k20_from_20_long_list():
    """AC-6: the new cut-offs work on a depth-20 list."""
    facts = [set() for _ in range(20)]
    facts[7], facts[15] = {"f1"}, {"f2"}
    got = row_metrics(
        chunk_facts=facts,
        pages=[f"p{i}" for i in range(20)],
        required={"f1": {"p7"}, "f2": {"p15"}},
        expected_docs={"p7", "p15"},
        n_relevant_chunks=2,
        token_counts=[10] * 20,
    )
    assert got["chunk_fact_recall@10"] == 0.5
    assert got["chunk_fact_recall@20"] == 1.0
    assert got["chunk_all_required@10"] == 0.0 and got["chunk_all_required@20"] == 1.0
    assert got["page_hit@5"] == 0.0 and got["page_hit@10"] == 1.0
    assert got["retrieved_tokens@10"] == 100 and got["retrieved_tokens@20"] == 200


def test_matched_k_closest_mean():
    """AC-7: mean cumulative tokens 100/row -> k=1 .. ; target 250 is nearest k=2 (200 vs 300)."""
    from handbook_rag.evaluation.metrics import matched_k

    rows = [[100, 100, 100], [100, 100, 100]]
    assert matched_k(rows, 260, depth=3) == 3
    assert matched_k(rows, 240, depth=3) == 2
    assert matched_k(rows, 10_000, depth=3) == 3


def test_matched_k_tie_goes_to_smaller_k():
    """AC-7: equidistant means pick the smaller k."""
    from handbook_rag.evaluation.metrics import matched_k

    assert matched_k([[100, 100, 100]], 150, depth=3) == 1


def test_paired_mean_and_paired_se():
    """AC-7: mean delta and sample sd (ddof=1) / sqrt(n)."""
    from handbook_rag.evaluation.metrics import paired

    s = paired([0.5, 0.0, 0.25, -0.25])
    # deviations 0.375, -0.125, 0.125, -0.375: sum sq 0.3125, var = 0.3125 / 3, se = sd / 2
    assert s.mean == pytest.approx(0.125) and s.n == 4
    assert s.se == pytest.approx(math.sqrt(0.3125 / 3) / 2)


def test_paired_empty_and_single():
    """AC-7: no values -> None; one value -> se 0.0."""
    from handbook_rag.evaluation.metrics import paired

    assert paired([]) is None
    s = paired([0.3])
    assert s.mean == 0.3 and s.se == 0.0 and s.n == 1


def test_best_top_k_greedy_suboptimal():
    """Spec 0012 AC-11: the largest set first (greedy) gives 3/4; two smaller sets give 4/4."""
    sets = [{"a", "b", "c"}, {"a", "b"}, {"c", "d"}]
    assert best_top_k(sets, {"a", "b", "c", "d"}, 2) == 1.0
    assert best_top_k(sets, {"a", "b", "c", "d"}, 1) == 3 / 4


def test_best_top_k_edges():
    """Spec 0012 AC-11: empty required -> None; k > n; irrelevant and dominated sets; no cover."""
    assert best_top_k([{"a"}], set(), 5) is None
    assert best_top_k([{"a"}, {"b"}], {"a", "b", "c"}, 10) == 2 / 3
    assert best_top_k([{"a"}, {"a", "b"}, set(), {"z"}], {"a", "b"}, 1) == 1.0
    assert best_top_k([set(), {"z"}], {"a"}, 3) == 0.0
    assert best_top_k([], {"a"}, 3) == 0.0
    assert best_top_k([{"a"}, {"a"}, {"b"}], {"a", "b"}, 2) == 1.0
