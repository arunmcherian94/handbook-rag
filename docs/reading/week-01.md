# Reading log: week 1

Notes from reading done for handbook-rag. Each entry: link, summary,
and what it changes in this project. Newest first within each date.

---

## Fri 16 Oct 2026

### Research: versioning evals and keeping the baseline comparable

Question: when the eval set changes, how do we tell a score change caused
by the eval apart from one caused by the system?

Read in full or in part:
- Anthropic, A statistical approach to model evaluations: https://www.anthropic.com/research/statistical-approach-to-model-evals
- LangSmith, evaluate on a specific dataset version: https://docs.smith.langchain.com/evaluation/how_to_guides/dataset_version
- LangSmith, compare experiment results: https://docs.smith.langchain.com/evaluation/how_to_guides/compare_experiment_results
- Langfuse, compare view with a baseline: https://langfuse.com/changelog/2025-11-06-compare-view-baseline-support
- OneUptime, maintaining a stale golden dataset: https://oneuptime.com/blog/post/2026-08-31-maintain-stale-llm-golden-dataset

Abstract, summary or search snippet only: Miller, Adding Error Bars to
Evals (arXiv 2411.00640); WorkBench Revisited (arXiv 2606.13715);
SWE-Bench Pro audit (Kili summary:
https://kili-technology.com/blog/data-story-ai-benchmark-audit-swe-bench-pro-verified);
pokedex-llm-benchmark releases (v1 and v2 declared not comparable).

Summary:
- Every change to an eval makes a new frozen version with a note of what
  changed. Relabels, new rows and scorer changes are recorded separately,
  because a relabel moves the score of an unchanged system.
- Every run records the eval version, its hash, the scorer version and
  the system config. Runs are compared only within one version. Langfuse
  and LangSmith both compare a candidate against a baseline row by row
  on the same dataset.
- When the eval changes, run the old system once on both versions. The
  difference is the eval's effect. Audits show it can be large: WorkBench
  fixes lifted GPT-4 about 8 points; the SWE-Bench Pro audit dropped one
  model from 78.8% to 59.5% on the same tasks.
- A scorer or judge change also means re-running the baseline.
- Keep a stable core of rows; the rows that didn't change give a
  like-for-like comparison across versions.
- Report a standard error with every score, and compare two systems on
  the same questions with a paired test (Anthropic).
- Mostly vendor docs and blogs; Anthropic is the only research source.
  The advice is consistent, but there's no single standard.

Takeaways for handbook-rag:
- We already version per question (CHANGELOG, `decision:` lines,
  `ref_source`, cut rows kept).
- Re-running the baseline is cheap: pinned corpus, frozen model and
  prompt, exact search. Answers from gpt-5.4-mini can still vary run to
  run.
- With 33 answerable rows, one row is about 3 points. Smaller answer
  changes are noise unless a paired comparison says otherwise.

Decisions informed: (b) eval versioning; spec 0004 run metadata (eval
version, file sha256, harness SHA), per-row output, standard errors.

### Hamel Husain and Shreya Shankar, AI Evals FAQ (four entries)

- How should I approach evaluating my RAG system?
  https://hamel.dev/blog/posts/evals-faq/how-should-i-approach-evaluating-my-rag-system.html
- How do I know if I can trust my automated eval?
  https://hamel.dev/blog/posts/evals-faq/how-do-i-know-if-i-can-trust-my-automated-eval.html
- Why binary pass/fail instead of 1–5 ratings?
  https://hamel.dev/blog/posts/evals-faq/why-do-you-recommend-binary-passfail-evaluations-instead-of-1-5-ratings-likert-scales.html
- How do we evaluate a model's ability to know what it doesn't know?
  https://hamel.dev/blog/posts/evals-faq/how-do-we-evaluate-a-models-ability-to-express-uncertainty-or-know-what-it-doesnt-know.html

Summary:
- RAG: score retrieval as a search problem (recall@k, precision@k, MRR)
  and generation separately: is the context relevant to the question, is
  the answer faithful to the context, does it address the question (from
  Jason Liu's "6 RAG evals"). Suggests building retrieval sets by
  generating questions from documents' key facts; gives no caveats.
- Trusting a judge: check it against human labels of the specific
  failure, with train/dev/test splits and an untouched test set. Report
  TPR and TNR, not one score; with rare failures, small false-alarm rates
  swamp reviewers. Code-checkable conditions need no labels. No label
  count, correction method or bar for "validated".
- Binary: pass/fail labels are more consistent than 1–5 scales. Partial
  credit comes from several binary sub-checks, such as counting expected
  facts. Silent on retrieval relevance and nDCG.
- Uncertainty: test both failure modes, refusing answerable questions and
  inventing answers to unanswerable ones (false premises, missing
  information, topics outside knowledge). Rough balance; diversity
  matters more than the ratio. Silent on exact strings and judges.

Takeaways for handbook-rag:
- Generating questions from pages wasn't used for v1: page wording
  flatters dense retrieval, and it can't produce out-of-corpus,
  contradiction or recency rows (35 of 52). A separate synthetic set,
  for scoring retrieval only, is a week 2 follow-up.
- Spec 0004 scores retrieval separately; faithfulness and
  answer-relevance judges are follow-ups, built only for failures found
  in coded traces.
- Our fact lists are already binary sub-checks.
- Spec 0004 reports false abstention (answerable rows) and invented
  answers (out-of-corpus rows) separately.
- v1.1 has no false-premise rows; follow-up for a later version.

Decisions informed: (c) no "validated judge" claim; (d) code checks;
Q1 binary; abstention reporting in spec 0004.

### Pinecone, Evaluation Measures in Information Retrieval

https://www.pinecone.io/learn/offline-evaluation/

Summary: defines recall@K, MRR, MAP@K and nDCG@K with code. nDCG assumes
graded relevance, which needs labels saying whether each item is more or
less relevant than others. Names binary relevance as MAP@K's weakness.
Warns that recall@K alone can mislead at large K. Silent on page vs
chunk level and on how to choose K.

Takeaways for handbook-rag:
- Binary nDCG@5 for the baseline (v1.1 has no grades). Graded nDCG from
  the required/alternate page tiers is a follow-up, after the tiers are
  reviewed as relevance labels.
- Report recall@1/3/5 together with MRR, not recall@5 alone.

Decisions informed: Q1 binary, Q2 k = 1/3/5.

### Weaviate, Evaluation Metrics for Search and Recommendation Systems

https://weaviate.io/blog/retrieval-evaluation-metrics

Summary: general definitions of rank-aware and non-rank-aware metrics
(precision, recall, MAP, MRR, nDCG@K). Doesn't address binary vs graded
relevance for our case or which K to report.

Takeaways for handbook-rag: none beyond the definitions. Q1 and Q2 rest
on our own reasons (no grades in v1.1; retrieval depth is 5).

Decisions informed: none directly.

### Research: RAG retrieval metrics when chunking changes (fresh research agent)

Question: are spec 0004's retrieval metrics too custom? What do people do when the chunking itself is the variable? The agent got only the setup and the scenarios, none of our proposals.

Read (pages fetched, summarised second-hand):
- Chroma, Evaluating chunking: https://www.trychroma.com/research/evaluating-chunking
- RAGAS context recall: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/
- DeepEval contextual recall: https://deepeval.com/docs/metrics-contextual-recall
- LlamaIndex retrieval evaluation: https://developers.llamaindex.ai/python/framework/module_guides/evaluating/usage_pattern_retrieval/
- arXiv 2505.21700 (string match, Recall@1–5): https://arxiv.org/html/2505.21700v2
- TruLens RAG triad, Phoenix retrieval relevance, LangSmith RAG tutorial (all LLM judges)

Snippet or abstract only: arXiv 2603.19251 (re-aligns gold spans after re-chunking); MultiHop-RAG (2401.15391); multi-hop survey (2204.09140); HiChunk (2509.11552); arXiv 2608.13867 (recall not comparable across chunk sizes); Aalto thesis (best-recall chunking gave the worst answer F1); dev.to "Your RAG eval is grading the chunker".

Summary:
- No single standard. BEIR, MTEB and LlamaIndex label fixed IDs, which break when chunks change. RAGAS, DeepEval, TruLens and Phoenix default to LLM judges.
- When chunking is the variable, the common advice is gold labels as text spans that don't depend on the chunker, mapped onto each chunking by a rule fixed up front. The rules seen are overlap, containment, token IoU and LLM judgement, and they give different numbers.
- Textbook recall over chunk IDs breaks with overlap and alternative evidence. Practice uses hit rate, recall over reference claims, or token recall.
- "Got everything needed" is reported as per-item recall or all-or-nothing (acc@k), often side by side.
- Scores are expected to change with chunking. Keep the labels fixed, and report retrieved tokens or precision, because bigger chunks inflate recall.
- Small sets are noisy: Chroma reports ±20–35 pt standard deviations.

Takeaways for handbook-rag:
- Our design (fact labels tied to text, recall over facts, OR across alternative sources) matches the closest common advice, done from labels instead of an LLM.
- Renamed to fact recall@k so it isn't read as textbook recall. Added all-required@k and retrieved tokens.
- Our containment rule is one of several in use, and it's lenient for straddling facts. It's fixed up front and kept constant.

Decisions informed: spec 0004 AC-2 reason, AC-3 metric set, Decisions table; NOTES "custom vs textbook metrics".

---

## Thu 15 Oct 2026

### Research: access control in RAG evals (three research subagents)

Question: should the eval set consider ACLs at all, and how do we keep
the frozen baseline comparable once week 2 adds a pre-filter?

Read in full or in part:
- OWASP LLM08:2025 Vector and Embedding Weaknesses: https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/
- OWASP LLM02:2025 Sensitive Information Disclosure: https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/
- Azure AI Search, security filter pattern: https://learn.microsoft.com/en-us/azure/search/search-security-trimming-for-azure-search
- Azure AI Search, document-level access control: https://learn.microsoft.com/en-us/azure/search/search-document-level-access-overview
- AWS, access control with metadata filtering in Bedrock Knowledge Bases: https://aws.amazon.com/blogs/machine-learning/access-control-for-vector-stores-using-metadata-filtering-with-knowledge-bases-for-amazon-bedrock/
- Auth0 / OpenFGA, secure RAG with LangChain: https://auth0.com/blog/building-a-secure-rag-with-python-langchain-and-openfga/
- AuthZed / SpiceDB, multi-tenant RAG: https://authzed.com/blog/building-a-multi-tenant-rag-with-fine-grain-authorization-using-motia-and-spicedb
- Oso, authorization in RAG: https://www-webflow.osohq.com/post/right-approach-to-authorization-in-rag
- Cerbos, RAG authorization recipe: https://docs.cerbos.dev/cerbos/0.42.0/recipes/ai/rag-authorization
- promptfoo red-team plugins (RBAC, BOLA, BFLA, cross-session leak) and red-team configuration: https://www.promptfoo.dev/docs/red-team/configuration/
- DeepTeam RBAC: https://www.trydeepteam.com/docs/red-teaming-vulnerabilities-rbac
- Inspect AI datasets: https://inspect.aisi.org.uk/datasets.html
- Anthropic, Demystifying evals for AI agents: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- VaultRAG, enforcing access control inside the retrieval query: https://dev.to/royalpinto007/enforcing-rag-access-control-inside-the-retrieval-query-not-after-it-4gm3
- vdf.ai, permission-aware private RAG: https://vdf.ai/blog/permission-aware-private-rag-on-premises/
- pgvector README: https://github.com/pgvector/pgvector
- ACORN, filtered vector search (SIGMOD 2024): https://arxiv.org/html/2403.04871v1
- Qdrant, vector search filtering: https://qdrant.tech/articles/vector-search-filtering/
- Securing the agent, multitenant retrieval (arXiv 2605.05287): https://arxiv.org/html/2605.05287

Abstract or snippet only: Authorization-First Retrieval (TrustNLP 2026),
arXiv 2603.23710 (filtered search in PostgreSQL), arXiv 2509.07789
(filtered ANN benchmark), ARBITER (arXiv 2512.20535), Descope on
post-retrieval checks, LangSmith metadata.

Summary:
- Every source enforces permissions as a deterministic layer in code or
  the database, applied before the prompt is built. Pre-filtering is the
  usual choice. None lets the LLM decide what a user may see.
- Permission correctness is tested with pass/fail cases (allowed user,
  denied user, same question across users), packaged apart from quality
  metrics: promptfoo's red-team config, DeepTeam as a separate package.
- Practitioner write-ups pair a leak rate (checked on retrieved chunks,
  target 0) with authorized recall, since denying everything scores zero
  leaks. One showed a quality-only eval passing a build with the ACL
  filter removed (leaks 0% → 82%, recall unchanged).
- With exact search, a pre-filter changes nothing for an all-access user
  and gives exact top-k over the visible subset for a restricted one.
  Restricted-user numbers aren't comparable to an unfiltered baseline.
  Filtered ANN (HNSW) is what breaks comparability, through candidate
  starvation.
- No source defines a standard over-blocking metric. Authorized recall
  per user is the usual stand-in.

Takeaways for handbook-rag:
- The quality set ignores ACLs and runs as an all-access user, so its
  numbers stay comparable to the baseline through week 2.
- Permission cases are deferred until the week 2 ACL design is known.
  The pointers above go into that spec.
- When HNSW arrives, recompute exact ground truth and report ANN recall
  as its own delta.

Decisions informed: ACLs deferred from the eval set (NOTES 2026-10-15),
(e) mix changed to 60 / 40.

---

## Wed 14 Oct 2026

### Hamel Husain: Your AI Product Needs Evals

Link: https://hamel.dev/blog/posts/evals/

Summary:
- Error analysis is the core activity. Open coding first: free notes
  per trace, recording the first upstream failure. Then axial coding:
  group the notes into a counted failure taxonomy. Repeat until new
  traces stop adding categories.
- Annotate about 30 traces yourself before letting an agent suggest
  failures. Eval categories come from observed failures, not from
  predetermined query types.
- Synthetic data: define dimensions, write about 20 tuples (one value
  per dimension) by hand, have an LLM generate more tuples, then turn
  tuples into queries in a separate prompt. The split avoids
  repetitive phrasing. If a failure is an obvious prompt gap, fix the
  prompt instead of generating tests for it.
- Prefer cheap code assertions wherever a rule can detect the failure.
  Keep LLM judges for persistent failures that need judgment.

Takeaways for handbook-rag:
- The six question types were set before error analysis, as coverage
  strata. PR #9's traces confirmed that two of them,
  contradictions/renames and version/recency, are real failure areas.
  Failure categories still come only from coded traces.
- Candidate questions use the two-step method: tuples first, questions
  in a separate prompt.
- Spec 0004 uses code checks first (citation present and valid, exact
  abstention string) and judges only for what code can't detect.

Decisions informed: (a) failure categories, today's two-step
generation method, (d) binary rubric (Thursday).

### Hamel Husain & Shreya Shankar: How many examples do I need for an eval?

Link: https://hamel.dev/blog/posts/evals-faq/how-many-examples-do-i-need-for-an-eval.html
AI Evals FAQ, item 3.

Summary:
- The answer depends on the stage. Discovery: about 100 diverse traces.
  Code checks: pass and fail examples for each condition. An LLM judge:
  about 100–200 labels per failure mode. A repeatable regression set
  often grows past 100.

Takeaways for handbook-rag:
- The eval set starts at 50–60 questions and grows from later traces.
  That is a starting set, not a judge-validation set, so the 100–200
  label count doesn't apply yet and no judge is claimed as validated.

Decisions informed: (c) judge claims (Thursday).

### Hamel Husain & Shreya Shankar: Why binary pass/fail instead of 1–5 ratings?

Link: https://hamel.dev/blog/posts/evals-faq/why-do-you-recommend-binary-passfail-evaluations-instead-of-1-5-ratings-likert-scales.html
AI Evals FAQ, item 4.

Summary:
- Binary pass/fail beats 1–5 scales: clearer decisions, more
  consistent labels. Track gradual progress as several binary
  sub-checks, e.g. k of n expected facts present.

Takeaways for handbook-rag:
- Every check in spec 0004 is binary. Partial credit is counted as
  sub-checks, not a score.

Decisions informed: (d) binary rubric (Thursday).

### Hamel Husain & Shreya Shankar: How do I know if I can trust my automated eval?

Link: https://hamel.dev/blog/posts/evals-faq/how-do-i-know-if-i-can-trust-my-automated-eval.html
AI Evals FAQ, item 5.

Summary:
- Validate a judge against human labels with a train / dev / test
  split (roughly 10–20 / 40–45 / 40–45%). Report true positive and
  true negative rates, not raw agreement. One judge per failure mode.

Takeaways for handbook-rag:
- No judge before the baseline traces are read.
- With 50–60 questions, every judgment is hand-checked instead of
  claiming a validated judge.

Decisions informed: (f) order, (c) judge claims (Thursday).

### Hamel Husain & Shreya Shankar: How do we evaluate a model's ability to know what it doesn't know?

Link: https://hamel.dev/blog/posts/evals-faq/how-do-we-evaluate-a-models-ability-to-express-uncertainty-or-know-what-it-doesnt-know.html
AI Evals FAQ, item 6.

Summary:
- Abstention evals need both answerable and unanswerable questions,
  roughly balanced. Pass = answers the answerable ones and refuses the
  unanswerable ones. Diversity matters more than the exact ratio.

Takeaways for handbook-rag:
- The eval set includes out-of-corpus questions alongside answerable
  ones, scored against the baseline's two fixed replies.

Decisions informed: (e) question mix.

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
- Rule of thumb: HNSW when the graph fits in memory; IVF plus
  quantization (e.g. DiskBBQ) when memory is the constraint; measure
  recall against exact search either way.

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
