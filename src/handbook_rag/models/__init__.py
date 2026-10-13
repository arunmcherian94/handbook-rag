"""Model ports, provider adapters and the factory that picks one (spec 0003, AC-10).

Pipeline code imports only from here: the ports (Embedder, Answerer, Completion) and the
factories. Adapters live in embedders/ and answerers/, one file per provider.
"""

from handbook_rag.models.base import Answerer, Completion, Embedder
from handbook_rag.models.factory import make_answerer, make_embedder

__all__ = ["Answerer", "Completion", "Embedder", "make_answerer", "make_embedder"]
