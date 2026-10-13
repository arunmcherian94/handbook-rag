"""Ports: the interfaces pipeline code depends on (ports and adapters / Strategy).

chunk, embed and ask see only these types, never a provider SDK, so swapping a model or
provider changes no pipeline code. They are Protocols rather than ABCs: adapters and test
fakes satisfy them structurally, without inheriting from anything.
"""

from dataclasses import dataclass
from typing import Protocol


class Embedder(Protocol):
    name: str  # "provider:model"; stored in chunk_embeddings.model

    def embed(self, texts: list[str]) -> list[list[float]]: ...


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
