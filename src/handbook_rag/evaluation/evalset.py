"""Parse docs/eval/eval-set-v1.md into rows (spec 0004, AC-1). Pure: text in, rows out."""

import re
from dataclasses import dataclass, field

FIXED_STRING_TYPES = ("ooc-in-scope", "ooc-off-topic")
ROW_TYPES = ("lookup", "synthesis", "contradiction", "recency", *FIXED_STRING_TYPES)

VERSION = re.compile(r"^# Eval set (v\d+\.\d+)\b", re.M)
SECTION_END = re.compile(r"^## \d+\.\s+Cut\b")
ROW = re.compile(r"^### Row (\d+)\b(.*)$")
FACT = re.compile(r"^- (F\d+)\.\s")
MARKER = re.compile(r"\[(required|optional)\]")
RECENCY = re.compile(r"^recency_basis:\s*(in-page|history-only)\b")
# One scan, in order: a path token (a/b.md, _index.md) or a line ref (L5, L5–9, L5-9).
CITE = re.compile(
    r"(?<![\w/.-])(?P<path>(?:[\w.-]+/)*[\w.-]+\.md)\b"
    r"|\bL(?P<a>\d+)(?:\s*[–-]\s*L?(?P<b>\d+))?\b"
)


class EvalSetError(ValueError):
    """A malformed row; the message starts with the row id."""


@dataclass(frozen=True)
class Fact:
    id: str  # "F3"
    required: bool  # [required]; False for [optional]
    # path (relative to content/handbook/) -> cited 1-based line numbers, ranges expanded, in
    # citation order. Empty: an answer-only fact (no citation), outside the retrieval metrics.
    cites: dict[str, tuple[int, ...]] = field(default_factory=dict)

    @property
    def answer_only(self) -> bool:
        return not self.cites


@dataclass(frozen=True)
class Row:
    id: int  # the original row number, e.g. 11
    type: str  # lookup | synthesis | contradiction | recency | ooc-in-scope | ooc-off-topic
    question: str
    expected_docs: tuple[str, ...] = ()  # relative to content/handbook/; empty for ooc rows
    facts: tuple[Fact, ...] = ()  # empty for ooc rows
    expected: str | None = None  # the fixed reply, ooc rows only
    recency_basis: str | None = None  # "in-page" | "history-only" | None
    conflict_unscored: bool = False  # the recency_basis line says the conflict is not scored

    @property
    def answerable(self) -> bool:
        return self.type not in FIXED_STRING_TYPES

    @property
    def required(self) -> tuple[Fact, ...]:
        """Required facts with a citation: the ones the retrieval metrics score."""
        return tuple(f for f in self.facts if f.required and not f.answer_only)


@dataclass(frozen=True)
class EvalSet:
    version: str  # "v1.2", from the "# Eval set v1.2 (...)" header
    rows: tuple[Row, ...]


def parse(text: str) -> EvalSet:
    """Rows from every section before "## 5. Cut", in file order.

    Raises EvalSetError naming the row on: no Q: line, an answerable row with no [required]
    fact, a fact with neither [required] nor [optional], a line ref before any path, an ooc row
    with no expected: line, or an unknown row type.
    """
    version = VERSION.search(text)
    if not version:
        raise EvalSetError("no '# Eval set vX.Y' header")
    blocks: list[tuple[int, str, list[str]]] = []
    for line in text.splitlines():
        if SECTION_END.match(line):
            break
        if m := ROW.match(line):
            blocks.append((int(m[1]), m[2], []))
        elif blocks:
            blocks[-1][2].append(line)
    return EvalSet(version[1], tuple(_row(*b) for b in blocks))


def _row(row_id: int, header: str, lines: list[str]) -> Row:
    def fail(msg: str) -> EvalSetError:
        return EvalSetError(f"row {row_id}: {msg}")

    # "— recency · process · trap T1": the type is the first field.
    row_type = header.strip().lstrip("—").split("·")[0].strip()
    if row_type not in ROW_TYPES:
        raise fail(f"unknown type {row_type!r}")
    question = expected = basis = None
    docs: tuple[str, ...] = ()
    facts: list[Fact] = []
    unscored = False
    for line in lines:
        if line.startswith("Q:"):
            question = line[2:].strip()
        elif line.startswith("expected_docs:"):
            docs = tuple(d.strip() for d in line.split(":", 1)[1].split(",") if d.strip())
        elif line.startswith("expected:"):
            expected = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("recency_basis:"):
            if not (m := RECENCY.match(line)):
                raise fail(f"recency_basis is neither in-page nor history-only: {line!r}")
            basis = m[1]
            unscored = "not scored" in line.lower()
        elif m := FACT.match(line):
            facts.append(_fact(m[1], line, fail))
    if not question:
        raise fail("no Q: line")
    if row_type in FIXED_STRING_TYPES:
        if expected is None:
            raise fail("ooc row has no expected: line")
        return Row(row_id, row_type, question, expected=expected)
    if not any(f.required for f in facts):
        raise fail("no [required] fact")
    return Row(row_id, row_type, question, docs, tuple(facts), None, basis, unscored)


def _fact(fact_id: str, line: str, fail) -> Fact:
    marker = MARKER.search(line)
    if not marker:
        raise fail(f"{fact_id} has neither [required] nor [optional]")
    cites: dict[str, list[int]] = {}
    path = None
    for m in CITE.finditer(line, marker.end()):
        if m["path"]:
            path = m["path"]
            continue
        if path is None:
            raise fail(f"{fact_id} has a line ref before any path: L{m['a']}")
        a = int(m["a"])
        lines = cites.setdefault(path, [])
        for n in range(a, int(m["b"] or a) + 1):
            if n not in lines:
                lines.append(n)
    # A path with no line refs is a bare mention, not a citation.
    return Fact(fact_id, marker[1] == "required", {p: tuple(ns) for p, ns in cites.items()})
