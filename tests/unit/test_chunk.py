import math
import uuid
from itertools import accumulate
from pathlib import Path

import pytest
import tiktoken

from handbook_rag.chunk import chunk_doc, chunk_structural, find_headings, headings
from handbook_rag.constants import CHECKOUT, CHUNK_CONFIGS, CHUNK_OVERLAP, CHUNK_SIZE
from handbook_rag.ingest import split_front_matter

ENC = tiktoken.get_encoding("cl100k_base")
DOC = uuid.UUID(int=1)
STRIDE = CHUNK_SIZE - CHUNK_OVERLAP
WORDS = [
    "alpha",
    "bravo",
    "charlie",
    "delta",
    "echo",
    "foxtrot",
    "golf",
    "hotel",
    "india",
    "juliet",
]


def prose(n_words: int) -> str:
    return " ".join(WORDS[(i * 7 + i // 3) % len(WORDS)] for i in range(n_words))


def start_byte(body: str, chunk_index: int) -> int:
    """Byte offset where window `chunk_index` starts, derived from the token stream."""
    return len(ENC.decode_bytes(ENC.encode(body)[: chunk_index * STRIDE]))


def test_windows_match_token_slices():
    """AC-1: windows are 512 tokens, starting every 448; last window ends at the stream end."""
    text = prose(3000)
    tokens = ENC.encode(text)
    chunks = chunk_doc(DOC, text, ENC)
    for i, c in enumerate(chunks):
        window = tokens[i * STRIDE : i * STRIDE + CHUNK_SIZE]
        assert c.chunk_index == i
        assert c.content == ENC.decode(window)
        assert c.token_count == len(window) <= CHUNK_SIZE
    assert all(c.token_count == CHUNK_SIZE for c in chunks[:-1])
    assert i * STRIDE + len(window) == len(tokens)


def test_chunk_count():
    """AC-1: n > 512 tokens gives 1 + ceil((n - 512) / 448) chunks, none entirely overlap."""
    for words in (600, 1000, 2500):
        text = prose(words)
        n = len(ENC.encode(text))
        assert n > CHUNK_SIZE
        assert len(chunk_doc(DOC, text, ENC)) == 1 + math.ceil((n - CHUNK_SIZE) / STRIDE)
    # exactly 512 tokens and exactly 512 + 448 tokens end on the window, with no extra one
    tokens = ENC.encode(prose(3000))
    assert len(chunk_doc(DOC, ENC.decode(tokens[:512]), ENC)) == 1
    assert len(chunk_doc(DOC, ENC.decode(tokens[: 512 + 448]), ENC)) == 2


def test_overlap_is_64_tokens_and_dedup_rebuilds_text():
    """AC-1: consecutive windows share 64 tokens; dropping the overlap restores the text."""
    text = prose(3000)
    chunks = chunk_doc(DOC, text, ENC)
    toks = [ENC.encode(c.content) for c in chunks]
    for a, b in zip(toks, toks[1:], strict=False):
        assert a[-CHUNK_OVERLAP:] == b[:CHUNK_OVERLAP]
    rebuilt = toks[0] + [t for ts in toks[1:] for t in ts[CHUNK_OVERLAP:]]
    assert ENC.decode(rebuilt) == text


def test_short_doc_is_one_chunk():
    """AC-1: a document shorter than one window becomes one chunk with the full content."""
    (c,) = chunk_doc(DOC, "# Hi\n\nshort body", ENC)
    assert c.content == "# Hi\n\nshort body"
    assert c.chunk_index == 0
    assert c.token_count == len(ENC.encode(c.content))
    assert c.heading == "Hi"


@pytest.mark.parametrize("body", ["", "  \n\t", "\n\n"])
def test_empty_doc_has_no_chunks(body):
    """AC-1: an empty or whitespace-only document produces none."""
    assert chunk_doc(DOC, body, ENC) == []


def test_heading_attribution_by_window_start():
    """AC-1: a chunk takes the last heading starting at or before its window start."""
    body = "intro\n# A\n" + prose(700) + "\n## B\n" + prose(900)
    pos_b = body.encode().find(b"## B")
    chunks = chunk_doc(DOC, body, ENC)
    expected = [
        None if start_byte(body, i) < body.encode().find(b"# A") else
        "A" if start_byte(body, i) < pos_b else "B"
        for i in range(len(chunks))
    ]  # fmt: skip
    assert [c.heading for c in chunks] == expected
    assert {"A", "B"} <= set(expected)


def test_text_before_first_heading_has_none():
    """AC-1: text before any heading gets heading None."""
    body = prose(700) + "\n# Late\n" + prose(100)
    chunks = chunk_doc(DOC, body, ENC)
    assert chunks[0].heading is None


def test_leading_blank_lines_before_heading():
    """AC-1: a doc opening with blank lines then a heading attributes chunk 0 to that heading."""
    (c,) = chunk_doc(DOC, "\n\n## Planning PTO\n\nTell your lead.", ENC)
    assert c.heading == "Planning PTO"


def test_heading_after_split_multibyte_char_at_window_start():
    """AC-1: a window opening on a split character's tail, then a heading, gets that heading."""
    prefix = "# Old\n\n" + "word " * 300
    body = prefix + "龘\n## New\n" + "more " * 400  # cl100k splits 龘 across 3 tokens
    tokens = ENC.encode(body)
    # Find a window start that lands inside the emoji's bytes, then chunk with that stride.
    emoji_at = len(prefix.encode())
    offs = [0]
    for t in tokens:
        offs.append(offs[-1] + len(ENC.decode_single_token_bytes(t)))
    start = next(i for i, o in enumerate(offs) if emoji_at < o < emoji_at + 3)
    chunks = chunk_doc(DOC, body, ENC, size=start + 50, overlap=50)
    assert chunks[1].heading == "New"


def test_heading_exactly_at_window_start_counts():
    """AC-1: a heading line beginning at the window's first byte is that chunk's heading."""
    prefix = " word" * 447 + "\n"
    assert len(ENC.encode(prefix)) == STRIDE
    body = prefix + "# Here\n" + prose(300)
    assert start_byte(body, 1) == len(prefix.encode())
    chunks = chunk_doc(DOC, body, ENC)
    assert [c.heading for c in chunks] == [None, "Here"]


@pytest.mark.parametrize("fence", ["```", "~~~", "   ```"])
def test_fenced_code_is_not_a_heading(fence):
    """AC-1: '#' lines inside ``` or ~~~ fences are never headings."""
    body = f"# Real\n{fence}\n# not a heading\n{fence}\n" + prose(900)
    assert find_headings(body)[1] == ["Real"]
    assert {c.heading for c in chunk_doc(DOC, body, ENC)} == {"Real"}


def test_fence_closes_only_on_same_char():
    """AC-1: a ~~~ line does not close a ``` fence; the heading after the real close counts."""
    body = "```\n~~~\n# inside\n```\n# After\n"
    assert find_headings(body)[1] == ["After"]


@pytest.mark.parametrize(
    "line, expected",
    [
        (
            "## Tips & Tricks for visa arrangements {#visa-tips}",
            "Tips & Tricks for visa arrangements",
        ),
        ("### Refinement {.h5}", "Refinement"),
        ("#### RED{.text-danger #red}", "RED"),
        ("### **United Arab Emirates 🇦🇪**", "United Arab Emirates 🇦🇪"),
        ("## Use {braces} in prose", "Use {braces} in prose"),
        ("## **Bold** start only", "**Bold** start only"),
        ("## **A** and **B**", "**A** and **B**"),
    ],
)
def test_heading_drops_hugo_attributes_and_whole_bold(line, expected):
    """AC-1: citation headings drop Hugo {#id}/{.class} attributes and whole-heading bold."""
    assert find_headings(line + "\n")[1] == [expected]


def test_heading_text_is_cleaned():
    """AC-1: trailing #'s and whitespace are stripped; non-headings are ignored."""
    body = "## Title ##  \n#nospace\n####### seven\n# \nplain # text\n"
    assert find_headings(body)[1] == ["Title"]


def test_multibyte_across_window_edge():
    """AC-1: emoji/CJK cut by a window edge neither raise nor leave U+FFFD; headings hold."""
    body = "# Title\n" + "🙂漢字🎉" * 500
    chunks = chunk_doc(DOC, body, ENC)
    assert len(chunks) > 1
    assert all("�" not in c.content for c in chunks)
    assert {c.heading for c in chunks} == {"Title"}


def test_special_token_text_in_body():
    """AC-1: '<|endoftext|>' in handbook text is chunked as plain text, not rejected."""
    body = "# T\nbefore <|endoftext|> after"
    (c,) = chunk_doc(DOC, body, ENC)
    assert "<|endoftext|>" in c.content


def test_chunk_ids_deterministic_and_parameterised():
    """AC-1: ids repeat for the same input and change with doc, size or overlap."""
    text = prose(1500)
    ids = lambda *a, **k: [c.chunk_id for c in chunk_doc(*a, **k)]  # noqa: E731
    base = ids(DOC, text, ENC)
    assert base == ids(DOC, text, ENC)
    assert len(set(base)) == len(base)
    assert not set(base) & set(ids(uuid.UUID(int=2), text, ENC))
    assert not set(base) & set(ids(DOC, text, ENC, size=256, overlap=32))
    assert not set(base) & set(ids(DOC, text, ENC, overlap=0))


# Structural chunker (spec 0005)

ROOT = Path(__file__).resolve().parents[2]
EXPENSES = ROOT / CHECKOUT / "content/handbook/finance/expenses.md"
V1 = CHUNK_CONFIGS["structural-v1"]["params"]


def structural(body: str, **params) -> list:
    return chunk_structural(DOC, body, ENC, config_id="test", **{**V1, **params})


@pytest.fixture(scope="module")
def expenses():
    """(file lines, chunks) for finance/expenses.md at the pin, chunked as structural-v1."""
    if not EXPENSES.exists():
        pytest.fail("Corpus checkout missing. Run `make corpus` first.")
    text = EXPENSES.read_text(encoding="utf-8")
    _, body = split_front_matter(text)
    offset = text[: len(text) - len(body)].count("\n")
    assert offset == 3
    return text.split("\n"), structural(body, line_offset=offset)


def test_line_ranges_match_source_file(expenses):
    """AC-9, AC-15: content is the file's lines line_start..line_end, front matter counted; only
    a sub-chunk of a split section may cut its first or last line."""
    lines, chunks = expenses
    whole = 0
    for k, c in enumerate(chunks):
        got = c.content.removesuffix("\n").split("\n")
        want = lines[c.line_start - 1 : c.line_end]
        assert len(got) == len(want)
        if got == want:
            whole += 1
            continue
        split = [d for d in chunks if d.heading_path == c.heading_path]
        assert len(split) > 1, f"chunk {k} is not a split sub-chunk but cuts a line"
        assert want[0].endswith(got[0]) and want[-1].startswith(got[-1])
        assert got[1:-1] == want[1:-1]
    assert whole > len(chunks) * 0.8


def test_expenses_two_4_1_headings_are_separate(expenses):
    """AC-6, AC-9, AC-15: the two `### 4.1` headings (lines 103, 346) are separate sections with
    their own ranges; their children's paths run through the right one."""
    lines, chunks = expenses
    assert lines[102].startswith("### 4.1 TRAVEL") and lines[345].startswith("### 4.1 NON-TRAVEL")
    by_line = {c.line_start: c for c in chunks}
    travel, non_travel = by_line[103], by_line[346]
    assert travel.heading_path == ("4. PROCEDURES", "4.1 TRAVEL RELATED EXPENSES")
    assert non_travel.heading_path == ("4. PROCEDURES", "4.1 NON-TRAVEL RELATED EXPENSES")
    assert travel.line_end < 105 and non_travel.line_end < 348  # children start new sections
    assert by_line[105].heading_path == (*travel.heading_path, "Airfare")
    assert by_line[348].heading_path == (
        *non_travel.heading_path,
        "Books (Audio/E-Books included)",
    )


def token_bounds(text: str, content: str, at: int) -> tuple[int, int, int]:
    """(start, end) token indices of content found in text from byte `at`, and its byte start."""
    raw = text.encode()
    offs = [0, *accumulate(len(ENC.decode_single_token_bytes(t)) for t in ENC.encode(text))]
    start = raw.index(content.encode(), at)
    return offs.index(start), offs.index(start + len(content.encode())), start


def test_over_max_section_splits_with_overlap_inside_section():
    """AC-7, AC-15: an over-max section splits at paragraphs, then sentences, then tokens; sub-
    chunks overlap by `overlap` tokens, all <= max, none crosses into the next section; a fence
    under max is never cut."""
    fence = "```\n" + "\n\n".join(f"code line {i} = {i};" for i in range(6)) + "\n```"
    sentences = " ".join(f"Sentence {WORDS[i % 10]} number {i} ends here." for i in range(40))
    section_a = f"# A\n\n{prose(30)}\n\n{fence}\n\n{sentences}\n\n{'x' * 400}\n\n"
    body = section_a + "## B\n\nshort b text\n"
    assert len(ENC.encode(fence)) < 60 < len(ENC.encode(sentences))
    chunks = structural(body, max_tokens=60, overlap=8, min_tokens=0)
    a = [c for c in chunks if c.heading == "A"]
    assert len(a) > 5 and all(c.heading_path == ("A",) for c in a)
    assert all(c.token_count <= 60 for c in chunks)
    assert all("## B" not in c.content for c in a)
    assert chunks[-1].content == "## B\n\nshort b text\n" and chunks[-1].heading_path == ("A", "B")
    assert any(fence in c.content for c in a)
    f0 = section_a.index(fence)
    at, prev_end = 0, None
    for c in a:
        start, end, at = token_bounds(section_a, c.content, at)
        assert not f0 < at + len(c.content) < f0 + len(fence)  # no window ends inside the fence
        if prev_end is not None:
            assert prev_end - start == 8
        prev_end = end
    assert end == len(ENC.encode(section_a))  # the last sub-chunk ends at the section's end
    assert "".join(c.content for c in a).count("Sentence") > 40  # sentences repeat in overlaps


def test_fence_over_max_is_cut():
    """AC-7: a fenced block that alone exceeds max_tokens is cut, every piece <= max."""
    body = "# A\n\n```\n" + prose(300) + "\n```\n"
    chunks = structural(body, max_tokens=60, overlap=8)
    assert len(chunks) > 1 and all(c.token_count <= 60 for c in chunks)


MERGE_BODY = """# P

parent text

## a

tiny a

## b

tiny b

### b1

tiny child

## c

tiny c

# Q

## d

tiny d
"""


def test_tiny_sections_merge_only_with_adjacent_siblings():
    """AC-8, AC-15: a tiny section takes its adjacent same-parent, same-level siblings and records
    each heading; never its parent's text, a child, or another parent's section."""
    chunks = structural(MERGE_BODY)
    assert [c.heading_path for c in chunks] == [
        ("P",),
        ("P", "a", "b"),
        ("P", "b", "b1"),
        ("P", "c"),  # b's child sits between b and c, so c is not adjacent to them
        ("Q",),
        ("Q", "d"),
    ]
    assert [c.heading for c in chunks] == ["P", "a", "b1", "c", "Q", "d"]
    assert "".join(c.content for c in chunks) == MERGE_BODY


def test_merge_stops_at_min_and_falls_back_to_preceding():
    """AC-8: absorbing stops once the group reaches min_tokens or would pass max; a last tiny
    sibling joins the preceding sibling group if it fits."""
    big = prose(80)
    body = f"# R\n\n## e\n\ntiny\n\n## f\n\n{big}\n\n## g\n\n{big}\n\n## h\n\ntiny h\n"
    chunks = structural(body, max_tokens=512, min_tokens=64)
    assert [c.heading_path for c in chunks] == [("R",), ("R", "e", "f"), ("R", "g", "h")]
    # f+g would pass max, so e takes f only; h has no following sibling and fits after g
    chunks = structural(body, max_tokens=150, min_tokens=64)
    assert [c.heading_path for c in chunks] == [("R",), ("R", "e", "f"), ("R", "g", "h")]
    # at max 100, f (116) splits and e stays alone; h joins nothing as g's span is over max
    chunks = structural(body, max_tokens=100, overlap=8, min_tokens=64)
    paths = [c.heading_path for c in chunks]
    assert paths[:2] == [("R",), ("R", "e")] and paths[-1] == ("R", "h")
    assert {("R", "f"), ("R", "g")} <= set(paths) and all(c.token_count <= 100 for c in chunks)
    assert all(c.token_count > 8 for c in chunks if c.heading_path in {("R", "f"), ("R", "g")})


def test_preamble_and_every_heading_level_are_boundaries():
    """AC-6, AC-15: text before the first heading has an empty path; headings at all six
    levels start sections; a whitespace-only preamble is dropped."""
    levels = "".join(f"{'#' * n} H{n}\n\nbody {n}\n\n" for n in range(1, 7))
    chunks = structural("intro text\n\n" + levels, min_tokens=0)
    assert chunks[0].heading_path == () and chunks[0].heading is None
    assert chunks[0].content == "intro text\n\n"
    assert [c.heading_path[-1] for c in chunks[1:]] == [f"H{n}" for n in range(1, 7)]
    assert chunks[6].heading_path == tuple(f"H{n}" for n in range(1, 7))
    assert [c.line_start for c in chunks] == [1, 3, 7, 11, 15, 19, 23]
    assert structural("\n\n# A\n\nx\n")[0].heading_path == ("A",)
    assert [h[1] for h in headings(levels)] == [1, 2, 3, 4, 5, 6]


def test_preamble_never_merges():
    """AC-6, AC-8: a tiny preamble stays its own chunk."""
    chunks = structural("hi\n\n# A\n\ntiny\n\n# B\n\ntiny\n")
    assert [c.heading_path for c in chunks] == [(), ("A", "B")]


def test_structural_ids_and_empty_body():
    """AC-9: ids are per doc, config and index; an empty body has no chunks."""
    a = structural(MERGE_BODY)
    assert [c.chunk_id for c in a] == [
        uuid.uuid5(uuid.NAMESPACE_URL, f"{DOC}:test:{i}") for i in range(len(a))
    ]
    assert structural(" \n\n") == []


def test_non_baseline_fixed_config_ids_differ():
    """AC-3: only the baseline keeps the spec 0003 id formula; another fixed config with the
    same size and overlap gets its own ids, so it can't take over the baseline's rows."""
    text = prose(1500)
    base = chunk_doc(DOC, text, ENC)
    other = chunk_doc(DOC, text, ENC, CHUNK_SIZE, CHUNK_OVERLAP, "fixed-512-64-b")
    assert base[0].chunk_id == uuid.uuid5(
        uuid.NAMESPACE_URL, f"{DOC}:{CHUNK_SIZE}:{CHUNK_OVERLAP}:0"
    )
    assert {c.chunk_id for c in base}.isdisjoint(c.chunk_id for c in other)
