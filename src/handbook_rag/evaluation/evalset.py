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
TAGS = re.compile(r"^(?:\s*\[(?:variant|rewording):[^\]]*\])+")  # editorial tags, not statement
DASH = " — "  # separates a fact's statement from its citation
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
    # The statement: after the marker and any [variant: ...] / [rewording: ...] tag, before the
    # " — " citation.
    # The reference text an answer-content assertion must pass on (spec 0010, AC-7).
    text: str = ""

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
    ref_source: str | None = None  # "llm-draft, reviewed" | "llm-draft, auto-reviewed" | ...

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
    fact, a fact with neither [required] nor [optional], a line ref before any path, a path
    with no L<n> line ref, a duplicate row or fact id, an ooc row with no expected: line, or an
    unknown row type.
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
    seen: set[int] = set()
    for row_id, _, _ in blocks:
        if row_id in seen:
            raise EvalSetError(f"row {row_id}: duplicate row id")
        seen.add(row_id)
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
    ref_source = None
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
        elif line.startswith("ref_source:"):
            ref_source = line.split(":", 1)[1].strip()
        elif m := FACT.match(line):
            if any(f.id == m[1] for f in facts):
                raise fail(f"duplicate fact id {m[1]}")
            facts.append(_fact(m[1], line, fail))
    if not question:
        raise fail("no Q: line")
    if row_type in FIXED_STRING_TYPES:
        if expected is None:
            raise fail("ooc row has no expected: line")
        return Row(row_id, row_type, question, expected=expected, ref_source=ref_source)
    if not any(f.required for f in facts):
        raise fail("no [required] fact")
    return Row(row_id, row_type, question, docs, tuple(facts), None, basis, unscored, ref_source)


def _fact(fact_id: str, line: str, fail) -> Fact:
    marker = MARKER.search(line)
    if not marker:
        raise fail(f"{fact_id} has neither [required] nor [optional]")
    cites: dict[str, list[int]] = {}
    first_path: int | None = None
    path = None
    path_has_ref = True  # whether the latest path has been followed by a line ref yet
    for m in CITE.finditer(line, marker.end()):
        if m["path"]:
            if first_path is None:
                first_path = m.start()
            if not path_has_ref:
                raise fail(f"{fact_id} cites {path} with no L<n> line ref")
            path, path_has_ref = m["path"], False
            continue
        if path is None:
            raise fail(f"{fact_id} has a line ref before any path: L{m['a']}")
        path_has_ref = True
        a = int(m["a"])
        lines = cites.setdefault(path, [])
        for n in range(a, int(m["b"] or a) + 1):
            if n not in lines:
                lines.append(n)
    if not path_has_ref:
        raise fail(f"{fact_id} cites {path} with no L<n> line ref")
    # Empty cites only when the fact line names no .md path: an answer-only fact.
    cited = {p: tuple(ns) for p, ns in cites.items()}
    head = line[marker.end() : first_path]  # up to the first cited path, or the whole line
    return Fact(fact_id, marker[1] == "required", cited, _text(line[marker.end() :], head))


def _text(rest: str, head: str) -> str:
    """The statement: rest up to the last " — " in head (rest starts where head does). No dash
    there (inline cites in parentheses) keeps all of rest."""
    cut = head.rfind(DASH)
    return TAGS.sub("", rest[:cut] if cut >= 0 else rest).strip()
