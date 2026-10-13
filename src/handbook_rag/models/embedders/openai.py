"""OpenAI embeddings adapter: translates the SDK's response into the Embedder port."""

from handbook_rag.constants import EMBED_DIMS


class OpenAIEmbedder:
    def __init__(self, client, model: str):
        self.client = client  # injected, so tests pass a fake client
        self.model = model
        self.name = f"openai:{model}"
        self.dims = EMBED_DIMS.get(model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.embeddings.create(model=self.model, input=texts)
        # Each vector carries its input index; sort by it rather than trusting list order.
        vectors = [d.embedding for d in sorted(resp.data, key=lambda d: d.index)]
        if len(vectors) != len(texts):
            raise ValueError(f"{self.name}: sent {len(texts)} inputs, got {len(vectors)} vectors")
        # The vector column is untyped, so a wrong dimension must fail here, before insert.
        if self.dims and any(len(v) != self.dims for v in vectors):
            raise ValueError(f"{self.name}: expected {self.dims} dims")
        return vectors
