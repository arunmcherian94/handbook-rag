# 0013. Chunk-level fact recall@k is the headline retrieval metric

- **Status:** accepted
- **Date:** 2026-10-16
- **Journal:** [2026-10-16 eval metric decisions](../journal/2026-10-16-eval-metric-decisions.md)

## Context
Earlier plan (2026-10-16, superseded 2026-10-16), spec 0004 inputs from the review: the pages behind `[required]` facts are the must-retrieve set (recall as a fraction); other expected docs are acceptable alternates (any hit). Replaced by: recall counts required facts, any cited source satisfies; markers on every row in v1.2. See spec 0004.

Custom vs textbook metrics: a fresh research agent found no standard for retrieval evals when chunking changes. The closest common advice is span labels fixed across chunkings (Chroma) and recall over reference facts (RAGAS and DeepEval, via an LLM). That's what we do, from labels. Textbook chunk recall is rejected: overlap and alternative pages inflate the denominator, and it shifts with chunking.

## Decision
- **Q1 binary relevance:** v1.1 has no relevance grades. nDCG@5 uses binary gains, stated as such. Graded nDCG from the required/alternate page tiers is a follow-up.
- **Q2 k = 1, 3, 5:** all 5 chunks go to the model, so @5 measures whether the answer could be reached and nothing above 5 means anything. @1 and @3 show ranking headroom for reranking (week 3) and for a smaller k. Reported with MRR, since recall@5 alone hides ranking (Pinecone).
- **Q3 chunk level is the headline.** A chunk counts as relevant if it contains a cited evidence line, so labels survive chunking changes in week 2. The headline metric is **fact recall@k** (required facts covered ÷ required facts), plus all-required@k. hit, MRR and nDCG count only chunks relevant to a required fact. Page level is reported as a diagnostic: page hit with chunk miss = a chunking problem (6 of 10 seed traces). At page level a page counts once, at its best rank.
- **Not reported:** precision@k (few expected pages: 26 of 33 rows have 1–2, and unlabelled relevant pages would count as misses) and MAP@k (identical to MRR for one page; nDCG covers several). Revisit precision if noisy context shows up as a failure mode.
- **Retrieved tokens are reported, because bigger chunks raise recall by covering more text.**
- **`retrieved_tokens@k`:** the total tokens in the top k chunks, averaged over rows. This is the quantity an equal-token-budget comparison needs. Per-chunk mean tokens would just be the chunk size.

## Consequences
- **Noise:** 33 answerable rows means one row is about 3 points. Spec 0004 reports a standard error next to each rate.
- The relevance rule for "contains a cited evidence line" was later loosened; see [0015](0015-span-overlap-relevance.md).
- Follow-ups (week 2): token precision/IoU when chunk size changes (Chroma); comparing chunkings at an equal retrieved-token budget.

## Informed by
- [Pinecone, Evaluation Measures in Information Retrieval](../reading/week-01.md#pinecone-evaluation-measures-in-information-retrieval)
- [Research: RAG retrieval metrics when chunking changes (fresh research agent)](../reading/week-01.md#research-rag-retrieval-metrics-when-chunking-changes-fresh-research-agent)
