"""OpenAI-compatible embeddings adapter (OpenAI and DeepInfra): SDK response -> Embedder port."""

import tiktoken

from handbook_rag.constants import EMBED_MODELS, TOKENIZER
from handbook_rag.models.base import InputTooLong


class OpenAIEmbedder:
    def __init__(
        self, client, provider: str, model: str, dims: int | None = None, kind: str = "document"
    ):
        entry = EMBED_MODELS.get(f"{provider}:{model}")
        if entry is None:
            known = ", ".join(EMBED_MODELS)
            raise ValueError(f"unknown embedding model {provider}:{model} (known: {known})")
        native, lowest = entry["native_dims"], entry["min_dims"]
        # Checked before any call: a bad size would otherwise cost a request (or a wrong column).
        if dims is not None and (lowest is None or not lowest <= dims <= native):
            allowed = f"{lowest} to {native}" if lowest is not None else "fixed"
            raise ValueError(f"{provider}:{model}@{dims}: dims must be {allowed}")
        self.client = client  # injected, so tests pass a fake client
        self.model = model
        self.requested_dims = dims
        self.kind = kind
        self.query_template = entry["query_template"]
        self.dims = dims or native
        self.name = f"{provider}:{model}" + (f"@{dims}" if dims else "")
        # cl100k only approximates a non-OpenAI tokenizer, so those models get half the limit.
        limit = entry["max_input_tokens"]
        self.max_input_tokens = limit if entry["exact_tokenizer"] else limit // 2
        self._enc = tiktoken.get_encoding(TOKENIZER)

    def prepare(self, texts: list[str]) -> list[str]:
        """The texts as sent (AC-3), each checked against the limit (AC-4). No API call, so dry
        runs use it too."""
        query = self.kind == "query"
        sent = [
            self.query_template.format(q=t) if query and self.query_template else t for t in texts
        ]
        for i, text in enumerate(sent):
            n = len(self._enc.encode(text, disallowed_special=()))
            if n > self.max_input_tokens:
                what = f"query {texts[i][:80]!r}" if query else f"input {i} of the batch"
                raise InputTooLong(
                    i, f"{self.name}: {what} is {n} tokens, over the {self.max_input_tokens} limit"
                )
        return sent

    def embed(self, texts: list[str]) -> list[list[float]]:
        sent = self.prepare(texts)
        request = {"model": self.model, "input": sent}
        if self.requested_dims:
            request["dimensions"] = self.requested_dims
        resp = self.client.embeddings.create(**request)
        # Each vector carries its input index; sort by it rather than trusting list order.
        vectors = [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]
        if len(vectors) != len(texts):
            raise ValueError(f"{self.name}: sent {len(texts)} inputs, got {len(vectors)} vectors")
        # The vector column is untyped, so a wrong dimension must fail here, before insert.
        if any(len(v) != self.dims for v in vectors):
            raise ValueError(f"{self.name}: expected {self.dims} dims")
        return vectors
