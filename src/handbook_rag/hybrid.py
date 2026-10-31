"""Lexical (Postgres FTS) and hybrid retrieval, fused with RRF (spec 0011).

Beside ask.py, not in it: the dense path and the answer path stay unchanged (AC-7, AC-8).
search() is the one entry point for the eval harness and the permissions runner; every mode
filters on the principal's groups before ranking (spec 0007, AC-8; spec 0011, AC-4).
"""

import random
import time
import uuid
from dataclasses import dataclass, fields

from handbook_rag import ask
from handbook_rag.constants import BASELINE_CONFIG, FUSION_DEPTH, RETRIEVERS, RRF_K
from handbook_rag.db import vector_literal
from handbook_rag.embed import embed_with_retry
from handbook_rag.identity import Principal
from handbook_rag.models import Embedder, Reranker

# AC-2: an OR of the question's lexemes, each quoted as a literal, so quotes, `or` and `-` carry
# no operator meaning. No lexemes (stop words only) gives NULL: nothing matches, and no error.
QUERY = """(SELECT string_agg(quote_literal(l), ' | ')
            FROM unnest(tsvector_to_array(to_tsvector('english', %(question)s))) AS l)::tsquery"""

FTS_SEARCH = f"""
WITH q AS (SELECT {QUERY} AS query)
SELECT c.chunk_id, c.doc_id, d.url_path, COALESCE(c.heading, d.title) AS heading, c.content,
       NULL::float8 AS distance,
       c.chunk_size, c.chunk_overlap, c.tokenizer, c.commit_sha,
       ts_rank_cd(c.fts, q.query) AS fts_score
FROM q, chunks c
JOIN documents d USING (doc_id)
WHERE c.config_id = %(config_id)s AND c.fts @@ q.query
  -- Spec 0011, AC-4: the principal's groups filter before ranking, as on the dense path.
  AND c.allowed_groups && %(groups)s::text[]
-- AC-3: normalization 0 (near-equal chunk lengths); chunk_id makes ties reproducible.
ORDER BY ts_rank_cd(c.fts, q.query) DESC, c.chunk_id
LIMIT %(k)s
"""

QUERY_EMPTY = f"SELECT {QUERY} IS NULL"

# AC-9: recorded with every fts or hybrid run.
FTS_SETTINGS = {"config": "english", "normalization": 0, "query": "or-of-lexemes"}


class StaleFTS(RuntimeError):
    """AC-6: the FTS column or its index is missing, or empty for the active config."""


@dataclass(frozen=True)
class Ranked(ask.Retrieved):
    """A Retrieved with its rank in each list (None when absent) and, from hybrid, its RRF
    score. distance is None for a chunk the dense list didn't find."""

    dense_rank: int | None = None
    fts_rank: int | None = None
    rrf_score: float | None = None
    fts_score: float | None = None
    rerank_score: float | None = None  # spec 0012, AC-3


class PairTooLong(ValueError):
    """Spec 0012, AC-4: a query-document pair estimated over the reranker's limit. Raised before
    any request; the client never truncates."""

    def __init__(self, chunk_id: uuid.UUID, estimate: float, limit: int):
        super().__init__(
            f"chunk {chunk_id}: estimated {estimate:.0f} tokens with the question, over the "
            f"reranker's {limit}; nothing is truncated (spec 0012, AC-4)"
        )
        self.chunk_id = chunk_id


@dataclass(frozen=True)
class RerankLists:
    """Spec 0012, AC-3: one question's dense list to RERANK_DEPTH (dense ranks 1..n) and the same
    chunks reranked. dense[:k] is the in-run dense top k (AC-11); reranked[:k] is the result.
    Latencies are wall-clock ms; pairs_over counts pairs over the limit (AC-4: always 0, since one
    over the limit raises)."""

    dense: list[Ranked]
    reranked: list[Ranked]
    dense_ms: float
    rerank_ms: float
    input_tokens: int | None
    pairs_over: int


def search_fts(
    conn, question: str, principal: Principal, k: int, config_id: str = BASELINE_CONFIG
) -> list[Ranked]:
    """AC-3: FTS top-k by ts_rank_cd over the chunks the principal may see."""
    rows = conn.execute(
        FTS_SEARCH,
        {"question": question, "k": k, "config_id": config_id, "groups": principal.group_list},
    ).fetchall()
    return [Ranked(n, *row[:-1], fts_rank=n, fts_score=row[-1]) for n, row in enumerate(rows, 1)]


def fuse(dense: list[ask.Retrieved], fts: list[Ranked], k: int) -> list[Ranked]:
    """AC-5: RRF, sum of 1/(RRF_K + rank) over the lists a chunk is in, equal weights. Ties go
    to the better dense rank (absent last), then chunk_id. The dense row's fields win."""
    base: dict[uuid.UUID, ask.Retrieved] = {}
    dense_rank: dict[uuid.UUID, int] = {}
    fts_rank: dict[uuid.UUID, int] = {}
    fts_score: dict[uuid.UUID, float | None] = {}
    for c in fts:
        base[c.chunk_id], fts_rank[c.chunk_id], fts_score[c.chunk_id] = c, c.n, c.fts_score
    for c in dense:
        base[c.chunk_id], dense_rank[c.chunk_id] = c, c.n
    score = {
        cid: sum(1 / (RRF_K + r[cid]) for r in (dense_rank, fts_rank) if cid in r) for cid in base
    }
    order = sorted(
        base,
        key=lambda cid: (-score[cid], dense_rank.get(cid, float("inf")), str(cid)),
    )[:k]
    plain = [f.name for f in fields(ask.Retrieved) if f.name != "n"]
    return [
        Ranked(
            n,
            **{name: getattr(base[cid], name) for name in plain},
            dense_rank=dense_rank.get(cid),
            fts_rank=fts_rank.get(cid),
            rrf_score=score[cid],
            fts_score=fts_score.get(cid),
        )
        for n, cid in enumerate(order, 1)
    ]


def search(
    conn,
    retriever: str,
    q: str | None,
    question: str,
    model: str,
    principal: Principal,
    k: int,
    config_id: str = BASELINE_CONFIG,
) -> list[ask.Retrieved]:
    """Top k in the given mode. q is the embedded question (a vector_literal); fts ignores it.
    dense is ask.search unchanged (AC-7); hybrid fuses both lists retrieved to FUSION_DEPTH."""
    if retriever == "dense":
        return ask.search(conn, q, model, principal, k, config_id)
    if retriever == "fts":
        return search_fts(conn, question, principal, k, config_id)
    if retriever == "hybrid":
        depth = max(k, FUSION_DEPTH)
        dense = ask.search(conn, q, model, principal, depth, config_id)
        return fuse(dense, search_fts(conn, question, principal, depth, config_id), k)
    raise ValueError(f"unknown retriever {retriever!r}; one of {', '.join(RETRIEVERS)}")


def retrieve(
    conn,
    retriever: str,
    embedder: Embedder | None,
    question: str,
    principal: Principal,
    k: int,
    config_id: str = BASELINE_CONFIG,
    sleep=time.sleep,
    rand=random.random,
) -> list[ask.Retrieved]:
    """search() for a question: embeds it (same retry policy as ask.retrieve) except in fts
    mode, which embeds nothing (AC-9), so embedder may be None there."""
    if retriever == "dense":  # AC-7: the dense path is ask.retrieve itself
        return ask.retrieve(conn, embedder, question, principal, k, sleep, rand, config_id)
    q = None
    if retriever != "fts":
        q = vector_literal(embed_with_retry(embedder, [question], sleep, rand)[0])
    return search(
        conn, retriever, q, question, embedder.name if embedder else "", principal, k, config_id
    )


def rerank_lists(
    conn,
    reranker: Reranker,
    q: str,
    question: str,
    model: str,
    principal: Principal,
    config_id: str = BASELINE_CONFIG,
    clock=time.perf_counter,
) -> RerankLists:
    """Spec 0012, AC-3, AC-4: the dense list to RERANK_DEPTH (ACL pre-filtered by ask.search),
    the truncation guard, then one rerank call; sorted by score desc, dense rank, chunk_id."""
    raise NotImplementedError


def query_empty(conn, question: str) -> bool:
    """AC-9: the question has no lexemes, so the FTS list is empty."""
    (empty,) = conn.execute(QUERY_EMPTY, {"question": question}).fetchone()
    return empty


def check_fts(conn, config_id: str) -> None:
    """AC-6: raises StaleFTS, naming the fix, unless chunks.fts and chunks_fts_idx exist and
    the config's chunks have FTS vectors. Run before any fts or hybrid retrieval."""
    (column, index) = conn.execute(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name = 'chunks' AND column_name = 'fts'), "
        "to_regclass('chunks_fts_idx') IS NOT NULL"
    ).fetchone()
    if not column or not index:
        missing = "column chunks.fts" if not column else "index chunks_fts_idx"
        raise StaleFTS(f"{missing} is missing. Run `make chunk` to apply db/init/003_chunks.sql.")
    (chunks, with_fts) = conn.execute(
        "SELECT count(*), count(fts) FROM chunks WHERE config_id = %s", (config_id,)
    ).fetchone()
    if chunks and not with_fts:
        raise StaleFTS(
            f"config {config_id!r} has {chunks} chunks but no fts. Drop chunks.fts and run "
            "`make chunk` to recreate it as a generated column."
        )
