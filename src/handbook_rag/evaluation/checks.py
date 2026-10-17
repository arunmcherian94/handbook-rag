"""Abstention labels and code checks on answers (spec 0004, AC-4, AC-5). Pure."""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from handbook_rag.ask import Citation
from handbook_rag.chunk import find_headings
from handbook_rag.prompts import NOT_FOUND, OUT_OF_SCOPE

FIXED_STRINGS = (NOT_FOUND, OUT_OF_SCOPE)
URL = re.compile(r"https?://|www\.", re.IGNORECASE)


@dataclass(frozen=True)
class Abstention:
    abstained: bool  # the trimmed answer equals either fixed string
    passed: bool | None  # ooc rows: trimmed answer == expected; None for answerable rows
    false_abstention: bool | None  # answerable rows: abstained; None for ooc rows
    label: str | None  # "abstain+extra" | "wrong-string" | None (diagnostic, no score impact)


@dataclass(frozen=True)
class CodeChecks:
    has_citation: bool
    citations_in_range: bool  # no invalid_citations
    headings_exist: bool
    no_url: bool
    truncated: bool  # reported, not a pass/fail check
    missing_headings: list[tuple[str, str]] = field(default_factory=list)  # (url_path, heading)

    @property
    def passed(self) -> bool:
        return self.has_citation and self.citations_in_range and self.headings_exist and self.no_url


def abstention(answer: str, expected: str | None) -> Abstention:
    """expected is the row's fixed string (ooc rows) or None (answerable rows).

    abstain+extra: starts with a fixed string and has more text. wrong-string: an ooc row whose
    answer is exactly the other fixed string.
    """
    a = answer.strip()
    abstained = a in FIXED_STRINGS
    extra = not abstained and a.startswith(FIXED_STRINGS)
    if expected is None:
        return Abstention(abstained, None, abstained, "abstain+extra" if extra else None)
    if abstained and a != expected:
        label = "wrong-string"
    elif extra:
        label = "abstain+extra"
    else:
        label = None
    return Abstention(abstained, a == expected, None, label)


def page_headings(body: str, title: str) -> set[str]:
    """Headings a citation may name for this page: chunk.find_headings texts plus the title
    (ask.SEARCH falls back to the title when a chunk has no heading)."""
    return set(find_headings(body)[1]) | {title}


def code_checks(
    answer: str,
    citations: Iterable[Citation],
    invalid_citations: list[int],
    truncated: bool,
    headings_by_url: Mapping[str, set[str]],
) -> CodeChecks:
    """AC-5 for one answerable, non-abstaining answer. headings_by_url maps url_path to
    page_headings of that page. A URL is http://, https:// or www."""
    cited = list(citations)
    missing = [
        (c.url_path, c.heading)
        for c in cited
        if c.heading not in headings_by_url.get(c.url_path, set())
    ]
    return CodeChecks(
        has_citation=bool(cited),
        citations_in_range=not invalid_citations,
        headings_exist=not missing,
        no_url=URL.search(answer) is None,
        truncated=truncated,
        missing_headings=missing,
    )
