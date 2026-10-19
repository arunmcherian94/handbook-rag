"""Embed chunks into chunk_embeddings (spec 0003, AC-3, AC-4; spec 0005 AC-4, AC-13).

Functional core, imperative shell: retry and bad-input isolation (embed_with_retry, embed_batch)
are pure, so they are unit-tested without a DB; run() is the shell that owns SQL and commits
once per successful (sub-)batch. `sleep` and `rand` are injected so tests check backoff timing
without waiting or randomness. Everything is scoped to one chunk config (spec 0005 AC-4), and
main() prints a cost estimate and spends only with --confirm (spec 0005 AC-13).
"""

import argparse
import hashlib
import logging
import random
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field

import openai

from handbook_rag.constants import (
    BACKOFF_BASE,
    BACKOFF_CAP,
    BASELINE_CONFIG,
    CHUNK_CONFIGS,
    EMBED_BATCH,
    EST_EMBED_USD_PER_1M,
    MAX_ATTEMPTS,
    MAX_INPUT_TOKENS,
    MAX_REQUEST_TOKENS,
    PROGRESS_EVERY,
    RETRY_4XX,
)
from handbook_rag.db import connect, vector_literal
from handbook_rag.models import Embedder, make_embedder

log = logging.getLogger(__name__)


@dataclass
class Pending:
    chunk_id: object
    doc_id: object
    content: str
    token_count: int


@dataclass
class Summary:
    embedded: int = 0
    skipped: int = 0
    failed: list = field(default_factory=list)  # (chunk_id, doc_id, status, message)

    @property
    def ok(self) -> bool:
        return not self.failed


class RetriesExhausted(Exception):
    pass


class FatalEmbedError(Exception):
    """401/403/404: retrying or splitting cannot help. The SDK error is __cause__."""


def _backoff(n: int, rand: Callable[[], float]) -> float:
    d = min(BACKOFF_CAP, BACKOFF_BASE * 2**n)
    return d / 2 + rand() * d / 2  # equal jitter


def _retry_after(e: openai.APIStatusError) -> float | None:
    try:
        return min(BACKOFF_CAP, max(0.0, float(e.response.headers["retry-after"])))
    except (KeyError, ValueError):
        return None


def embed_with_retry(embedder: Embedder, texts: list[str], sleep, rand) -> list[list[float]]:
    for n in range(MAX_ATTEMPTS):
        try:
            return embedder.embed(texts)
        except (openai.BadRequestError, openai.UnprocessableEntityError):
            raise  # caller isolates the bad input
        except (
            openai.AuthenticationError,
            openai.PermissionDeniedError,
            openai.NotFoundError,
        ) as e:
            raise FatalEmbedError(f"HTTP {e.status_code}: {e}") from e
        except openai.RateLimitError as e:
            err, delay = e, _retry_after(e)
        except openai.APIStatusError as e:
            if e.status_code < 500 and e.status_code not in RETRY_4XX:
                raise  # other 4xx: caller isolates it like bad input
            err, delay = e, None
        except openai.APIConnectionError as e:  # includes APITimeoutError
            err, delay = e, None
        if n == MAX_ATTEMPTS - 1:
            log.error(
                "embed failed after %d attempts: %s: %s", MAX_ATTEMPTS, type(err).__name__, err
            )
            raise RetriesExhausted(f"{type(err).__name__} after {MAX_ATTEMPTS} attempts") from err
        sleep(_backoff(n, rand) if delay is None else delay)
    raise AssertionError("unreachable")


def _fail(item: Pending, status, message: str) -> tuple:
    log.error(
        "permanent failure chunk_id=%s doc_id=%s status=%s: %s",
        item.chunk_id,
        item.doc_id,
        status,
        message,
    )
    return (item.chunk_id, item.doc_id, status, message)


def embed_batch(embedder, items: list[Pending], sleep, rand, on_success) -> list[tuple]:
    """Embed items; return permanent failures. RetriesExhausted/FatalEmbedError propagate."""
    failures, ok = [], []
    for it in items:
        if not it.content.strip():
            failures.append(_fail(it, "local", "empty or whitespace-only content"))
        elif it.token_count > MAX_INPUT_TOKENS:
            failures.append(_fail(it, "local", f"{it.token_count} tokens > {MAX_INPUT_TOKENS}"))
        else:
            ok.append(it)
    _send(embedder, ok, sleep, rand, on_success, failures)
    return failures


def _send(embedder, items, sleep, rand, on_success, failures) -> None:
    if not items:
        return
    if len(items) > 1 and sum(i.token_count for i in items) > MAX_REQUEST_TOKENS:
        return _split(embedder, items, sleep, rand, on_success, failures)
    try:
        vectors = embed_with_retry(embedder, [i.content for i in items], sleep, rand)
    except openai.APIStatusError as e:  # 400/422 and other non-fatal 4xx (e.g. 413)
        if len(items) > 1:
            return _split(embedder, items, sleep, rand, on_success, failures)
        failures.append(_fail(items[0], e.status_code, str(e)))
        return
    on_success(items, vectors)


def _split(embedder, items, sleep, rand, on_success, failures) -> None:
    mid = len(items) // 2
    _send(embedder, items[:mid], sleep, rand, on_success, failures)
    _send(embedder, items[mid:], sleep, rand, on_success, failures)


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


PENDING = """
SELECT c.chunk_id, c.doc_id, c.content, c.token_count FROM chunks c
WHERE NOT EXISTS (SELECT 1 FROM chunk_embeddings e WHERE e.chunk_id = c.chunk_id AND e.model = %s)
  AND c.config_id = %s
ORDER BY c.chunk_id
"""
SKIPPED = """
SELECT count(*) FROM chunks c JOIN chunk_embeddings e ON e.chunk_id = c.chunk_id
WHERE e.model = %s AND c.config_id = %s
"""
# The estimate must match what run() would embed, so it takes the same first `limit` rows.
COST = """
SELECT count(*), coalesce(sum(token_count), 0) FROM (
    SELECT c.token_count FROM chunks c
    WHERE NOT EXISTS (
        SELECT 1 FROM chunk_embeddings e WHERE e.chunk_id = c.chunk_id AND e.model = %s
    )
      AND c.config_id = %s
    ORDER BY c.chunk_id LIMIT %s
) t
"""
# Insert only if the chunk still holds the text that was embedded: a concurrent `make chunk`
# may have changed or deleted it, and a stale vector must never sit beside new text (AC-2).
INSERT = """
INSERT INTO chunk_embeddings (chunk_id, model, embedding)
SELECT c.chunk_id, %s, %s::vector FROM chunks c WHERE c.chunk_id = %s AND md5(c.content) = %s
ON CONFLICT DO NOTHING
"""


def pending_cost(conn, model, config_id, limit=None) -> tuple[int, int]:
    """(count, summed token_count) of the chunks run() would embed for this config and model."""
    return tuple(conn.execute(COST, (model, config_id, limit)).fetchone())


def run(
    conn,
    embedder,
    batch=EMBED_BATCH,
    limit=None,
    sleep=time.sleep,
    rand=random.random,
    config_id=BASELINE_CONFIG,
) -> Summary:
    summary = Summary()
    summary.skipped = conn.execute(SKIPPED, (embedder.name, config_id)).fetchone()[0]
    sql, params = PENDING, [embedder.name, config_id]
    if limit is not None:
        sql, params = sql + " LIMIT %s", [embedder.name, config_id, limit]
    rows = [Pending(*r) for r in conn.execute(sql, params).fetchall()]
    conn.commit()

    def on_success(items, vectors):
        with conn.cursor() as cur:
            inserted = 0
            for i, v in zip(items, vectors, strict=True):
                cur.execute(INSERT, (embedder.name, vector_literal(v), i.chunk_id, _md5(i.content)))
                inserted += cur.rowcount
        conn.commit()  # one commit per successful (sub-)batch (AC-4)
        summary.embedded += inserted
        if inserted < len(items):
            log.warning(
                "%d chunks changed or vanished while embedding; left for the next run",
                len(items) - inserted,
            )

    start = time.monotonic()
    for n, i in enumerate(range(0, len(rows), batch), 1):
        chunk = rows[i : i + batch]
        try:
            summary.failed += embed_batch(embedder, chunk, sleep, rand, on_success)
        except Exception:  # log where the run stopped, whatever stopped it (AC-3)
            log.error(
                "run stopped in batch chunk_id %s .. %s", chunk[0].chunk_id, chunk[-1].chunk_id
            )
            raise
        if n % PROGRESS_EVERY == 0:
            log.info(
                "embedded %d/%d pending (%.0fs)",
                summary.embedded,
                len(rows),
                time.monotonic() - start,
            )
    return summary


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="Embed chunks that have no embedding for the model.")
    ap.add_argument("--config", default=BASELINE_CONFIG, help="chunk config_id to embed")
    ap.add_argument("--confirm", action="store_true", help="spend; without it, a dry run")
    ap.add_argument("--limit", type=int, default=None, help="embed at most N pending chunks")
    args = ap.parse_args(argv)
    if args.config not in CHUNK_CONFIGS:
        raise SystemExit(f"unknown config {args.config!r}; known: {', '.join(CHUNK_CONFIGS)}")
    embedder = make_embedder()
    try:
        with connect() as conn:
            n, tokens = pending_cost(conn, embedder.name, args.config, args.limit)
            conn.commit()
            usd = tokens / 1e6 * EST_EMBED_USD_PER_1M
            print(
                f"embed {args.config}: {n} pending chunks for {embedder.name}, "
                f"~{tokens} tokens, estimated ${usd:.4f}"
            )
            if not args.confirm:
                print("Dry run: add CONFIRM=1 to spend.")
                return 0
            s = run(conn, embedder, limit=args.limit, config_id=args.config)
    except (RetriesExhausted, FatalEmbedError) as e:
        log.error("embedding stopped: %s", e)
        return 2
    log.info(
        "embedded %d, skipped %d (already embedded for %s), failed %d",
        s.embedded,
        s.skipped,
        embedder.name,
        len(s.failed),
    )
    return 1 if s.failed else 0


if __name__ == "__main__":
    sys.exit(main())
