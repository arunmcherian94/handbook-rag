"""AC-10: adapter request/response contracts and the provider:model factory (fake client)."""

import pytest
from fakes import FakeEmbedder, FakeOpenAIClient

from handbook_rag.models import make_answerer, make_embedder
from handbook_rag.models.answerers.openai import OpenAIAnswerer
from handbook_rag.models.embedders.openai import OpenAIEmbedder
from handbook_rag.models.factory import EMBEDDERS, embed_usd_per_1m


def test_embedder_request_shape_and_index_order():
    client = FakeOpenAIClient(dims=1536)
    emb = OpenAIEmbedder(client, "openai", "text-embedding-3-small")
    vectors = emb.embed(["a", "b", "c"])
    kind, req = client.requests[0]
    assert kind == "embeddings"
    assert req == {"model": "text-embedding-3-small", "input": ["a", "b", "c"]}
    # The fake returns data in reverse; the adapter must re-sort by index.
    assert [v[0] for v in vectors] == [0.0, 1.0, 2.0]
    assert emb.name == "openai:text-embedding-3-small"


def test_embedder_rejects_wrong_dims():
    emb = OpenAIEmbedder(FakeOpenAIClient(dims=8), "openai", "text-embedding-3-small")
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
    with pytest.raises(ValueError, match=r"\(registered: deepinfra, openai\)"):
        make_embedder("local:minilm")
    monkeypatch.setitem(
        EMBEDDERS, "local", lambda model, dims, kind: FakeEmbedder(name=f"local:{model}", kind=kind)
    )
    assert make_embedder("local:minilm").name == "local:minilm"


SMALL = "text-embedding-3-small"
LARGE = "text-embedding-3-large"
QWEN = "Qwen/Qwen3-Embedding-8B"


def test_embedder_name_with_and_without_dims():
    """AC-1: the name is the full spec incl. @dims; dims default to the model's native size."""
    assert OpenAIEmbedder(FakeOpenAIClient(), "openai", SMALL).name == f"openai:{SMALL}"
    big = OpenAIEmbedder(FakeOpenAIClient(), "openai", LARGE, 1536)
    assert (big.name, big.dims) == (f"openai:{LARGE}@1536", 1536)
    assert OpenAIEmbedder(FakeOpenAIClient(), "openai", LARGE).dims == 3072


@pytest.mark.parametrize(
    ("model", "dims"), [(LARGE, 4000), (SMALL, 0), (SMALL, 2000), ("nope", None), ("nope", 8)]
)
def test_embedder_rejects_bad_dims_or_model_before_any_call(model, dims):
    """AC-1: out-of-range @dims and unknown models fail at construction, zero requests."""
    client = FakeOpenAIClient()
    with pytest.raises(ValueError):
        OpenAIEmbedder(client, "openai", model, dims)
    assert client.requests == []


def test_dimensions_sent_only_when_requested():
    """AC-1: @dims adds `dimensions`; the default request stays exactly model + input."""
    client = FakeOpenAIClient(dims=1536)
    OpenAIEmbedder(client, "openai", LARGE, 1536).embed(["a"])
    assert client.requests[0][1] == {"model": LARGE, "input": ["a"], "dimensions": 1536}
    client = FakeOpenAIClient(dims=1536)
    OpenAIEmbedder(client, "openai", SMALL).embed(["a"])
    assert set(client.requests[0][1]) == {"model", "input"}


def test_embedder_rejects_wrong_dims_for_requested_size():
    """AC-1: the response is checked against the size in use, not the native size."""
    emb = OpenAIEmbedder(FakeOpenAIClient(dims=3072), "openai", LARGE, 1536)
    with pytest.raises(ValueError, match="1536"):
        emb.embed(["a"])


def test_qwen_query_template_and_documents_as_is():
    """AC-3: query mode sends the exact instruction string; document mode sends text as-is."""
    expected = (
        "Instruct: Given a question about the GitLab handbook, retrieve the passages "
        "that answer it\nQuery:what is X"
    )
    client = FakeOpenAIClient(dims=4096)
    OpenAIEmbedder(client, "deepinfra", QWEN, None, "query").embed(["what is X"])
    assert client.requests[0][1] == {"model": QWEN, "input": [expected]}
    client = FakeOpenAIClient(dims=4096)
    OpenAIEmbedder(client, "deepinfra", QWEN, None, "document").embed(["what is X"])
    assert client.requests[0][1]["input"] == ["what is X"]


def test_query_mode_without_template_sends_text_unchanged():
    """AC-3: models without a template are unaffected by kind."""
    client = FakeOpenAIClient(dims=3072)
    OpenAIEmbedder(client, "openai", LARGE, None, "query").embed(["what is X"])
    assert client.requests[0][1]["input"] == ["what is X"]


def test_max_input_tokens_halved_for_non_openai_tokenizer():
    """AC-4: exact tokenizer uses the provider limit; otherwise half of it."""
    assert OpenAIEmbedder(FakeOpenAIClient(), "deepinfra", QWEN).max_input_tokens == 16384
    assert OpenAIEmbedder(FakeOpenAIClient(), "openai", SMALL).max_input_tokens == 8192


def test_over_length_inputs_raise_before_any_request():
    """AC-4: an over-limit query or document fails naming the input; nothing is truncated."""
    long = "word " * 9000
    client = FakeOpenAIClient()
    with pytest.raises(ValueError, match=r"query 'word word"):
        OpenAIEmbedder(client, "openai", SMALL, None, "query").embed([long])
    with pytest.raises(ValueError, match="input 1 of the batch"):
        OpenAIEmbedder(client, "openai", SMALL).embed(["ok", long])
    assert client.requests == []


def test_embed_usd_per_1m():
    """AC-5: price by model ignoring @dims; an unknown model raises."""
    assert embed_usd_per_1m(f"openai:{LARGE}@1536") == 0.13
    with pytest.raises(ValueError, match="no price"):
        embed_usd_per_1m("openai:nope")


def test_factory_rejects_bad_kind():
    """AC-3: kind is document or query."""
    with pytest.raises(ValueError, match="kind"):
        make_embedder(f"openai:{SMALL}", kind="other")


def test_factory_builds_deepinfra_embedder(monkeypatch):
    """AC-2: deepinfra builds through the registry with its base_url and key (no call)."""
    monkeypatch.setenv("DEEPINFRA_API_KEY", "di-test-not-real")
    emb = make_embedder(f"deepinfra:{QWEN}@1024", kind="query")
    assert (emb.name, emb.kind, emb.dims) == (f"deepinfra:{QWEN}@1024", "query", 1024)
    assert str(emb.client.base_url).startswith("https://api.deepinfra.com/v1/openai")
    assert emb.client.max_retries == 0
