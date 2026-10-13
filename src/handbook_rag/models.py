"""Model ports and provider adapters (spec 0003, AC-10).

Pipeline code depends only on the Embedder / Answerer protocols. Adding a provider means one
adapter class plus one branch in the factory; models are chosen by `provider:model` strings.
"""

import os
from dataclasses import dataclass
from typing import Protocol

from handbook_rag.constants import (
    DEFAULT_ANSWER_MODEL,
    DEFAULT_EMBED_MODEL,
    EMBED_DIMS,
    MAX_COMPLETION_TOKENS,
    REASONING_EFFORT,
)


class Embedder(Protocol):
    name: str  # stored in chunk_embeddings.model

    def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int
    truncated: bool  # stopped at the output token cap


class Answerer(Protocol):
    name: str

    def answer(self, system: str, user: str) -> Completion: ...


class OpenAIEmbedder:
    def __init__(self, client, model: str):
        self.client = client
        self.model = model
        self.name = f"openai:{model}"
        self.dims = EMBED_DIMS.get(model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.embeddings.create(model=self.model, input=texts)
        vectors = [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]
        if len(vectors) != len(texts):
            raise ValueError(f"{self.name}: sent {len(texts)} inputs, got {len(vectors)} vectors")
        if self.dims and any(len(v) != self.dims for v in vectors):
            raise ValueError(f"{self.name}: expected {self.dims} dims")
        return vectors


class OpenAIAnswerer:
    def __init__(
        self,
        client,
        model: str,
        effort: str = REASONING_EFFORT,
        max_completion_tokens: int = MAX_COMPLETION_TOKENS,
    ):
        self.client = client
        self.model = model
        self.name = f"openai:{model}"
        self.effort = effort
        self.max_completion_tokens = max_completion_tokens

    def answer(self, system: str, user: str) -> Completion:
        # No `tools` are passed: the model cannot call any (AC-6).
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            reasoning_effort=self.effort,
            max_completion_tokens=self.max_completion_tokens,
        )
        choice = resp.choices[0]
        return Completion(
            text=choice.message.content or "",
            input_tokens=resp.usage.prompt_tokens,
            output_tokens=resp.usage.completion_tokens,
            truncated=choice.finish_reason == "length",
        )


def _split(spec: str) -> tuple[str, str]:
    provider, sep, model = spec.partition(":")
    if not sep or not provider or not model:
        raise ValueError(f"model spec must be 'provider:model', got {spec!r}")
    return provider, model


def _openai_client(**kwargs):
    from openai import OpenAI

    return OpenAI(**kwargs)


def make_embedder(spec: str | None = None) -> Embedder:
    provider, model = _split(spec or os.environ.get("EMBED_MODEL") or DEFAULT_EMBED_MODEL)
    if provider == "openai":
        # embed.run owns retries (capped, logged); SDK retries would stack on top.
        return OpenAIEmbedder(_openai_client(max_retries=0), model)
    raise ValueError(f"unknown embedding provider {provider!r}")


def make_answerer(spec: str | None = None) -> Answerer:
    provider, model = _split(spec or os.environ.get("ANSWER_MODEL") or DEFAULT_ANSWER_MODEL)
    if provider == "openai":
        return OpenAIAnswerer(_openai_client(), model)
    raise ValueError(f"unknown answer provider {provider!r}")
