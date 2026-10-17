import uuid

import pytest

from handbook_rag.evaluation.evalset import Fact, Row
from handbook_rag.evaluation.evidence import (
    EvidenceError,
    matches,
    normalise,
    relevant_chunks,
)

A, B, C = (uuid.uuid4() for _ in range(3))

PAGES = {
    "a.md": ["# Title", "", "Laptops   are\trefreshed every three years.", "   ", "Tail line."],
    "b.md": ["Stipend is 1,500 USD.", "Only in b."],
}
CHUNKS = {
    "a.md": [(A, "# Title\n\nLaptops are refreshed every\nthree years.\n"), (B, "Tail")],
    "b.md": [(C, "Stipend is 1,500 USD.\nOnly in b.")],
}


def read_page(path):
    if path not in PAGES:
        raise FileNotFoundError(path)
    return PAGES[path]


def page_chunks(path):
    return CHUNKS.get(path, [])


def fact(fid="F1", required=True, **cites):
    return Fact(id=fid, required=required, cites={k.replace("_", "."): v for k, v in cites.items()})


def row(*facts, rid=7, type="lookup"):
    return Row(id=rid, type=type, question="Q?", facts=facts)


def run(*rows):
    return relevant_chunks(rows, read_page, page_chunks)


def test_normalise():
    """AC-2: whitespace runs collapse to one space; ends stripped."""
    assert normalise("  a \t b\n\nc  ") == "a b c"


def test_matches_full_line():
    """AC-2: a cited line contained in full matches."""
    assert matches(["Only in b."], "Stipend.\nOnly in b.")


LONG = "Purchase the items you need using your own funds and submit a claim in Navan."


def test_matches_partial_line_too_short_does_not():
    """AC-2: a cut-off piece under MIN_PIECE characters doesn't match."""
    assert not matches(["Tail line."], "Tail")
    assert not matches([LONG], "own funds and submit a claim in Navan.")  # 38 chars


def test_matches_straddled_line_at_chunk_start_or_end():
    """AC-2: a line the chunk window cut matches on a piece of at least MIN_PIECE characters,
    at the chunk's start (suffix of the line) or end (prefix of the line)."""
    assert matches([LONG], "your own funds and submit a claim in Navan.\nNext line.")
    assert matches([LONG], "Earlier text.\nPurchase the items you need using your own")


def test_matches_piece_must_sit_at_the_chunk_edge():
    """AC-2: a piece in the middle of a chunk isn't a straddle (the line would be whole)."""
    assert not matches([LONG], "Before. your own funds and submit a claim in Navan. After.")


def test_matches_whitespace_normalised():
    """AC-2: a line split across newlines or with odd spacing still matches."""
    assert matches(
        ["Laptops   are\trefreshed every three years."], "Laptops are refreshed every\nthree years."
    )


def test_matches_ignores_blank_lines():
    """AC-2: blank cited lines match nothing (otherwise every chunk would match)."""
    assert not matches(["", "   \t"], "anything")
    assert matches(["", "anything"], "anything")


def test_relevant_chunks_full_line():
    """AC-2: chunks holding a cited line are the fact's relevant set; blank lines ignored."""
    ev = run(row(fact(a_md=(3, 4))))
    assert ev.relevant == {(7, "F1"): frozenset({A})}
    assert ev.warnings == []


def test_relevant_chunks_or_across_pages():
    """AC-2, AC-3: a fact citing several pages is relevant to the union of their chunks."""
    ev = run(row(fact(a_md=(3,), b_md=(1,))))
    assert ev.relevant[(7, "F1")] == frozenset({A, C})


def test_page_with_only_blank_lines_contributes_nothing():
    """AC-2: a page whose cited lines are all blank adds no chunks; others still count."""
    ev = run(row(fact(a_md=(2, 4), b_md=(2,))))
    assert ev.relevant[(7, "F1")] == frozenset({C})


def test_required_unmatchable_raises_naming_row_and_fact():
    """AC-2: a required fact with no relevant chunk fails the run, naming row and fact."""
    with pytest.raises(EvidenceError) as e:
        run(row(fact("F1", a_md=(3,)), fact("F2", a_md=(5,)), rid=11))
    msg = str(e.value)
    assert "row 11 F2 (required)" in msg
    assert "a.md" in msg
    assert "F1" not in msg


def test_optional_unmatchable_warns():
    """AC-2: an unmatchable optional fact is a warning and an empty relevant set."""
    ev = run(row(fact("F1", a_md=(3,)), fact("F3", required=False, a_md=(5,)), rid=23))
    assert ev.warnings == ["row 23 F3 (optional): no stored chunk contains a cited line of a.md"]
    assert ev.relevant[(23, "F3")] == frozenset()
    assert ev.relevant[(23, "F1")] == frozenset({A})


def test_out_of_range_line_and_missing_file():
    """AC-2: a line past the end of its file or a missing file errors (required), warns
    (optional)."""
    with pytest.raises(EvidenceError, match=r"row 7 F1 \(required\): line\(s\) L99 out of range"):
        run(row(fact(a_md=(3, 99))))
    with pytest.raises(EvidenceError, match=r"row 7 F1 \(required\): cited file x.md not found"):
        run(row(fact(x_md=(1,))))
    ev = run(row(fact("F1", a_md=(3,)), fact("F2", required=False, a_md=(3, 99))))
    assert ev.warnings == ["row 7 F2 (optional): line(s) L99 out of range for a.md (5 lines)"]
    assert ev.relevant[(7, "F2")] == frozenset({A})


def test_answer_only_facts_and_ooc_rows_skipped():
    """AC-2: facts with no citation and ooc rows aren't checked or keyed."""
    ev = run(
        row(fact("F1", a_md=(3,)), fact("F2")),
        Row(id=9, type="ooc-off-topic", question="Q?", expected="Out of scope."),
    )
    assert set(ev.relevant) == {(7, "F1")}
