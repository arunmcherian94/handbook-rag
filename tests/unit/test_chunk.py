import math
import uuid

import pytest
import tiktoken

from handbook_rag.chunk import chunk_doc, find_headings
from handbook_rag.constants import CHUNK_OVERLAP, CHUNK_SIZE

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
