from pathlib import Path

import pytest

from handbook_rag.evaluation.evalset import EvalSetError, parse

HEADER = "# Eval set v1.2 (2026-10-16)\n\n## 1. Trap rows\n\n"
ANSWERABLE = """\
### Row 11 — recency · process · trap T1
Q: how do i buy my laptop?
expected_docs: a/laptop.md, finance/expenses.md
citation: "Equipment" (finance/expenses.md L1)
facts:
- F1. [required] GitLab issues it. — a/laptop.md § "Ordering" L24–24
- F2. [optional] Monitor from the stipend. — finance/expenses.md § "Equipment" L417
recency_basis: history-only (only commit c72b6af5ef shows it). Scored: F1.
notes: see finance/expenses.md L753 and other/page.md L9–12.
"""
OOC = """\
### Row 14 — ooc-in-scope · single-fact · trap –
Q: What is the fertility benefit amount?
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg fertility` → total-rewards/benefits/_index.md L152–156
"""


def one(body):
    return parse(HEADER + body).rows[0]


def cites(fact_text):
    """The cites of F1 in a minimal answerable row."""
    row = one(f"### Row 1 — lookup · single-fact\nQ: q?\nfacts:\n- F1. [required] {fact_text}\n")
    return row.facts[0].cites


def test_answerable_row():
    """AC-1: id, type, question, expected docs, facts with markers and cites, recency_basis."""
    es = parse(HEADER + ANSWERABLE)
    assert es.version == "v1.2"
    (row,) = es.rows
    assert (row.id, row.type, row.question) == (11, "recency", "how do i buy my laptop?")
    assert row.expected_docs == ("a/laptop.md", "finance/expenses.md")
    assert row.answerable and row.expected is None
    assert [(f.id, f.required) for f in row.facts] == [("F1", True), ("F2", False)]
    assert row.facts[0].cites == {"a/laptop.md": (24,)}
    assert row.facts[1].cites == {"finance/expenses.md": (417,)}
    assert row.required == (row.facts[0],)
    assert row.recency_basis == "history-only"
    assert not row.conflict_unscored


def test_ooc_row():
    """AC-1: an out-of-corpus row carries the expected string, unquoted, and no facts."""
    row = one(OOC)
    assert (row.id, row.type, row.answerable) == (14, "ooc-in-scope", False)
    assert row.expected == "I don't know based on the provided handbook excerpts."
    assert row.facts == () and row.expected_docs == ()


def test_cut_rows_skipped():
    """AC-1: rows under "## 5. Cut" are not parsed, even if malformed."""
    cut = "## 5. Cut (owner, 2026-10-15)\n\n### Row 1 — lookup · single-fact\n- F1. no marker\n"
    assert [r.id for r in parse(HEADER + ANSWERABLE + OOC + cut).rows] == [11, 14]


def test_conflict_unscored_and_in_page():
    """AC-1: a recency_basis line saying "not scored" marks the conflict unscored."""
    body = ANSWERABLE.replace(
        "recency_basis: history-only (only commit c72b6af5ef shows it). Scored: F1.",
        "recency_basis: in-page (cross-page). Conflict Not Scored on this row.",
    )
    row = one(body)
    assert row.recency_basis == "in-page"
    assert row.conflict_unscored


def test_no_recency_basis():
    """AC-1: recency_basis is optional."""
    row = one(ANSWERABLE.replace("recency_basis:", "flag:"))
    assert row.recency_basis is None and not row.conflict_unscored


@pytest.mark.parametrize(
    ("fact", "expected"),
    [
        (
            'Two pages. — a/p.md § "h" L26–26; b/q.md § "h" L74–74',
            {"a/p.md": (26,), "b/q.md": (74,)},
        ),
        ('Reuse. — a/p.md § "h" L11–11 and § "h2" L99–101', {"a/p.md": (11, 99, 100, 101)}),
        ('Out of order. — a/p.md § "h" L448–448; § "Equipment" L422–422', {"a/p.md": (448, 422)}),
        ('Comma. — values/_index.md § "CREDIT" L14, L16', {"values/_index.md": (14, 16)}),
        ("Hyphen. — a/p.md L5-7", {"a/p.md": (5, 6, 7)}),
        (
            'Front matter. — company/op.md § "Acknowledging CREDIT" L77–79; (front matter) L3',
            {"company/op.md": (77, 78, 79, 3)},
        ),
        ("Derived. — derived from people-group/types.md L25", {"people-group/types.md": (25,)}),
        ('Paren. — p/types.md § "Overview" (Public Holiday) L60', {"p/types.md": (60,)}),
        (
            "Intro. — p/onboarding/_index.md (intro, no heading) L8–8",
            {"p/onboarding/_index.md": (8,)},
        ),
        (
            r'Escaped. — cx/r/_index.md § "1. The \"Hands on Keyboard\" Boundary" L26; (intro) L6',
            {"cx/r/_index.md": (26, 6)},
        ),
        (
            'Belgium: no carryover (t/bv-belgium.md § "Vacation Leave" L217). Ireland: approval'
            ' (t/ireland.md § "Time Off" L402). India: (entity/india.md § "Leave" L268–269).',
            {"t/bv-belgium.md": (217,), "t/ireland.md": (402,), "entity/india.md": (268, 269)},
        ),
        ("Root page. — _index.md L4", {"_index.md": (4,)}),
        ('Dupes. — a/p.md L5–6; § "h" L6–7; a/p.md L5', {"a/p.md": (5, 6, 7)}),
    ],
)
def test_citation_variants(fact, expected):
    """AC-1: paths and line refs in one ordered scan; refs go to the latest path."""
    assert cites(fact) == expected


def test_answer_only_fact():
    """AC-1: a fact with no citation is allowed and answer-only."""
    row = one(
        "### Row 22 — lookup · conditional\nQ: q?\nfacts:\n"
        "- F1. [required] Depends on the entity. — framing derived from the sections in F2–F6\n"
        "- F2. [optional] Germany. — entity/gmbh.md L132–133\n"
    )
    assert row.facts[0].answer_only and row.facts[0].cites == {}
    assert row.required == ()  # answer-only required facts are outside the retrieval metrics


@pytest.mark.parametrize(
    ("body", "match"),
    [
        ("### Row 7 — lookup · single-fact\nfacts:\n- F1. [required] x — a/p.md L1\n", "no Q:"),
        ("### Row 7 — trivia · single-fact\nQ: q?\n", "unknown type 'trivia'"),
        ("### Row 7\nQ: q?\n", "unknown type"),
        ("### Row 7 — lookup · list\nQ: q?\nfacts:\n- F1. [optional] x — a/p.md L1\n", "required"),
        ("### Row 7 — lookup · list\nQ: q?\nfacts:\n- F1. x — a/p.md L1\n", "F1 has neither"),
        ("### Row 7 — lookup · list\nQ: q?\nfacts:\n- F1. [required] L3 of a/p.md\n", "before"),
        (
            "### Row 7 — lookup · list\nQ: q?\nfacts:\n"
            "- F1. [required] Mention of a/p.md. — b/q.md L9\n",
            "F1 cites a/p.md with no L<n> line ref",
        ),
        ("### Row 7 — ooc-off-topic · list\nQ: q?\n", "no expected:"),
        ("### Row 7 — recency · list\nQ: q?\nrecency_basis: maybe\n", "recency_basis"),
    ],
)
def test_malformed_row(body, match):
    """AC-1: a malformed row fails the run, naming the row."""
    with pytest.raises(EvalSetError, match=f"^row 7: .*{match}"):
        parse(HEADER + body)


def test_path_without_line_ref():
    """AC-1: a fact citing a .md path with no L<n> ref fails; it is not silently answer-only."""
    with pytest.raises(EvalSetError, match=r"^row 1: F1 cites a/p\.md with no L<n> line ref$"):
        cites("Bare path. — a/p.md")


def test_lines_prose_ref():
    """AC-1: "lines 40-42" is not an L<n> ref, so the cited path has no line ref and fails."""
    with pytest.raises(
        EvalSetError, match=r"^row 1: F1 cites finance/expenses\.md with no L<n> line ref$"
    ):
        cites("Prose ref. — finance/expenses.md lines 40-42")


def test_duplicate_row_id():
    """AC-1: two rows with the same id fail the run, naming the row."""
    body = '### Row 3 — ooc-off-topic · x\nQ: q?\nexpected: "no"\n'
    with pytest.raises(EvalSetError, match=r"^row 3: duplicate row id$"):
        parse(HEADER + body + body)


def test_duplicate_fact_id():
    """AC-1: two facts with the same id in one row fail the run, naming the row and fact."""
    body = (
        "### Row 4 — lookup · list\nQ: q?\nfacts:\n"
        "- F1. [required] x — a/p.md L1\n- F1. [optional] y — a/p.md L2\n"
    )
    with pytest.raises(EvalSetError, match=r"^row 4: duplicate fact id F1$"):
        parse(HEADER + body)


def test_missing_header():
    """AC-1: no version header, no eval set."""
    with pytest.raises(EvalSetError, match="no '# Eval set vX.Y' header"):
        parse(ANSWERABLE)


def test_real_eval_set():
    """AC-1: the committed eval set parses to its documented counts."""
    path = Path(__file__).resolve().parents[2] / "docs/eval/eval-set-v1.md"
    es = parse(path.read_text())
    answerable = [r for r in es.rows if r.answerable]
    facts = [f for r in answerable for f in r.facts]
    assert es.version == "v1.2"
    assert (len(es.rows), len(answerable)) == (52, 33)
    assert len(facts) == 187
    assert {(r.id, f.id) for r in answerable for f in r.facts if f.answer_only} == {
        (22, "F1"),
        (58, "F1"),
    }
    assert {r.id for r in es.rows if r.conflict_unscored} == {50, 53, 58}
    bases = [r.recency_basis for r in es.rows if r.recency_basis]
    assert (bases.count("in-page"), bases.count("history-only")) == (8, 8)
    row11 = next(r for r in es.rows if r.id == 11)
    laptop = "eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md"
    assert row11.facts[2].cites == {laptop: (11, 99, 100, 101)}


@pytest.mark.parametrize(
    ("fact", "text"),
    [
        ('GitLab issues it. — a/laptop.md § "Ordering" L24', "GitLab issues it."),
        ("[variant: Brazil] Self-procure. — a/b.md L11", "Self-procure."),
        ("[rewording: which entity] GSI. — a/b.md L1", "GSI."),
        ("Depends on the entity. — framing derived from F2–F6", "Depends on the entity."),
        ("A — B. — a/b.md L1", "A — B."),
        ("Belgium: no carryover (a/b.md L217).", "Belgium: no carryover (a/b.md L217)."),
    ],
)
def test_fact_text(fact, text):
    """Spec 0010 AC-7: the statement is the reference text; the citation is cut off."""
    row = one(f"### Row 1 — lookup · single-fact\nQ: q?\nfacts:\n- F1. [required] {fact}\n")
    assert row.facts[0].text == text


def test_ref_source():
    """Spec 0010 AC-6: ref_source is parsed for answerable and ooc rows."""
    body = (
        ANSWERABLE
        + "ref_source: llm-draft, reviewed\n\n"
        + OOC
        + "ref_source: llm-draft, auto-reviewed\n"
    )
    rows = parse(HEADER + body).rows
    assert [r.ref_source for r in rows] == ["llm-draft, reviewed", "llm-draft, auto-reviewed"]


def test_real_eval_set_text_and_ref_source():
    """Spec 0010 AC-6, AC-7: every required fact has a statement; 26 reviewed, 26 auto-reviewed."""
    path = Path(__file__).resolve().parents[2] / "docs/eval/eval-set-v1.md"
    es = parse(path.read_text())
    required = [f for r in es.rows for f in r.facts if f.required]
    assert all(f.text and "§" not in f.text for f in required)
    sources = [r.ref_source for r in es.rows]
    counts = sources.count("llm-draft, reviewed"), sources.count("llm-draft, auto-reviewed")
    assert counts == (26, 26)
