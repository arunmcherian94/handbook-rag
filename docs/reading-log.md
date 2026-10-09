# Reading log

Notes from reading done for handbook-rag. Each entry: link, summary,
and what it changes in this project. Newest first within each date.

---

## Fri 9 Oct 2026

### Concepts from discussion (no single source)

Embeddings and dimensions:
- Dimension count (e.g. 1,536 for OpenAI text-embedding-3-small,
  3,072 for -3-large; open models often 384/768/1,024) is a model
  design choice, not a magic number. More dims = more room for fine
  distinctions, but more storage, slower comparisons, and index limits
  (pgvector HNSW: 2,000 dims for `vector`). More dims ≠ better
  retrieval on my corpus; week 2 compares models.
- Toy example: "Can I claim my home wifi bill?" scores ~0.997 against
  "Internet costs are reimbursed up to a monthly cap" with no shared
  keywords. Embeddings match meaning, not words. (Also why keyword
  search still matters for exact strings and versions: week 3.)
- Real dimensions have no human labels; meaning is spread across them.
  You can only compare embeddings, not read them.
- A real normalized 1,536-dim vector: values mostly within ±0.05,
  min/max around ±0.1, length exactly 1.0, ~6 KB in pgvector.
  (Synthetic sample generated for shape only.)

ANN, HNSW, IVF, DiskBBQ:
- ANN is the category: find probably-closest vectors by examining only
  part of the data. Trades recall for speed. HNSW and IVF are two
  approaches within it.
- HNSW: layered graph, greedy walk. Best speed/recall; slow build;
  memory-hungry.
- IVF (IVFFlat): cluster up front, search only the nearest clusters.
  Faster build, less memory, lower recall at the same speed; misses
  neighbours just across a cluster boundary.
- Quantization: store vectors at lower precision (binary ≈ 1 bit per
  number instead of 4 bytes). Much smaller; re-check top candidates
  with full vectors to recover accuracy.
- DiskBBQ (Elastic, Elasticsearch 9.2): evolved IVF with hierarchical
  k-means, vectors may sit in more than one cluster (softens the
  boundary problem), compressed with BBQ (Better Binary Quantization),
  read selectively from disk. Vendor-reported: ~15 ms queries in
  ~100 MB memory. Elastic's own caveat: HNSW still wins for 99%+
  recall at very low latency.
  Link: https://www.elastic.co/search-labs/blog/diskbbq-elasticsearch-introduction

Takeaways for handbook-rag:
- None of the ANN choices matter at current scale; exact search stays.
- Interview line: HNSW when the graph fits in memory; IVF plus
  quantization (e.g. DiskBBQ) when memory is the constraint; measure
  recall against exact search either way.
- Claims ledger: I operated Elasticsearch as a datastore. DiskBBQ is
  knowledge, not experience.

### pgvector README: similarity, distance, exact search, indexing

Links:
- README (official): https://github.com/pgvector/pgvector
- Full README mirror: https://pgxn.org/dist/vector
- HNSW intuition (Pinecone): https://www.pinecone.io/learn/hnsw
- HNSW intuition (gentler): https://towardsdatascience.com/whats-the-story-with-hnsw-d1402c37a44e
- HNSW paper (depth, later): https://arxiv.org/pdf/1603.09320

Summary:
- Embedding = text turned into a vector (a point in ~1,000+ dimensions).
  Similar meaning lands close together. Retrieval = find the points
  closest to the question's point.
- Cosine similarity = angle between two vectors (1 same direction, 0
  unrelated). Cosine distance = 1 − similarity. pgvector `<=>` returns
  DISTANCE, so sort ascending.
- Other measures: L2 `<->` (straight-line), inner product `<#>`
  (returned negated). For length-1 (normalized) vectors, e.g. OpenAI
  embeddings, all three give the same ranking; inner product is fastest.
- Exact search (pgvector default): compare against every row, perfect
  recall at the DB level. Cost grows linearly with rows. Storage is
  4 bytes × dims + 8 per vector (1,536 dims ≈ 6 KB).
- ANN indexes look at a fraction of rows, so they are approximate:
  adding one changes results, not just speed (unlike a B-tree).
- HNSW: multi-layer graph, sparse long jumps on top, dense at the
  bottom; greedy search can stop at a local best and miss the true
  nearest. Knobs: m (connections, default 16), ef_construction (build
  effort, default 64), ef_search (candidates kept per query, default 40).
  Better speed/recall than IVFFlat, slower build, more memory, no
  training step. `vector` type indexable up to 2,000 dims.
- IVFFlat: clusters vectors into lists, searches the nearest few
  (probes, default 1). Misses neighbours across cluster boundaries.
  Must be built after data exists.
- Filtering trap: with ANN indexes, WHERE is applied AFTER the index
  scan. 10% match + ef_search 40 → ~4 rows back. Fix: iterative index
  scans (0.8.0+), partial indexes, or partitioning.
- Multitenancy: a shared ANN index lets one tenant's vectors affect
  another's recall; isolate with list partitioning or separate tables.
- Index is only used if ORDER BY is a raw distance operator ascending
  with LIMIT (not `1 - distance DESC`).
- Monitor ANN recall by comparing against exact search.

Takeaways for handbook-rag:
- Baseline uses exact search. DB-level recall is perfect, so any
  recall@k miss is caused by chunking/embeddings, not the index.
- Query form from day one: `ORDER BY embedding <=> $q LIMIT k`.
- Prefer an embedding model ≤ 2,000 dims so HNSW stays an option.
- Week 2 ACL pre-filter: the filtering trap is the mechanism behind
  "filtering starves the candidate set". Test iterative scans there.
- When HNSW is added: run the eval with index on vs. off; the recall
  difference is the price of the speed.

### Pinecone: Chunking Strategies for LLM Applications

Link: https://www.pinecone.io/learn/chunking-strategies
Roie Schwaber-Cohen & Arjun Patel, 28 Jun 2025.

Summary:
- Why chunk: fit the embedding model's window (excess tokens are
  truncated), and make each chunk meaningful enough to be found.
- Too small loses context; too large dilutes the embedding. Long
  context doesn't remove the need (cost, latency, lost-in-the-middle).
- Rule of thumb: if a chunk makes sense to a human on its own, it will
  to the model.
- Decide using: data type, embedding model, query length/complexity,
  and how results are used (search vs. RAG vs. agent).
- Methods, simplest first: fixed-size (recommended default) →
  sentence/paragraph → recursive character → structure-based
  (Markdown headings, code blocks) → semantic (split where embedding
  distance shifts) → contextual (LLM-written context prepended,
  Anthropic 2024).
- Tuning: test a range (128/256 small, 512/1024 large) against
  representative queries.
- Chunk expansion: retrieve neighbouring chunks around a hit at query
  time. Small chunks for search, wider context for the answer.

Takeaways for handbook-rag:
- Baseline = fixed-size, matching the article's default.
- Ignore its suggestion to size chunks at the embedding model's max
  window: too large for precise retrieval, and it contradicts its own
  128–1024 test range.
- Overlap is barely covered; the spec needs its own reasoning for it.
- Week 2 experiments map directly: structure-based Markdown, semantic,
  contextual; size sweep within 128–1024.
- Chunk expansion → NOTES.md as a later idea, not the critical path.

### Hamel Husain & Shreya Shankar: How should I approach evaluating my RAG system?

Link: https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html
AI Evals FAQ (published 10 Jun 2025, modified 1 Sep 2026).

Summary:
- Evaluate retrieval and generation separately. Retrieval first.
- Retrieval is a search problem: Recall@k, Precision@k, MRR against
  query → relevant-doc pairs.
- Generation: error analysis → human labels → targeted LLM judges →
  validate judges against human labels (TPR/TNR), then correct the
  measured failure rate. Never use off-the-shelf judge prompts
  unvalidated.
- Framework: Jason Liu's "There Are Only 6 RAG Evals". Tier 1 = IR
  metrics; tiers 2–3 = context relevance (C|Q), faithfulness (A|C),
  answer relevance (A|Q).
- Error analysis surfaces domain-specific failure modes that deserve
  their own evaluators.

Takeaways for handbook-rag:
- Harness reports retrieval metrics and judge results separately;
  retrieval metrics are primary.
- Expected domain failure modes: renames, stale numbers, entity vs.
  general conflicts, restricted-user leaks.
- DIVERGENCE: the article suggests generating retrieval questions
  synthetically from documents. Not doing that: page-derived questions
  reuse the page's wording and inflate retrieval scores, and can't
  produce contradiction, rename or restricted-user cases. Method: I set
  dimensions, an LLM drafts, I edit and verify every answer.

### Hamel Husain & Shreya Shankar: How do I choose the right chunk size for my document processing tasks?

Link: https://hamel.dev/blog/posts/evals-faq/how-do-i-choose-the-right-chunk-size-for-my-document-processing-tasks.html
AI Evals FAQ (published 6 Jun 2025).

Summary:
- About document processing, NOT RAG: the model sees every chunk, so
  chunking is about how much it can reason over at once.
- Fixed-output tasks (extract, answer one question, classify): largest
  chunk likely to contain the answer, minus irrelevant text.
- Expansive-output tasks (summarise, exhaustive extraction): smaller
  chunks, process independently, aggregate (map-reduce). Respect
  content boundaries.
- Trade-off: global context vs. local focus. Treat chunk size as a
  hyperparameter; validate by experiment.

Takeaways for handbook-rag:
- Doesn't decide the baseline's retrieval chunk size.
- Lost-in-the-middle applies to the answer call (top-k stuffed into one
  prompt): a week 4 context-assembly concern.
- Confirms the plan: baseline picks one reasonable value; week 2
  measures alternatives against it.

### Not read
- Chip Huyen, *AI Engineering*, ch. 6: paywalled. Replaced tonight by
  the Pinecone chunking article and the pgvector README. Revisit if
  access becomes available.

---

## Earlier (week 1)

Source: Hamel Husain & Shreya Shankar, *AI Evals FAQ*,
https://hamel.dev/blog/posts/evals-faq/ (updated 21 Sep 2026)

### FAQ item 1: Why is error analysis so important?

Link: https://hamel.dev/blog/posts/evals-faq/#q-why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed

Summary (from Pawel Huryn's infographic embedded in the item; cite as
his visualisation, not Hamel's words):
- Loop: traces → open coding → axial coding → re-code, until
  saturation. ~100 diverse traces is the rule of thumb.
- Specification failures: fix the prompt first. Generalization
  failures: candidates for evaluators.
- Don't generate synthetic data without failure hypotheses; define at
  least 3 dimensions first.
- Prefer code-based evals where possible. LLM judges get one narrow
  failure mode each, binary, aligned to human labels via TPR/TNR.

### FAQ item 2: Reference answer or rubric first?

Link: https://hamel.dev/blog/posts/evals-faq/#q-do-i-need-a-reference-answer-before-annotating-data

Key idea: criteria drift. Expected answers must stay revisable once
real outputs have been read.

---

## Pending (Sat 10 Oct, before eval set work)

- [ ] FAQ 3, How many examples: https://hamel.dev/blog/posts/evals-faq/how-many-examples-do-i-need-for-an-eval.html
- [ ] FAQ 4, Binary vs Likert: https://hamel.dev/blog/posts/evals-faq/why-do-you-recommend-binary-passfail-evaluations-instead-of-1-5-ratings-likert-scales.html
- [ ] FAQ 5, Trusting the automated eval: https://hamel.dev/blog/posts/evals-faq/how-do-i-know-if-i-can-trust-my-automated-eval.html
- [ ] FAQ 6, "I don't know": https://hamel.dev/blog/posts/evals-faq/how-do-we-evaluate-a-models-ability-to-express-uncertainty-or-know-what-it-doesnt-know.html
