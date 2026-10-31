"""Run the eval set against the frozen baseline (spec 0004, AC-6, AC-7, AC-8). Imperative shell.

Order: verify the corpus pin, check the stored chunks match it, parse the eval set, run the
evidence check, print the row count,
mode and estimated cost; spend (embed, answer) only with --confirm; write the run folder.
run() takes the connection, embedder and answerer as ports, so tests drive it with fakes.
Spec 0011: --retriever dense|fts|hybrid picks the retrieval mode (dense by default; the others
are retrieval-only, since hybrid enters the answer path only by ADR). fts embeds nothing.
Spec 0012: --retriever rerank reranks the dense top RERANK_DEPTH with a cross-encoder, once per
row; the same run's dense order is kept per row, so the comparison is paired within the run.
"""

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import tiktoken

from handbook_rag import acl, ask, hybrid, identity
from handbook_rag.constants import (
    BASELINE_CONFIG,
    CHECKOUT,
    COMPARE_ROWS,
    CORPUS_PREFIX,
    DEFAULT_RETRIEVER,
    EST_ANSWER_USD_PER_ROW,
    EVAL_DEPTH,
    EVAL_KS,
    EVAL_RUNS,
    EVAL_SET,
    FUSION_DEPTH,
    QUALITY_SET_USER,
    REGRESSION_ROWS,
    RERANK_DEPTH,
    RERANK_TOKEN_MARGIN,
    RETRIEVERS,
    RRF_K,
    TOKENIZER,
    TOP_K,
)
from handbook_rag.corpus import read_manifest, verify
from handbook_rag.db import connect, vector_literal
from handbook_rag.embed import embed_with_retry
from handbook_rag.evaluation import evidence as evidence_mod
from handbook_rag.evaluation.checks import abstention, code_checks, page_headings
from handbook_rag.evaluation.evalset import Row, parse
from handbook_rag.evaluation.evidence import Evidence, EvidenceError
from handbook_rag.evaluation.metrics import row_metrics
from handbook_rag.evaluation.report import (
    render_compare,
    render_md,
    render_rerank,
    rerank_summary,
    summarize,
)
from handbook_rag.identity import Principal
from handbook_rag.ingest import derive_title, split_front_matter
from handbook_rag.models import (
    Answerer,
    Embedder,
    InputTooLong,
    Reranker,
    describe_embedder,
    describe_reranker,
    embed_usd_per_1m,
    make_answerer,
    make_embedder,
    make_reranker,
    resolve_answer_spec,
    resolve_embed_spec,
)
from handbook_rag.prompts import SYSTEM_PROMPT
from handbook_rag.spend import log_spend, paid

HEADLINE = ("chunk_fact_recall@5", "chunk_all_required@5", "chunk_mrr", "retrieved_tokens@5")


def to_run(rows: list[Row], retrieval_only: bool) -> list[Row]:
    """Retrieval-only mode skips ooc rows: they have no retrieval metrics."""
    return [r for r in rows if r.answerable or not retrieval_only]


def estimate(
    rows: list[Row],
    retrieval_only: bool,
    usd_per_1m: float,
    sent: Callable[[str], str] = str,
    embeds: bool = True,
    rerank: dict | None = None,
    chunk_tokens: int = 0,
) -> dict:
    """AC-8, spec 0006 AC-10, spec 0008 AC-5: tokens of each question as sent (sent(), e.g. with a
    query instruction) for the embedding cost at the given price (twice for an answerable row:
    the k=5 and the depth-20 query); a flat per-row answer cost. Spec 0011 AC-9: embeds=False
    (fts) embeds nothing, so no tokens and $0. Spec 0012 AC-9: rerank (the reranker's
    describe_reranker settings) embeds each question once and scores RERANK_DEPTH pairs per row,
    each priced at question + chunk_tokens (the config's longest chunk) + template tokens."""
    enc = tiktoken.get_encoding(TOKENIZER)
    tokens = rerank_tokens = 0
    if embeds:
        per_row = 1 if rerank else 2  # rerank: one query vector serves both lists
        tokens = sum(
            len(enc.encode(sent(r.question), disallowed_special=()))
            * (per_row if r.answerable else 1)
            for r in rows
        )
    if rerank:
        rerank_tokens = sum(
            RERANK_DEPTH
            * (
                len(enc.encode(r.question, disallowed_special=()))
                + chunk_tokens
                + rerank["template_tokens"]
            )
            for r in rows
        )
    embed_usd = tokens * usd_per_1m / 1_000_000
    rerank_usd = rerank_tokens * rerank["usd_per_1m"] / 1_000_000 if rerank else 0.0
    answer_usd = 0.0 if retrieval_only else len(rows) * EST_ANSWER_USD_PER_ROW
    return {
        "embed_tokens": tokens,
        "embed_usd": embed_usd,
        "rerank_tokens": rerank_tokens,
        "rerank_usd": rerank_usd,
        "answer_usd": answer_usd,
        "total_usd": embed_usd + rerank_usd + answer_usd,
    }


def new_run_dir(out_root: Path, meta: dict) -> Path:
    """Create the run folder `<date>-<8 hex>` under out_root; an existing one raises, so a
    folder is never shared. The paid mains create it before spending, so a failed run's spend
    line names its partial folder (spec 0009, AC-3)."""
    out = out_root / f"{meta['timestamp'][:10]}-{uuid.uuid4().hex[:8]}"
    out.mkdir(parents=True)
    return out


def _git(*args: str) -> str:
    """git in the harness repo (cwd), not the corpus checkout (corpus.git_out)."""
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def stored_chunk_params(conn, pinned_sha: str, config_id: str) -> tuple[dict, str]:
    """AC-4, AC-6: (config, corpus_sha) as stored: the chunk_configs row and the commit its
    chunks were built from. Fails on an unknown config, a config without chunks, or chunks built
    from another commit than the pin."""
    cfg = conn.execute(
        "SELECT strategy, params, tokenizer FROM chunk_configs WHERE config_id = %s", (config_id,)
    ).fetchone()
    if cfg is None:
        raise SystemExit(f"unknown config {config_id!r}; run `make chunk CONFIG={config_id}`")
    shas = conn.execute(
        "SELECT DISTINCT commit_sha FROM chunks WHERE config_id = %s", (config_id,)
    ).fetchall()
    if not shas:
        raise SystemExit(f"config {config_id!r} has no chunks; run `make chunk CONFIG={config_id}`")
    stale = {sha for (sha,) in shas} != {pinned_sha}
    if stale:
        found = ", ".join(sorted(sha for (sha,) in shas))
        raise SystemExit(
            f"chunks are stale vs CORPUS.md (chunks {found}, pin {pinned_sha}); "
            "run `make ingest` and `make chunk`"
        )
    strategy, params, tokenizer = cfg
    return {
        "config_id": config_id,
        "strategy": strategy,
        "params": params,
        "tokenizer": tokenizer,
    }, pinned_sha


def metadata(
    version: str,
    eval_bytes: bytes,
    corpus_sha: str,
    chunk_params: dict,
    embed_model: str,
    answer_model: str | None,
    rows: int,
    limit: int | None,
    *,
    user_id: str | None = None,
    policy_version: str | None = None,
    policy_sha256: str | None = None,
    retriever: str = DEFAULT_RETRIEVER,
    rerank: dict | None = None,
) -> dict:
    """AC-6, AC-12 run metadata. corpus_sha and chunk_params (the stored config) come from
    stored_chunk_params (the DB); chunk_params in the output is the config's params.
    answer_model None means retrieval-only. Spec 0007, AC-9: user_id and the policy version and
    sha256 record who the run was. Spec 0011, AC-9: the retriever, for hybrid the fusion
    settings, for fts and hybrid the FTS settings. Spec 0012, AC-9: for rerank, the reranker's
    settings (describe_reranker), depth and truncation handling; run() adds input_tokens."""
    return {
        "eval_version": version,
        "eval_sha256": hashlib.sha256(eval_bytes).hexdigest(),
        "harness_sha": _git("rev-parse", "HEAD").strip(),
        "harness_dirty": bool(_git("status", "--porcelain").strip()),
        "corpus_sha": corpus_sha,
        "config_id": chunk_params["config_id"],
        "chunk_params": {
            "strategy": chunk_params["strategy"],
            **chunk_params["params"],
            "tokenizer": chunk_params["tokenizer"],
        },
        "embed_model": embed_model,
        "answer_model": answer_model,
        "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
        "k": TOP_K,
        "eval_depth": EVAL_DEPTH,
        "timestamp": datetime.now(UTC).isoformat(),
        "rows": rows,
        "mode": "retrieval-only" if answer_model is None else "full",
        "limit": limit,
        "user_id": user_id,
        "policy_version": policy_version,
        "policy_sha256": policy_sha256,
        "retriever": retriever,
        **({"rrf_k": RRF_K, "fusion_depth": FUSION_DEPTH} if retriever == "hybrid" else {}),
        **({"fts": hybrid.FTS_SETTINGS} if retriever in ("fts", "hybrid") else {}),
        **({"rerank": rerank_settings(rerank)} if retriever == "rerank" else {}),
    }


def rerank_settings(rerank: dict | None) -> dict:
    """Spec 0012, AC-9: what a rerank run records about its reranker (no key)."""
    if rerank is None:
        raise ValueError("retriever 'rerank' needs the reranker's settings")
    return {
        "model": rerank["model"],
        "depth": RERANK_DEPTH,
        "instruction": rerank["instruction"],
        "max_input_tokens": rerank["max_input_tokens"],
        "template_tokens": rerank["template_tokens"],
        "token_margin": RERANK_TOKEN_MARGIN,
        "truncation": "none; refuse over limit",
        "usd_per_1m": rerank["usd_per_1m"],
        "price_source": rerank["price_source"],
    }


# A baseline comparison holds everything fixed except ONE of the chunk config, the embed model or
# the retriever (spec 0005 AC-11, 0006 AC-6, 0008 AC-6, 0011 AC-10); changing several at once is
# reported separately. A baseline without a retriever key is dense.
SAME_AS_BASELINE = ("eval_sha256", "corpus_sha", "k", "eval_depth", "limit")
SAME_IF_BOTH_ANSWERED = ("answer_model", "system_prompt_sha256")


def baseline_mismatch(base_meta: dict, meta: dict) -> list[str]:
    """Metadata keys on which this run and the baseline differ, beyond the chunk config."""
    keys = list(SAME_AS_BASELINE)
    if base_meta.get("answer_model") and meta.get("answer_model"):
        keys += SAME_IF_BOTH_ANSWERED
    diff = [
        f"{k}: baseline {base_meta.get(k)!r}, this run {meta.get(k)!r}"
        for k in keys
        if base_meta.get(k) != meta.get(k)
    ]
    changed = _changed_axes(base_meta, meta)
    if len(changed) > 1:
        diff.append(
            f"{' and '.join(k for k, _, _ in changed)} changed together: baseline "
            f"({', '.join(str(x) for _, x, _ in changed)}), this run "
            f"({', '.join(str(x) for _, _, x in changed)}); "
            "change one at a time (spec 0008 AC-6, spec 0011 AC-10)"
        )
    return diff


AXES = (
    ("config_id", "chunk config", None),
    ("embed_model", "embed model", None),
    # a literal, not DEFAULT_RETRIEVER: runs before spec 0011 were dense, whatever an ADR sets
    ("retriever", "retriever", "dense"),
)


def _changed_axes(base_meta: dict, meta: dict) -> list[tuple[str, object, object]]:
    """(key, baseline value, this run's value) for each change axis that differs."""
    out = []
    no_embed = "fts" in (base_meta.get("retriever", "dense"), meta.get("retriever", "dense"))
    for key, _, default in AXES:
        if key == "embed_model" and no_embed:  # AC-10: fts never uses the embedding model
            continue
        was, now = base_meta.get(key, default), meta.get(key, default)
        if was != now:
            out.append((key, was, now))
    return out


def baseline_change(base_meta: dict, meta: dict) -> str | None:
    """The one thing that changed against the baseline (spec 0008 AC-6, spec 0011 AC-10); None if
    nothing or several things."""
    changed = _changed_axes(base_meta, meta)
    if len(changed) != 1:
        return None
    return next(label for key, label, _ in AXES if key == changed[0][0])


def _lookup(
    conn, chunks: list[ask.Retrieved]
) -> tuple[dict[uuid.UUID, str], list[int], list[list[str] | None]]:
    """(doc_id -> documents.path with CORPUS_PREFIX, per rank the stored chunks.token_count and
    heading_path).

    The stored count is authoritative: re-encoding chunk text can differ at window edges.
    """
    rows = conn.execute(
        "SELECT c.chunk_id, c.token_count, d.doc_id, d.path, c.heading_path "
        "FROM chunks c JOIN documents d USING (doc_id) WHERE c.chunk_id = ANY(%s)",
        ([c.chunk_id for c in chunks],),
    ).fetchall()
    paths = {doc_id: path for _, _, doc_id, path, _ in rows}
    counts = {chunk_id: n for chunk_id, n, _, _, _ in rows}
    hps = {chunk_id: hp for chunk_id, _, _, _, hp in rows}
    return paths, [counts[c.chunk_id] for c in chunks], [hps[c.chunk_id] for c in chunks]


def _headings_by_n(
    citations: list[ask.Citation],
    chunks: list[ask.Retrieved],
    paths: dict[uuid.UUID, str],
    checkout: Path,
) -> dict[int, set[str]]:
    """AC-5: citation number -> page_headings of the cited chunk's page, read from the pinned
    file (checkout / documents.path). Citations are all in range (ask.parse_citations)."""
    by_path: dict[str, set[str]] = {}
    out: dict[int, set[str]] = {}
    for c in citations:
        path = paths[chunks[c.n - 1].doc_id]
        if path not in by_path:
            front_matter, body = split_front_matter((checkout / path).read_text(encoding="utf-8"))
            by_path[path] = page_headings(body, derive_title(front_matter, body, path))
        out[c.n] = by_path[path]
    return out


def record(
    conn,
    row: Row,
    ev: Evidence,
    chunks: list[ask.Retrieved],
    deep: list[ask.Retrieved],
    result: ask.AskResult | None,
    checkout: Path = CHECKOUT,
    fts_query_empty: bool | None = None,
    rerank: hybrid.RerankLists | None = None,
) -> dict:
    """One rows.jsonl line (schema in report.py). chunks is the k=5 list the model saw; deep the
    depth-20 list ([] for an ooc row). result is None in retrieval-only mode. Spec 0011 AC-9:
    a hybrid.Ranked entry also carries its dense and fts ranks and RRF score; fts_query_empty
    (None for dense) is recorded when given. Spec 0012 AC-9, AC-11: rerank (the row's
    RerankLists) adds every candidate with its dense and rerank ranks, score and facts, the
    latencies and the reranker's token count; entries also carry rerank_score."""
    paths, tokens, heading_paths = _lookup(conn, chunks)
    pages = [paths[c.doc_id].removeprefix(CORPUS_PREFIX) for c in chunks]
    relevant = {f.id: ev.relevant[(row.id, f.id)] for f in row.required}

    def facts_of(cs: list[ask.Retrieved]) -> list[set[str]]:
        # Only required cited facts: the rank metrics are defined over them (AC-3).
        return [{fid for fid, ids in relevant.items() if c.chunk_id in ids} for c in cs]

    chunk_facts = facts_of(chunks)
    deep_facts = facts_of(deep)
    deep_paths, deep_tokens, _ = _lookup(conn, deep) if deep else ({}, [], [])
    deep_pages = [deep_paths[c.doc_id].removeprefix(CORPUS_PREFIX) for c in deep]
    metrics: dict[str, float] = {}
    if relevant:  # an answerable row whose required facts are all answer-only scores nothing
        args = (
            {f.id: set(f.cites) for f in row.required},
            set(row.expected_docs),
            len(frozenset().union(*relevant.values())),
        )
        # Spec 0006 AC-6: k<=5 and the rank metrics come from the list the model saw; @10/@20
        # from the deep list.
        m_deep = row_metrics(deep_facts, deep_pages, *args, deep_tokens, ks=EVAL_KS)
        m5 = row_metrics(
            chunk_facts, pages, *args, tokens, ks=tuple(k for k in EVAL_KS if k <= TOP_K)
        )
        metrics = m_deep | m5

    def ranks(c: ask.Retrieved) -> dict:
        if not isinstance(c, hybrid.Ranked):
            return {}
        out = {"dense_rank": c.dense_rank, "fts_rank": c.fts_rank, "rrf_score": c.rrf_score}
        return out | ({"rerank_score": c.rerank_score} if c.rerank_score is not None else {})

    rec = {
        "row": row.id,
        "type": row.type,
        "recency_basis": row.recency_basis,
        "answerable": row.answerable,
        "conflict_unscored": row.conflict_unscored,
        "retrieved": [
            {
                "rank": c.n,
                "chunk_id": str(c.chunk_id),
                "doc_id": str(c.doc_id),
                "path": page,
                "heading": c.heading,
                "heading_path": hp,
                "distance": c.distance,
                "tokens": n,
                "facts": sorted(facts),
                "page_relevant": page in row.expected_docs,
                **ranks(c),
            }
            for c, page, n, facts, hp in zip(
                chunks, pages, tokens, chunk_facts, heading_paths, strict=True
            )
        ],
        "deep": [
            {
                "rank": i,
                "chunk_id": str(c.chunk_id),
                "tokens": n,
                "facts": sorted(facts),
                "page_relevant": page in row.expected_docs,
                **ranks(c),
            }
            for i, (c, page, n, facts) in enumerate(
                zip(deep, deep_pages, deep_tokens, deep_facts, strict=True), start=1
            )
        ],
        "required_facts": sorted(f.id for f in row.required),
        "near_tie": bool(deep)
        and [c.chunk_id for c in deep[:TOP_K]] != [c.chunk_id for c in chunks],
        "metrics": metrics,
        "page_hit_no_chunk": bool(metrics)
        and metrics[f"page_hit@{TOP_K}"] == 1
        and metrics[f"chunk_hit@{TOP_K}"] == 0,
        "answer": None,
        "citations": [],
        "invalid_citations": [],
        "truncated": None,
        "abstention": None,
        "checks": None,
    }
    if fts_query_empty is not None:
        rec["fts_query_empty"] = fts_query_empty
    if rerank is not None:
        rerank_rank = {c.chunk_id: c.n for c in rerank.reranked}
        rec["candidates"] = [
            {
                "dense_rank": c.dense_rank,
                "rerank_rank": rerank_rank[c.chunk_id],
                "chunk_id": str(c.chunk_id),
                "facts": sorted(facts),
                "rerank_score": c.rerank_score,
            }
            for c, facts in zip(rerank.dense, facts_of(rerank.dense), strict=True)
        ]
        rec["latency_ms"] = {"dense": rerank.dense_ms, "rerank": rerank.rerank_ms}
        rec["rerank"] = {
            "input_tokens": rerank.input_tokens,
            "pairs": len(rerank.dense),
            "pairs_over": rerank.pairs_over,
        }
    if result is None:
        return rec
    abst = abstention(result.answer, row.expected if not row.answerable else None)
    rec |= {
        "answer": result.answer,
        "citations": [
            {"n": c.n, "url_path": c.url_path, "heading": c.heading} for c in result.citations
        ],
        "invalid_citations": result.invalid_citations,
        "truncated": result.truncated,
        "abstention": asdict(abst),
    }
    if row.answerable and not abst.abstained:
        checks = code_checks(
            result.answer,
            result.citations,
            result.invalid_citations,
            result.truncated,
            _headings_by_n(result.citations, chunks, paths, checkout),
        )
        rec["checks"] = asdict(checks) | {"passed": checks.passed}
    return rec


def run(
    conn,
    rows: list[Row],
    ev: Evidence,
    embedder: Embedder | None,
    answerer: Answerer | None,
    *,
    principal: Principal,
    meta: dict,
    out_root: Path = EVAL_RUNS,
    checkout: Path = CHECKOUT,
    config_id: str = BASELINE_CONFIG,
    baseline: tuple[str, dict, list[dict]] | None = None,
    out: Path | None = None,
    retriever: str = DEFAULT_RETRIEVER,
    reranker: Reranker | None = None,
    sleep=time.sleep,
    rand=random.random,
) -> Path:
    """Retrieve (and answer, unless answerer is None) every row; write the run folder (AC-7).
    Every retrieval runs as `principal` (spec 0007, AC-8).

    answerer None is retrieval-only mode: ooc rows are skipped and the answer model is never
    called. config_id scopes retrieval; baseline (id, summary, records) adds the AC-14 comparison
    to summary.md. checkout is the pinned corpus the AC-5 heading check reads. out is a folder
    from new_run_dir() (one is created under out_root if None). Returns the folder.

    Spec 0012: rerank (needs a reranker) embeds each question once and reranks once; the top 5
    and the deep list are cuts of the same reranked list. Spec 0011: retriever picks the mode;
    fts needs no embedder (None). Full mode (an answerer)
    is dense only: ask.ask is the answer path (AC-8).
    """
    if answerer is not None and retriever != "dense":
        raise ValueError("full mode is dense only; hybrid enters the answer path by ADR (AC-8)")
    if retriever == "rerank" and reranker is None:  # before anything is embedded (review fix)
        raise ValueError("retriever 'rerank' needs a reranker")
    out = out if out is not None else new_run_dir(out_root, meta)
    records: list[dict] = []
    # Appended per row, so a crash mid-run keeps what was paid for.
    with (out / "rows.jsonl").open("w", encoding="utf-8") as f:
        for row in to_run(rows, answerer is None):
            lists = None
            if answerer is None and retriever == "rerank":
                result = None
                q = vector_literal(embed_with_retry(embedder, [row.question], sleep, rand)[0])
                lists = hybrid.rerank_lists(
                    conn, reranker, q, row.question, embedder.name, principal, config_id
                )
                if not lists.dense:
                    raise SystemExit(
                        f"no embeddings for {embedder.name}; run `make embed` for the cost, "
                        "then `make paid-embed`"
                    )
                chunks = lists.reranked[:TOP_K]
            elif answerer is None:
                result = None
                chunks = hybrid.retrieve(
                    conn, retriever, embedder, row.question, principal, TOP_K, config_id
                )
                # An empty FTS list is legitimate; a hybrid list the dense side found nothing
                # for would silently be FTS-only.
                dense_found = retriever == "dense" or any(
                    getattr(c, "dense_rank", None) for c in chunks
                )
                if retriever != "fts" and not dense_found:
                    raise SystemExit(
                        f"no embeddings for {embedder.name}; run `make embed` for the cost, "
                        "then `make paid-embed`"
                    )
            else:
                result = ask.ask(
                    conn, embedder, answerer, row.question, principal, TOP_K, config_id=config_id
                )
                chunks = result.chunks
            if lists is not None:
                deep = lists.reranked[:EVAL_DEPTH] if row.answerable else []
            elif row.answerable:
                deep = hybrid.retrieve(
                    conn, retriever, embedder, row.question, principal, EVAL_DEPTH, config_id
                )
            else:
                deep = []
            fts = retriever in ("fts", "hybrid")
            empty = hybrid.query_empty(conn, row.question) if fts else None
            rec = record(conn, row, ev, chunks, deep, result, checkout, empty, lists)
            records.append(rec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            recall = rec["metrics"].get(f"chunk_fact_recall@{TOP_K}")
            shown = "-" if recall is None else f"{recall:.2f}"
            print(f"row {row.id}: chunk_fact_recall@{TOP_K} {shown}", file=sys.stderr)
    ran = [r for r in to_run(rows, answerer is None) if r.answerable]
    notes = {
        "answer_only_facts": [f"row {r.id} {f.id}" for r in ran for f in r.facts if f.answer_only],
        "no_retrieval_facts": [r.id for r in ran if not r.required],
        "evidence_warnings": ev.warnings,
    }
    if retriever == "rerank":  # AC-9: the provider's total, None if any response lacked it
        used = [r["rerank"]["input_tokens"] for r in records if r.get("rerank")]
        total = None if None in used else sum(used)
        meta = meta | {"rerank": meta.get("rerank", {}) | {"input_tokens": total}}
    if baseline:
        meta = meta | {
            "baseline": baseline[0],
            "baseline_change": baseline_change(baseline[1]["meta"], meta),
        }
    target = None
    if baseline:
        target = baseline[1]["groups"]["overall"][f"retrieved_tokens@{TOP_K}"]["mean"]
    summary = summarize(records, meta, notes, target_tokens=target)
    if retriever == "rerank":  # AC-10, AC-11: paired within this run
        summary["rerank"] = rerank_summary(records)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    md = render_md(summary)
    if retriever == "rerank":
        md += "\n" + render_rerank(summary["rerank"])
    if baseline:
        base_id, base_summary, base_records = baseline
        md += "\n" + render_compare(
            summary,
            records,
            base_summary,
            base_records,
            base_id,
            list(dict.fromkeys(COMPARE_ROWS + REGRESSION_ROWS)),
        )
        if retriever == "rerank":  # AC-12
            md += (
                "\nContinuity only (spec 0012 AC-12): the baseline embedded its questions "
                "separately, so its query vectors can differ from this run's (the row 32 and 93 "
                "drift). The decision rests on the in-run comparison above.\n"
            )
    (out / "summary.md").write_text(md, encoding="utf-8")
    return out


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run the eval set (spec 0004).")
    ap.add_argument("--confirm", action="store_true", help="spend: call the embed/answer models")
    ap.add_argument("--limit", type=int, help="run only the first n rows")
    ap.add_argument("--retrieval-only", action="store_true", help="skip the answer model")
    ap.add_argument("--config", default=BASELINE_CONFIG, help="chunk config to evaluate")
    ap.add_argument("--baseline", metavar="RUN_ID", help="compare against this earlier run")
    ap.add_argument(
        "--retriever",
        choices=RETRIEVERS,
        default=DEFAULT_RETRIEVER,
        help="retrieval mode (spec 0011, 0012); all but dense are retrieval-only",
    )
    return ap


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if args.retriever != "dense" and not args.retrieval_only:
        raise SystemExit(
            f"--retriever {args.retriever} needs --retrieval-only: it enters the answer path "
            "only by ADR (spec 0011 AC-8, spec 0012 AC-8)"
        )

    baseline = None
    if args.baseline:
        folder = EVAL_RUNS / args.baseline
        try:
            baseline = (
                args.baseline,
                json.loads((folder / "summary.json").read_text(encoding="utf-8")),
                [
                    json.loads(line)
                    for line in (folder / "rows.jsonl").read_text(encoding="utf-8").splitlines()
                ],
            )
        except FileNotFoundError:
            raise SystemExit(
                f"baseline run {args.baseline} not found in {EVAL_RUNS} (summary.json, "
                "rows.jsonl); re-run the baseline retrieval-only first: "
                "`make paid-eval CONFIG=fixed-512-64 RETRIEVAL_ONLY=1`"
            ) from None

    m = read_manifest()
    error = verify(m)
    if error:
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    eval_bytes = EVAL_SET.read_bytes()
    eval_set = parse(eval_bytes.decode("utf-8"))
    rows = list(eval_set.rows[: args.limit] if args.limit is not None else eval_set.rows)

    try:  # AC-1, AC-5: unknown model or bad @dims fails the dry run
        query_embedder = describe_embedder(resolve_embed_spec(), kind="query")
        spec = query_embedder.name
        usd_per_1m = embed_usd_per_1m(spec)
    except ValueError as e:
        raise SystemExit(str(e)) from None

    with connect() as conn:
        chunk_params, corpus_sha = stored_chunk_params(conn, m.sha, args.config)
        try:
            ev = evidence_mod.check(rows, conn, args.config)
        except EvidenceError as e:
            raise SystemExit(str(e)) from None
        for w in ev.warnings:
            print(f"warning: {w}", file=sys.stderr)

        # AC-5: a stale ACL aborts before anything else; AC-9: the quality set runs as admin.
        policy = acl.load_policy(conn)
        try:
            acl.check_stale(conn, policy)
        except (acl.StaleACL, acl.AclError) as e:
            raise SystemExit(str(e)) from None
        principal = identity.load(QUALITY_SET_USER, policy)
        if args.retriever in ("fts", "hybrid"):  # spec 0011 AC-6: after the ACL check, dry run too
            try:
                hybrid.check_fts(conn, args.config)
            except hybrid.StaleFTS as e:
                raise SystemExit(str(e)) from None

        todo = to_run(rows, args.retrieval_only)
        n_ans = sum(r.answerable for r in todo)
        mode = "retrieval-only" if args.retrieval_only else "full"
        if args.retriever != "fts":  # fts embeds nothing
            try:  # AC-4: every query as sent is within the limit before anything is spent
                query_embedder.prepare([r.question for r in todo])
            except InputTooLong as e:
                raise SystemExit(str(e)) from None
        # Spec 0012 AC-9: the reranker's settings (no key) price the pairs; an unknown model
        # fails the dry run. Pairs are priced at the config's longest chunk.
        rerank = describe_reranker() if args.retriever == "rerank" else None
        (chunk_tokens,) = conn.execute(
            "SELECT COALESCE(max(token_count), 0) FROM chunks WHERE config_id = %s", (args.config,)
        ).fetchone()
        cost = estimate(
            todo,
            args.retrieval_only,
            usd_per_1m,
            lambda q: query_embedder.prepare([q])[0],
            embeds=args.retriever != "fts",
            rerank=rerank,
            chunk_tokens=chunk_tokens,
        )
        print(
            f"eval {eval_set.version}, config {args.config}: {len(todo)} rows ({n_ans} answerable, "
            f"{len(todo) - n_ans} ooc), mode {mode}, "
            f"retriever {args.retriever}"
        )
        print(
            f"estimated cost: ${cost['total_usd']:.4f} (embed ~{cost['embed_tokens']} tokens "
            f"${cost['embed_usd']:.6f}, answers ${cost['answer_usd']:.4f})"
        )
        if rerank:
            worst = hybrid.worst_pair(
                [r.question for r in todo], chunk_tokens, rerank["template_tokens"]
            )
            if worst > rerank["max_input_tokens"]:  # AC-4: refuse before any spend
                raise SystemExit(
                    f"longest rerank pair estimated at {worst:.0f} tokens, over the reranker's "
                    f"{rerank['max_input_tokens']}; nothing is truncated (spec 0012 AC-4)"
                )
            print(
                f"rerank: {rerank['model']}, depth {RERANK_DEPTH}, ~{cost['rerank_tokens']} tokens "
                f"${cost['rerank_usd']:.4f} at ${rerank['usd_per_1m']}/1M "
                f"({rerank['price_source']}); longest pair ~{worst:.0f} of "
                f"{rerank['max_input_tokens']} tokens, no truncation"
            )
        meta = metadata(
            eval_set.version,
            eval_bytes,
            corpus_sha,
            chunk_params,
            spec,
            None if args.retrieval_only else resolve_answer_spec(),
            len(todo),
            args.limit,
            user_id=principal.user_id,
            policy_version=policy.version,
            policy_sha256=policy.sha256,
            retriever=args.retriever,
            rerank=rerank,
        )
        # AC-6: a baseline that differs in more than one change fails the dry run.
        if baseline and (diff := baseline_mismatch(baseline[1]["meta"], meta)):
            raise SystemExit(
                f"baseline {baseline[0]} differs in more than one change (chunk config, embed "
                "model or retriever; spec 0008 AC-6, spec 0011 AC-10):\n  " + "\n  ".join(diff)
            )
        if not paid(args.confirm, "eval"):  # spec 0009
            return 0

        # Built only after confirm, so a dry run needs no API key.
        embedder = None if args.retriever == "fts" else make_embedder(spec, kind="query")
        if embedder is not None:
            (has_embeddings,) = conn.execute(
                "SELECT EXISTS (SELECT 1 FROM chunk_embeddings e JOIN chunks c USING (chunk_id) "
                "WHERE c.config_id = %s AND e.model = %s)",
                (args.config, embedder.name),
            ).fetchone()
            if not has_embeddings:
                raise SystemExit(
                    f"config {args.config!r} has no embeddings for {embedder.name}; "
                    f"run `make embed CONFIG={args.config}` for the cost, then `make paid-embed`"
                )
        answerer = None if args.retrieval_only else make_answerer()
        reranker = make_reranker() if rerank else None
        out, status = new_run_dir(EVAL_RUNS, meta), "failed"
        try:
            run(
                conn,
                rows,
                ev,
                embedder,
                answerer,
                principal=principal,
                meta=meta,
                config_id=args.config,
                baseline=baseline,
                out=out,
                retriever=args.retriever,
                reranker=reranker,
            )
            status = "ok"
        finally:  # spec 0009, AC-3: logged even when the run fails after spending
            log_spend(
                "eval",
                cost["total_usd"],
                run_id=out.name,
                embed_model=embedder and embedder.name,
                answer_model=answerer and answerer.name,
                status=status,
            )

    overall = json.loads((out / "summary.json").read_text(encoding="utf-8"))["groups"]["overall"]
    print(f"wrote {out}")
    for key in HEADLINE:
        if key in overall:
            s = overall[key]
            print(f"  {key}: {s['mean']:.3f} ± {s['se']:.3f} (n={s['n']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
