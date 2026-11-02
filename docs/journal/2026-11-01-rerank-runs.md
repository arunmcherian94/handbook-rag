# 2026-11-01: cross-encoder reranker runs, spec 0012

The two measurement runs from the [spec 0012 build](2026-10-31-rerank-build.md) (#53), and the decision under the rule fixed before the runs: the reranker is not adopted.

## Runs
Both runs are at harness `aba4828` (#53 merged), config `fixed-512-64`, 3-large@1536, `Qwen/Qwen3-Reranker-4B` over the dense top 50, retrieval-only, admin for the eval.

| run | retriever | run ID | dry-run estimate |
|---|---|---|---|
| eval vs `2026-10-21-d83f3edc` | rerank | `2026-11-01-d5286816` | $0.0250 |
| permissions-v1 | rerank | `2026-11-01-afb31160` | $0.0594 |

- **Truncation share:** 0.000 in both runs. The longest pair was ~938 (eval) and ~933 (permissions) of 32,768 tokens on the cl100k × 1.5 estimate.
- **Provider tokens:** 930,422 input tokens for the eval, 563.9 per pair, against the dry run's ~998,500 estimate.

## Paired comparison within the run (AC-11, primary; n = 32)
- **chunk_fact_recall@5, reranked − dense top 5:** −0.041, paired SE 0.058, −0.70 SE.
- **Rows:** won 3, lost 6, tied 23.
  - Won: 52 (0 → 0.5), 53 (0 → 1), 8 (0.5 → 1).
  - Lost: 44 (0.8 → 0), 49, 35, 89 (each 0.5 → 0), 58, 23 (each 1 → 0.5).
- **Headroom captured (headline, fixed):** −0.139 = (0.542 − 0.583) / (0.875 − 0.583).
- **Headroom within this run:** −0.139. This run's dense@5 is 0.583 and its ceiling 0.875, both the same as `d83f3edc`, so the two figures agree and show no query-vector drift on this metric.

### recall@k, both orderings (AC-10)

| k | dense | rerank |
|---|---|---|
| 3 | 0.510 | 0.458 |
| 4 | 0.552 | 0.484 |
| 5 | 0.583 | 0.542 |
| 6 | 0.651 | 0.567 |
| 7 | 0.682 | 0.578 |
| 8 | 0.744 | 0.609 |
| 9 | 0.744 | 0.640 |
| 10 | 0.744 | 0.664 |

Rerank is below dense at every k from 3 to 10.

### The targeted rows (spec 0010's rank 6–8 misses)

| row | fact | dense rank | rerank rank | in top 5 (dense → rerank) |
|---|---|---|---|---|
| 8 | F1 | 6 | 5 | no → yes |
| 8 | F4 | 2 | 1 | yes → yes |
| 53 | F1 | 6 | 1 | no → yes |
| 49 | F1 | 8 | 15 | no → no |
| 49 | F4 | 3 | 10 | yes → no |
| 55 | F1 | 8 | 38 | no → no |
| 89 | F2 | 5 | 34 | yes → no |
| 89 | F4 | 8 | 40 | no → no |

Two of the five rows gain (8, 53). Rows 49 and 89 lose a fact they had at dense rank 3 or 5, and row 55's fact falls from rank 8 to 38.

### Latency
Rerank p50 / p95: 4,154 / 5,489 ms per query, against an in-run dense search p50 of 337 ms. The rerank figure is an API round trip for 50 pairs, not local compute.

## Continuity comparison (AC-12)
Against `2026-10-21-d83f3edc`: chunk_fact_recall@5 −0.041, paired SE 0.058, −0.70 SE. The figures match the in-run comparison because this run's dense top 5 gives the same chunk_fact_recall@5 as `d83f3edc` on all 32 scored rows (recomputed from `rows.jsonl`). `d83f3edc` embedded its questions separately (the row 32 and 93 drift), so the decision rests on the in-run comparison. Other changes against `d83f3edc`: chunk_mrr −0.016, chunk_fact_recall@10 −0.081, page_hit@5 +0.031, page_mrr +0.051.

## Permissions (rerank vs dense `086eca8a`)
- **Leak** is 0 at k = 5 and k = 20. **Over-block** is 0 at both.
- **Authorized recall:** 0.958 @5 and 0.976 @20 (n = 28), against dense's 0.878 and 1.000 (n = 26).
- **Not paired as reported:** validity is computed per retriever. On rerank, P-097 and P-098 (cut-row targets, stored invalid) become valid, so 52 cases score instead of 50, and both score 1.0.
- **Same 26 cases:** @5, dense 0.878 against rerank 0.955; P-038 and P-042 go 0 → 1. @20, dense 1.000 against rerank 0.974; P-087 goes 1 → 0.333.

## Why the reranker scores lower
From the run's saved candidate lists (dense rank, rerank rank and score for all 50 candidates per row) and the chunk text in Postgres. No extra calls. Strongest evidence first:

1. **It doesn't separate the fact chunk from its on-topic neighbours.**
   - The dense top 50 is already on topic, and the reranker rates many of those chunks as fully relevant. On 8 of 32 rows, 5 or more candidates score ≥ 0.99.
   - 14 fact chunks fell out of the dense top 5. Seven of them scored ≥ 0.9 and lost to a slightly higher score: row 44's chunk with F2–F5 scored 0.998 against a fifth place of 0.999, row 35 0.981 against 0.992, row 49 0.944 against 0.979. Rows 23, 34 and 58 are the same pattern.
   - Across all 71 fact chunks in the dense top 50, 28 moved up and 33 moved down; the median rank went from 6 to 8. Fact-bearing top-5 slots fell from 35 to 30 of 160.
2. **It scores some fact chunks as irrelevant.**
   - Four of the 14 scored below 0.1 (rows 89, 93, and 100 twice). Three scored 0.25–0.69 (rows 9, 11, 99).
   - Row 89, "whats our exit policy": all 50 candidates score ≤ 0.056, so the reranker found nothing it judged relevant and its order carries little signal. Dense had the offboarding chunks at ranks 5 and 8; reranked, they fall to 34 and 40. The F2 chunk opens with the general "Offboarding Overview" text, and the fact comes later in the window.
   - Row 55, "Who leads Customer Success these days?": F1 is one name in a table of executive assistants (score 0.039, rank 8 → 38).
   - Both are consistent with the fixed 512-token windows mixing the fact with other text, and with colloquial questions. Neither cause is tested here.
3. **Some wins aren't credited.** chunk_fact_recall counts required facts only. On row 55, the reranked #1 is the "CS Leadership" table naming Sherrod Patching (optional F2, dense rank 27), so the reranked top 5 names the leader and still scores 0. This is one row and doesn't change the result.

What this suggests for later, untested: a reranker over this candidate pool needs chunks that carry one topic (the week-4 chunking work) or clearer queries (query understanding) before it can pick the fact chunk out of an on-topic pool. The 0.875 ceiling counts what the dense top 50 holds, not what a reranker can separate.

## Decision: reranker not adopted (pre-set rule, 1 Nov)
The rule was fixed before the runs: adopt at ≥ +2 paired SE with leak and over-block 0; between 1 and 2 SE, not adopted with a re-test noted; below 1 SE, not adopted. The in-run paired delta is −0.70 SE, so the reranker is not adopted. Leak and over-block are 0, so the permissions result doesn't change the outcome.

- `DEFAULT_RETRIEVER` stays `"dense"`, and `ask.py` and the answer path are unchanged. ADR-0023 is not written.
- `--retriever rerank` stays as a measurement flag.
- Follow-ups that waited on the reranker don't fire: the self-hosted reranker and the 0.6B/8B sizes need an adopted reranker, and the heading-path prefix re-test asked for the reranker in place ([follow-ups](../follow-ups.md)).

## Caveats
- **The "why" is descriptive:** it reads the rank and score patterns of one run. No variant (instruction, depth, chunking) was run to test a cause.
- **n = 32:** one eval set, one model, one instruction (the model card's default, written for web search), depth 50.
