# Week 1 (5–17 Oct 2026): pinned corpus, naive RAG baseline, eval set, harness, baseline numbers

**Outcome:** a measured naive RAG baseline over the pinned GitLab handbook (4,088 docs, 22,378 chunks). It has a 52-row eval set and a harness that scores retrieval and answers with code only, no LLM judge. Every week 2+ experiment is compared against these numbers. 17 PRs.

## 1. What was built, in order

| Stage | PRs | What it is |
|---|---|---|
| Scaffold | #1–2 | uv, Postgres + pgvector (docker compose), Makefile, test harness, spec template |
| Corpus pin (spec 0001) | #3 | Blobless sparse clone of the handbook repo pinned at `5273b21`; `make corpus` refuses a dirty or wrong checkout |
| Ingestion (spec 0002) | #4 | 4,177 files found, 4,088 ingested, 89 skipped (85 empty, 4 drafts); each ingest mirrors the snapshot |
| Workflow | #5–6 | Spec-driven flow, review gate, reading log |
| Naive baseline (spec 0003) | #7–8 | Fixed 512/64-token chunks → text-embedding-3-small → top-5 cosine → gpt-5.4-mini with a strict grounding prompt and two fixed abstention strings; JSONL traces |
| Error analysis | #9 | Open coding of 10 seed traces, done before any metric design |
| Eval set | #10–12 | v1 → v1.2: 52 rows (33 answerable, 19 out-of-corpus), references cited to line ranges in the pin, required/optional facts |
| Eval harness (spec 0004) | #13–15 | Evidence check, chunk- and page-level retrieval metrics, abstention and code checks, SE per metric, cost guard |
| Agent workflow | #16 | `orchestrate` skill for subagent slices |
| Baseline numbers | #17 | Run `2026-10-17-3748df5b`, committed with takeaways and a shared metrics glossary |

## 2. Key decisions and why

**Corpus**
- **Whole handbook, not just the pages the seed questions touch.** A narrow corpus has too few distractors and inflates retrieval scores. → [ADR-0001](../decisions/0001-corpus-scope-and-pin.md)
- **Pinned SHA, blobless clone.** It keeps full history for recency work without fetching every blob. Shallow and treeless clones were rejected (they lose history, or path logs become slow). → [corpus notes](../corpus.md)
- **Redirect stubs with a body are kept.** 4 of 6 carry rename knowledge found nowhere else ("PRR retired, replaced by PREP").
- **Mirror on ingest.** Rows not in the snapshot are deleted, so a page pulled from public can't still be served. This matters for ACLs later. → [ADR-0002](../decisions/0002-ingest-mirrors-snapshot.md)

**Chunking and embedding** → [ADR-0003](../decisions/0003-baseline-chunking-512-64.md), [ADR-0004](../decisions/0004-embedding-model-and-schema.md), [journal 2026-10-12](../journal/2026-10-12-baseline-decisions.md)
- **Chunking is required, not optional.** 180 docs exceed the 8,191-token embedding limit.
- **512 tokens / 64 overlap.** Mid-range, so week 2 can sweep both sides. The "most docs fit in 1024" assumption was checked and was wrong: only 42% fit. Overlap 64 (12.5%) keeps any sentence up to 64 tokens whole in at least one chunk, for +12.6% embedded tokens (≈ $0.02).
- **Embedding cost barely depends on chunk size** (10.3–11.3M tokens across settings), so size is chosen for quality.
- **text-embedding-3-small.** Cheapest option, its tokenizer is exactly cl100k, and it's the standard reference point. Open embedders become a measured week 2 comparison.
- **Embeddings table keyed `(chunk_id, model)` with an untyped `vector` column,** so models of different dimensions coexist.

**Answering** → [ADR-0005](../decisions/0005-answer-model-and-api.md), [ADR-0006](../decisions/0006-grounding-prompt-fixed-abstentions.md)
- **gpt-5.4-mini.** One provider with the embeddings, and a Claude judge later is cross-family (no self-preference). Cost wasn't the deciding factor.
- **Chat Completions over Responses.** No reasoning and a single turn, so Responses' advantages don't apply. Chat Completions is also the portable format for open and local models.
- **Two fixed abstention strings** (in scope but not found / out of scope). Code can then tell a retrieval miss from an out-of-scope question without a judge.
- **Parametric leakage is a known risk.** The handbook is surely in pretraining, so retrieval and answers are scored separately.
- **Answer model and prompt frozen through week 3,** so answer changes are attributable to retrieval.

**Engineering patterns** → [ADR-0007](../decisions/0007-embedding-failure-handling.md), [ADR-0008](../decisions/0008-design-patterns.md), [journal 2026-10-13](../journal/2026-10-13-baseline-build.md)
- **Ports and adapters:** `Embedder` / `Answerer` Protocols, plus a factory on `provider:model` strings that are also the DB key.
- **Dependency injection** of clients, sleep and clock, so tests run at zero cost with no network.
- **Functional core, imperative shell:** a pure chunk / prompt / citation core.
- **Layered embedding failure handling:** pre-checks, binary split on 400/422, stop on auth errors, `Retry-After` on 429, a 6-attempt cap.
- **Content-hash guard:** a vector is stored only if it matches the chunk's current text.

**Eval design** → ADRs [0010](../decisions/0010-eval-questions-human-authored.md), [0011](../decisions/0011-acls-deferred-from-quality-set.md), [0012](../decisions/0012-eval-versioning.md), [0013](../decisions/0013-retrieval-metrics.md), [0014](../decisions/0014-abstention-scoring.md), [0016](../decisions/0016-code-checks-before-judges.md), [0017](../decisions/0017-history-decides-currency.md); [error analysis](../journal/2026-10-13-error-analysis.md)
- **Error analysis before metrics.** Coding the 10 seed traces showed "right page, wrong chunk" (6/10) and "retrieved but not used" (7/10). That shaped what to measure.
- **Question types are coverage strata, not failure categories.** Categories come only from coded traces.
- **Questions are human-authored, never generated from pages.** Page wording flatters dense retrieval, and the method can't produce out-of-corpus, contradiction or recency rows.
- **ACLs deferred to week 2.** The quality set runs as an all-access user; permission cases become a separate leak-rate suite.
- **Git history decides currency, never facts.** Facts cite the pin only. Recency rows are labelled `history-only` vs `in-page`, so a later fix can be measured on the same facts.
- **Headline = chunk-level fact recall@k** (required facts covered ÷ required facts). A chunk is relevant if it contains a cited line, so the labels survive chunking changes. Page level is diagnostic: page hit with chunk miss means a chunking problem.
- **Everything code can check is graded by code.** No judge until a coded failure needs one, and then it's reported as "checked against N labels, TPR/TNR", never as "validated".
- **SE and n on every rate.** At 33 rows, one row is about 3 points.
- **Versioned eval.** A run records the eval sha256, harness SHA and corpus SHA, and runs are compared only within one eval version.

**Harness** → [ADR-0015](../decisions/0015-span-overlap-relevance.md), [journal 2026-10-17](../journal/2026-10-17-eval-harness.md)
- **Evidence check before any spend.** Every required fact's cited lines must exist in a stored chunk, or the run fails.
- **Span-overlap matching:** 16% of cited lines straddle a chunk boundary, so a ≥40-character piece at a chunk edge counts. Fixed for all later experiments.
- **`retrieved_tokens@k` reported next to recall,** because bigger chunks raise recall just by covering more text.

## 3. What the gates caught (examples)

Full lists are in the journal: [2026-10-07](../journal/2026-10-07-corpus-and-ingestion.md), [2026-10-13](../journal/2026-10-13-baseline-build.md), [2026-10-17](../journal/2026-10-17-eval-harness.md).

- **Data integrity:** ingest only checked HEAD, so a dirty or empty checkout could have wiped or mislabelled rows. `url_path` wasn't lowercased (Hugo lowercases URLs). A re-chunk during embedding could store a vector for stale text.
- **Correctness:** `<|endoftext|>` in a question crashed after the paid call. The query embedding had no retries. The headings check compared the DB with itself, so it could never fail.
- **Cost safety:** `make eval CONFIRM=0` spent money, because any non-empty value passed.
- **Eval validity:** trap hypotheses written from memory didn't exist in the pin, so rows were recoded or cut. Rows were mislabelled out-of-corpus when the pin partly answered them. Missing expected docs would have scored correct retrievals as misses.
- **Process:** the plan gate kept out Alembic, CI, a settings framework and pre-commit. It also reversed a rule that would have dropped informative redirect stubs.

## 4. Baseline results

Run `2026-10-17-3748df5b`, $0.21 → [summary.md](../eval/results/2026-10-17-3748df5b/summary.md)

| Metric | Value |
|---|---|
| chunk_fact_recall@5 | 0.50 ± 0.08 |
| chunk_hit@5 / page_hit@5 | 0.59 / 0.81 |
| chunk_mrr | 0.38 |
| ooc_pass | 0.89 (17/19) |
| false_abstention | 0.39 |
| code_checks_passed | 0.95 |

**Reading:**
- **Retrieval is the bottleneck,** specifically chunk-level: the right page is found far more often than the right chunk.
- **Synthesis is weakest:** 0/8 rows got all their required facts into the top 5.
- **Recency is next:** fact recall@5 is 0.35, and chunks carry no dates.
- **The model over-abstains.** That needs row-by-row coding before the week 3 answer-model check.

## 5. Known limitations

Open items: [follow-ups](../follow-ups.md).

- **Fixed windows cite a chunk by its start heading,** even when the fact sits in a later section.
- **Partial abstentions** ("I don't know the exact date…") aren't caught by exact-match detection.
- **Lenient span matching** slightly inflates recall. Token IoU would replace it.
- **Small n:** 8 rows per question type, so per-type differences are directional only.
- **Fact-list review:** 26 rows' reference facts were auto-reviewed by subagents and still need a hand check before any judge uses them.
- **Hugo shortcode data** (per-country tables) isn't in the corpus.

## 6. Into week 2

**Planned work:**
- chunking sweep (size, overlap, structure-aware)
- 3-model embedding comparison
- ACL pre-filter and its leak suite
- contextual retrieval

**Check against the baseline:**
- chunk_fact_recall@5
- the page-hit/chunk-miss list (rows 52, 53, 8, 10, 99, 38, 89)
- synthesis all_required@5
- recency recall
- `retrieved_tokens@5`, so that a gain isn't just more text

## 7. How the work ran

- **Spec-first:** every build traces to AC IDs in a merged spec, and anything not traceable becomes a follow-up.
- **Before every PR:** `make test`, `make lint` and `/code-review`, with findings ranked; must-fix items fixed by default, the rest confirmed first; then a clean-room clone check.
- **Subagents** for eval-row review and planning research. From week 2, file-disjoint slices via the `orchestrate` skill ([ADR-0018](../decisions/0018-subagent-orchestration.md)). Workflow: [ADR-0009](../decisions/0009-spec-driven-workflow.md).

## 8. Reading that shaped decisions

Full entries: [reading/week-01.md](../reading/week-01.md).

- [Hamel Husain, Your AI Product Needs Evals](../reading/week-01.md#hamel-husain-your-ai-product-needs-evals): do error analysis before choosing metrics, which is why the seed traces were coded first.
- [AI Evals FAQ: binary pass/fail; trusting automated evals](../reading/week-01.md#hamel-husain--shreya-shankar-why-binary-passfail-instead-of-15-ratings): binary fact checks rather than scales, and no "validated judge" claim without labels and TPR/TNR ([ADR-0016](../decisions/0016-code-checks-before-judges.md)).
- [Pinecone, Evaluation Measures in IR](../reading/week-01.md#pinecone-evaluation-measures-in-information-retrieval): report MRR next to recall@k, because recall alone hides ranking ([ADR-0013](../decisions/0013-retrieval-metrics.md)).
- [Research: RAG retrieval metrics when chunking changes](../reading/week-01.md#research-rag-retrieval-metrics-when-chunking-changes-fresh-research-agent): labels fixed to evidence lines so they survive re-chunking, plus retrieved tokens next to recall.
- [Research: versioning evals](../reading/week-01.md#research-versioning-evals-and-keeping-the-baseline-comparable): runs are compared within one eval version, and the baseline is re-run on a new version ([ADR-0012](../decisions/0012-eval-versioning.md)).
- [Research: access control in RAG evals](../reading/week-01.md#research-access-control-in-rag-evals-three-research-subagents): permissions are a deterministic layer with their own leak suite, so ACLs stay out of the quality set ([ADR-0011](../decisions/0011-acls-deferred-from-quality-set.md)).
