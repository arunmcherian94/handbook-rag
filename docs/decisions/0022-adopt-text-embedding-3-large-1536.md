# 0022. Adopt text-embedding-3-large@1536 as the default embedding model (departs from the AC-9 rule)

- **Status:** accepted (2026-10-21, PR #31; `DEFAULT_EMBED_MODEL` switched in the follow-up PR). Supersedes the model choice in [ADR-0004](0004-embedding-model-and-schema.md).
- **Date:** 2026-10-21
- **Journal:** [2026-10-21 embedding comparison](../journal/2026-10-21-embedding-comparison.md)
- **Spec:** [0008](../../specs/0008-embedding-model-comparison.md), AC-9

## Context
- Every run so far uses `openai:text-embedding-3-small` on `fixed-512-64`. The embedding model was the next single change after chunking closed (spec 0006).
- Baseline: run `2026-10-19-d2625d91`, chunk_fact_recall@5 0.495 ± 0.081, n = 32, retrieved tokens@5 2,335.
- Rule set before any run (AC-9): adopt a candidate only if its mean paired delta in chunk_fact_recall at the matched k exceeds 2 paired SEs (sd of per-row deltas / √n).
- Both candidates ran at 1,536 dims, the size of 3-small, so only the model changed. Eval set v1.2, corpus 5273b21, exact cosine search, query mode per AC-3.
- Neither passed AC-9 in the retrieval-only runs. Arun then chose to decide on answer quality too, so all three models were run with the answer model (gpt-5.4-mini, k = 5).

## Results
Retrieval-only (vs `2026-10-19-d2625d91`):

| candidate | run | recall@5 | paired delta | paired SE | mean / SE | rows won / lost / tied | embed cost (est.) |
|---|---|---|---|---|---|---|---|
| openai:text-embedding-3-large@1536 | `2026-10-21-d83f3edc` | 0.583 ± 0.075 | +0.088 | 0.045 | **1.97** | 7 / 2 / 23 | $1.36 |
| deepinfra:Qwen/Qwen3-Embedding-8B@1536 | `2026-10-21-c5d62f36` | 0.586 ± 0.082 | +0.091 | 0.076 | **1.20** | 7 / 2 / 23 | $0.10 |

Full answer runs (52 rows, same harness `26808da`, vs `2026-10-21-18f10293`):

| model | run | recall@5 | false abstention (n = 33) | correct ooc abstention (n = 19) | judged vs 3-small (better / worse / tie) |
|---|---|---|---|---|---|
| 3-small | `2026-10-21-18f10293` | 0.495 | 11, 0.333 ± 0.082 | 17 | n/a |
| 3-large@1536 | `2026-10-21-e602bd95` | 0.583 | 10, 0.303 ± 0.080 | 17 | 5 / 2 / 9 |
| Qwen3-8B@1536 | `2026-10-21-9719cae6` | 0.586 | 10, 0.303 ± 0.080 | 15 | 6 / 4 / 6 |

- Paired false abstention vs 3-small: 3-large −0.030 ± 0.053, Qwen −0.030 ± 0.081. Code checks pass on every non-abstaining row for all three.
- Qwen row 47 (France statutory PTO) asserts "20 statutory vacation days", a phrase found in the corpus only on the Belgium page: a wrong-entity hallucination. Qwen row 112 answers "Yes" from a distractor page. 3-small answered no ooc row.
- The judged column is Claude reading the answers against the reference facts (not yet reviewed by Arun): directional, one run per model, no estimate of generator variance.
- 3-large recall@10 +2.42 SE and MRR +2.51 SE (post-hoc). Bootstrap 95% CI for the recall@5 delta: [+0.004, +0.178].

## Decision
- **Adopt `openai:text-embedding-3-large@1536` as `DEFAULT_EMBED_MODEL`.** Every retrieval metric moves up with the lowest variance of the two candidates, and answers show no measured harm and 5 better / 2 worse by judgment.
- On rows 44 and 49 its losses are partial (recall 0.8 and 0.5); Qwen's are total.
- **This departs from AC-9.** 1.97 is under 2. The rule guards against moving the bar after seeing numbers, and this does that. It is Arun's call. At n = 32 the eval cannot reliably detect about +0.09: the claim is "probably better, cheap, reversible", not "proven better".
- Same provider, key, SDK and tokenizer; no `make ask` query-mode prerequisite. The $1.36 re-embed is done and the vectors are stored.
- 3-small vectors stay in `chunk_embeddings`, so switching back is a constant change.

## Consequences
- `DEFAULT_EMBED_MODEL` changed in the follow-up PR.
- permissions-v1 AC-11 re-checked under 3-large: 50 of 52 valid; P-097 and P-098 dropped ([changelog](../eval/CHANGELOG.md)).
- The 3-large@3072 follow-up becomes a dims-only test against the new default.
- Prefix arm (AC-8 step 4) run on 21 Oct, `2026-10-21-586b1635`: +0.031 ± 0.059 (0.51 SE) at k=5, deeper recall down. **Not adopted (Arun): the default stays unprefixed `fixed-512-64`.** Re-test after the week-3 reranker.
- Most false abstention is generator behaviour (rows 49, 100, 58 abstain with full or high recall), so the answer model is the bigger lever (follow-ups: "False abstention", answer-model check).

## Alternatives considered
- **Keep 3-small:** valid under the rule, and the previous text of this ADR. Rejected on the weight of a consistent direction across retrieval and answers, at low cost and with easy reversal.
- **Adopt Qwen:** rejected. Same mean gain, double the variance, an ooc hallucination (row 47), a second provider and key, 4× slower embedding, and `make ask` would need query mode first.
