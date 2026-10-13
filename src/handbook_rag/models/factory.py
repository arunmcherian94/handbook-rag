"""Factory + registry: turn a `provider:model` string into an adapter.

The same string is the config value (EMBED_MODEL / ANSWER_MODEL), the chunk_embeddings.model
key and the trace field, so every layer names a model the same way. Adding a provider means
one adapter file plus one registry entry; the lookup below never changes.

Builders construct the SDK client here, not in the adapter, so adapters take an injected
client (dependency injection) and tests pass a fake one.
"""

import os
from collections.abc import Callable

from handbook_rag.constants import DEFAULT_ANSWER_MODEL, DEFAULT_EMBED_MODEL
from handbook_rag.models.answerers.openai import OpenAIAnswerer
from handbook_rag.models.base import Answerer, Embedder
from handbook_rag.models.embedders.openai import OpenAIEmbedder


def _openai_client(**kwargs):
    from openai import OpenAI  # imported lazily: only a real run needs the SDK client

    return OpenAI(**kwargs)


# embed.run owns retries (capped, logged); SDK retries would stack on top, so they are off.
EMBEDDERS: dict[str, Callable[[str], Embedder]] = {
    "openai": lambda model: OpenAIEmbedder(_openai_client(max_retries=0), model),
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


def make_embedder(spec: str | None = None) -> Embedder:
    return _build(
        EMBEDDERS, "embedding", spec or os.environ.get("EMBED_MODEL") or DEFAULT_EMBED_MODEL
    )


def make_answerer(spec: str | None = None) -> Answerer:
    return _build(
        ANSWERERS, "answer", spec or os.environ.get("ANSWER_MODEL") or DEFAULT_ANSWER_MODEL
    )
