import hashlib
from pathlib import Path

import pytest

from handbook_rag.evaluation.assertions import (
    ASSERTIONS_PATH,
    AUTO_REVIEWED,
    FIXED_STRINGS,
    REVIEW_PATH,
    REVIEWED,
    AssertionsError,
    Node,
    ReviewRow,
    eligible,
    load_assertions,
    load_review,
    matches,
    score,
)
from handbook_rag.evaluation.evalset import parse
from handbook_rag.evaluation.metrics import mean_se

EVAL_PATH = Path("docs/eval/eval-set-v1.md")
SHA = "a" * 64


def num(value, unit=None):
    return Node("number", float(value), unit)


def term(value, *variants):
    return Node("term", value, variants=variants)


def real():
    text = EVAL_PATH.read_bytes()
    return parse(text.decode()), hashlib.sha256(text).hexdigest()


def _self_test_cases():
    es, sha = real()
    review = load_review(REVIEW_PATH)
    loaded = load_assertions(ASSERTIONS_PATH, es, sha, review)
    facts = {(r.id, f.id): f for r in es.rows for f in r.facts}
    return [
        pytest.param(e.node, facts[(e.row, e.fact)].text, id=f"{e.row}-{e.fact}")
        for by_fact in loaded.entries.values()
        for e in by_fact.values()
        if e.expressible
    ] or [pytest.param(None, None, id="no-entries", marks=pytest.mark.skip("empty file"))]


@pytest.mark.parametrize("node,text", _self_test_cases())
def test_committed_entries_self_test(node, text):
    """Spec 0010 AC-7: a committed entry passes its fact text, fails both fixed strings."""
    assert matches(node, text)
    assert not any(matches(node, s) for s in FIXED_STRINGS)


@pytest.mark.parametrize(
    "node,text,expected",
    [
        (num(1500), "The stipend is $1,500 per year.", True),
        (num(1500), "It is 1500 USD.", True),
        (num(1500), "Limit of 15000", False),
        (num(1500), "Limit of 1,500,000", False),
        (num(1500), "Limit of 1,500.50", False),
        (num(15), "15% of salary", True),
        (num(2.5), "about 2.5 weeks", True),
        (num(2.5), "about 25 weeks", False),
        (num(25), "twenty-five days", True),
        (num(25), "twenty five days", True),
        (num(2000), "two thousand dollars", True),
        (num(300), "three hundred", True),
        (num(18), "eighteen", True),
        (num(20), "twenty", True),
        (num(5), "there were five", True),
        (num(30), "within 30-day window", True),
        (num(30, "days"), "within 30 days", True),
        (num(1, "days"), "after 1 day", True),
        (num(30, "days"), "within 30 weeks", False),
        (num(30, "days"), "30", False),
        (num(1500, "USD"), "a $1,500 allowance", True),
        (num(1500, "USD"), "1,500 US dollars", True),
        (num(1500, "USD"), "USD 1500", True),
        (num(1500, "USD"), "1,500 euros", False),
        (num(1500, "EUR"), "€1,500", True),
        (num(10, "%"), "10% or 10 percent", True),
        (num(10, "%"), "10 people", False),
        (num(3, "months"), "3 months", True),
        (term("stipend"), "The STIPEND   applies", True),
        (term("pto"), "Ptolemy ruled", False),
        (term("pto"), "take PTO.", True),
        (term("stipend", "allowance"), "an allowance", True),
        (term("stipend", "allowance"), "no match", False),
        (term("time off"), "Time\n  off is fine", True),
        (term("c++"), "we use c++ here", True),
    ],
)
def test_matcher_leaf(node, text, expected):
    """Spec 0010 AC-5/AC-7: number and term matching with normalisation."""
    assert matches(node, text) is expected


def test_matcher_nesting():
    """Spec 0010 AC-7: all_of / any_of, nested."""
    a, b = num(5), term("pto")
    assert matches(Node("all_of", children=(a, b)), "5 days of PTO")
    assert not matches(Node("all_of", children=(a, b)), "5 days")
    assert matches(Node("any_of", children=(a, b)), "PTO")
    assert not matches(Node("any_of", children=(a, b)), "nothing")
    nested = Node("all_of", children=(a, Node("any_of", children=(b, term("leave")))))
    assert matches(nested, "five days of leave")
    assert not matches(nested, "five days")


def test_fixed_strings_fail():
    """Spec 0010 AC-7: both abstentions fail a number and a term."""
    for s in FIXED_STRINGS:
        assert not matches(num(1500), s)
        assert not matches(term("stipend", "allowance"), s)


# --- loader gates (AC-5, AC-6) ---

HEADER = "# Eval set v1.2 (2026-10-16)\n\n## 1. Rows\n\n"


def row_md(rid, rtype="lookup", source="llm-draft, reviewed", facts=("F1", "F2", "F3")):
    if rtype.startswith("ooc"):
        return f'### Row {rid} — {rtype}\nQ: q?\nexpected: "x"\nref_source: {source}\n'
    lines = {
        "F1": '- F1. [required] Costs $5. — a/b.md § "S" L1',
        "F2": '- F2. [optional] Maybe. — a/b.md § "S" L2',
        "F3": "- F3. [required] Answer-only fact.",
    }
    body = "\n".join(lines[f] for f in facts)
    return f"### Row {rid} — {rtype}\nQ: q?\nfacts:\n{body}\nref_source: {source}\n"


EVALSET = parse(
    HEADER
    + row_md(1)
    + row_md(2, source=AUTO_REVIEWED)
    + row_md(3, rtype="ooc-in-scope")
    + row_md(4, source="human")
)
GOOD = {
    "F1": {"expressible": True, "assert": {"number": 5, "unit": "USD"}},
    "F3": {"expressible": False, "reason": "free text"},
}


def review(checked=True, changed=False):
    return {2: ReviewRow(2, "answerable", checked, changed, "")}


def write(tmp_path, rows, sha=SHA, version="v1.2"):
    import yaml

    p = tmp_path / "a.yaml"
    p.write_text(yaml.safe_dump({"eval_version": version, "eval_sha256": sha, "rows": rows}))
    return p


def load(tmp_path, rows, rev=None, **kw):
    return load_assertions(
        write(tmp_path, rows, **kw), EVALSET, SHA, review() if rev is None else rev
    )


def test_empty_rows_load(tmp_path):
    """Spec 0010 AC-6: an empty rows loads."""
    assert load(tmp_path, {}).entries == {}
    p = tmp_path / "n.yaml"
    p.write_text(f"eval_version: v1.2\neval_sha256: {SHA}\nrows:\n")
    assert load_assertions(p, EVALSET, SHA, {}).entries == {}


def test_committed_file_loads():
    """Spec 0010 AC-6, AC-12: the committed file matches the real eval set and passes every gate."""
    es, sha = real()
    got = load_assertions(ASSERTIONS_PATH, es, sha, load_review(REVIEW_PATH))
    assert got.eval_version == es.version and got.eval_sha256 == sha


def test_valid_reviewed_row_loads(tmp_path):
    """Spec 0010 AC-5/AC-6: an owner-reviewed row with all required facts loads."""
    got = load(tmp_path, {1: GOOD})
    e = got.entries[1]
    assert e["F1"].node == Node("number", 5.0, "USD")
    assert e["F3"].reason == "free text"


def test_node_parsing(tmp_path):
    """Spec 0010 AC-5: term variants and nested nodes parse."""
    rows = {
        1: {
            "F1": {
                "expressible": True,
                "assert": {
                    "all_of": [{"term": "x", "variants": ["y"]}, {"any_of": [{"number": 2}]}]
                },
            },
            "F3": {"expressible": False, "reason": "r"},
        }
    }
    node = load(tmp_path, rows).entries[1]["F1"].node
    assert node.children[0] == Node("term", "x", variants=("y",))
    assert node.children[1].children[0] == Node("number", 2.0)


def test_gate_sha(tmp_path):
    """Spec 0010 AC-6: eval_sha256 mismatch refuses the file."""
    with pytest.raises(AssertionsError, match="eval_sha256"):
        load(tmp_path, {}, sha="b" * 64)


def test_gate_version(tmp_path):
    """Spec 0010 AC-6: eval_version mismatch refuses the file."""
    with pytest.raises(AssertionsError, match="eval_version"):
        load(tmp_path, {}, version="v1.3")


def test_gate_unknown_row(tmp_path):
    """Spec 0010 AC-6: a row not in the eval set."""
    with pytest.raises(AssertionsError, match="row 99"):
        load(tmp_path, {99: GOOD})


def test_gate_ooc_row(tmp_path):
    """Spec 0010 AC-6: an ooc row."""
    with pytest.raises(AssertionsError, match="row 3"):
        load(tmp_path, {3: GOOD})


def test_gate_ineligible_row(tmp_path):
    """Spec 0010 AC-6: a row that is neither owner-reviewed nor checked auto-reviewed."""
    with pytest.raises(AssertionsError, match="row 4"):
        load(tmp_path, {4: GOOD})


@pytest.mark.parametrize("rev", [{}, review(checked=False), review(changed=True)])
def test_auto_reviewed_needs_checked_unchanged(tmp_path, rev):
    """Spec 0010 AC-6: auto-reviewed rows are refused unless checked=y and changed=n."""
    with pytest.raises(AssertionsError, match="row 2"):
        load(tmp_path, {2: GOOD}, rev=rev)


def test_auto_reviewed_checked_loads(tmp_path):
    """Spec 0010 AC-6: checked=y and changed=n makes an auto-reviewed row loadable."""
    assert 2 in load(tmp_path, {2: GOOD}, rev=review()).entries


def test_gate_fact_not_in_row(tmp_path):
    """Spec 0010 AC-6: a fact id not in the row."""
    with pytest.raises(AssertionsError, match="row 1 F9"):
        load(tmp_path, {1: {**GOOD, "F9": GOOD["F3"]}})


def test_gate_fact_not_required(tmp_path):
    """Spec 0010 AC-6: an [optional] fact."""
    with pytest.raises(AssertionsError, match="row 1 F2"):
        load(tmp_path, {1: {**GOOD, "F2": GOOD["F3"]}})


def test_gate_omitted_required_fact(tmp_path):
    """Spec 0010 AC-6: a listed row omitting a required (here answer-only) fact."""
    with pytest.raises(AssertionsError, match="row 1.*F3"):
        load(tmp_path, {1: {"F1": GOOD["F1"]}})


@pytest.mark.parametrize(
    "entry",
    [
        {"expressible": True},
        {"expressible": False},
        {"expressible": False, "reason": "r", "assert": {"number": 1}},
        {"expressible": True, "assert": {"number": 1}, "reason": "r"},
        {"expressible": "yes", "assert": {"number": 1}},
        {"expressible": True, "assert": {"regex": "x"}},
        {"expressible": True, "assert": {"number": 1, "term": "x"}},
        {"expressible": True, "assert": {"number": 1, "variants": ["x"]}},
        {"expressible": True, "assert": {"term": "x", "unit": "days"}},
        {"expressible": True, "assert": {"number": "five"}},
        {"expressible": True, "assert": {"number": True}},
        {"expressible": True, "assert": {"term": 5}},
        {"expressible": True, "assert": {"term": "x", "variants": "y"}},
        {"expressible": True, "assert": {"all_of": []}},
        {"expressible": True, "assert": {"all_of": [{"number": 1, "bogus": 2}]}},
        {"expressible": True, "assert": "text"},
    ],
)
def test_schema_errors_name_row_and_fact(tmp_path, entry):
    """Spec 0010 AC-5: unknown keys/kinds, wrong types, missing assert/reason are load errors."""
    with pytest.raises(AssertionsError, match="row 1 F1"):
        load(tmp_path, {1: {"F1": entry, "F3": GOOD["F3"]}})


def test_eligible():
    """Spec 0010 AC-6: eligibility by ref_source, review and answerability."""
    rows = {r.id: r for r in EVALSET.rows}
    assert eligible(rows[1], {})
    assert not eligible(rows[3], {})
    assert not eligible(rows[4], {})
    assert eligible(rows[2], review())
    assert not eligible(rows[2], review(checked=False))
    assert REVIEWED != AUTO_REVIEWED


# --- review file (AC-11) ---


def test_committed_review_lists_auto_reviewed_rows():
    """Spec 0010 AC-11: exactly the auto-reviewed ids, in eval-set order, with the right types."""
    es, _ = real()
    rev = load_review(REVIEW_PATH)
    expected = [r for r in es.rows if r.ref_source == AUTO_REVIEWED]
    assert len(expected) == 26
    assert list(rev) == [r.id for r in expected]
    for r in expected:
        got = rev[r.id]
        assert got.type == ("answerable" if r.answerable else "ooc")


TABLE = "| row | type | checked | changed | note |\n|---|---|---|---|---|\n"


def review_file(tmp_path, body):
    p = tmp_path / "r.md"
    p.write_text("intro\n\n" + body)
    return p


def test_review_parses(tmp_path):
    """Spec 0010 AC-11: y/n cells and a note parse."""
    p = review_file(tmp_path, TABLE + "| 5 | answerable | y | n | ok |\n| 14 | ooc | n | y | |\n")
    assert load_review(p) == {
        5: ReviewRow(5, "answerable", True, False, "ok"),
        14: ReviewRow(14, "ooc", False, True, ""),
    }


@pytest.mark.parametrize(
    "body",
    [
        "no table here\n",
        TABLE + "| 5 | answerable | yes | n | |\n",
        TABLE + "| 5 | answerable | n | | |\n",
        TABLE + "| 5 | other | n | n | |\n",
        TABLE + "| 5 | answerable | n | n | |\n| 5 | answerable | n | n | |\n",
        TABLE + "| x | answerable | n | n | |\n",
    ],
)
def test_review_malformed(tmp_path, body):
    """Spec 0010 AC-11: bad cells, duplicates or a missing table are errors."""
    with pytest.raises(AssertionsError):
        load_review(review_file(tmp_path, body))


# --- scoring (AC-8) ---


def scored_assertions(tmp_path, rows):
    return load(tmp_path, rows, rev=review())


def run(answers):
    return {rid: {"answer": a} for rid, a in answers.items()}


def test_score_values(tmp_path):
    """Spec 0010 AC-8: fact_pass, row_pass, SE, counts, abstention, eligible_not_in_file."""
    two = {
        "F1": {"expressible": True, "assert": {"number": 5}},
        "F3": {"expressible": True, "assert": {"term": "answer"}},
    }
    only_na = {
        "F1": {"expressible": False, "reason": "r"},
        "F3": {"expressible": False, "reason": "r"},
    }
    a = scored_assertions(tmp_path, {1: two, 2: only_na})
    # row 2 is auto-reviewed and checked in review(); row 1 passes one of two facts
    rep = score(a, EVALSET, review(), run({1: "It costs 5.", 2: "x"}))
    r1, r2 = rep.rows
    assert (r1.row, r1.fact_pass, r1.row_pass, r1.abstained) == (1, 0.5, False, False)
    assert [(f.fact, f.passed) for f in r1.facts] == [("F1", True), ("F3", False)]
    assert (r2.fact_pass, r2.row_pass) == (None, None)
    assert [f.passed for f in r2.facts] == [None, None]
    assert rep.fact_pass == mean_se([0.5], binary=False)
    assert rep.row_pass == mean_se([0.0], binary=True)
    assert (rep.n_rows_scored, rep.n_expressible, rep.n_not_expressible) == (1, 2, 2)
    assert rep.eligible_not_in_file == ()


def test_score_means_and_eligible_not_in_file(tmp_path):
    """Spec 0010 AC-8: means over several rows; eligible rows without entries are listed."""
    one = {
        "F1": {"expressible": True, "assert": {"number": 5}},
        "F3": {"expressible": False, "reason": "r"},
    }
    a = scored_assertions(tmp_path, {1: one})
    rep = score(a, EVALSET, review(), run({1: "5"}))
    assert rep.fact_pass == mean_se([1.0], binary=False)
    assert rep.eligible_not_in_file == (2,)
    assert rep.n_not_expressible == 1
    assert score(a, EVALSET, {}, run({1: "5"})).eligible_not_in_file == ()


def test_score_abstention_fails_everything(tmp_path):
    """Spec 0010 AC-8: an abstained answer fails every assertion."""
    rows = {
        1: {
            "F1": {"expressible": True, "assert": {"term": "stipend"}},
            "F3": {"expressible": True, "assert": {"number": 5}},
        }
    }
    a = scored_assertions(tmp_path, rows)
    for s in FIXED_STRINGS:
        (r,) = score(a, EVALSET, review(), run({1: s})).rows
        assert r.abstained and r.fact_pass == 0.0 and r.row_pass is False


def test_score_empty_and_missing(tmp_path):
    """Spec 0010 AC-8: empty file scores n = 0; a missing row or answer is an error."""
    rep = score(scored_assertions(tmp_path, {}), EVALSET, review(), {})
    assert rep.rows == () and rep.fact_pass is None and rep.row_pass is None
    assert rep.eligible_not_in_file == (1, 2)
    a = scored_assertions(tmp_path, {1: GOOD})
    with pytest.raises(AssertionsError, match="row 1"):
        score(a, EVALSET, review(), {})
    with pytest.raises(AssertionsError, match="row 1"):
        score(a, EVALSET, review(), {1: {}})


@pytest.mark.parametrize(
    "body",
    [
        "rows:\n  1:\n    F1: {expressible: false, reason: x}\n  1:\n    F3: {expressible: true}\n",
        "rows:\n  1:\n    F1: {expressible: false, reason: x}\n    F1: {expressible: true}\n",
    ],
    ids=["row", "fact"],
)
def test_duplicate_keys_refused(tmp_path, body):
    """Spec 0010 AC-6: a duplicate row or fact key refuses the file instead of dropping entries."""
    p = tmp_path / "d.yaml"
    p.write_text(f"eval_version: v1.2\neval_sha256: {SHA}\n{body}")
    with pytest.raises(AssertionsError, match="duplicate key"):
        load_assertions(p, EVALSET, SHA, review())
