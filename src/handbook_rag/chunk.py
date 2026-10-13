"""Split ingested documents into fixed-size token windows (spec 0003, AC-1, AC-2)."""

import argparse
import re
import sys
import uuid
from bisect import bisect_right
from dataclasses import dataclass
from itertools import accumulate
from pathlib import Path

import tiktoken

from handbook_rag.corpus import read_manifest, verify
from handbook_rag.db import connect

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
TOKENIZER = "cl100k_base"
SCHEMA = Path("db/init/003_chunks.sql")
BATCH = 500

HEADING = re.compile(r"#{1,6}[ \t]+(.*)")
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
ATTRS = re.compile(r"\s*\{[#.][^}]*\}\s*$")  # Hugo heading attributes: {#id}, {.class #id}
BOLD = re.compile(r"^(\*\*|__)((?:(?!\1).)+)\1$")  # a heading wrapped whole in bold


@dataclass(frozen=True)
class Chunk:
    chunk_id: uuid.UUID
    chunk_index: int
    content: str
    token_count: int
    heading: str | None


@dataclass
class RunResult:
    skipped: bool
    sha: str
    docs: int = 0
    chunks: int = 0
    changed: int = 0
    deleted: int = 0


def find_headings(body: str) -> tuple[list[int], list[str]]:
    """Byte offsets and text of ATX headings outside fenced code blocks."""
    starts: list[int] = []
    texts: list[str] = []
    fence: str | None = None  # the open fence's run of ` or ~
    offset = 0
    for line in body.split("\n"):
        f = FENCE.match(line)
        if fence is None and f:
            fence = f.group(1)
        elif (
            fence is not None and f and f.group(1)[0] == fence[0] and len(f.group(1)) >= len(fence)
        ):
            fence = None
        elif fence is None and (m := HEADING.fullmatch(line.rstrip("\r"))):
            text = re.sub(r"(^|[ \t]+)#+[ \t]*$", "", m.group(1)).strip()
            text = BOLD.sub(r"\2", ATTRS.sub("", text)).strip()
            if text:
                starts.append(offset)
                texts.append(text)
        offset += len(line.encode("utf-8")) + 1
    return starts, texts


def first_text_byte(raw: bytes, a: int, b: int) -> int:
    """Offset of the first non-blank character in raw[a:b], past any cut-off multi-byte tail.

    Headings are matched from here, so a chunk opening with blank lines (or the remains of a
    split character) and then a heading is attributed to that heading.
    """
    while a < b and 0x80 <= raw[a] < 0xC0:  # UTF-8 continuation bytes
        a += 1
    while a < b and raw[a] in b" \t\r\n\x0b\x0c":
        a += 1
    return a


def chunk_doc(
    doc_id: uuid.UUID, body: str, enc, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[Chunk]:
    """Windows of `size` tokens every size-overlap tokens; the last one reaches the end.

    Slices the body by byte offset so content is the exact source text. A multi-byte
    character cut by a window edge is dropped there; the overlap carries it whole.
    """
    if not body.strip():
        return []
    tokens = enc.encode(body, disallowed_special=())  # handbook text may contain <|endoftext|>
    offsets = [0, *accumulate(len(enc.decode_single_token_bytes(t)) for t in tokens)]
    raw = body.encode("utf-8")
    h_starts, h_texts = find_headings(body)
    stride = size - overlap
    chunks = []
    for i, start in enumerate(range(0, len(tokens), stride)):
        end = min(start + size, len(tokens))
        content = raw[offsets[start] : offsets[end]].decode("utf-8", errors="ignore")
        k = bisect_right(h_starts, first_text_byte(raw, offsets[start], offsets[end])) - 1
        chunks.append(
            Chunk(
                chunk_id=uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{size}:{overlap}:{i}"),
                chunk_index=i,
                content=content,
                token_count=end - start,
                heading=h_texts[k] if k >= 0 else None,
            )
        )
        if end == len(tokens):
            break
    return chunks


UPSERT = """
INSERT INTO chunks (chunk_id, doc_id, chunk_index, content, token_count, heading,
                    chunk_size, chunk_overlap, tokenizer, commit_sha)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (chunk_id) DO UPDATE SET
    doc_id = EXCLUDED.doc_id, chunk_index = EXCLUDED.chunk_index,
    content = EXCLUDED.content, token_count = EXCLUDED.token_count,
    heading = EXCLUDED.heading, chunk_size = EXCLUDED.chunk_size,
    chunk_overlap = EXCLUDED.chunk_overlap, tokenizer = EXCLUDED.tokenizer,
    commit_sha = EXCLUDED.commit_sha
"""


def up_to_date(conn, sha: str) -> int | None:
    """Existing chunk count if every chunk is current and every non-empty doc has chunks."""
    total, current = conn.execute(
        """SELECT count(*), count(*) FILTER (
               WHERE commit_sha = %s AND chunk_size = %s AND chunk_overlap = %s AND tokenizer = %s)
           FROM chunks""",
        (sha, CHUNK_SIZE, CHUNK_OVERLAP, TOKENIZER),
    ).fetchone()
    (uncovered,) = conn.execute(
        """SELECT EXISTS (SELECT 1 FROM documents d WHERE d.body ~ '\\S'
                          AND NOT EXISTS (SELECT 1 FROM chunks c WHERE c.doc_id = d.doc_id))"""
    ).fetchone()
    return total if total and total == current and not uncovered else None


def flush(conn, rows: list[tuple]) -> int:
    """Upsert a batch; drop embeddings of chunks whose text changed. Returns that count."""
    ids = [r[0] for r in rows]
    old = dict(
        conn.execute("SELECT chunk_id, content FROM chunks WHERE chunk_id = ANY(%s)", (ids,))
    )
    changed = [r[0] for r in rows if r[0] in old and old[r[0]] != r[3]]
    if changed:  # a stale vector must never sit beside new text
        conn.execute("DELETE FROM chunk_embeddings WHERE chunk_id = ANY(%s)", (changed,))
    with conn.cursor() as cur:
        cur.executemany(UPSERT, rows)
    return len(changed)


def run(conn, force: bool = False) -> RunResult:
    m = read_manifest()
    error = verify(m)
    if error:
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    enc = tiktoken.get_encoding(TOKENIZER)
    with conn.transaction():
        conn.execute(SCHEMA.read_text())
        (stale,) = conn.execute(
            "SELECT EXISTS (SELECT 1 FROM documents WHERE commit_sha <> %s)", (m.sha,)
        ).fetchone()
        if stale:
            raise SystemExit("documents are stale vs CORPUS.md. Run `make ingest` first.")
        if not force and (count := up_to_date(conn, m.sha)) is not None:
            return RunResult(skipped=True, sha=m.sha, chunks=count)

        result = RunResult(skipped=False, sha=m.sha)
        ids: list[uuid.UUID] = []
        rows: list[tuple] = []
        with conn.cursor(name="chunk_docs") as docs:
            docs.execute("SELECT doc_id, body FROM documents ORDER BY doc_id")
            for doc_id, body in docs:
                result.docs += 1
                for c in chunk_doc(doc_id, body, enc):
                    ids.append(c.chunk_id)
                    rows.append(
                        (c.chunk_id, doc_id, c.chunk_index, c.content, c.token_count, c.heading,
                         CHUNK_SIZE, CHUNK_OVERLAP, TOKENIZER, m.sha)
                    )  # fmt: skip
                if len(rows) >= BATCH:
                    result.changed += flush(conn, rows)
                    rows = []
        if rows:
            result.changed += flush(conn, rows)
        # The table holds exactly one parameter set; embeddings cascade.
        result.deleted = conn.execute(
            "DELETE FROM chunks c WHERE NOT EXISTS "
            "(SELECT 1 FROM unnest(%s::uuid[]) AS keep(id) WHERE keep.id = c.chunk_id)",
            (ids,),
        ).rowcount
        result.chunks = len(ids)
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Chunk ingested documents (spec 0003).")
    ap.add_argument("--force", action="store_true", help="skip the early-exit check")
    args = ap.parse_args(argv)
    with connect() as conn:
        r = run(conn, force=args.force)
    params = f"{CHUNK_SIZE}/{CHUNK_OVERLAP} {TOKENIZER}"
    if r.skipped:
        print(
            f"chunks up to date: sha {r.sha[:12]}, {params}, {r.chunks} chunks "
            "(use FORCE=1 to rebuild)"
        )
    else:
        print(
            f"chunked {r.docs} docs -> {r.chunks} chunks ({params}, sha {r.sha[:12]}); "
            f"content changed {r.changed}, deleted {r.deleted}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
