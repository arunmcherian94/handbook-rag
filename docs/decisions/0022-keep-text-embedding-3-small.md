# 0022. Keep text-embedding-3-small: neither 3-large@1536 nor Qwen3-Embedding-8B@1536 passes the 2-paired-SE rule

- **Status:** proposed (2026-10-21; Arun to accept in the spec 0008 PR)
- **Date:** 2026-10-21
- **Journal:** [2026-10-21 embedding comparison](../journal/2026-10-21-embedding-comparison.md)
- **Spec:** [0008](../../specs/0008-embedding-model-comparison.md), AC-9

## Context
- Every run so far uses `openai:text-embedding-3-small` on `fixed-512-64`. The embedding model was the next single change after chunking closed (spec 0006).
- Baseline: run `2026-10-19-d2625d91`, chunk_fact_recall@5 0.495 ± 0.081, n = 32, retrieved tokens@5 2,335.
- Rule set before any run (AC-9): adopt a candidate only if its mean paired delta in chunk_fact_recall at the matched k exceeds 2 paired SEs (sd of per-row deltas / √n).
- Both candidates ran at 1,536 dims, the size of 3-small, so only the model changed. Retrieval-only, eval set v1.2, corpus 5273b21, exact cosine search, query mode per AC-3.

## Results
| candidate | run | recall@5 | matched k | paired delta | paired SE | mean / SE | rows won / lost / tied | embed cost (est.) |
|---|---|---|---|---|---|---|---|---|
| openai:text-embedding-3-large@1536 | `2026-10-21-d83f3edc` | 0.583 ± 0.075 | 5 | +0.088 | 0.045 | **1.97** | 7 / 2 / 23 | $1.36 |
| deepinfra:Qwen/Qwen3-Embedding-8B@1536 | `2026-10-21-c5d62f36` | 0.586 ± 0.082 | 5 | +0.091 | 0.076 | **1.20** | 7 / 2 / 23 | $0.10 |

- Both candidates move every headline metric up. 3-large: chunk_hit@5 +0.125, chunk_mrr +0.123, recall@20 +0.142. Qwen: chunk_all_required@5 +0.094, chunk_ndcg@5 0.456 vs 0.295.
- Both lose the same two rows, 44 and 49, which 3-small gets fully right. On row 49 both new models put `people-group/general-onboarding/tanewki-tips.md` at rank 1. Qwen loses each by a full 1.0, which is why its SE is larger.

## Decision
- **Keep text-embedding-3-small.** Neither candidate clears 2 paired SEs, so the result is "no difference" under AC-9. `DEFAULT_EMBED_MODEL` is unchanged, and the prefix arm (AC-8 step 4) does not run.
- The candidates' vectors stay in `chunk_embeddings` under their own names (44,756 rows), at no cost, for the follow-ups below.

## Consequences
- 3-large missed narrowly (1.97), so the trigger in [follow-ups](../follow-ups.md#from-the-spec-0008-review-2026-10-21) applies: run 3-large@3072, with dims as the one change, before week 6.
- At n = 32, a true gain of about +0.09 in recall is near the edge of what the eval set can detect. The synthetic retrieval set (follow-ups) would decide cases like these with more power.
- If a later run adopts Qwen or another non-OpenAI model, `make ask` needs query mode first (follow-ups).

## Alternatives considered
- **Adopt 3-large on the direction of the evidence:** rejected. That moves the rule after seeing the numbers, which the rule exists to prevent.
- **Adopt Qwen as the cheapest (13× cheaper than 3-large):** rejected. It isn't better than 3-small by the rule, and it adds a second provider and key for no measured gain.
