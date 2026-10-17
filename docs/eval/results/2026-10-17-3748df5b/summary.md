# Eval summary

## Takeaways

Baseline (week 1). LLM-drafted, human-reviewed in PR #17.

**Previous fixes:** none (first run).

**Improve next:**
- **Chunk retrieval.** The right page is in the top 5 for 81% of rows but the right chunk only for 59%; half the required facts are reachable at k=5 (chunk_fact_recall@5 0.50). Seven rows hit the page and miss every relevant chunk (page_hit_no_chunk), which points at chunk boundaries and ranking rather than missing pages. Check: chunk_fact_recall@5 and the page_hit_no_chunk list shrink.
- **Synthesis.** No synthesis row gets all its required facts into the top 5 (0/8). The facts span sections and k=5 doesn't reach them. Check: synthesis chunk_all_required@5 rises above 0.
- **Recency.** Fact recall@5 is 0.35, because chunks carry no dates, so old and new sources rank alike. Check: recency chunk_fact_recall@5, in both history-only and in-page rows.
- **False abstention.** The model refuses 39% of answerable rows, which is more than retrieval misses alone explain. Code each one first (evidence in context or not); the answer-model check depends on that and must happen before the week 3 freeze. Check: false_abstention falls without ooc_pass dropping.

**Holding:** 17/19 out-of-corpus rows pass, and both misses still declined, just with the other fixed string. 19/20 answers pass every code check; the one failure is a missing citation.

**Caveat:** n = 8 per type (SE about ±0.15), so treat differences between types as directional only.

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: 76b3fceea4946b5096cdcb145cc487c8fcb4ddcb
- harness_dirty: False
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- chunk_params: {'chunk_size': 512, 'chunk_overlap': 64, 'tokenizer': 'cl100k_base'}
- embed_model: openai:text-embedding-3-small
- answer_model: openai:gpt-5.4-mini
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- timestamp: 2026-10-17T07:20:58.955684+00:00
- rows: 52
- mode: full
- limit: None

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.058 | 32 |
| chunk_all_required@3 | 0.312 | 0.082 | 32 |
| chunk_all_required@5 | 0.406 | 0.087 | 32 |
| chunk_fact_recall@1 | 0.177 | 0.061 | 32 |
| chunk_fact_recall@3 | 0.417 | 0.078 | 32 |
| chunk_fact_recall@5 | 0.495 | 0.081 | 32 |
| chunk_hit@1 | 0.250 | 0.077 | 32 |
| chunk_hit@3 | 0.531 | 0.088 | 32 |
| chunk_hit@5 | 0.594 | 0.087 | 32 |
| chunk_mrr | 0.380 | 0.071 | 32 |
| chunk_ndcg@5 | 0.295 | 0.056 | 32 |
| page_fact_recall@1 | 0.318 | 0.082 | 32 |
| page_fact_recall@3 | 0.579 | 0.082 | 32 |
| page_fact_recall@5 | 0.641 | 0.076 | 32 |
| page_hit@1 | 0.438 | 0.088 | 32 |
| page_hit@3 | 0.688 | 0.082 | 32 |
| page_hit@5 | 0.812 | 0.069 | 32 |
| page_mrr | 0.575 | 0.072 | 32 |
| page_ndcg@5 | 0.511 | 0.065 | 32 |
| retrieved_tokens@1 | 444 | 23 | 32 |
| retrieved_tokens@3 | 1396 | 31 | 32 |
| retrieved_tokens@5 | 2335 | 45 | 32 |
| ooc_pass | 0.895 | 0.070 | 19 |
| false_abstention | 0.394 | 0.085 | 33 |
| code_checks_passed | 0.950 | 0.049 | 20 |
| has_citation | 0.950 | 0.049 | 20 |
| citations_in_range | 1.000 | 0.000 | 20 |
| headings_exist | 1.000 | 0.000 | 20 |
| no_url | 1.000 | 0.000 | 20 |
| truncated | 0.000 | 0.000 | 52 |

Abstention labels: wrong-string 2

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@3 | 0.500 | 0.177 | 8 |
| chunk_all_required@5 | 0.625 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.562 | 0.175 | 8 |
| chunk_fact_recall@5 | 0.688 | 0.162 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.427 | 0.139 | 8 |
| chunk_ndcg@5 | 0.296 | 0.082 | 8 |
| page_fact_recall@1 | 0.357 | 0.175 | 8 |
| page_fact_recall@3 | 0.670 | 0.158 | 8 |
| page_fact_recall@5 | 0.857 | 0.080 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 1.000 | 0.000 | 8 |
| page_mrr | 0.660 | 0.132 | 8 |
| page_ndcg@5 | 0.594 | 0.104 | 8 |
| retrieved_tokens@1 | 471 | 41 | 8 |
| retrieved_tokens@3 | 1452 | 55 | 8 |
| retrieved_tokens@5 | 2374 | 90 | 8 |
| false_abstention | 0.375 | 0.171 | 8 |
| code_checks_passed | 1.000 | 0.000 | 5 |
| has_citation | 1.000 | 0.000 | 5 |
| citations_in_range | 1.000 | 0.000 | 5 |
| headings_exist | 1.000 | 0.000 | 5 |
| no_url | 1.000 | 0.000 | 5 |
| truncated | 0.000 | 0.000 | 8 |

Abstention labels: none

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.375 | 0.171 | 8 |
| chunk_all_required@3 | 0.625 | 0.171 | 8 |
| chunk_all_required@5 | 0.750 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.375 | 0.183 | 8 |
| chunk_fact_recall@3 | 0.688 | 0.162 | 8 |
| chunk_fact_recall@5 | 0.750 | 0.164 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@3 | 0.750 | 0.153 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.521 | 0.152 | 8 |
| chunk_ndcg@5 | 0.527 | 0.141 | 8 |
| page_fact_recall@1 | 0.500 | 0.189 | 8 |
| page_fact_recall@3 | 0.750 | 0.164 | 8 |
| page_fact_recall@5 | 0.750 | 0.164 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.688 | 0.162 | 8 |
| page_ndcg@5 | 0.675 | 0.155 | 8 |
| retrieved_tokens@1 | 428 | 50 | 8 |
| retrieved_tokens@3 | 1343 | 72 | 8 |
| retrieved_tokens@5 | 2367 | 72 | 8 |
| false_abstention | 0.444 | 0.166 | 9 |
| code_checks_passed | 1.000 | 0.000 | 5 |
| has_citation | 1.000 | 0.000 | 5 |
| citations_in_range | 1.000 | 0.000 | 5 |
| headings_exist | 1.000 | 0.000 | 5 |
| no_url | 1.000 | 0.000 | 5 |
| truncated | 0.000 | 0.000 | 9 |

Abstention labels: none

## by_type: ooc-in-scope

| metric | mean | ± SE | n |
|---|---|---|---|
| ooc_pass | 0.900 | 0.095 | 10 |
| truncated | 0.000 | 0.000 | 10 |

Abstention labels: wrong-string 1

## by_type: ooc-off-topic

| metric | mean | ± SE | n |
|---|---|---|---|
| ooc_pass | 0.889 | 0.105 | 9 |
| truncated | 0.000 | 0.000 | 9 |

Abstention labels: wrong-string 1

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.062 | 0.062 | 8 |
| chunk_fact_recall@3 | 0.229 | 0.130 | 8 |
| chunk_fact_recall@5 | 0.354 | 0.156 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.500 | 0.177 | 8 |
| chunk_mrr | 0.260 | 0.125 | 8 |
| chunk_ndcg@5 | 0.181 | 0.093 | 8 |
| page_fact_recall@1 | 0.125 | 0.125 | 8 |
| page_fact_recall@3 | 0.479 | 0.165 | 8 |
| page_fact_recall@5 | 0.479 | 0.165 | 8 |
| page_hit@1 | 0.125 | 0.117 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.365 | 0.113 | 8 |
| page_ndcg@5 | 0.312 | 0.111 | 8 |
| retrieved_tokens@1 | 409 | 57 | 8 |
| retrieved_tokens@3 | 1376 | 70 | 8 |
| retrieved_tokens@5 | 2279 | 90 | 8 |
| false_abstention | 0.250 | 0.153 | 8 |
| code_checks_passed | 0.833 | 0.152 | 6 |
| has_citation | 0.833 | 0.152 | 6 |
| citations_in_range | 1.000 | 0.000 | 6 |
| headings_exist | 1.000 | 0.000 | 6 |
| no_url | 1.000 | 0.000 | 6 |
| truncated | 0.000 | 0.000 | 8 |

Abstention labels: none

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@1 | 0.083 | 0.055 | 8 |
| chunk_fact_recall@3 | 0.188 | 0.097 | 8 |
| chunk_fact_recall@5 | 0.188 | 0.097 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.375 | 0.171 | 8 |
| chunk_mrr | 0.312 | 0.162 | 8 |
| chunk_ndcg@5 | 0.177 | 0.094 | 8 |
| page_fact_recall@1 | 0.292 | 0.160 | 8 |
| page_fact_recall@3 | 0.417 | 0.175 | 8 |
| page_fact_recall@5 | 0.479 | 0.165 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.588 | 0.165 | 8 |
| page_ndcg@5 | 0.466 | 0.132 | 8 |
| retrieved_tokens@1 | 467 | 40 | 8 |
| retrieved_tokens@3 | 1414 | 57 | 8 |
| retrieved_tokens@5 | 2320 | 114 | 8 |
| false_abstention | 0.500 | 0.177 | 8 |
| code_checks_passed | 1.000 | 0.000 | 4 |
| has_citation | 1.000 | 0.000 | 4 |
| citations_in_range | 1.000 | 0.000 | 4 |
| headings_exist | 1.000 | 0.000 | 4 |
| no_url | 1.000 | 0.000 | 4 |
| truncated | 0.000 | 0.000 | 8 |

Abstention labels: none

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.500 | 0.177 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.417 | 0.175 | 8 |
| chunk_fact_recall@5 | 0.542 | 0.177 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.385 | 0.149 | 8 |
| chunk_ndcg@5 | 0.280 | 0.103 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@3 | 0.479 | 0.165 | 8 |
| page_fact_recall@5 | 0.604 | 0.160 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.542 | 0.143 | 8 |
| page_ndcg@5 | 0.513 | 0.129 | 8 |
| retrieved_tokens@1 | 402 | 60 | 8 |
| retrieved_tokens@3 | 1327 | 70 | 8 |
| retrieved_tokens@5 | 2224 | 101 | 8 |
| false_abstention | 0.250 | 0.153 | 8 |
| code_checks_passed | 0.833 | 0.152 | 6 |
| has_citation | 0.833 | 0.152 | 6 |
| citations_in_range | 1.000 | 0.000 | 6 |
| headings_exist | 1.000 | 0.000 | 6 |
| no_url | 1.000 | 0.000 | 6 |
| truncated | 0.000 | 0.000 | 8 |

Abstention labels: none

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.062 | 0.062 | 8 |
| chunk_fact_recall@3 | 0.375 | 0.157 | 8 |
| chunk_fact_recall@5 | 0.500 | 0.164 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.302 | 0.120 | 8 |
| chunk_ndcg@5 | 0.197 | 0.071 | 8 |
| page_fact_recall@1 | 0.232 | 0.153 | 8 |
| page_fact_recall@3 | 0.670 | 0.158 | 8 |
| page_fact_recall@5 | 0.732 | 0.130 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.483 | 0.126 | 8 |
| page_ndcg@5 | 0.393 | 0.105 | 8 |
| retrieved_tokens@1 | 477 | 35 | 8 |
| retrieved_tokens@3 | 1501 | 35 | 8 |
| retrieved_tokens@5 | 2428 | 60 | 8 |
| false_abstention | 0.375 | 0.171 | 8 |
| code_checks_passed | 1.000 | 0.000 | 5 |
| has_citation | 1.000 | 0.000 | 5 |
| citations_in_range | 1.000 | 0.000 | 5 |
| headings_exist | 1.000 | 0.000 | 5 |
| no_url | 1.000 | 0.000 | 5 |
| truncated | 0.000 | 0.000 | 8 |

Abstention labels: none

## Lists

- page_hit_no_chunk: 52, 53, 8, 10, 99, 38, 89
- conflict_unscored: 53, 50, 58

## answer_only_facts

- row 58 F1
- row 22 F1

## no_retrieval_facts

- 22

## evidence_warnings

none
