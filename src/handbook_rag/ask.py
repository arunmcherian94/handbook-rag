"""Naive RAG baseline: retrieve, answer from excerpts, cite by number, trace (spec 0003).

Functional core, imperative shell: build_prompt and parse_citations are pure and unit-tested;
retrieve and ask do the I/O. The embedder and answerer arrive as ports (see models/base.py),
and `clock` is injected so latency fields are testable.
"""

import argparse
import json
import random
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import tiktoken

from handbook_rag import acl, identity
from handbook_rag.constants import (
    BASELINE_CONFIG,
    EST_ANSWER_USD_PER_ROW,
    MAX_CITATION,
    TOKENIZER,
    TOP_K,
    TRACE_PATH,
)
from handbook_rag.corpus import read_manifest, verify
from handbook_rag.db import connect, vector_literal
from handbook_rag.embed import embed_with_retry
from handbook_rag.identity import Principal
from handbook_rag.models import (
    Answerer,
    Completion,
    Embedder,
    describe_embedder,
    embed_usd_per_1m,
    make_answerer,
    make_embedder,
    resolve_answer_spec,
    resolve_embed_spec,
)
from handbook_rag.prompts import NOT_FOUND, SYSTEM_PROMPT
from handbook_rag.spend import log_spend, paid

SEARCH = """
-- No section heading (intro text, or a doc without headings): cite the doc title instead.
SELECT c.chunk_id, c.doc_id, d.url_path, COALESCE(c.heading, d.title) AS heading, c.content,
       e.embedding <=> %(q)s::vector AS distance,
       c.chunk_size, c.chunk_overlap, c.tokenizer, c.commit_sha
FROM chunk_embeddings e
JOIN chunks c USING (chunk_id)
JOIN documents d USING (doc_id)
WHERE e.model = %(model)s AND c.config_id = %(config_id)s
  -- Spec 0007, AC-8: the principal's groups filter before ranking; there is no unfiltered path.
  AND c.allowed_groups && %(groups)s::text[]
-- OpenAI embeddings are unit-normalised, so <=> (cosine) and <#> (neg. inner product) rank alike.
-- Choose between them on cost and index support. <-> is L2 distance, <+> is L1.
-- chunk_id breaks exact ties (duplicate pages chunk identically), so the order is reproducible.
ORDER BY e.embedding <=> %(q)s::vector, c.chunk_id
LIMIT %(k)s
"""

# [2], [1, 3], [1-3], [1–3], [1; 2] and mixes like [1-2, 4].
_ITEM = r"\d+(?:\s*[-–]\s*\d+)?"
CITATION = re.compile(rf"\[\s*({_ITEM}(?:\s*[,;]\s*{_ITEM})*)\s*\]")


@dataclass(frozen=True)
class Retrieved:
    n: int  # 1-based rank, the number the model cites
    chunk_id: uuid.UUID
    doc_id: uuid.UUID
    url_path: str
    heading: str  # section heading, or the doc title when the chunk has none
    content: str
    distance: float
    chunk_size: int
    chunk_overlap: int
    tokenizer: str
    commit_sha: str


@dataclass(frozen=True)
class Citation:
    n: int
    url_path: str
    heading: str


@dataclass
class AskResult:
    question: str
    answer: str
    citations: list[Citation]
    invalid_citations: list[int]
    chunks: list[Retrieved]
    k: int
    embed_model: str
    answer_model: str
    tokens: dict[str, int]
    latency_ms: dict[str, float]
    truncated: bool
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


def search(
    conn, q: str, model: str, principal: Principal, k: int, config_id: str = BASELINE_CONFIG
) -> list[Retrieved]:
    """Exact cosine top-k of an embedded query (a vector_literal) over the chunks the principal
    may see (spec 0007, AC-8). retrieve() and the permissions suite both go through here."""
    rows = conn.execute(
        SEARCH,
        {"q": q, "model": model, "k": k, "config_id": config_id, "groups": principal.group_list},
    ).fetchall()
    return [Retrieved(n, *row) for n, row in enumerate(rows, 1)]


def retrieve(
    conn,
    embedder: Embedder,
    question: str,
    principal: Principal,
    k: int = TOP_K,
    sleep=time.sleep,
    rand=random.random,
    config_id: str = BASELINE_CONFIG,
) -> list[Retrieved]:
    """Exact cosine top-k for the embedder's model; no index (AC-5), over the chunks the
    principal may see (spec 0007, AC-8: principal is required, there is no unfiltered path).

    The embedder's SDK retries are off, so the query goes through the same capped retry policy.
    """
    q = vector_literal(embed_with_retry(embedder, [question], sleep, rand)[0])
    return search(conn, q, embedder.name, principal, k, config_id)


def build_prompt(question: str, chunks: list[Retrieved]) -> tuple[str, str]:
    excerpts = "\n\n".join(f"[{c.n}] {c.url_path} — {c.heading}\n{c.content}" for c in chunks)
    return SYSTEM_PROMPT, f"Handbook excerpts:\n\n{excerpts}\n\nQuestion: {question}"


def _expand(group: str) -> list[int]:
    """'1-3, 5' -> [1, 2, 3, 5]. A descending range keeps both ends as written."""
    out: list[int] = []
    for part in re.split(r"\s*[,;]\s*", group.strip()):
        m = re.fullmatch(r"(\d+)(?:\s*[-–]\s*(\d+))?", part)
        a, b = int(m[1]), int(m[2] or m[1])
        out += range(a, b + 1) if a <= b else [a, b]
    return out


def parse_citations(text: str, chunks: list[Retrieved]) -> tuple[list[Citation], list[int]]:
    """Map cited numbers to chunks. Out-of-range numbers are returned, not dropped (AC-6)."""
    by_n = {c.n: c for c in chunks}
    valid: list[int] = []
    invalid: list[int] = []
    for group in CITATION.findall(text):
        numbers = [int(x) for x in re.findall(r"\d+", group)]
        if max(numbers) > MAX_CITATION:
            continue
        for n in _expand(group):
            seen = valid if n in by_n else invalid
            if n not in seen:
                seen.append(n)
    return [Citation(n, by_n[n].url_path, by_n[n].heading) for n in valid], invalid


def ask(
    conn,
    embedder: Embedder,
    answerer: Answerer,
    question: str,
    principal: Principal,
    k: int = TOP_K,
    clock=time.perf_counter,
    config_id: str = BASELINE_CONFIG,
) -> AskResult:
    t0 = clock()
    chunks = retrieve(conn, embedder, question, principal, k, config_id=config_id)
    t1 = clock()
    if chunks:
        system, user = build_prompt(question, chunks)
        completion = answerer.answer(system, user)
    else:
        # Spec 0007, AC-8: nothing visible to this principal gets the standard reply, never a
        # permission message (and no model call: there is nothing to answer from).
        completion = Completion(NOT_FOUND, 0, 0, False)
    t2 = clock()
    citations, invalid = parse_citations(completion.text, chunks)
    return AskResult(
        question=question,
        answer=completion.text,
        citations=citations,
        invalid_citations=invalid,
        chunks=chunks,
        k=k,
        embed_model=embedder.name,
        answer_model=answerer.name,
        tokens={
            "answer_input": completion.input_tokens,
            "answer_output": completion.output_tokens,
            # Estimate: the Embedder protocol doesn't expose usage; same cl100k tokenizer.
            "query_embed": len(
                tiktoken.get_encoding(TOKENIZER).encode(question, disallowed_special=())
            ),
        },
        latency_ms={
            "retrieve": (t1 - t0) * 1000,
            "answer": (t2 - t1) * 1000,
            "total": (t2 - t0) * 1000,
        },
        truncated=completion.truncated,
    )


def append_trace(result: AskResult, path: Path = TRACE_PATH) -> dict:
    """Append one JSON line per ask (AC-8)."""
    shas = sorted({c.commit_sha for c in result.chunks})
    first = result.chunks[0] if result.chunks else None
    record = {
        "timestamp": result.timestamp,
        "corpus_sha": shas[0] if len(shas) == 1 else shas or None,
        "chunk_params": first
        and {
            "chunk_size": first.chunk_size,
            "chunk_overlap": first.chunk_overlap,
            "tokenizer": first.tokenizer,
        },
        "embed_model": result.embed_model,
        "answer_model": result.answer_model,
        "k": result.k,
        "question": result.question,
        "retrieved": [{"chunk_id": str(c.chunk_id), "distance": c.distance} for c in result.chunks],
        "answer": result.answer,
        "citations": [
            {"n": c.n, "url_path": c.url_path, "heading": c.heading} for c in result.citations
        ],
        "invalid_citations": result.invalid_citations,
        "truncated": result.truncated,
        "tokens": result.tokens,
        "latency_ms": result.latency_ms,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def format_result(result: AskResult) -> str:
    lines = [result.answer, "", "Sources:"]
    lines += [f"  [{c.n}] {c.url_path} — {c.heading}" for c in result.citations]
    if not result.citations:
        lines.append("  (none)")
    warnings = []
    if result.invalid_citations:
        warnings.append(f"invalid citations {result.invalid_citations}")
    if result.truncated:
        warnings.append("answer truncated at the output token cap")
    if warnings:
        lines += ["", "WARNING: " + "; ".join(warnings)]
    lines += ["", "Retrieved:"]
    lines += [f"  [{c.n}] {c.distance:.4f} {c.url_path} — {c.heading}" for c in result.chunks]
    t, ms = result.tokens, result.latency_ms
    lines += [
        "",
        f"tokens: answer in {t['answer_input']}, out {t['answer_output']}, "
        f"query embed ~{t['query_embed']} | latency: retrieve {ms['retrieve']:.0f} ms, "
        f"answer {ms['answer']:.0f} ms, total {ms['total']:.0f} ms",
    ]
    return "\n".join(lines)


def estimate(question: str, embed_spec: str) -> float:
    """Spec 0009, AC-1: one query embed at the model's price plus the flat per-answer cost."""
    tokens = len(tiktoken.get_encoding(TOKENIZER).encode(question, disallowed_special=()))
    return tokens * embed_usd_per_1m(embed_spec) / 1_000_000 + EST_ANSWER_USD_PER_ROW


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Ask the GitLab handbook a question.")
    ap.add_argument("question")
    ap.add_argument("--as", dest="user_id", required=True, help="fixture user to ask as")
    ap.add_argument("--k", type=int, default=TOP_K)
    ap.add_argument("--confirm", action="store_true", help="spend; without it, a dry run")
    args = ap.parse_args(argv)
    if error := verify(read_manifest()):
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    try:  # an unknown model or bad @dims fails the dry run
        embed_spec = describe_embedder(resolve_embed_spec()).name
        usd = estimate(args.question, embed_spec)
    except ValueError as e:
        raise SystemExit(str(e)) from None
    answer_spec = resolve_answer_spec()
    with connect() as conn:
        # Checked here, not in ask(): an empty retrieval there means nothing visible to the
        # principal and must look like any other NOT_FOUND (spec 0007, AC-8).
        (embedded,) = conn.execute(
            "SELECT EXISTS (SELECT 1 FROM chunk_embeddings WHERE model = %s)", (embed_spec,)
        ).fetchone()
        if not embedded:
            raise SystemExit(
                f"no embeddings for {embed_spec}; run `make embed` for the cost, "
                "then `make paid-embed`"
            )
        policy = acl.load_policy(conn)
        try:
            acl.check_stale(conn, policy)  # spec 0007, AC-5: never filter on stale ACLs
        except (acl.StaleACL, acl.AclError) as e:
            raise SystemExit(str(e)) from None
        principal = identity.load(args.user_id, policy)
        print(f"ask as {args.user_id}: {embed_spec}, {answer_spec}, estimated cost ${usd:.4f}")
        if not paid(args.confirm, "ask"):  # spec 0009, AC-1
            return 0
        # Built only after confirm, so a dry run needs no API key.
        embedder, answerer = make_embedder(embed_spec), make_answerer(answer_spec)
        status = "failed"
        try:
            result = ask(conn, embedder, answerer, args.question, principal, args.k)
            status = "ok"
        finally:  # spec 0009, AC-3: logged even when the run fails after spending
            log_spend(
                "ask",
                usd,
                run_id=None,
                embed_model=embed_spec,
                answer_model=answer_spec,
                status=status,
            )
    print(format_result(result))
    append_trace(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
