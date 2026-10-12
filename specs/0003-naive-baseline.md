# 0003: Naive RAG baseline

- Status: approved
- Date: 2026-10-12
- Depends on: 0002

## Problem

There is no end-to-end path from a question to a cited answer yet. Week 2 (chunking experiments) and week 3 (hybrid search) need a fixed, simple, reproducible baseline to measure against. It must be honest, not good: every choice is the plain default, so later gains are attributable to the change that produced them.

## Acceptance criteria

- AC-1: **Chunking.** `make chunk` splits every ingested document into fixed-size cl100k token windows (512 tokens, 64 overlap) and stores them in a `chunks` table:
  - `chunk_id`: deterministic, `uuid5(doc_id:chunk_size:chunk_overlap:chunk_index)`.
  - `doc_id` (FK to `documents`), `chunk_index`, `content`, `token_count`.
  - `heading`: text of the nearest preceding markdown heading, ignoring `#` lines inside code fences. It's for citation only and is **not** used to split.
  - `chunk_size`, `chunk_overlap`, `tokenizer`: the parameters used.
  - A document shorter than one window becomes one chunk. An empty document produces none.
- AC-2: **Idempotent.** Re-running chunking on the same corpus SHA and parameters produces identical `chunk_id`s and content. Chunks of documents no longer in `documents` are removed, together with their embeddings. Everything happens in one transaction, like ingestion, and only after `corpus.verify()` passes.
- AC-3: **Embedding.** `make embed` gives each chunk one embedding per model in a `chunk_embeddings` table (`chunk_id`, `model`, `embedding vector`), with the model name recorded. Requests are batched, and rate limits are retried with exponential backoff.
- AC-4: **Resumable.** If an embedding run dies midway, re-running embeds only chunks that have no embedding for that model. No chunk is ever paid for twice. Each batch is committed as it completes.
- AC-5: **Retrieval.** `retrieve(question, k)` embeds the question with the same model and returns the top-k chunks for that model by **exact** cosine search: `ORDER BY embedding <=> $q LIMIT k` (ascending, raw operator). No vector index is created.
- AC-6: **Answer.** One LLM call answers from the retrieved chunks only. It cites the chunks it used, rendered as `url_path` + heading text and never as section numbers. It says it doesn't know when the chunks don't contain the answer. The model cites chunks by number, code maps the numbers to citations, and out-of-range numbers are flagged.
- AC-7: **CLI.** `make ask Q="..."` prints:
  - the answer and the citations
  - the retrieved chunks with their distances
  - the tokens used and the latency
- AC-8: **Traces.** Every ask appends one JSON line to `runs/` (gitignored) with these fields:
  - timestamp, corpus SHA, chunk parameters
  - embedding model, answer model, k
  - question, retrieved `chunk_id`s and distances
  - answer, tokens, latency
- AC-9: **Tests.**
  - Unit tests for the chunker: sizes, overlap, heading attribution, short doc, and empty edge cases.
  - Embedding and LLM calls are faked. No test spends money or needs an API key.
  - The fakes check real behaviour, against real Postgres:
    - retrieval ordering
    - resumability
    - backoff
    - adapter request and response shapes
    - citation mapping
  - The existing tests stay green, and ruff is clean.
- AC-10: **Swappable models.** Changing the embedding or answer model, including adding a provider, needs only a new adapter class and a config value (`EMBED_MODEL`, `ANSWER_MODEL` as `provider:model`). The chunk, retrieve, ask and trace code doesn't change. Embeddings from different models (and dimensions) coexist, so models can be compared without re-chunking.
- AC-11: **Design note.** After implementation, NOTES.md has a short section naming the design patterns used and why.

## Out of scope

- splitting on markdown headings or any structure-aware chunking
- hybrid search, BM25, full-text search
- reranking, query rewriting, HyDE, multi-query
- contextual retrieval
- ACL logic or any filtering by acl_tags
- any vector index (HNSW, IVFFlat)
- the eval harness, metrics, LLM judges
- UI, API server, streaming
- caching, cost dashboards, optimisation of any kind
- writing or editing eval questions or reference answers (Arun's job)

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| Search | Exact cosine search, no ANN index | **HNSW/IVFFlat now:** approximate. Exact search gives perfect recall at the DB level, so recall@k misses are attributable to chunking and embeddings, not the index. |
| Distance | Cosine (`<=>`), with the query written as `ORDER BY embedding <=> $q LIMIT k` | **`1 - distance DESC`:** a future HNSW index would not be used. OpenAI vectors are normalised, so cosine, L2 and inner product rank identically anyway. |
| Store | pgvector in the existing Postgres | **Elasticsearch:** the docs are already in Postgres. Vectors, metadata and ACLs live in one store, the ACL pre-filter is a SQL `WHERE`, updates are transactional, and the scale is small. Known gap: Postgres full-text ranking is not BM25, so revisit in week 3. |
| Chunking | Fixed-size token windows, on purpose | **Structural, semantic or contextual chunking:** those are week 2's experiments, and this baseline is what they're measured against. |
| Chunk size / overlap | 512 / 64 (12.5%), about 22.4k chunks | **1024/128:** only 42% of docs fit one 1024 chunk, each vector averages more topics (dilution), and it leaves no room to sweep upward. **256/32:** 43k chunks, and hits lose context. Overlap protects facts that straddle a boundary; the cost is near-duplicate hits in top-k. |
| Embedding model | OpenAI `text-embedding-3-small`, 1536 dims | **3-large:** 3072 dims, over the 2,000-dim HNSW limit unless reduced, and 6.5× the price. **Voyage, Gemini, Cohere:** comparable, but the tokenizer differs from cl100k, so chunk sizes become approximate. **Local open models (BGE-M3, Qwen3-Embedding-0.6B):** an estimated 1–3 h on an M2 with 8 GB, plus torch. They're a week 2 comparison. |
| Answer model | OpenAI `gpt-5.4-mini`, lowest reasoning effort, frozen through week 3 | **Claude Sonnet 5.5:** about 2× the cost and a second provider. **Opus 5.5:** about 5× the cost, and thinking can't be disabled. **Haiku 5.5 or nano:** cheapest, but weaker grounding could blur error analysis. Single provider: a Claude judge later is cross-family. |
| k | 5 | **10:** more lost-in-the-middle and more duplicate overlap hits. 5×512 ≈ 2.6k tokens of context. The eval can sweep k without re-embedding. |
| Embedding storage | A separate `chunk_embeddings` table, untyped `vector`, PK `(chunk_id, model)` | **A `vector(1536)` column on `chunks`:** a model change would mean a schema change, and two models couldn't coexist. pgvector can still index one model later through an expression index plus a partial index. |
| Model wiring | `Embedder` / `Answerer` protocols, provider adapters, a factory on `provider:model`, injected into the pipeline | **Calling the SDK inline:** swapping a model would touch every call site, and tests would need network mocks. |
| Dependencies | `tiktoken`, `openai` | **The `pgvector` Python adapter:** it only converts lists to vector literals and pulls in numpy. psycopg sends `'[…]'::vector` as text. |

## Open questions

- The exact parameter name and lowest value for gpt-5.4-mini reasoning effort. Check against the API reference during the build.
- The embeddings per-request input cap (count and tokens), which sets the batch size. Check during the build.

## Verification

- `make chunk` twice gives the same count (about 22,378) and identical IDs.
- A test embed of about 20 chunks measures throughput. The full `make embed` runs only after Arun's go-ahead. Re-running `make embed` embeds 0.
- Vector sanity check:
  - 1536 dims, norm ≈ 1.0.
  - The cosine of "Can I claim my home wifi bill?" against the internet-reimbursement chunk is higher than against an unrelated time-off chunk.
- `make ask` runs on the seed questions. Report mechanical breakage only (empty retrieval, bad citations, wrong heading, truncated chunks).
- `make test` and `make lint` pass.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] NOTES.md updated (including the AC-11 design note)
