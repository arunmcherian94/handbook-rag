"""Model ports, provider adapters and the factory that picks one (spec 0003, AC-10).

Pipeline code imports only from here: the ports (Embedder, Answerer, Completion, Reranker) and
the factories. Adapters live in embedders/, answerers/ and rerankers/, one file per provider.
"""

from handbook_rag.models.base import (
    Answerer,
    Completion,
    Embedder,
    InputTooLong,
    Reranker,
    RerankResult,
)
from handbook_rag.models.factory import (
    describe_embedder,
    embed_usd_per_1m,
    make_answerer,
    make_embedder,
    resolve_answer_spec,
    resolve_embed_spec,
)

__all__ = [
    "Answerer",
    "Completion",
    "Embedder",
    "InputTooLong",
    "RerankResult",
    "Reranker",
    "describe_embedder",
    "embed_usd_per_1m",
    "make_answerer",
    "make_embedder",
    "resolve_answer_spec",
    "resolve_embed_spec",
]
