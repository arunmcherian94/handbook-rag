"""ChatModel adapter, factory and price lookup (spec 0013, AC-1, AC-16). No network."""

import pytest
from fakes import FakeOpenAIClient

from handbook_rag.constants import MAX_COMPLETION_TOKENS, REASONING_EFFORT
from handbook_rag.models import answer_usd_per_1m, make_chat_model
from handbook_rag.models.chat.openai import OpenAIChatModel
from handbook_rag.models.factory import CHAT_MODELS

MESSAGES = [{"role": "user", "content": "hi"}]
TOOLS = [{"type": "function", "function": {"name": "retrieve", "strict": True}}]


def _sent(client):
    assert len(client.requests) == 1
    return client.requests[0][1]


@pytest.mark.parametrize("choice", ["auto", "none"])
def test_request_shape(choice):
    """AC-1: exact request kwargs; tools pass through; no timeout unless given."""
    client = FakeOpenAIClient()
    OpenAIChatModel(client, "m").complete(MESSAGES, TOOLS, choice)
    assert _sent(client) == {
        "model": "m",
        "messages": MESSAGES,
        "tools": TOOLS,
        "tool_choice": choice,
        "parallel_tool_calls": False,
        "reasoning_effort": REASONING_EFFORT,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
    }


def test_request_effort_cap_and_timeout():
    """AC-1: effort and cap are configurable; timeout is sent only when given."""
    client = FakeOpenAIClient()
    model = OpenAIChatModel(client, "m", effort="low", max_completion_tokens=7)
    model.complete(MESSAGES, TOOLS, "auto", timeout=12.5)
    sent = _sent(client)
    assert (sent["reasoning_effort"], sent["max_completion_tokens"], sent["timeout"]) == (
        "low",
        7,
        12.5,
    )


def test_tool_calls_mapped_with_raw_arguments():
    """AC-1: ids, names and argument strings are kept; invalid JSON is not parsed or rejected."""
    calls = [("c1", "retrieve", '{"query": "x", "page": 1}'), ("c2", "retrieve", "{not json")]
    step = OpenAIChatModel(FakeOpenAIClient(tool_calls=calls, answer=None), "m").complete(
        MESSAGES, TOOLS, "auto"
    )
    assert [(c.id, c.name, c.arguments) for c in step.tool_calls] == calls
    assert step.text == ""


def test_no_tool_calls_is_empty_tuple():
    """AC-1: message.tool_calls None maps to ()."""
    step = OpenAIChatModel(FakeOpenAIClient(answer="done"), "m").complete(MESSAGES, TOOLS, "auto")
    assert step.tool_calls == ()
    assert (step.text, step.finish_reason, step.truncated) == ("done", "stop", False)


def test_usage_and_truncation_mapped():
    """AC-1: token counts map; finish_reason 'length' reads as truncated."""
    step = OpenAIChatModel(FakeOpenAIClient(finish_reason="length"), "m").complete(
        MESSAGES, TOOLS, "auto"
    )
    assert (step.input_tokens, step.output_tokens) == (50, 10)
    assert step.truncated


def test_factory_builds_named_adapter(monkeypatch):
    """AC-1: make_chat_model builds an OpenAIChatModel from the spec."""
    fake = FakeOpenAIClient()
    monkeypatch.setattr("handbook_rag.models.factory._openai_client", lambda **kw: fake)
    model = make_chat_model("openai:x")
    assert isinstance(model, OpenAIChatModel)
    assert model.name == "openai:x"
    assert model.client is fake
    assert "openai" in CHAT_MODELS


def test_factory_uses_answer_spec_env(monkeypatch):
    """AC-1: the spec resolves as for the answerer (ANSWER_MODEL)."""
    monkeypatch.setattr(
        "handbook_rag.models.factory._openai_client", lambda **kw: FakeOpenAIClient()
    )
    monkeypatch.setenv("ANSWER_MODEL", "openai:y")
    assert make_chat_model().name == "openai:y"


def test_factory_rejects_unknown_provider():
    """AC-1: an unknown provider raises, naming the registered ones."""
    with pytest.raises(ValueError, match=r"unknown chat provider 'acme' \(registered: openai\)"):
        make_chat_model("acme:x")


def test_answer_price_known():
    """AC-16: (input, output) USD per 1M tokens from ANSWER_MODELS."""
    assert answer_usd_per_1m("openai:gpt-5.4-mini") == (0.75, 4.50)


def test_answer_price_unknown_raises():
    """AC-16: an unknown model raises and names the known ones."""
    with pytest.raises(ValueError, match="openai:gpt-5.4-mini"):
        answer_usd_per_1m("openai:nope")
