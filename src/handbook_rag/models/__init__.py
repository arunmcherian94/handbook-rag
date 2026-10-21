"""Model ports, provider adapters and the factory that picks one (spec 0003, AC-10).

Pipeline code imports only from here: the ports (Embedder, Answerer, Completion) and the
factories. Adapters live in embedders/ and answerers/, one file per provider.
"""

from handbook_rag.models.base import Answerer, Completion, Embedder, InputTooLong
from handbook_rag.models.factory import (
    describe_embedder,
    embed_usd_per_1m,
    make_answerer,
    make_embedder,
    resolve_embed_spec,
)

__all__ = [
    "Answerer",
    "Completion",
    "Embedder",
    "InputTooLong",
    "describe_embedder",
    "embed_usd_per_1m",
    "make_answerer",
    "make_embedder",
    "resolve_embed_spec",
]
