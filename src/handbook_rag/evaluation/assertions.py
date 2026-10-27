"""Answer-content assertions: per-fact must-contain checks on stored answers (spec 0010, AC-5 to
AC-8, AC-11). Pure apart from reading the YAML and the review file. An answer-content check, not
a measure of whether an answer is right or supported."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from handbook_rag.evaluation.evalset import EvalSet, Row
from handbook_rag.evaluation.metrics import Stat, mean_se
from handbook_rag.prompts import NOT_FOUND, OUT_OF_SCOPE

FIXED_STRINGS = (NOT_FOUND, OUT_OF_SCOPE)  # both abstentions every assertion must fail on (AC-7)
FACT_PASS = "answer_content_fact_pass"
ROW_PASS = "answer_content_row_pass"
ASSERTIONS_PATH = Path("eval/assertions/assertions-v1.yaml")
REVIEW_PATH = Path("docs/eval/fact-list-review.md")
REVIEWED = "llm-draft, reviewed"  # owner-reviewed: eligible as is
AUTO_REVIEWED = "llm-draft, auto-reviewed"  # eligible once checked=y and changed=n
NODE_KINDS = ("number", "term", "all_of", "any_of")


class AssertionsError(ValueError):
    """A malformed or refused assertions or review file; the message names the row and fact."""


@dataclass(frozen=True)
class Node:
    kind: str  # one of NODE_KINDS
    value: float | str | None = None  # number: the value; term: the text; None for all_of/any_of
    unit: str | None = None  # number only, optional
    variants: tuple[str, ...] = ()  # term only: accepted alternatives
    children: tuple["Node", ...] = ()  # all_of / any_of only


@dataclass(frozen=True)
class Entry:
    row: int
    fact: str  # "F4"
    expressible: bool
    node: Node | None = None  # set iff expressible
    reason: str | None = None  # set iff not expressible: one line, for the week 6 judge


@dataclass(frozen=True)
class Assertions:
    eval_version: str
    eval_sha256: str
    entries: dict[int, dict[str, Entry]] = field(default_factory=dict)  # row -> fact -> entry


@dataclass(frozen=True)
class ReviewRow:
    row: int
    type: str  # "answerable" | "ooc"
    checked: bool
    changed: bool
    note: str


@dataclass(frozen=True)
class FactResult:
    fact: str
    expressible: bool
    passed: bool | None  # None when not expressible


@dataclass(frozen=True)
class RowResult:
    row: int
    abstained: bool  # the stored answer is a fixed string (it fails every assertion)
    facts: tuple[FactResult, ...]
    fact_pass: float | None  # passed / expressible; None with no expressible fact
    row_pass: bool | None  # every expressible fact passed; None with no expressible fact


@dataclass(frozen=True)
class ScoreReport:
    rows: tuple[RowResult, ...]  # rows in the file, eval-set order
    fact_pass: Stat | None  # mean of RowResult.fact_pass, mean_se(binary=False)
    row_pass: Stat | None  # mean of RowResult.row_pass, mean_se(binary=True)
    n_rows_scored: int  # rows with >= 1 expressible fact
    n_expressible: int
    n_not_expressible: int  # counted, not dropped
    eligible_not_in_file: tuple[int, ...]  # eligible answerable rows with no entries yet


_ONES = {
    w: i
    for i, w in enumerate(
        "zero one two three four five six seven eight nine ten eleven twelve thirteen "
        "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split()
    )
}
_TENS = {
    w: 10 * i
    for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split(), 2)
}
_MULT = {"hundred": 100, "thousand": 1000}
_WORD_NUMBER = re.compile(
    r"\b(?:(?P<tens>" + "|".join(_TENS) + r")"
    r"(?:[-\s](?P<one>one|two|three|four|five|six|seven|eight|nine))?"
    r"|(?P<small>" + "|".join(_ONES) + r"))\b(?:\s+(?P<mult>hundred|thousand))?"
)
_NUMBER = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)")
# unit -> (accepted before the number, accepted after it); regex fragments, lowercase
_UNITS = {
    "days": ((), ("days?",)),
    "weeks": ((), ("weeks?",)),
    "months": ((), ("months?",)),
    "years": ((), ("years?",)),
    "hours": ((), ("hours?",)),
    "%": ((), ("%", "percent", "per cent")),
    "usd": (("us\\$", "\\$", "usd"), ("usd", "us dollars?", "dollars?")),
    "eur": (("€", "eur"), ("eur", "euros?")),
    "gbp": (("£", "gbp"), ("gbp", "pounds?")),
}


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def _words_to_digits(text: str) -> str:
    def sub(m: re.Match) -> str:
        n = _TENS[m["tens"]] + _ONES.get(m["one"] or "", 0) if m["tens"] else _ONES[m["small"]]
        return str(n * _MULT[m["mult"]] if m["mult"] else n)

    return _WORD_NUMBER.sub(sub, text)


def _unit_ok(unit: str, before: str, after: str) -> bool:
    key = unit.lower()
    pre, post = _UNITS.get(key, ((), (re.escape(key) + "s?",)))
    if any(re.search(r"(?<!\w)(?:" + p + r")\s*$", before) for p in pre):
        return True
    return any(re.match(r"[\s-]*(?:" + p + r")(?!\w)", after) for p in post)


def _number_matches(node: Node, text: str) -> bool:
    text = _words_to_digits(_norm(text))
    for m in _NUMBER.finditer(text):
        if float(m[1].replace(",", "")) != float(node.value):
            continue
        if node.unit is None or _unit_ok(node.unit, text[: m.start()], text[m.end() :]):
            return True
    return False


def matches(node: Node, text: str) -> bool:
    """Whether text satisfies node (AC-5 normalisation)."""
    if node.kind == "number":
        return _number_matches(node, text)
    if node.kind == "term":
        norm = _norm(text)
        return any(
            re.search(r"(?<!\w)" + re.escape(_norm(t)) + r"(?!\w)", norm)
            for t in (str(node.value), *node.variants)
        )
    results = (matches(c, text) for c in node.children)
    return all(results) if node.kind == "all_of" else any(results)


def _node(raw: object, where: str) -> Node:
    def fail(msg: str) -> AssertionsError:
        return AssertionsError(f"{where}: {msg}")

    if not isinstance(raw, dict):
        raise fail("a node must be a mapping")
    kinds = [k for k in raw if k in NODE_KINDS]
    if len(kinds) != 1:
        raise fail(f"a node needs exactly one of {', '.join(NODE_KINDS)}, got keys {list(raw)}")
    kind = kinds[0]
    allowed = {kind, {"number": "unit", "term": "variants"}.get(kind)}
    if extra := [k for k in raw if k not in allowed]:
        raise fail(f"unknown key {extra[0]!r} in a {kind} node")
    value = raw[kind]
    if kind == "number":
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise fail("number must be numeric")
        unit = raw.get("unit")
        if "unit" in raw and not (isinstance(unit, str) and unit.strip()):
            raise fail("unit must be a non-empty string")
        return Node("number", float(value), unit)
    if kind == "term":
        if not isinstance(value, str) or not value.strip():
            raise fail("term must be a non-empty string")
        variants = raw.get("variants", [])
        if not isinstance(variants, list) or not all(
            isinstance(v, str) and v.strip() for v in variants
        ):
            raise fail("variants must be a list of non-empty strings")
        return Node("term", value, variants=tuple(variants))
    if not isinstance(value, list) or not value:
        raise fail(f"{kind} must be a non-empty list of nodes")
    children = tuple(_node(c, f"{where} {kind}[{i}]") for i, c in enumerate(value))
    return Node(kind, children=children)


def _entry(row: int, fact: str, raw: object) -> Entry:
    where = f"row {row} {fact}"
    if not isinstance(raw, dict):
        raise AssertionsError(f"{where}: an entry must be a mapping")
    if "expressible" not in raw or not isinstance(raw["expressible"], bool):
        raise AssertionsError(f"{where}: expressible must be true or false")
    if raw["expressible"]:
        if extra := [k for k in raw if k not in ("expressible", "assert")]:
            raise AssertionsError(f"{where}: unknown key {extra[0]!r}")
        if "assert" not in raw:
            raise AssertionsError(f"{where}: expressible entry has no assert")
        return Entry(row, fact, True, node=_node(raw["assert"], where))
    if extra := [k for k in raw if k not in ("expressible", "reason")]:
        raise AssertionsError(f"{where}: unknown key {extra[0]!r}")
    reason = raw.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise AssertionsError(f"{where}: non-expressible entry needs a reason")
    return Entry(row, fact, False, reason=reason.strip())


class _UniqueKeyLoader(yaml.SafeLoader):
    """safe_load that refuses a duplicate key: a second `11:` block would drop reviewed entries."""


def _unique_mapping(loader: yaml.SafeLoader, node: yaml.MappingNode) -> dict:
    keys = [loader.construct_object(k) for k, _ in node.value]
    if dupes := sorted({str(k) for k in keys if keys.count(k) > 1}):
        raise AssertionsError(
            f"duplicate key(s) {', '.join(dupes)} at line {node.start_mark.line + 1}"
        )
    return loader.construct_mapping(node)


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def load_assertions(
    path: Path, evalset: EvalSet, eval_sha: str, review: Mapping[int, ReviewRow]
) -> Assertions:
    """Load and validate the YAML (AC-5), refusing the whole file on any AC-6 gate."""
    raw = yaml.load(Path(path).read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    if not isinstance(raw, dict):
        raise AssertionsError(f"{path}: expected a mapping")
    if extra := [k for k in raw if k not in ("eval_version", "eval_sha256", "rows")]:
        raise AssertionsError(f"{path}: unknown top-level key {extra[0]!r}")
    if raw.get("eval_sha256") != eval_sha:
        raise AssertionsError(
            f"eval_sha256 {raw.get('eval_sha256')!r} differs from the eval set ({eval_sha})"
        )
    if raw.get("eval_version") != evalset.version:
        raise AssertionsError(
            f"eval_version {raw.get('eval_version')!r} differs from the eval set "
            f"({evalset.version})"
        )
    rows = raw.get("rows") or {}
    if not isinstance(rows, dict):
        raise AssertionsError("rows must be a mapping")
    by_id = {r.id: r for r in evalset.rows}
    for rid in rows:
        if isinstance(rid, bool) or not isinstance(rid, int):
            raise AssertionsError(f"row {rid!r}: row ids are integers")
        if rid not in by_id:
            raise AssertionsError(f"row {rid}: not in the eval set")
        if not by_id[rid].answerable:
            raise AssertionsError(f"row {rid}: out-of-corpus row, assertions are not allowed")
        if not eligible(by_id[rid], review):
            raise AssertionsError(
                f"row {rid}: not eligible (ref_source {by_id[rid].ref_source!r}, "
                "needs owner review or checked=y and changed=n in the review file)"
            )
    entries: dict[int, dict[str, Entry]] = {}
    for row in evalset.rows:  # eval-set order
        if row.id not in rows:
            continue
        facts = rows[row.id]
        if not isinstance(facts, dict):
            raise AssertionsError(f"row {row.id}: expected a mapping of fact id to entry")
        required = {f.id for f in row.facts if f.required}
        for fid in facts:
            if fid not in {f.id for f in row.facts}:
                raise AssertionsError(f"row {row.id} {fid}: no such fact in the row")
            if fid not in required:
                raise AssertionsError(f"row {row.id} {fid}: not a [required] fact")
        if missing := [f.id for f in row.facts if f.required and f.id not in facts]:
            raise AssertionsError(f"row {row.id}: omits required fact(s) {', '.join(missing)}")
        entries[row.id] = {
            f.id: _entry(row.id, f.id, facts[f.id]) for f in row.facts if f.id in facts
        }
    return Assertions(raw["eval_version"], raw["eval_sha256"], entries)


def score(
    assertions: Assertions,
    evalset: EvalSet,
    review: Mapping[int, ReviewRow],
    run_rows: Mapping[int, dict],
) -> ScoreReport:
    """Run every entry against run_rows[row]["answer"] (a rows.jsonl record) (AC-8)."""
    results: list[RowResult] = []
    n_expressible = n_not = 0
    for row in evalset.rows:
        if row.id not in assertions.entries:
            continue
        record = run_rows.get(row.id)
        if record is None or not isinstance(record.get("answer"), str):
            raise AssertionsError(f"row {row.id}: no answer in the run data")
        answer = record["answer"]
        facts = tuple(
            FactResult(e.fact, e.expressible, matches(e.node, answer) if e.expressible else None)
            for e in assertions.entries[row.id].values()
        )
        graded = [f.passed for f in facts if f.expressible]
        n_expressible += len(graded)
        n_not += len(facts) - len(graded)
        results.append(
            RowResult(
                row.id,
                answer.strip() in FIXED_STRINGS,
                facts,
                sum(graded) / len(graded) if graded else None,
                all(graded) if graded else None,
            )
        )
    scored = [r for r in results if r.fact_pass is not None]
    return ScoreReport(
        tuple(results),
        mean_se([r.fact_pass for r in scored], binary=False),
        mean_se([float(r.row_pass) for r in scored], binary=True),
        len(scored),
        n_expressible,
        n_not,
        tuple(r.id for r in evalset.rows if r.id not in assertions.entries and eligible(r, review)),
    )


_CELL = {"y": True, "n": False}


def load_review(path: Path) -> dict[int, ReviewRow]:
    """Parse the fact-list review table (AC-11). y/n cells only; anything else is an error."""
    out: dict[int, ReviewRow] = {}
    in_table = False
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not in_table:
            if [c.lower() for c in cells[:5]] == ["row", "type", "checked", "changed", "note"]:
                in_table = True
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        if len(cells) < 5 or not cells[0].isdigit():
            raise AssertionsError(f"review: malformed table line {line!r}")
        row = int(cells[0])
        if row in out:
            raise AssertionsError(f"review row {row}: duplicate")
        if cells[1] not in ("answerable", "ooc"):
            raise AssertionsError(f"review row {row}: type must be answerable or ooc")
        for name, cell in (("checked", cells[2]), ("changed", cells[3])):
            if cell not in _CELL:
                raise AssertionsError(f"review row {row}: {name} must be y or n, got {cell!r}")
        out[row] = ReviewRow(
            row, cells[1], _CELL[cells[2]], _CELL[cells[3]], "|".join(cells[4:]).strip()
        )
    if not in_table:
        raise AssertionsError("review: no table with columns row, type, checked, changed, note")
    return out


def eligible(row: Row, review: Mapping[int, ReviewRow]) -> bool:
    """AC-6: answerable, and owner-reviewed, or auto-reviewed with checked=y and changed=n."""
    if not row.answerable:
        return False
    if row.ref_source == REVIEWED:
        return True
    r = review.get(row.id)
    return row.ref_source == AUTO_REVIEWED and r is not None and r.checked and not r.changed
