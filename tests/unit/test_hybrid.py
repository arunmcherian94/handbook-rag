import inspect
import uuid

import pytest
from fakes import make_principal

from handbook_rag import ask, hybrid
from handbook_rag.constants import FUSION_DEPTH, RRF_K


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
