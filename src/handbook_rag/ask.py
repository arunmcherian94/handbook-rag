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

from handbook_rag.constants import MAX_CITATION, TOKENIZER, TOP_K, TRACE_PATH
from handbook_rag.db import connect, vector_literal
from handbook_rag.embed import embed_with_retry
from handbook_rag.models import Answerer, Embedder, make_answerer, make_embedder
from handbook_rag.prompts import SYSTEM_PROMPT

SEARCH = """
-- No section heading (intro text, or a doc without headings): cite the doc title instead.
SELECT c.chunk_id, c.doc_id, d.url_path, COALESCE(c.heading, d.title) AS heading, c.content,
       e.embedding <=> %(q)s::vector AS distance,
       c.chunk_size, c.chunk_overlap, c.tokenizer, c.commit_sha
FROM chunk_embeddings e
JOIN chunks c USING (chunk_id)
JOIN documents d USING (doc_id)
WHERE e.model = %(model)s
ORDER BY e.embedding <=> %(q)s::vector
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


def retrieve(
    conn, embedder: Embedder, question: str, k: int = TOP_K, sleep=time.sleep, rand=random.random
) -> list[Retrieved]:
    """Exact cosine top-k for the embedder's model; no index (AC-5).

    The embedder's SDK retries are off, so the query goes through the same capped retry policy.
    """
    q = vector_literal(embed_with_retry(embedder, [question], sleep, rand)[0])
    rows = conn.execute(SEARCH, {"q": q, "model": embedder.name, "k": k}).fetchall()
    return [Retrieved(n, *row) for n, row in enumerate(rows, 1)]


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
    k: int = TOP_K,
    clock=time.perf_counter,
) -> AskResult:
    t0 = clock()
    chunks = retrieve(conn, embedder, question, k)
    t1 = clock()
    if not chunks:
        raise SystemExit(f"no embeddings for {embedder.name}; run `make embed`")
    system, user = build_prompt(question, chunks)
    completion = answerer.answer(system, user)
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
    first = result.chunks[0]
    record = {
        "timestamp": result.timestamp,
        "corpus_sha": shas[0] if len(shas) == 1 else shas,
        "chunk_params": {
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Ask the GitLab handbook a question.")
    ap.add_argument("question")
    ap.add_argument("--k", type=int, default=TOP_K)
    args = ap.parse_args(argv)
    embedder, answerer = make_embedder(), make_answerer()
    with connect() as conn:
        result = ask(conn, embedder, answerer, args.question, args.k)
    print(format_result(result))
    append_trace(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
