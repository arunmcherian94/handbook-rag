# Week 3 (27 Oct – 1 Nov 2026): answer evaluation, hybrid search and a cross-encoder reranker, both not adopted

**Outcome:** production retrieval is unchanged: dense search on `fixed-512-64`, text-embedding-3-large@1536, with the SQL ACL pre-filter. Answer evaluation now classifies false abstentions and checks answer content with code-only assertions. It found the retrieval side mostly a ranking or depth problem at k = 5. Two ranking changes were built and measured against a 2-paired-SE bar set before each run. Hybrid search (Postgres full-text search + dense, RRF) scored −1.08 SE and the cross-encoder reranker −0.70 SE, so neither was adopted, and `DEFAULT_RETRIEVER` stays `dense`. Leak and over-block stayed 0 on both new paths. This summary covers PRs #45–#54.

## 1. Decisions

### Answer evaluation, code-first → [spec 0010](../../specs/0010-answer-evaluation.md) (#45, #46), claims corrections (#47, #50); journal [27 Oct](../journal/2026-10-27-answer-eval.md)
- **Baseline:** resolved by rule to `2026-10-21-e602bd95` (3-large@1536, `fixed-512-64`, gpt-5.4-mini). No paid calls: everything runs over stored run data.
- **False abstentions (n = 10 of 33 answerable):**

  | class | n | rows |
  |---|---|---|
  | generator_refusal (all required facts in the top 5) | 2 | 58, 100 |
  | partial_retrieval | 3 | 8, 49, 89 |
  | retrieval_miss | 4 | 53, 55, 65, 92 |
  | not_classifiable (no cited required fact) | 1 | 22 |

  - 7 of the 9 classifiable rows are missing a required fact from the top 5. In 5 of those 7 (8, 49, 53, 55, 89), every missing fact sits at rank 6–8. Only rows 65 and 92 have a required fact outside the top 20.
  - So the retrieval side is mostly a ranking or depth problem at k = 5, not a coverage gap. That pointed at reranking or k before chunking or embedding changes.
- **Answer-content check:** `answer_content_fact_pass` 0.403 ± 0.079 and `answer_content_row_pass` 0.258 ± 0.079 (n = 31). There are 66 expressible facts. 7 facts are `expressible: false` and counted for the week 6 judge.
  - It means "mentions the key content", not "states it correctly". Term rules can't see negation (rows 49, 53, 100).
  - Claude drafted the assertions from each fact's own text, and Arun reviewed every one. No variant was taken from the answers being scored.
- **Corrections (#47):** 10 rows abstained on `e602bd95`, not 11 (11 is the 3-small baseline, `18f10293`). 10 of the 26 auto-reviewed fact-list rows were checked, not 26. #50 closed a follow-up that turned out to be wrong: the fact-list review file was already in eval-set order.

### Hybrid search: built, measured, not adopted → [spec 0011](../../specs/0011-hybrid-search.md) (#48, #49, #51); journal [29 Oct, build](../journal/2026-10-29-hybrid-build.md), [30 Oct, runs and audit](../journal/2026-10-30-hybrid-runs.md)
- **Built:** a Postgres full-text list (`ts_rank_cd` over a generated `tsvector` column, an OR of the question's lexemes, no IDF), fused with the dense list by RRF (k = 60, depth 50, equal weights, fixed before any run). The same ACL pre-filter is on the FTS path, and the static predicate test covers it. `--retriever dense|fts|hybrid`, with `dense` as the default.
- **Result,** run `2026-10-30-e1e47d72` vs `2026-10-21-d83f3edc` (n = 32): chunk_fact_recall@5 0.521 against 0.583, paired −0.062 ± 0.057, **−1.08 SE**. 3 rows won, 7 lost. At @20 the delta is +0.025 (+0.68 SE). fts alone (`2026-10-30-e95364c1`) scored 0.148.
- **Permissions** (`2026-10-30-a4975b23`): leak 0 and over-block 0 at k = 5 and 20.
- **Why it scores lower** (a read-only audit at no cost):
  - FTS adds no fact chunks beyond dense's top 50. The best possible top 5 is 0.875 with or without FTS's top 50, so fusion can only reorder dense's candidates.
  - Equal-weight RRF ranks chunks found by both lists above good dense-only ones. A chunk in both top-50 lists beats a dense-only chunk even at dense rank 1.
  - The OR query matches a median 51% of chunks, so FTS rank is close to noise.
  - No offline variant came near +2 SE, including a simulated BM25 list built from `tsvector` counts.
- **Decision (Arun, 31 Oct):** not adopted. Dense stays the default, so no ADR is needed. A re-test waits for an eval set with keyword-heavy questions.

### Cross-encoder reranker: built, measured, not adopted → [spec 0012](../../specs/0012-cross-encoder-reranker.md) (#52, #53, #54); journal [31 Oct, build](../journal/2026-10-31-rerank-build.md), [1 Nov, runs](../journal/2026-11-01-rerank-runs.md)
- **Built:** DeepInfra `Qwen/Qwen3-Reranker-4B` scores the dense top 50, and the top k is cut from the reranked order. A pair over the 32,768-token limit fails the run; nothing is truncated. `--retriever rerank`, off by default. The reranker only sees candidates the SQL pre-filter already allowed.
- **Primary comparison:** paired within one run, the reranked top 5 against the same run's dense top 5, on identical query vectors. `d83f3edc` is for continuity only.
- **Result,** run `2026-11-01-d5286816` (n = 32): chunk_fact_recall@5 0.542 against 0.583, paired −0.041 ± 0.058, **−0.70 SE**. 3 rows won, 6 lost, 23 tied. Rerank is below dense at every k from 3 to 10. Headroom captured: −0.139.
  - Of the targeted rank 6–8 rows, 8 and 53 gain. Rows 49 and 89 lose a fact from dense rank 3 or 5, and row 55's fact falls from rank 8 to 38.
  - Truncation share 0. Rerank p50 4,154 ms per query (an API round trip), against dense search's 337 ms.
- **Permissions** (`2026-11-01-afb31160`): leak 0 and over-block 0 at k = 5 and 20. Authorized recall 0.958 @5 (n = 28). On the 26 cases both runs score, it is 0.955 against dense's 0.878 @5, and 0.974 against 1.000 @20.
- **Decision (pre-set rule, 1 Nov):** below 1 SE, so not adopted. `DEFAULT_RETRIEVER` stays `"dense"`, ADR-0023 is not written, and `--retriever rerank` stays as a measurement flag.

## 2. Learnings
- **The 0.875 ceiling counts what the candidates hold, not what a ranker can separate.** ([journal](../journal/2026-11-01-rerank-runs.md#why-the-reranker-scores-lower))
  - Neither change could reach a fact chunk outside dense's top 50 (FTS added none), and both lost.
  - The reranker rates many on-topic candidates near 1.0 (5 or more at ≥ 0.99 on 8 of 32 rows), so fact chunks lose on small margins (row 44: 0.998 against 0.999).
  - It also scores some fact chunks as irrelevant: on row 89 ("whats our exit policy"), all 50 candidates score ≤ 0.056.
  - Fixed 512-token windows that mix the fact with other text, and colloquial questions, fit both patterns. Neither cause is tested.
  - Required-facts-only scoring also hides one reranker gain (row 55, an optional fact at #1).
- **An in-run paired comparison removes query-vector drift as a variable.** Spec 0012 compared the reranked list with the dense list from the same query vector. This run's dense top 5 gave the same chunk_fact_recall@5 as `d83f3edc` on all 32 scored rows, so the continuity and in-run figures agree. ([journal](../journal/2026-11-01-rerank-runs.md#continuity-comparison-ac-12))
- **Postgres FTS without IDF is close to noise on conversational questions.** Words like `pleas`, `need` and `get` survive as lexemes, and the OR query matches about half the corpus. The FTS top 20 holds no fact chunk that dense's top 50 lacks. ([journal](../journal/2026-10-30-hybrid-runs.md#why-hybrid-scores-lower))
- **Counts in claims need checking against the run they name.** The 11-abstention figure came from the 3-small baseline, not `e602bd95`. #47 corrected it, listing the same 10 rows from both run files. ([journal](../journal/2026-10-27-answer-eval.md#answer-content-check))

## 3. Week 3 takeaway
Answer evaluation located the loss: most retrieval-side false abstentions have their missing fact at dense rank 6–8. Two ranking changes over dense's candidates were then built with the ACL filter on every path, and measured against bars set before the runs. Both scored below dense, and both were recorded as not adopted rather than tuned on the 32 rows that would score them. The dense configuration from week 2 stands. The open question is now whether the candidates themselves (chunk boundaries, query wording) let any ranker separate the fact chunk.

## 4. Open after week 3
- **Re-test triggers:**
  - hybrid, once the eval set has keyword-heavy questions
  - 3-large@3072, before week 6
  - an HNSW `ef_search` sweep, before any production ANN index
- **No longer triggered:** the self-hosted reranker and the 0.6B/8B Qwen sizes need an adopted reranker. The heading-prefix re-test asked for the reranker in place.
- **Open:**
  - the fixed-512 size and overlap sweep, with context assembly
  - a synthetic retrieval set, because n = 32 can't detect gains of about 0.05
  - the LLM judge for correctness and groundedness, and the 7 `expressible: false` facts
  - the `PERMISSIONS=on|off` spec (Arun)
  - a live decline test of the paid-call hook
