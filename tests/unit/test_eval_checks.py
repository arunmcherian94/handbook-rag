import pytest

from handbook_rag.ask import Citation
from handbook_rag.evaluation.checks import abstention, code_checks, page_headings
from handbook_rag.prompts import NOT_FOUND, OUT_OF_SCOPE


@pytest.mark.parametrize("expected", [NOT_FOUND, OUT_OF_SCOPE])
def test_abstention_ooc_exact_passes(expected):
    """AC-4: an ooc row passes on its exact string, whitespace trimmed."""
    a = abstention(f"  {expected}\n", expected)
    assert a.abstained is True
    assert a.passed is True
    assert a.false_abstention is None
    assert a.label is None


def test_abstention_ooc_wrong_string():
    """AC-4: the other fixed string fails and is labelled wrong-string."""
    a = abstention(NOT_FOUND, OUT_OF_SCOPE)
    assert (a.abstained, a.passed, a.false_abstention, a.label) == (
        True,
        False,
        None,
        "wrong-string",
    )


@pytest.mark.parametrize("prefix", [NOT_FOUND, OUT_OF_SCOPE])
def test_abstention_ooc_abstain_plus_extra(prefix):
    """AC-4: a fixed string followed by more text fails and is labelled abstain+extra."""
    a = abstention(f"{prefix} But generally, X is Y.", OUT_OF_SCOPE)
    assert (a.abstained, a.passed, a.false_abstention, a.label) == (
        False,
        False,
        None,
        "abstain+extra",
    )


def test_abstention_ooc_answered():
    """AC-4: an ooc row answered with content fails, no label."""
    a = abstention("Paris is the capital of France.", OUT_OF_SCOPE)
    assert (a.abstained, a.passed, a.false_abstention, a.label) == (False, False, None, None)


@pytest.mark.parametrize("fixed", [NOT_FOUND, OUT_OF_SCOPE])
def test_abstention_answerable_false_abstention(fixed):
    """AC-4: an answerable row answered with either fixed string is a false abstention."""
    a = abstention(f" {fixed} ", None)
    assert (a.abstained, a.passed, a.false_abstention, a.label) == (True, None, True, None)


def test_abstention_answerable_abstain_plus_extra():
    """AC-4: abstain+extra on an answerable row is labelled, not a false abstention."""
    a = abstention(f"{NOT_FOUND} However, see [1].", None)
    assert (a.abstained, a.passed, a.false_abstention, a.label) == (
        False,
        None,
        False,
        "abstain+extra",
    )


def test_abstention_answerable_answered():
    """AC-4: a normal answer is not an abstention and has no label."""
    a = abstention("Yes, see [1].", None)
    assert (a.abstained, a.passed, a.false_abstention, a.label) == (False, None, False, None)


def test_page_headings_include_title():
    """AC-5: headings outside code fences plus the page title."""
    body = "Intro\n\n## Leave policy\n\n```\n# not a heading\n```\n\n### Parental leave\n"
    assert page_headings(body, "Paid time off") == {
        "Leave policy",
        "Parental leave",
        "Paid time off",
    }
    assert page_headings("no headings", "Title") == {"Title"}


HEADINGS = {"/handbook/a/": {"A title", "Section 1"}, "/handbook/b/": {"B title"}}


def checks(answer="Yes [1].", citations=None, invalid=None, truncated=False):
    if citations is None:
        citations = [Citation(1, "/handbook/a/", "Section 1")]
    return code_checks(answer, citations, invalid or [], truncated, HEADINGS)


def test_code_checks_all_pass():
    """AC-5: a cited, in-range, existing-heading, URL-free answer passes."""
    c = checks(
        citations=[Citation(1, "/handbook/a/", "Section 1"), Citation(2, "/handbook/b/", "B title")]
    )
    assert c.has_citation and c.citations_in_range and c.headings_exist and c.no_url
    assert c.truncated is False
    assert c.missing_headings == []
    assert c.passed is True


def test_code_checks_no_citation():
    """AC-5: an answer without citations fails has_citation."""
    c = checks(answer="Yes.", citations=[])
    assert c.has_citation is False
    assert c.passed is False


def test_code_checks_out_of_range():
    """AC-5: any invalid citation number fails citations_in_range."""
    c = checks(answer="Yes [1] [9].", invalid=[9])
    assert c.citations_in_range is False
    assert c.has_citation is True
    assert c.passed is False


def test_code_checks_missing_heading():
    """AC-5: a heading not on its page, or a page with no headings known, is listed."""
    c = checks(
        citations=[
            Citation(1, "/handbook/a/", "Section 1"),
            Citation(2, "/handbook/a/", "Gone"),
            Citation(3, "/handbook/z/", "Section 1"),
        ]
    )
    assert c.headings_exist is False
    assert c.missing_headings == [("/handbook/a/", "Gone"), ("/handbook/z/", "Section 1")]
    assert c.passed is False


@pytest.mark.parametrize(
    "answer",
    ["See https://example.com [1].", "See http://x.io [1].", "See WWW.example.com [1]."],
)
def test_code_checks_url(answer):
    """AC-5: http://, https:// or www. (any case) fails no_url."""
    c = checks(answer=answer)
    assert c.no_url is False
    assert c.passed is False


def test_code_checks_truncated_reported_not_scored():
    """AC-5: truncation is passed through and doesn't affect passed."""
    c = checks(truncated=True)
    assert c.truncated is True
    assert c.passed is True


def test_code_checks_accepts_iterator():
    """AC-5: citations may be any iterable, consumed once."""
    c = checks(citations=iter([Citation(1, "/handbook/a/", "Section 1")]))
    assert c.has_citation and c.headings_exist
