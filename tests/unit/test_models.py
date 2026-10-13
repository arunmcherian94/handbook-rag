"""AC-10: adapter request/response contracts and the provider:model factory (fake client)."""

import pytest
from fakes import FakeEmbedder, FakeOpenAIClient

from handbook_rag.models import make_answerer, make_embedder
from handbook_rag.models.answerers.openai import OpenAIAnswerer
from handbook_rag.models.embedders.openai import OpenAIEmbedder
from handbook_rag.models.factory import EMBEDDERS


def test_embedder_request_shape_and_index_order():
    client = FakeOpenAIClient(dims=1536)
    emb = OpenAIEmbedder(client, "text-embedding-3-small")
    vectors = emb.embed(["a", "b", "c"])
    kind, req = client.requests[0]
    assert kind == "embeddings"
    assert req == {"model": "text-embedding-3-small", "input": ["a", "b", "c"]}
    # The fake returns data in reverse; the adapter must re-sort by index.
    assert [v[0] for v in vectors] == [0.0, 1.0, 2.0]
    assert emb.name == "openai:text-embedding-3-small"


def test_embedder_rejects_wrong_dims():
    emb = OpenAIEmbedder(FakeOpenAIClient(dims=8), "text-embedding-3-small")
    with pytest.raises(ValueError, match="1536"):
        emb.embed(["a"])


def test_answerer_request_shape_no_tools():
    client = FakeOpenAIClient(answer="Yes [1].")
    out = OpenAIAnswerer(client, "gpt-5.4-mini").answer("SYS", "USER")
    kind, req = client.requests[0]
    assert kind == "chat"
    assert req["model"] == "gpt-5.4-mini"
    assert req["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user", "content": "USER"},
    ]
    assert req["reasoning_effort"] == "none"
    assert req["max_completion_tokens"] == 1024
    assert "tools" not in req
    assert (out.text, out.input_tokens, out.output_tokens, out.truncated) == (
        "Yes [1].",
        50,
        10,
        False,
    )


def test_answerer_flags_truncation():
    out = OpenAIAnswerer(FakeOpenAIClient(finish_reason="length"), "gpt-5.4-mini").answer("s", "u")
    assert out.truncated


def test_factory_defaults_and_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-not-real")  # client construction only; no call
    monkeypatch.delenv("EMBED_MODEL", raising=False)
    monkeypatch.setenv("ANSWER_MODEL", "openai:gpt-5.4-nano")
    assert make_embedder().name == "openai:text-embedding-3-small"
    assert make_answerer().name == "openai:gpt-5.4-nano"
    assert make_embedder().client.max_retries == 0


@pytest.mark.parametrize("spec", ["text-embedding-3-small", "openai:", ":model"])
def test_factory_rejects_malformed_spec(spec):
    with pytest.raises(ValueError, match="provider:model"):
        make_embedder(spec)


def test_factory_rejects_unknown_provider():
    with pytest.raises(ValueError, match="unknown embedding provider 'voyage'"):
        make_embedder("voyage:voyage-3")
    with pytest.raises(ValueError, match="unknown answer provider 'acme'"):
        make_answerer("acme:x")


def test_registry_adds_provider_without_factory_change(monkeypatch):
    """AC-10: a new provider is one registry entry; the error names what is registered."""
    with pytest.raises(ValueError, match=r"\(registered: openai\)"):
        make_embedder("local:minilm")
    monkeypatch.setitem(EMBEDDERS, "local", lambda model: FakeEmbedder(name=f"local:{model}"))
    assert make_embedder("local:minilm").name == "local:minilm"
