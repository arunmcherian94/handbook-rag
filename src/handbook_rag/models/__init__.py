"""Model ports, provider adapters and the factory that picks one (spec 0003, AC-10).

Pipeline code imports only from here: the ports (Embedder, Answerer, Completion, Reranker) and
the factories. Adapters live in embedders/, answerers/ and rerankers/, one file per provider.
"""

from handbook_rag.models.base import (
    Answerer,
    ChatModel,
    ChatStep,
    Completion,
    Embedder,
    InputTooLong,
    Reranker,
    RerankResult,
    ToolCall,
)
from handbook_rag.models.factory import (
    answer_usd_per_1m,
    describe_embedder,
    describe_reranker,
    embed_usd_per_1m,
    make_answerer,
    make_chat_model,
    make_embedder,
    make_reranker,
    resolve_answer_spec,
    resolve_embed_spec,
)
from handbook_rag.models.rerankers.deepinfra import (
    FatalRerankError,
    RerankConnectionError,
    RerankHTTPError,
    RerankResponseError,
    RerankRetriesExhausted,
)

__all__ = [
    "Answerer",
    "ChatModel",
    "ChatStep",
    "Completion",
    "Embedder",
    "FatalRerankError",
    "InputTooLong",
    "RerankConnectionError",
    "RerankHTTPError",
    "RerankResponseError",
    "RerankResult",
    "RerankRetriesExhausted",
    "Reranker",
    "ToolCall",
    "answer_usd_per_1m",
    "describe_embedder",
    "describe_reranker",
    "embed_usd_per_1m",
    "make_answerer",
    "make_chat_model",
    "make_embedder",
    "make_reranker",
    "resolve_answer_spec",
    "resolve_embed_spec",
]
