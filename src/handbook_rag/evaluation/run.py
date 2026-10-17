"""Run the eval set against the frozen baseline (spec 0004, AC-6, AC-7, AC-8). Imperative shell.

Order: verify the corpus pin, check the stored chunks match it, parse the eval set, run the
evidence check, print the row count,
mode and estimated cost; spend (embed, answer) only with --confirm; write the run folder.
run() takes the connection, embedder and answerer as ports, so tests drive it with fakes.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import tiktoken

from handbook_rag import ask
from handbook_rag.constants import (
    CHECKOUT,
    CORPUS_PREFIX,
    EST_ANSWER_USD_PER_ROW,
    EST_EMBED_USD_PER_1M,
    EVAL_RUNS,
    EVAL_SET,
    TOKENIZER,
    TOP_K,
)
from handbook_rag.corpus import read_manifest, verify
from handbook_rag.db import connect
from handbook_rag.evaluation import evidence as evidence_mod
from handbook_rag.evaluation.checks import abstention, code_checks, page_headings
from handbook_rag.evaluation.evalset import Row, parse
from handbook_rag.evaluation.evidence import Evidence, EvidenceError
from handbook_rag.evaluation.metrics import row_metrics
from handbook_rag.evaluation.report import render_md, summarize
from handbook_rag.ingest import derive_title, split_front_matter
from handbook_rag.models import Answerer, Embedder, make_answerer, make_embedder
from handbook_rag.prompts import SYSTEM_PROMPT

HEADLINE = ("chunk_fact_recall@5", "chunk_all_required@5", "chunk_mrr", "retrieved_tokens@5")


def to_run(rows: list[Row], retrieval_only: bool) -> list[Row]:
    """Retrieval-only mode skips ooc rows: they have no retrieval metrics."""
    return [r for r in rows if r.answerable or not retrieval_only]


def estimate(rows: list[Row], retrieval_only: bool) -> dict:
    """AC-8: question tokens for the embedding cost; a flat per-row answer cost."""
    enc = tiktoken.get_encoding(TOKENIZER)
    tokens = sum(len(enc.encode(r.question, disallowed_special=())) for r in rows)
    embed_usd = tokens * EST_EMBED_USD_PER_1M / 1_000_000
    answer_usd = 0.0 if retrieval_only else len(rows) * EST_ANSWER_USD_PER_ROW
    return {
        "embed_tokens": tokens,
        "embed_usd": embed_usd,
        "answer_usd": answer_usd,
        "total_usd": embed_usd + answer_usd,
    }


def _git(*args: str) -> str:
    """git in the harness repo (cwd), not the corpus checkout (corpus.git_out)."""
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def stored_chunk_params(conn, pinned_sha: str) -> tuple[dict, str]:
    """AC-6: (chunk_params, corpus_sha) as stored in chunks, which holds exactly one parameter
    set (chunk.py). Fails on zero or several sets, or chunks built from another commit."""
    sets = conn.execute(
        "SELECT DISTINCT chunk_size, chunk_overlap, tokenizer, commit_sha FROM chunks"
    ).fetchall()
    if len(sets) != 1:
        raise SystemExit(
            f"chunks table holds {len(sets)} parameter sets, expected exactly 1; run `make chunk`"
        )
    size, overlap, tokenizer, sha = sets[0]
    if sha != pinned_sha:
        raise SystemExit(
            f"chunks are stale vs CORPUS.md (chunks {sha}, pin {pinned_sha}); "
            "run `make ingest` and `make chunk`"
        )
    return {"chunk_size": size, "chunk_overlap": overlap, "tokenizer": tokenizer}, sha


def metadata(
    version: str,
    eval_bytes: bytes,
    corpus_sha: str,
    chunk_params: dict,
    embed_model: str,
    answer_model: str | None,
    rows: int,
    limit: int | None,
) -> dict:
    """AC-6 run metadata. corpus_sha and chunk_params come from stored_chunk_params (the DB).
    answer_model None means retrieval-only."""
    return {
        "eval_version": version,
        "eval_sha256": hashlib.sha256(eval_bytes).hexdigest(),
        "harness_sha": _git("rev-parse", "HEAD").strip(),
        "harness_dirty": bool(_git("status", "--porcelain").strip()),
        "corpus_sha": corpus_sha,
        "chunk_params": chunk_params,
        "embed_model": embed_model,
        "answer_model": answer_model,
        "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
        "k": TOP_K,
        "timestamp": datetime.now(UTC).isoformat(),
        "rows": rows,
        "mode": "retrieval-only" if answer_model is None else "full",
        "limit": limit,
    }


def _paths(conn, chunks: list[ask.Retrieved]) -> dict[uuid.UUID, str]:
    """doc_id -> documents.path (repo-relative, with CORPUS_PREFIX)."""
    ids = list({c.doc_id for c in chunks})
    rows = conn.execute("SELECT doc_id, path FROM documents WHERE doc_id = ANY(%s)", (ids,))
    return dict(rows.fetchall())


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
    result: ask.AskResult | None,
    enc,
    checkout: Path = CHECKOUT,
) -> dict:
    """One rows.jsonl line (schema in report.py). result is None in retrieval-only mode."""
    paths = _paths(conn, chunks)
    pages = [paths[c.doc_id].removeprefix(CORPUS_PREFIX) for c in chunks]
    relevant = {f.id: ev.relevant[(row.id, f.id)] for f in row.required}
    # Only required cited facts: the rank metrics are defined over them (AC-3).
    chunk_facts = [{fid for fid, ids in relevant.items() if c.chunk_id in ids} for c in chunks]
    tokens = [len(enc.encode(c.content, disallowed_special=())) for c in chunks]
    metrics: dict[str, float] = {}
    if relevant:  # an answerable row whose required facts are all answer-only scores nothing
        metrics = row_metrics(
            chunk_facts,
            pages,
            {f.id: set(f.cites) for f in row.required},
            set(row.expected_docs),
            len(frozenset().union(*relevant.values())),
            tokens,
        )
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
                "distance": c.distance,
                "tokens": n,
                "facts": sorted(facts),
                "page_relevant": page in row.expected_docs,
            }
            for c, page, n, facts in zip(chunks, pages, tokens, chunk_facts, strict=True)
        ],
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
    embedder: Embedder,
    answerer: Answerer | None,
    *,
    meta: dict,
    out_root: Path = EVAL_RUNS,
    checkout: Path = CHECKOUT,
) -> Path:
    """Retrieve (and answer, unless answerer is None) every row; write the run folder (AC-7).

    answerer None is retrieval-only mode: ooc rows are skipped and the answer model is never
    called. checkout is the pinned corpus the AC-5 heading check reads. Returns the folder.
    """
    enc = tiktoken.get_encoding(TOKENIZER)
    out = out_root / f"{meta['timestamp'][:10]}-{uuid.uuid4().hex[:8]}"
    out.mkdir(parents=True)
    records: list[dict] = []
    # Appended per row, so a crash mid-run keeps what was paid for.
    with (out / "rows.jsonl").open("w", encoding="utf-8") as f:
        for row in to_run(rows, answerer is None):
            if answerer is None:
                result = None
                chunks = ask.retrieve(conn, embedder, row.question, TOP_K)
                if not chunks:
                    raise SystemExit(f"no embeddings for {embedder.name}; run `make embed`")
            else:
                result = ask.ask(conn, embedder, answerer, row.question, TOP_K)
                chunks = result.chunks
            rec = record(conn, row, ev, chunks, result, enc, checkout)
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
    summary = summarize(records, meta, notes)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "summary.md").write_text(render_md(summary), encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the eval set (spec 0004).")
    ap.add_argument("--confirm", action="store_true", help="spend: call the embed/answer models")
    ap.add_argument("--limit", type=int, help="run only the first n rows")
    ap.add_argument("--retrieval-only", action="store_true", help="skip the answer model")
    args = ap.parse_args(argv)

    m = read_manifest()
    error = verify(m)
    if error:
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    eval_bytes = EVAL_SET.read_bytes()
    eval_set = parse(eval_bytes.decode("utf-8"))
    rows = list(eval_set.rows[: args.limit] if args.limit is not None else eval_set.rows)

    with connect() as conn:
        chunk_params, corpus_sha = stored_chunk_params(conn, m.sha)
        try:
            ev = evidence_mod.check(rows, conn)
        except EvidenceError as e:
            raise SystemExit(str(e)) from None
        for w in ev.warnings:
            print(f"warning: {w}", file=sys.stderr)

        todo = to_run(rows, args.retrieval_only)
        n_ans = sum(r.answerable for r in todo)
        mode = "retrieval-only" if args.retrieval_only else "full"
        cost = estimate(todo, args.retrieval_only)
        print(
            f"eval {eval_set.version}: {len(todo)} rows ({n_ans} answerable, "
            f"{len(todo) - n_ans} ooc), mode {mode}"
        )
        print(
            f"estimated cost: ${cost['total_usd']:.4f} (embed ~{cost['embed_tokens']} tokens "
            f"${cost['embed_usd']:.6f}, answers ${cost['answer_usd']:.4f})"
        )
        if not args.confirm:
            print("Dry run: add CONFIRM=1 to spend.")
            return 0

        # Built only after confirm, so a dry run needs no API key.
        embedder = make_embedder()
        answerer = None if args.retrieval_only else make_answerer()
        meta = metadata(
            eval_set.version,
            eval_bytes,
            corpus_sha,
            chunk_params,
            embedder.name,
            answerer.name if answerer else None,
            len(todo),
            args.limit,
        )
        out = run(conn, rows, ev, embedder, answerer, meta=meta)

    overall = json.loads((out / "summary.json").read_text(encoding="utf-8"))["groups"]["overall"]
    print(f"wrote {out}")
    for key in HEADLINE:
        if key in overall:
            s = overall[key]
            print(f"  {key}: {s['mean']:.3f} ± {s['se']:.3f} (n={s['n']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
