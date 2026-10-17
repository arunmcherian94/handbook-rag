"""Evidence check and relevance rule (spec 0004, AC-2).

The single owner of the relevance rule: a chunk is relevant to a fact if it comes from a cited
page and contains at least one cited non-blank line, whitespace-normalised. A line of at least
MIN_PIECE characters matches in full as a substring of the chunk, or (for a line the chunk window
cut) as a piece of at least MIN_PIECE characters at the chunk's start or end. A shorter line
(e.g. "{.h2}", "##### France") matches only if it equals some whole line of the chunk, so it
can't match text inside a longer line. Everything downstream sees only the resulting chunk-id
sets.
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


def matches(lines: Iterable[str], content: str) -> bool:
    """True if any non-blank line, normalised, matches the content: a line under MIN_PIECE
    characters equals a whole normalised line of the content; a longer one is in the normalised
    content in full or straddles its boundary."""
    haystack = normalise(content)
    whole_lines = {normalise(line) for line in content.split("\n")}
    return any(
        n in whole_lines if len(n) < MIN_PIECE else n in haystack or straddles(n, haystack)
        for n in map(normalise, lines)
        if n
    )


def _fact_chunks(
    cites: dict[str, tuple[int, ...]],
    read_page: Callable[[str], list[str]],
    page_chunks: Callable[[str], list[tuple[uuid.UUID, str]]],
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
        ids.update(cid for cid, content in page_chunks(path) if matches(lines, content))
    if not ids and not problems:
        problems.append(f"no stored chunk contains a cited line of {', '.join(cites)}")
    return ids, problems


def relevant_chunks(
    rows: Iterable[Row],
    read_page: Callable[[str], list[str]],
    page_chunks: Callable[[str], list[tuple[uuid.UUID, str]]],
) -> Evidence:
    """Pure core of the check. read_page(path) -> the file's lines; page_chunks(path) ->
    (chunk_id, content) for every stored chunk of that page. Paths are eval-set paths.

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


def check(rows: Iterable[Row], conn, checkout: Path = CHECKOUT) -> Evidence:
    """relevant_chunks over the pinned checkout and the chunks table (documents.path is
    CORPUS_PREFIX + the eval-set path)."""
    cache: dict[str, list[tuple[uuid.UUID, str]]] = {}

    def read_page(path: str) -> list[str]:
        text = (checkout / CORPUS_PREFIX / path).read_text(encoding="utf-8")
        return text.removesuffix("\n").split("\n")

    def page_chunks(path: str) -> list[tuple[uuid.UUID, str]]:
        if path not in cache:
            cache[path] = conn.execute(
                "SELECT c.chunk_id, c.content FROM chunks c JOIN documents d USING (doc_id) "
                "WHERE d.path = %s",
                (CORPUS_PREFIX + path,),
            ).fetchall()
        return cache[path]

    return relevant_chunks(rows, read_page, page_chunks)
