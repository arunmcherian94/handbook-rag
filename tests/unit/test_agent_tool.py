"""retrieve tool: schema, validation, paging, numbering (spec 0013, AC-2 to AC-5)."""

import json
import uuid

import pytest
from fakes import FakeEmbedder, make_principal

from handbook_rag.agent.tool import EMPTY_PAGE, TOOL, TOOL_NAME, TurnTool
from handbook_rag.ask import Retrieved, build_prompt
from handbook_rag.constants import AGENT_MAX_QUERY_TOKENS, TOP_K
from handbook_rag.models import ToolCall

PRINCIPAL = make_principal("staff")


def chunk(i: int) -> Retrieved:
    return Retrieved(
        i, uuid.UUID(int=i), uuid.UUID(int=1000 + i), f"/handbook/p{i}/", f"H{i}", f"text {i}",
        0.1 * i, 512, 64, "cl100k_base", "sha",
    )  # fmt: skip


class FakeRetrieve:
    def __init__(self, total=20):
        self.pool = [chunk(i) for i in range(1, total + 1)]
        self.calls: list[tuple] = []

    def __call__(self, conn, embedder, query, principal, k, config_id):
        self.calls.append((conn, embedder, query, principal, k, config_id))
        return self.pool[:k]


def call(query="q", page=1, **extra) -> ToolCall:
    return ToolCall("c1", TOOL_NAME, json.dumps({"query": query, "page": page, **extra}))


def make(total=20):
    fake = FakeRetrieve(total)
    ticks = iter(range(100))
    tool = TurnTool(
        "conn", FakeEmbedder(), PRINCIPAL, "cfg", fake, clock=lambda: next(ticks) / 1000
    )
    return tool, fake


def test_schema_shape():
    """AC-2: strict schema with query and page only, no principal field (AC-5)."""
    fn = TOOL["function"]
    assert TOOL["type"] == "function" and fn["name"] == "retrieve" and fn["strict"] is True
    p = fn["parameters"]
    assert set(p["properties"]) == {"query", "page"} == set(p["required"])
    assert p["additionalProperties"] is False
    assert p["properties"]["query"]["type"] == "string"
    assert p["properties"]["page"] == {**p["properties"]["page"], "type": "integer",
                                       "minimum": 1, "maximum": 4}  # fmt: skip


def test_description_content():
    """AC-2: the description carries the paging and rewording guidance and an example."""
    d = TOOL["function"]["description"]
    phrases = [
        "GitLab handbook",
        f"{TOP_K} numbered excerpts per page",
        "page 1",
        "next page",
        "reword",
        "one search per part",
        "expense report approval by manager",
    ]
    for phrase in phrases:
        assert phrase in d


def test_paging_slices():
    """AC-2: page 2 is ranks 6-10 and asks the retriever for k=10."""
    tool, fake = make()
    r = tool.execute(call(page=2))
    assert r.accepted and fake.calls[0][4] == 2 * TOP_K
    assert r.numbers == (1, 2, 3, 4, 5)
    assert r.chunk_ids == tuple(str(uuid.UUID(int=i)) for i in range(6, 11))
    assert "p6/" in r.content and "p5/" not in r.content
    assert fake.calls[0][5] == "cfg"


@pytest.mark.parametrize(
    ("arguments", "name", "fragment"),
    [
        ("{}", "search", "unknown tool"),
        ("not json", "retrieve", "valid JSON"),
        ("[1]", "retrieve", "JSON object"),
        ('{"query": "q", "page": 1, "user_id": "x"}', "retrieve", "user_id"),
        ('{"query": "q"}', "retrieve", "missing argument(s): page"),
        ('{"page": 1}', "retrieve", "missing argument(s): query"),
        ('{"query": 3, "page": 1}', "retrieve", "query must be a string"),
        ('{"query": "q", "page": "1"}', "retrieve", "page must be an integer"),
        ('{"query": "q", "page": true}', "retrieve", "page must be an integer"),
        ('{"query": "q", "page": 1.5}', "retrieve", "page must be an integer"),
        ('{"query": "q", "page": 0}', "retrieve", "from 1 to 4"),
        ('{"query": "q", "page": 5}', "retrieve", "from 1 to 4"),
        ('{"query": "  ", "page": 1}', "retrieve", "query is empty"),
    ],
)
def test_rejections(arguments, name, fragment):
    """AC-2: a malformed call is rejected with a next step, before any retrieval."""
    tool, fake = make()
    r = tool.execute(ToolCall("c1", name, arguments))
    assert not r.accepted and fragment in r.error
    assert r.content == f"Error: {r.error}"
    assert r.numbers == () and r.chunk_ids == ()
    assert fake.calls == [] and tool.excerpts == []


def test_query_too_long_rejected():
    """AC-2: a query over the token limit is rejected."""
    tool, fake = make()
    r = tool.execute(call(query="word " * (AGENT_MAX_QUERY_TOKENS + 1)))
    assert not r.accepted and "tokens" in r.error and fake.calls == []
    assert tool.execute(call(query="word " * AGENT_MAX_QUERY_TOKENS)).accepted


@pytest.mark.parametrize("key", ["user_id", "groups", "as"])
def test_extra_principal_args_rejected(key):
    """AC-5: no argument can name a user or group; the key is named in the error."""
    tool, fake = make()
    r = tool.execute(call(**{key: "admin"}))
    assert not r.accepted and key in r.error and fake.calls == []


def test_same_principal_every_call():
    """AC-5: every executed call gets the identical bound Principal."""
    tool, fake = make()
    tool.execute(call("a"))
    tool.execute(call("b", 2))
    tool.execute(call("c", 3))
    assert len(fake.calls) == 3
    assert all(c[3] is PRINCIPAL for c in fake.calls)


def test_numbering_across_calls():
    """AC-4: numbers are per turn, first-return order; a repeated chunk keeps its number."""
    tool, fake = make()
    first = tool.execute(call("a", 1))
    assert first.numbers == (1, 2, 3, 4, 5)
    second = tool.execute(call("b", 2))  # ranks 6-10, new chunks
    assert second.numbers == (6, 7, 8, 9, 10)
    fake.pool = [fake.pool[7], fake.pool[0]] + fake.pool[10:]  # chunk 8 then chunk 1, then new
    third = tool.execute(call("c", 1))
    assert third.numbers == (9 - 1, 1, 11, 12, 13)
    assert third.content.startswith("[8] /handbook/p8/")
    assert [e.n for e in tool.excerpts] == list(range(1, 14))
    assert tool.excerpts[7].chunk_id == uuid.UUID(int=8)


def test_repeat_rejected_only_after_accept():
    """AC-2: an identical (stripped query, page) is refused once accepted; rejected calls and
    other pages or queries are not."""
    tool, fake = make()
    tool.execute(call("q", 5))  # rejected, not registered
    assert tool.execute(call(" q ", 1)).accepted
    r = tool.execute(call("q", 1))
    assert not r.accepted and "already shown" in r.error and "reword" in r.error
    assert len(fake.calls) == 1
    assert tool.execute(call("q", 2)).accepted and tool.execute(call("other", 1)).accepted


def test_empty_page():
    """AC-2/AC-3: nothing on the page gives EMPTY_PAGE, accepted."""
    tool, _ = make(total=3)
    r = tool.execute(call(page=2))
    assert r.accepted and r.content == EMPTY_PAGE == "No excerpts found."
    assert r.numbers == () and tool.excerpts == []


def test_latency_from_clock():
    """AC-2: latency comes from the injected clock (ticks of 1 ms)."""
    tool, _ = make()
    assert tool.execute(call()).latency_ms == pytest.approx(1.0)


def test_format_matches_build_prompt():
    """AC-2: excerpts are formatted exactly as ask.build_prompt formats its block."""
    tool, fake = make()
    r = tool.execute(call())
    _, user = build_prompt("Q", tool.excerpts)
    assert user == f"Handbook excerpts:\n\n{r.content}\n\nQuestion: Q"


def test_retry_sleep_respects_time_left(monkeypatch):
    """AC-8 (review fix): with time_left, the retriever gets a sleep that raises ToolTimeout
    rather than wait past the turn's time; a short wait still sleeps."""
    from handbook_rag.agent import tool as tool_mod
    from handbook_rag.agent.tool import ToolTimeout

    slept: list[float] = []
    monkeypatch.setattr(tool_mod.time, "sleep", slept.append)
    seen = {}

    def retrieve(conn, embedder, query, principal, k, config_id, sleep=None):
        seen["sleep"] = sleep
        return []

    t = TurnTool(None, None, make_principal("staff"), retrieve=retrieve, clock=lambda: 0.0)
    t.execute(ToolCall("c1", "retrieve", '{"query": "q", "page": 1}'), time_left=5.0)
    seen["sleep"](1.0)
    assert slept == [1.0]
    with pytest.raises(ToolTimeout):
        seen["sleep"](5.0)
    t.execute(ToolCall("c2", "retrieve", '{"query": "q2", "page": 1}'))
    assert seen["sleep"] is None  # no time_left: the retriever's own default
