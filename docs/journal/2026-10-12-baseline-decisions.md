# 2026-10-12: baseline decisions, spec 0003

- **Baseline chunking:** → [ADR-0003](../decisions/0003-baseline-chunking-512-64.md)
- **Embedding model and schema:** → [ADR-0004](../decisions/0004-embedding-model-and-schema.md)
- **Answer model and API:** → [ADR-0005](../decisions/0005-answer-model-and-api.md)
- **Grounding prompt and fixed abstentions:** → [ADR-0006](../decisions/0006-grounding-prompt-fixed-abstentions.md)
- **k=5:** recall@5 is the standard operating point. 5×512 ≈ 2.6k tokens of context. k is coupled to chunk size (k × size = context budget), and the eval can sweep k without re-embedding.
- Links:
  - [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
  - [text-embedding-3-small](https://developers.openai.com/api/docs/models/text-embedding-3-small)
  - [pgvector README](https://github.com/pgvector/pgvector)
  - [Open embedding models roundup (premai)](https://blog.premai.io/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting)
  - [Pinecone chunking strategies](https://www.pinecone.io/learn/chunking-strategies)

---

Prev: [2026-10-07: corpus and ingestion](2026-10-07-corpus-and-ingestion.md) · Next: [2026-10-13: baseline build, spec 0003](2026-10-13-baseline-build.md)
