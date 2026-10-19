"""Evidence check and relevance rule (spec 0004, AC-2; spec 0005, AC-4, AC-10).

The single owner of the relevance rule: a chunk is relevant to a fact if it comes from a cited
page and contains at least one cited non-blank line, whitespace-normalised. A line of at least
MIN_PIECE characters matches in full as a substring of the chunk, or (for a line the chunk window
cut) as a piece of at least MIN_PIECE characters at the chunk's start or end. A shorter line
(e.g. "{.h2}", "##### France") matches only if it equals some whole line of the chunk, so it
can't match text inside a longer line. Chunk windows are cut at token offsets, not line breaks,
so the chunk's first line and (unless the chunk ends with a newline) its last line may be
fragments and don't count as whole; a short line there is found whole in the neighbouring chunk,
which overlaps this one. A line-aligned chunk (line_start set, spec 0005 AC-10) is the exception:
an edge line that equals the full source line at its line number counts as whole, so a short
cited line right under a heading can match. Baseline chunks have NULL line ranges and keep the
rule above. The check reads only the given config's chunks (AC-4). Everything downstream sees
only the resulting chunk-id sets.
"""

import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from handbook_rag.constants import CHECKOUT, CORPUS_PREFIX, MIN_PIECE
from handbook_rag.evaluation.evalset import Row

FactKey = tuple[int, str]  # (row id, fact id)


class EvidenceError(Exception):
    """A required fact can't be matched; the message names every such row and fact."""


@dataclass
class Evidence:
    # Chunk ids relevant to each cited fact (required and optional), keyed by (row, fact).
    relevant: dict[FactKey, frozenset[uuid.UUID]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)  # unmatchable optional facts


def normalise(text: str) -> str:
    """Collapse every whitespace run to one space and strip."""
    return " ".join(text.split())


def straddles(line: str, haystack: str, min_piece: int = MIN_PIECE) -> bool:
    """The chunk starts with a suffix, or ends with a prefix, of the line, at least min_piece
    characters long: the line straddles the chunk boundary (both already normalised)."""
    return any(
        haystack.startswith(line[-i:]) or haystack.endswith(line[:i])
        for i in range(min_piece, len(line))
    )


def matches(
    lines: Iterable[str], content: str, whole_edges: tuple[bool, bool] = (False, False)
) -> bool:
    """True if any non-blank line, normalised, matches the content: a line under MIN_PIECE
    characters equals a whole normalised line of the content; a longer one is in the normalised
    content in full or straddles its boundary. The content's first line, and its last unless
    the content ends with a newline, may be cut by the window, so they aren't whole lines unless
    whole_edges[0] / [1] say the first / last line equals a full source line."""
    haystack = normalise(content)
    # [1:-1] drops the first piece and the last: a fragment, or "" after a trailing newline.
    pieces = content.split("\n")
    whole_lines = {normalise(line) for line in pieces[1:-1]}
    if whole_edges[0]:
        whole_lines.add(normalise(pieces[0]))
    if whole_edges[1]:
        whole_lines.add(normalise(pieces[-1]))
    return any(
        n in whole_lines if len(n) < MIN_PIECE else n in haystack or straddles(n, haystack)
        for n in map(normalise, lines)
        if n
    )


def _whole_edges(
    page: list[str], content: str, line_start: int | None, line_end: int | None
) -> tuple[bool, bool]:
    """Whether a line-aligned chunk's first and last lines equal the full source lines at its
    stored line_start and line_end."""
    if line_start is None or line_end is None:
        return (False, False)
    pieces = content.split("\n")
    first = 1 <= line_start <= len(page) and pieces[0] == page[line_start - 1]
    last = pieces[-1] == "" or (1 <= line_end <= len(page) and pieces[-1] == page[line_end - 1])
    return (first, last)


def _fact_chunks(
    cites: dict[str, tuple[int, ...]],
    read_page: Callable[[str], list[str]],
    page_chunks: Callable[[str], list[tuple[uuid.UUID, str, int | None, int | None]]],
) -> tuple[set[uuid.UUID], list[str]]:
    """Union over cited pages of the chunks containing a cited line; and any problems."""
    ids: set[uuid.UUID] = set()
    problems: list[str] = []
    for path, numbers in cites.items():
        try:
            page = read_page(path)
        except FileNotFoundError:
            problems.append(f"cited file {path} not found")
            continue
        past = [n for n in numbers if not 1 <= n <= len(page)]
        if past:
            problems.append(
                f"line(s) {', '.join(f'L{n}' for n in past)} out of range for {path} "
                f"({len(page)} lines)"
            )
        lines = [page[n - 1] for n in numbers if 1 <= n <= len(page)]
        if not any(normalise(line) for line in lines):
            continue  # every cited line blank: the page contributes nothing
        ids.update(
            cid
            for cid, content, line_start, line_end in page_chunks(path)
            if matches(lines, content, _whole_edges(page, content, line_start, line_end))
        )
    if not ids and not problems:
        problems.append(f"no stored chunk contains a cited line of {', '.join(cites)}")
    return ids, problems


def relevant_chunks(
    rows: Iterable[Row],
    read_page: Callable[[str], list[str]],
    page_chunks: Callable[[str], list[tuple[uuid.UUID, str, int | None, int | None]]],
) -> Evidence:
    """Pure core of the check. read_page(path) -> the file's lines; page_chunks(path) ->
    (chunk_id, content, line_start, line_end) for every stored chunk of that page. Paths are
    eval-set paths.

    Raises EvidenceError listing every required fact with no relevant chunk, or with a cited
    line number past the end of its file (also a missing file). Optional facts in that state
    become warnings. Answer-only facts and ooc rows are skipped.
    """
    evidence = Evidence()
    errors: list[str] = []
    for row in rows:
        if not row.answerable:
            continue
        for fact in row.facts:
            if fact.answer_only:
                continue
            ids, problems = _fact_chunks(fact.cites, read_page, page_chunks)
            evidence.relevant[(row.id, fact.id)] = frozenset(ids)
            kind = "required" if fact.required else "optional"
            messages = [f"row {row.id} {fact.id} ({kind}): {p}" for p in problems]
            (errors if fact.required else evidence.warnings).extend(messages)
    if errors:
        raise EvidenceError("evidence check failed:\n" + "\n".join(errors))
    return evidence


def check(rows: Iterable[Row], conn, config_id: str, checkout: Path = CHECKOUT) -> Evidence:
    """relevant_chunks over the pinned checkout and one config's chunks (documents.path is
    CORPUS_PREFIX + the eval-set path)."""
    cache: dict[str, list[tuple[uuid.UUID, str, int | None, int | None]]] = {}

    def read_page(path: str) -> list[str]:
        text = (checkout / CORPUS_PREFIX / path).read_text(encoding="utf-8")
        return text.removesuffix("\n").split("\n")

    def page_chunks(path: str) -> list[tuple[uuid.UUID, str, int | None, int | None]]:
        if path not in cache:
            cache[path] = conn.execute(
                "SELECT c.chunk_id, c.content, c.line_start, c.line_end FROM chunks c "
                "JOIN documents d USING (doc_id) "
                "WHERE d.path = %s AND c.config_id = %s",
                (CORPUS_PREFIX + path, config_id),
            ).fetchall()
        return cache[path]

    return relevant_chunks(rows, read_page, page_chunks)
