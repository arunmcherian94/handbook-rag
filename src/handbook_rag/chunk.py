"""Split ingested documents into chunks under a named config (spec 0003; 0005; 0006).

`fixed` configs cut token windows (chunk_doc); `structural` configs cut at headings and split
or merge inside them (chunk_structural); `structural-packed` configs pack whole sections up to
max_tokens (chunk_packed). Functional core, imperative shell: all are pure functions of a body,
unit-tested without a DB; run() owns the transaction.
"""

import argparse
import re
import sys
import uuid
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from itertools import accumulate

import tiktoken
from psycopg.types.json import Jsonb

from handbook_rag.constants import (
    BASELINE_CONFIG,
    CHECKOUT,
    CHUNK_BATCH,
    CHUNK_CONFIGS,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHUNKS_SCHEMA,
    TOKENIZER,
)
from handbook_rag.corpus import read_manifest, verify
from handbook_rag.db import connect

HEADING = re.compile(r"#{1,6}[ \t]+(.*)")
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
ATTRS = re.compile(r"\s*\{[#.][^}]*\}\s*$")  # Hugo heading attributes: {#id}, {.class #id}
BOLD = re.compile(r"^(\*\*|__)((?:(?!\1).)+)\1$")  # a heading wrapped whole in bold
SENTENCE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Chunk:
    chunk_id: uuid.UUID
    chunk_index: int
    content: str
    token_count: int
    heading: str | None
    heading_path: tuple[str, ...] | None = None
    line_start: int | None = None
    line_end: int | None = None


@dataclass
class RunResult:
    skipped: bool
    sha: str
    docs: int = 0
    chunks: int = 0
    changed: int = 0
    deleted: int = 0


def lines_with_fence(body: str):
    """(start byte, line, inside_fence) per line; fence open/close lines count as inside."""
    fence: str | None = None  # the open fence's run of ` or ~
    offset = 0
    for line in body.split("\n"):
        f = FENCE.match(line)
        if fence is None and f:
            fence = f.group(1)
            yield offset, line, True
        elif (
            fence is not None and f and f.group(1)[0] == fence[0] and len(f.group(1)) >= len(fence)
        ):
            fence = None
            yield offset, line, True
        else:
            yield offset, line, fence is not None
        offset += len(line.encode("utf-8")) + 1


def headings(body: str) -> list[tuple[int, int, str]]:
    """(start byte, level, text) of ATX headings outside fenced code blocks (spec 0005, AC-6)."""
    found = []
    for offset, line, fenced in lines_with_fence(body):
        if not fenced and (m := HEADING.fullmatch(line.rstrip("\r"))):
            text = re.sub(r"(^|[ \t]+)#+[ \t]*$", "", m.group(1)).strip()
            text = BOLD.sub(r"\2", ATTRS.sub("", text)).strip()
            if text:
                found.append((offset, len(line) - len(line.lstrip("#")), text))
    return found


def find_headings(body: str) -> tuple[list[int], list[str]]:
    """Byte offsets and text of ATX headings outside fenced code blocks."""
    hs = headings(body)
    return [h[0] for h in hs], [h[2] for h in hs]


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
    doc_id: uuid.UUID,
    body: str,
    enc,
    size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    config_id: str = BASELINE_CONFIG,
    with_path: bool = False,
) -> list[Chunk]:
    """Windows of `size` tokens every size-overlap tokens; the last one reaches the end.

    Slices the body by byte offset so content is the exact source text. A multi-byte
    character cut by a window edge is dropped there; the overlap carries it whole.
    Baseline ids keep their spec 0003 formula (AC-3); any other fixed config names itself in
    the id, so it can never take over the baseline's rows. with_path also records the full
    path of the attributed heading, () before the first one (spec 0006, AC-4).
    """
    key = f"{size}:{overlap}" if config_id == BASELINE_CONFIG else config_id
    if not body.strip():
        return []
    tokens = enc.encode(body, disallowed_special=())  # handbook text may contain <|endoftext|>
    offsets = [0, *accumulate(len(enc.decode_single_token_bytes(t)) for t in tokens)]
    raw = body.encode("utf-8")
    h_starts, h_texts = find_headings(body)
    h_paths = [s.path for s in sections(body) if s.level > 0] if with_path else []
    stride = size - overlap
    chunks = []
    for i, start in enumerate(range(0, len(tokens), stride)):
        end = min(start + size, len(tokens))
        content = raw[offsets[start] : offsets[end]].decode("utf-8", errors="ignore")
        k = bisect_right(h_starts, first_text_byte(raw, offsets[start], offsets[end])) - 1
        chunks.append(
            Chunk(
                chunk_id=uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{key}:{i}"),
                chunk_index=i,
                content=content,
                token_count=end - start,
                heading=h_texts[k] if k >= 0 else None,
                heading_path=(h_paths[k] if k >= 0 else ()) if with_path else None,
            )
        )
        if end == len(tokens):
            break
    return chunks


@dataclass(frozen=True)
class Section:
    start: int  # byte offsets into the body
    end: int
    level: int  # 0 for the preamble
    path: tuple[str, ...]
    parent: int | None  # index of the parent heading's section; None at the doc root


def sections(body: str) -> list[Section]:
    """One section per heading, to the next heading at any level; preamble first (AC-6).

    The preamble (text before the first heading) has level 0 and path (); whitespace-only
    sections are dropped.
    """
    raw = body.encode("utf-8")
    hs = headings(body)
    out: list[Section] = []
    first = hs[0][0] if hs else len(raw)
    if raw[:first].strip():
        out.append(Section(0, first, 0, (), None))
    stack: list[int] = []  # indices into out of the open ancestors
    for k, (start, level, text) in enumerate(hs):
        while stack and out[stack[-1]].level >= level:
            stack.pop()
        parent = stack[-1] if stack else None
        path = (out[parent].path if parent is not None else ()) + (text,)
        end = hs[k + 1][0] if k + 1 < len(hs) else len(raw)
        out.append(Section(start, end, level, path, parent))
        stack.append(len(out) - 1)
    return out


def merge_groups(secs: list[Section], count, max_tokens: int, min_tokens: int) -> list[list[int]]:
    """Group section indices: tiny sections absorb adjacent siblings (AC-8).

    A section under min_tokens takes the following sections while each is its sibling (same
    parent instance and level), the span stays <= max_tokens and the group is under min. If
    none was taken, it joins the preceding group when that group is its adjacent siblings and
    the span fits. `count(a, b)` is the token count of body bytes a..b.
    """

    def sibling(a: int, b: int) -> bool:
        x, y = secs[a], secs[b]
        return x.level > 0 and x.level == y.level and x.parent == y.parent

    groups: list[list[int]] = []
    i = 0
    while i < len(secs):
        group = [i]
        j = i + 1
        if secs[i].level > 0 and count(secs[i].start, secs[i].end) < min_tokens:
            while (
                j < len(secs)
                and sibling(i, j)
                and count(secs[i].start, secs[j - 1].end) < min_tokens
                and count(secs[i].start, secs[j].end) <= max_tokens
            ):
                group.append(j)
                j += 1
            prev = groups[-1] if groups else None
            if (
                len(group) == 1
                and prev
                and prev[-1] == i - 1
                and sibling(prev[0], i)
                and count(secs[prev[0]].start, secs[i].end) <= max_tokens
            ):
                prev.append(i)
                i = j
                continue
        groups.append(group)
        i = j
    return groups


def paragraph_starts(text: str) -> list[int]:
    """Byte offsets (in text) of paragraphs after the first: a non-blank line after a blank one,
    outside fenced code, so a fence is one paragraph (AC-7)."""
    starts = []
    blank = False
    for offset, line, fenced in lines_with_fence(text):
        is_blank = not line.strip()
        if blank and not is_blank and offset:
            starts.append(offset)
        blank = is_blank and not fenced
    return starts


def split_points(text: str, tokens: list[int], offsets: list[int], max_tokens: int) -> list[int]:
    """Token indices where pieces of at most max_tokens start: paragraphs, then sentences in
    paragraphs over max, then raw token cuts in pieces still over max (AC-7)."""
    raw = text.encode("utf-8")

    def snap(byte: int) -> int:
        return bisect_left(offsets, byte)

    def refine(a: int, b: int, level: int) -> list[int]:  # cut points strictly inside (a, b)
        if b - a <= max_tokens:
            return []
        if level == 0:
            inner = [snap(x) for x in paragraph_starts(text)]
        elif level == 1:
            piece = raw[offsets[a] : offsets[b]].decode("utf-8", errors="ignore")
            base = offsets[a]
            inner = [
                snap(base + len(piece[: m.end()].encode("utf-8"))) for m in SENTENCE.finditer(piece)
            ]
        else:
            return list(range(a + 1, b))  # each token a piece; packing fills to max
        cuts = sorted({c for c in inner if a < c < b})
        bounds = [a, *cuts, b]
        out = []
        for x, y in zip(bounds, bounds[1:], strict=False):
            out += refine(x, y, level + 1)
            out.append(y)
        return out[:-1]

    return refine(0, len(tokens), 0)


def pack(n: int, cuts: list[int], max_tokens: int, overlap: int) -> list[tuple[int, int]]:
    """Token windows over 0..n ending on cut points, each <= max_tokens; each next window
    starts `overlap` tokens before the previous end (AC-7)."""
    if n <= max_tokens:
        return [(0, n)]
    bounds = [*cuts, n]
    windows = []
    start, prev_end = 0, 0
    while True:
        limit = start + max_tokens
        k = bisect_right(bounds, limit) - 1
        end = bounds[k] if k >= 0 and bounds[k] > prev_end else min(limit, n)
        windows.append((start, end))
        if end == n:
            return windows
        prev_end, start = end, max(end - overlap, 0)


def emit(
    doc_id: uuid.UUID,
    raw: bytes,
    enc,
    groups: list[list[Section]],
    path_of,
    *,
    config_id: str,
    max_tokens: int,
    overlap: int,
    line_offset: int,
) -> list[Chunk]:
    """Chunks for groups of consecutive sections: each group's span is one chunk, or is split
    with overlap inside it when over max (spec 0005, AC-7, AC-9). `path_of(group)` is the
    heading_path its chunks record; heading is the first section's."""
    newlines = [i for i, b in enumerate(raw) if b == 0x0A]
    chunks = []
    for group in groups:
        first = group[0]
        a, b = first.start, group[-1].end
        path = path_of(group)
        text = raw[a:b].decode("utf-8")
        tokens = enc.encode(text, disallowed_special=())
        offsets = [0, *accumulate(len(enc.decode_single_token_bytes(t)) for t in tokens)]
        cuts = split_points(text, tokens, offsets, max_tokens) if len(tokens) > max_tokens else []
        for s, e in pack(len(tokens), cuts, max_tokens, overlap):
            start = a + offsets[s]
            content = raw[start : a + offsets[e]].decode("utf-8", errors="ignore")
            line_start = 1 + bisect_left(newlines, start) + line_offset
            i = len(chunks)
            chunks.append(
                Chunk(
                    chunk_id=uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{config_id}:{i}"),
                    chunk_index=i,
                    content=content,
                    token_count=e - s,
                    heading=first.path[-1] if first.path else None,
                    heading_path=path,
                    line_start=line_start,
                    line_end=line_start + len(content.removesuffix("\n").split("\n")) - 1,
                )
            )
    return chunks


def span_counter(raw: bytes, enc):
    """count(a, b): the token count of body bytes a..b, encoded as one span."""

    def count(a: int, b: int) -> int:
        return len(enc.encode(raw[a:b].decode("utf-8"), disallowed_special=()))

    return count


def chunk_structural(
    doc_id: uuid.UUID,
    body: str,
    enc,
    *,
    config_id: str,
    max_tokens: int,
    overlap: int,
    min_tokens: int,
    line_offset: int = 0,
) -> list[Chunk]:
    """Sections at headings, tiny siblings merged, big spans split (spec 0005, AC-6 to AC-9).

    line_offset is the number of front-matter lines ingest stripped, so line_start/line_end
    are 1-based lines of the source file.
    """
    if not body.strip():
        return []
    raw = body.encode("utf-8")
    secs = sections(body)
    groups = merge_groups(secs, span_counter(raw, enc), max_tokens, min_tokens)
    return emit(
        doc_id, raw, enc, [[secs[g] for g in group] for group in groups],
        lambda group: group[0].path + tuple(s.path[-1] for s in group[1:]),
        config_id=config_id, max_tokens=max_tokens, overlap=overlap, line_offset=line_offset,
    )  # fmt: skip


def pack_sections(secs: list[Section], count, max_tokens: int) -> list[list[int]]:
    """Group section indices greedily in order while the span stays <= max_tokens, at any
    heading level; a section over max is a group of its own (spec 0006, AC-3)."""
    groups: list[list[int]] = []
    for i, sec in enumerate(secs):
        if groups and count(secs[groups[-1][0]].start, sec.end) <= max_tokens:
            groups[-1].append(i)
        else:
            groups.append([i])
    return groups


def chunk_packed(
    doc_id: uuid.UUID,
    body: str,
    enc,
    *,
    config_id: str,
    max_tokens: int,
    overlap: int,
    line_offset: int = 0,
) -> list[Chunk]:
    """Whole sections packed up to max_tokens; an over-max section split alone (spec 0006,
    AC-3, AC-4). No overlap between packs; heading_path is the first section's real path."""
    if not body.strip():
        return []
    raw = body.encode("utf-8")
    secs = sections(body)
    groups = pack_sections(secs, span_counter(raw, enc), max_tokens)
    return emit(
        doc_id, raw, enc, [[secs[g] for g in group] for group in groups],
        lambda group: group[0].path,
        config_id=config_id, max_tokens=max_tokens, overlap=overlap, line_offset=line_offset,
    )  # fmt: skip


UPSERT = """
INSERT INTO chunks (chunk_id, doc_id, chunk_index, content, token_count, heading,
                    chunk_size, chunk_overlap, tokenizer, commit_sha,
                    config_id, heading_path, line_start, line_end, allowed_groups)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (chunk_id) DO UPDATE SET
    doc_id = EXCLUDED.doc_id, chunk_index = EXCLUDED.chunk_index,
    content = EXCLUDED.content, token_count = EXCLUDED.token_count,
    heading = EXCLUDED.heading, chunk_size = EXCLUDED.chunk_size,
    chunk_overlap = EXCLUDED.chunk_overlap, tokenizer = EXCLUDED.tokenizer,
    commit_sha = EXCLUDED.commit_sha, config_id = EXCLUDED.config_id,
    heading_path = EXCLUDED.heading_path, line_start = EXCLUDED.line_start,
    line_end = EXCLUDED.line_end, allowed_groups = EXCLUDED.allowed_groups
"""


def register_config(conn, config_id: str) -> dict:
    """Record a code-defined config on first use; fail if the stored row drifted (AC-1)."""
    cfg = CHUNK_CONFIGS.get(config_id)
    if cfg is None:
        raise SystemExit(f"unknown chunk config {config_id!r}; known: {', '.join(CHUNK_CONFIGS)}")
    conn.execute(
        """INSERT INTO chunk_configs (config_id, strategy, params, tokenizer)
           VALUES (%s, %s, %s, %s) ON CONFLICT (config_id) DO NOTHING""",
        (config_id, cfg["strategy"], Jsonb(cfg["params"]), TOKENIZER),
    )
    stored = conn.execute(
        "SELECT strategy, params, tokenizer FROM chunk_configs WHERE config_id = %s", (config_id,)
    ).fetchone()
    if stored != (cfg["strategy"], cfg["params"], TOKENIZER):
        raise SystemExit(
            f"chunk config {config_id!r} drifted: stored {stored}, code "
            f"{(cfg['strategy'], cfg['params'], TOKENIZER)}. Use a new config_id."
        )
    return cfg


def up_to_date(conn, sha: str, config_id: str) -> int | None:
    """This config's chunk count if all are at sha and every non-empty doc has one (AC-3).

    Params and tokenizer are guarded by register_config.
    """
    total, current = conn.execute(
        """SELECT count(*), count(*) FILTER (WHERE commit_sha = %s)
           FROM chunks WHERE config_id = %s""",
        (sha, config_id),
    ).fetchone()
    (uncovered,) = conn.execute(
        """SELECT EXISTS (SELECT 1 FROM documents d WHERE d.body ~ '\\S'
                          AND NOT EXISTS (SELECT 1 FROM chunks c
                                          WHERE c.doc_id = d.doc_id AND c.config_id = %s))""",
        (config_id,),
    ).fetchone()
    return total if total and total == current and not uncovered else None


def front_matter_lines(path: str, body: str) -> int:
    """Lines ingest stripped above the body in the pinned file (AC-9)."""
    text = (CHECKOUT / path).read_text(encoding="utf-8")  # as ingest reads it
    if not text.endswith(body):
        raise SystemExit(f"{path}: stored body is not the file's tail. Run `make ingest`.")
    return text[: len(text) - len(body)].count("\n")


def chunker(cfg: dict, config_id: str, enc):
    """(doc_id, path, body) -> chunks, plus the (chunk_size, chunk_overlap) the rows store.

    embed_prefix changes only the embedded text (spec 0006, AC-5), so it is not a chunker
    param; a prefixed fixed config records heading paths for the prefix (AC-4).
    """
    p = {k: v for k, v in cfg["params"].items() if k != "embed_prefix"}
    if cfg["strategy"] == "fixed":
        with_path = "embed_prefix" in cfg["params"]
        return (
            lambda d, _, b: chunk_doc(d, b, enc, p["size"], p["overlap"], config_id, with_path)
        ), (p["size"], p["overlap"])
    fn = chunk_packed if cfg["strategy"] == "structural-packed" else chunk_structural
    return (
        lambda d, path, b: fn(
            d, b, enc, config_id=config_id, **p,
            line_offset=front_matter_lines(path, b) if b.strip() else 0,
        )
    ), (p["max_tokens"], p["overlap"])  # fmt: skip


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


def run(conn, config_id: str = BASELINE_CONFIG, force: bool = False) -> RunResult:
    m = read_manifest()
    error = verify(m)
    if error:
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    enc = tiktoken.get_encoding(TOKENIZER)
    with conn.transaction():
        conn.execute(CHUNKS_SCHEMA.read_text())
        cfg = register_config(conn, config_id)
        chunk, (size, overlap) = chunker(cfg, config_id, enc)
        (stale,) = conn.execute(
            "SELECT EXISTS (SELECT 1 FROM documents WHERE commit_sha <> %s)", (m.sha,)
        ).fetchone()
        if stale:
            raise SystemExit("documents are stale vs CORPUS.md. Run `make ingest` first.")
        if not force and (count := up_to_date(conn, m.sha, config_id)) is not None:
            return RunResult(skipped=True, sha=m.sha, chunks=count)

        result = RunResult(skipped=False, sha=m.sha)
        ids: list[uuid.UUID] = []
        rows: list[tuple] = []
        with conn.cursor(name="chunk_docs") as docs:
            docs.execute("SELECT doc_id, path, body, acl_tags FROM documents ORDER BY doc_id")
            for doc_id, path, body, acl_tags in docs:
                result.docs += 1
                for c in chunk(doc_id, path, body):
                    ids.append(c.chunk_id)
                    hp = list(c.heading_path) if c.heading_path is not None else None
                    rows.append(
                        (c.chunk_id, doc_id, c.chunk_index, c.content, c.token_count, c.heading,
                         size, overlap, TOKENIZER, m.sha,
                         config_id, hp, c.line_start, c.line_end, acl_tags)
                    )  # fmt: skip
                if len(rows) >= CHUNK_BATCH:
                    result.changed += flush(conn, rows)
                    rows = []
        if rows:
            result.changed += flush(conn, rows)
        # Rows of this config not produced now are stale; embeddings cascade (AC-3).
        result.deleted = conn.execute(
            "DELETE FROM chunks c WHERE c.config_id = %s AND NOT EXISTS "
            "(SELECT 1 FROM unnest(%s::uuid[]) AS keep(id) WHERE keep.id = c.chunk_id)",
            (config_id, ids),
        ).rowcount
        result.chunks = len(ids)
    return result


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Chunk ingested documents (spec 0003, 0005).")
    ap.add_argument("--config", default=BASELINE_CONFIG, help="chunk config id (constants)")
    ap.add_argument("--force", action="store_true", help="skip the early-exit check")
    args = ap.parse_args(argv)
    with connect() as conn:
        r = run(conn, config_id=args.config, force=args.force)
    params = f"config {args.config} {CHUNK_CONFIGS[args.config]['params']} {TOKENIZER}"
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
