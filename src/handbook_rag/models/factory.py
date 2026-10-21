"""Factory + registry: turn a `provider:model` string into an adapter.

The same string is the config value (EMBED_MODEL / ANSWER_MODEL), the chunk_embeddings.model
key and the trace field, so every layer names a model the same way. Adding a provider means
one adapter file plus one registry entry; the lookup below never changes.

Builders construct the SDK client here, not in the adapter, so adapters take an injected
client (dependency injection) and tests pass a fake one.
"""

import os
from collections.abc import Callable

from handbook_rag.constants import (
    DEEPINFRA_BASE_URL,
    DEFAULT_ANSWER_MODEL,
    DEFAULT_EMBED_MODEL,
    EMBED_MODELS,
)
from handbook_rag.models.answerers.openai import OpenAIAnswerer
from handbook_rag.models.base import Answerer, Embedder
from handbook_rag.models.embedders.openai import OpenAIEmbedder


def _openai_client(**kwargs):
    from openai import OpenAI  # imported lazily: only a real run needs the SDK client

    return OpenAI(**kwargs)


# embed.run owns retries (capped, logged); SDK retries would stack on top, so they are off.
# Builders take (model, dims, kind).
EMBEDDERS: dict[str, Callable[[str, int | None, str], Embedder]] = {
    "openai": lambda model, dims, kind: OpenAIEmbedder(
        _openai_client(max_retries=0), "openai", model, dims, kind
    ),
    "deepinfra": lambda model, dims, kind: OpenAIEmbedder(
        _openai_client(
            base_url=DEEPINFRA_BASE_URL, api_key=os.environ["DEEPINFRA_API_KEY"], max_retries=0
        ),
        "deepinfra",
        model,
        dims,
        kind,
    ),
}
ANSWERERS: dict[str, Callable[[str], Answerer]] = {
    "openai": lambda model: OpenAIAnswerer(_openai_client(), model),
}


def _split(spec: str) -> tuple[str, str]:
    provider, sep, model = spec.partition(":")
    if not sep or not provider or not model:
        raise ValueError(f"model spec must be 'provider:model', got {spec!r}")
    return provider, model


def _build(registry: dict, kind: str, spec: str):
    provider, model = _split(spec)
    if provider not in registry:
        known = ", ".join(sorted(registry))
        raise ValueError(f"unknown {kind} provider {provider!r} (registered: {known})")
    return registry[provider](model)


def resolve_embed_spec(spec: str | None = None) -> str:
    """The embedding model in use: the argument, then EMBED_MODEL, then the default."""
    return spec or os.environ.get("EMBED_MODEL") or DEFAULT_EMBED_MODEL


def parse_embed_spec(spec: str) -> tuple[str, str, int | None]:
    """'provider:model[@dims]' -> (provider, model, dims or None) (spec 0008, AC-1)."""
    provider, model = _split(spec)
    model, sep, dims = model.partition("@")
    if not sep:
        return provider, model, None
    if not model or not dims.isdigit():
        raise ValueError(f"model spec must be 'provider:model[@dims]', got {spec!r}")
    return provider, model, int(dims)


def embed_usd_per_1m(spec: str) -> float:
    """AC-5: the model's price; an unknown model raises rather than borrowing another's."""
    provider, model, _ = parse_embed_spec(spec)
    entry = EMBED_MODELS.get(f"{provider}:{model}")
    if entry is None:
        known = ", ".join(EMBED_MODELS)
        raise ValueError(f"no price for embedding model {spec!r} (known: {known})")
    return entry["usd_per_1m"]


def make_embedder(spec: str | None = None, kind: str = "document") -> Embedder:
    spec = resolve_embed_spec(spec)
    provider, model, dims = parse_embed_spec(spec)
    if kind not in ("document", "query"):
        raise ValueError(f"embedder kind must be 'document' or 'query', got {kind!r}")
    if provider not in EMBEDDERS:
        known = ", ".join(sorted(EMBEDDERS))
        raise ValueError(f"unknown embedding provider {provider!r} (registered: {known})")
    return EMBEDDERS[provider](model, dims, kind)


def make_answerer(spec: str | None = None) -> Answerer:
    return _build(
        ANSWERERS, "answer", spec or os.environ.get("ANSWER_MODEL") or DEFAULT_ANSWER_MODEL
    )
