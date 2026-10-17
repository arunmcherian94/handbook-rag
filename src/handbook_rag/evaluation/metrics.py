"""Retrieval metrics (spec 0004, AC-3). Pure functions over ranked lists and relevance sets.

Relevance is binary. Rank lists are in retrieval order (index 0 = rank 1).
"""

import math
import statistics
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from handbook_rag.constants import EVAL_KS, NDCG_K


@dataclass(frozen=True)
class Stat:
    mean: float
    se: float  # standard error: sqrt(p(1-p)/n) if the metric is binary, else sample sd / sqrt(n)
    n: int


def hit_at(rel: Sequence[bool], k: int) -> float:
    """1.0 if any of the top k is relevant."""
    return 1.0 if any(rel[:k]) else 0.0


def mrr(rel: Sequence[bool]) -> float:
    """1 / rank of the first relevant item, 0.0 if none."""
    for i, r in enumerate(rel, start=1):
        if r:
            return 1.0 / i
    return 0.0


def ndcg_at(rel: Sequence[bool], k: int, n_relevant: int) -> float:
    """Binary nDCG@k; the ideal DCG puts min(n_relevant, k) relevant items first.

    One relevant at rank 3 of one -> 0.50; relevant at ranks 1 and 4 of two -> 0.88.
    0.0 when n_relevant is 0.
    """
    if n_relevant <= 0:
        return 0.0
    dcg = sum(1.0 / math.log2(i + 1) for i, r in enumerate(rel[:k], start=1) if r)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(n_relevant, k) + 1))
    return dcg / ideal


def fact_recall_at(chunk_facts: Sequence[set[str]], required: set[str], k: int) -> float:
    """Required facts with at least one relevant chunk in the top k / len(required).

    chunk_facts[i] = ids of the facts the chunk at rank i+1 is relevant to. A fact counts once.
    """
    if not required:
        raise ValueError("fact recall needs at least one required fact")
    return len(_covered(chunk_facts, required, k)) / len(required)


def all_required_at(chunk_facts: Sequence[set[str]], required: set[str], k: int) -> float:
    """1.0 if every required fact is covered in the top k, else 0.0."""
    return 1.0 if _covered(chunk_facts, required, k) == required else 0.0


def first_page_hits(pages: Sequence[str], targets: set[str]) -> list[bool]:
    """Page-level relevance by rank: True at a page's first (best) rank if it's a target."""
    seen: set[str] = set()
    hits: list[bool] = []
    for page in pages:
        hits.append(page in targets and page not in seen)
        seen.add(page)
    return hits


def row_metrics(
    chunk_facts: Sequence[set[str]],
    pages: Sequence[str],
    required: Mapping[str, set[str]],
    expected_docs: set[str],
    n_relevant_chunks: int,
    token_counts: Sequence[int],
    ks: Sequence[int] = EVAL_KS,
) -> dict[str, float]:
    """Every AC-3 metric for one answerable row.

    chunk_facts: per rank, the required fact ids the chunk is relevant to.
    pages: per rank, the chunk's page (eval-set path).
    required: required cited fact id -> its cited pages.
    n_relevant_chunks: chunks in the corpus relevant to any required fact (nDCG's ideal).
    token_counts: per rank, the chunk's token count.

    Keys (k in ks): chunk_fact_recall@k, chunk_all_required@k, chunk_hit@k, chunk_mrr,
    chunk_ndcg@5 (NDCG_K), page_fact_recall@k, page_hit@k, page_mrr, page_ndcg@5,
    retrieved_tokens@k (sum of the top-k token counts). Page rank metrics are over
    expected_docs, each page at its best rank; page fact recall: a fact is covered if any of
    its cited pages is in the top k.
    """
    chunk_rel = [bool(f) for f in chunk_facts]
    page_rel = first_page_hits(pages, expected_docs)
    req = set(required)
    out: dict[str, float] = {}
    for k in ks:
        out[f"chunk_fact_recall@{k}"] = fact_recall_at(chunk_facts, req, k)
        out[f"chunk_all_required@{k}"] = all_required_at(chunk_facts, req, k)
        out[f"chunk_hit@{k}"] = hit_at(chunk_rel, k)
    out["chunk_mrr"] = mrr(chunk_rel)
    out[f"chunk_ndcg@{NDCG_K}"] = ndcg_at(chunk_rel, NDCG_K, n_relevant_chunks)
    for k in ks:
        top = set(pages[:k])
        covered = sum(1 for cited in required.values() if cited & top)
        out[f"page_fact_recall@{k}"] = covered / len(required)
        out[f"page_hit@{k}"] = hit_at(page_rel, k)
    out["page_mrr"] = mrr(page_rel)
    out[f"page_ndcg@{NDCG_K}"] = ndcg_at(page_rel, NDCG_K, len(expected_docs))
    for k in ks:
        out[f"retrieved_tokens@{k}"] = sum(token_counts[:k])
    return out


def mean_se(values: Sequence[float], binary: bool) -> Stat | None:
    """Mean, standard error and n; None for no values; se 0.0 for one value.

    binary is the metric's kind, set by the caller (never inferred from the values): True
    uses sqrt(p(1-p)/n), False the sample sd (ddof=1) / sqrt(n).
    """
    n = len(values)
    if n == 0:
        return None
    mean = statistics.fmean(values)
    if n == 1:
        return Stat(mean, 0.0, 1)
    if binary:
        se = math.sqrt(mean * (1 - mean) / n)
    else:
        se = statistics.stdev(values) / math.sqrt(n)
    return Stat(mean, se, n)


def _covered(chunk_facts: Sequence[set[str]], required: set[str], k: int) -> set[str]:
    hit: set[str] = set()
    for facts in chunk_facts[:k]:
        hit |= facts
    return hit & required
