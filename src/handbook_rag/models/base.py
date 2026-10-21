"""Ports: the interfaces pipeline code depends on (ports and adapters / Strategy).

chunk, embed and ask see only these types, never a provider SDK, so swapping a model or
provider changes no pipeline code. They are Protocols rather than ABCs: adapters and test
fakes satisfy them structurally, without inheriting from anything.
"""

from dataclasses import dataclass
from typing import Protocol


class Embedder(Protocol):
    name: str  # "provider:model[@dims]"; stored in chunk_embeddings.model (spec 0008, AC-1)
    kind: str  # "document" (embed) or "query" (eval retrieval); changes only what is sent (AC-3)
    max_input_tokens: int  # effective cl100k limit per input, already halved where AC-4 says so

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class InputTooLong(ValueError):
    """An input over the model's limit, raised before any call (spec 0008, AC-4); index is its
    position in the batch, so the caller can name the chunk or query."""

    def __init__(self, index: int, message: str):
        super().__init__(message)
        self.index = index


@dataclass(frozen=True)
class Completion:
    """Provider-neutral answer result, so traces look the same for every provider."""

    text: str
    input_tokens: int
    output_tokens: int
    truncated: bool  # stopped at the output token cap


class Answerer(Protocol):
    name: str  # "provider:model"

    def answer(self, system: str, user: str) -> Completion: ...
