# 0004. text-embedding-3-small; embeddings keyed (chunk_id, model)

- **Status:** accepted
- **Date:** 2026-10-12
- **Journal:** [2026-10-12 baseline decisions](../journal/2026-10-12-baseline-decisions.md)

## Context
Embedding options considered:
- OpenAI 3-small ($0.02/1M, 1536d) vs 3-large ($0.13, 3072d, which needs `dimensions` to fit the 2,000-dim HNSW limit).
- Voyage-4, Gemini, Cohere v4.
- Open models: Qwen3-Embedding, BGE-M3, nomic, EmbeddingGemma.

Local models on this machine (M2, 8 GB, shared with Colima): a 0.3–0.6B embedder takes an estimated 1–3 h for the corpus. Answer models that fit (3–4B) are weak at grounding and abstention.

## Decision
- Chose 3-small: cheapest, its tokenizer is exactly cl100k, and it's the standard reference point. About $0.21 for the corpus, about 11–15 min at Tier 1 (1M TPM), but about 4.5 h on the free tier (40k TPM).
- Embeddings go in their own table (`chunk_id`, `model`) with an untyped `vector` column, so models of different dimensions coexist for week 2 comparisons. pgvector indexes one model later with an expression index plus a partial index (README FAQ).
- **No `dims` column on `chunk_embeddings`:** `vector_dims(embedding)` derives it, so a stored copy could only drift. The adapter checks each vector's length against the model's known dims before insert. Retrieval filters to one model, and `<=>` raises on mismatched dims anyway.

## Consequences
Open embedders become a measured week 2 comparison, not a guess.

Links:
- [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
- [text-embedding-3-small](https://developers.openai.com/api/docs/models/text-embedding-3-small)
- [pgvector README](https://github.com/pgvector/pgvector)
- [Open embedding models roundup (premai)](https://blog.premai.io/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting)
