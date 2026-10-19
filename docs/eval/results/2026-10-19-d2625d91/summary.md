# Eval summary

## Takeaways

- **New comparison baseline for spec 0006.** `fixed-512-64`, retrieval-only, scored to depth 20. Its top 5 match `2026-10-17-3748df5b` on all 33 answerable rows, in order, with no near-ties. The extra depth-20 retrieve didn't change what the model sees, so recall@5 is still 0.495 and page_hit@5 0.812.
- **Depth adds recall:** chunk_fact_recall is 0.495 @5, 0.589 @10 and 0.677 @20. Seven rows (10, 55, 59, 65, 87, 92, 99) find no fact even at 20, so chunking can't fix them; they are for hybrid search and reranking (week 3).
- **Why a new run instead of reusing 3748df5b:** the run metadata gained `eval_depth`, so the old run fails the baseline compatibility check.

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: 21334f046d3d073e3387f6c3c131ad1de47e0868
- harness_dirty: False
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- config_id: fixed-512-64
- chunk_params: {'strategy': 'fixed', 'size': 512, 'overlap': 64, 'tokenizer': 'cl100k_base'}
- embed_model: openai:text-embedding-3-small
- answer_model: None
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- eval_depth: 20
- timestamp: 2026-10-19T14:30:11.673724+00:00
- rows: 33
- mode: retrieval-only
- limit: None

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.058 | 32 |
| chunk_all_required@10 | 0.469 | 0.088 | 32 |
| chunk_all_required@20 | 0.562 | 0.088 | 32 |
| chunk_all_required@3 | 0.312 | 0.082 | 32 |
| chunk_all_required@5 | 0.406 | 0.087 | 32 |
| chunk_fact_recall@1 | 0.177 | 0.061 | 32 |
| chunk_fact_recall@10 | 0.589 | 0.078 | 32 |
| chunk_fact_recall@20 | 0.677 | 0.073 | 32 |
| chunk_fact_recall@3 | 0.417 | 0.078 | 32 |
| chunk_fact_recall@5 | 0.495 | 0.081 | 32 |
| chunk_hit@1 | 0.250 | 0.077 | 32 |
| chunk_hit@10 | 0.688 | 0.082 | 32 |
| chunk_hit@20 | 0.781 | 0.073 | 32 |
| chunk_hit@3 | 0.531 | 0.088 | 32 |
| chunk_hit@5 | 0.594 | 0.087 | 32 |
| chunk_mrr | 0.380 | 0.071 | 32 |
| chunk_ndcg@5 | 0.295 | 0.056 | 32 |
| page_fact_recall@1 | 0.318 | 0.082 | 32 |
| page_fact_recall@10 | 0.761 | 0.071 | 32 |
| page_fact_recall@20 | 0.792 | 0.067 | 32 |
| page_fact_recall@3 | 0.579 | 0.082 | 32 |
| page_fact_recall@5 | 0.641 | 0.076 | 32 |
| page_hit@1 | 0.438 | 0.088 | 32 |
| page_hit@10 | 0.844 | 0.064 | 32 |
| page_hit@20 | 0.875 | 0.058 | 32 |
| page_hit@3 | 0.688 | 0.082 | 32 |
| page_hit@5 | 0.812 | 0.069 | 32 |
| page_mrr | 0.575 | 0.072 | 32 |
| page_ndcg@5 | 0.511 | 0.065 | 32 |
| retrieved_tokens@1 | 444 | 23 | 32 |
| retrieved_tokens@10 | 4639 | 78 | 32 |
| retrieved_tokens@20 | 9441 | 100 | 32 |
| retrieved_tokens@3 | 1396 | 31 | 32 |
| retrieved_tokens@5 | 2335 | 45 | 32 |

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.625 | 0.171 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.500 | 0.177 | 8 |
| chunk_all_required@5 | 0.625 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.750 | 0.134 | 8 |
| chunk_fact_recall@20 | 0.812 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.562 | 0.175 | 8 |
| chunk_fact_recall@5 | 0.688 | 0.162 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.427 | 0.139 | 8 |
| chunk_ndcg@5 | 0.296 | 0.082 | 8 |
| page_fact_recall@1 | 0.357 | 0.175 | 8 |
| page_fact_recall@10 | 0.920 | 0.062 | 8 |
| page_fact_recall@20 | 0.920 | 0.062 | 8 |
| page_fact_recall@3 | 0.670 | 0.158 | 8 |
| page_fact_recall@5 | 0.857 | 0.080 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 1.000 | 0.000 | 8 |
| page_mrr | 0.660 | 0.132 | 8 |
| page_ndcg@5 | 0.594 | 0.104 | 8 |
| retrieved_tokens@1 | 471 | 41 | 8 |
| retrieved_tokens@10 | 4710 | 152 | 8 |
| retrieved_tokens@20 | 9420 | 211 | 8 |
| retrieved_tokens@3 | 1452 | 55 | 8 |
| retrieved_tokens@5 | 2374 | 90 | 8 |

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.375 | 0.171 | 8 |
| chunk_all_required@10 | 0.750 | 0.153 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.625 | 0.171 | 8 |
| chunk_all_required@5 | 0.750 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.375 | 0.183 | 8 |
| chunk_fact_recall@10 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@3 | 0.688 | 0.162 | 8 |
| chunk_fact_recall@5 | 0.750 | 0.164 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.750 | 0.153 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.521 | 0.152 | 8 |
| chunk_ndcg@5 | 0.527 | 0.141 | 8 |
| page_fact_recall@1 | 0.500 | 0.189 | 8 |
| page_fact_recall@10 | 0.750 | 0.164 | 8 |
| page_fact_recall@20 | 0.750 | 0.164 | 8 |
| page_fact_recall@3 | 0.750 | 0.164 | 8 |
| page_fact_recall@5 | 0.750 | 0.164 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.750 | 0.153 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.688 | 0.162 | 8 |
| page_ndcg@5 | 0.675 | 0.155 | 8 |
| retrieved_tokens@1 | 428 | 50 | 8 |
| retrieved_tokens@10 | 4559 | 166 | 8 |
| retrieved_tokens@20 | 9406 | 248 | 8 |
| retrieved_tokens@3 | 1343 | 72 | 8 |
| retrieved_tokens@5 | 2367 | 72 | 8 |

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.375 | 0.171 | 8 |
| chunk_all_required@20 | 0.500 | 0.177 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.062 | 0.062 | 8 |
| chunk_fact_recall@10 | 0.458 | 0.177 | 8 |
| chunk_fact_recall@20 | 0.646 | 0.156 | 8 |
| chunk_fact_recall@3 | 0.229 | 0.130 | 8 |
| chunk_fact_recall@5 | 0.354 | 0.156 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.500 | 0.177 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.500 | 0.177 | 8 |
| chunk_mrr | 0.260 | 0.125 | 8 |
| chunk_ndcg@5 | 0.181 | 0.093 | 8 |
| page_fact_recall@1 | 0.125 | 0.125 | 8 |
| page_fact_recall@10 | 0.688 | 0.162 | 8 |
| page_fact_recall@20 | 0.688 | 0.162 | 8 |
| page_fact_recall@3 | 0.479 | 0.165 | 8 |
| page_fact_recall@5 | 0.479 | 0.165 | 8 |
| page_hit@1 | 0.125 | 0.117 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.750 | 0.153 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.365 | 0.113 | 8 |
| page_ndcg@5 | 0.312 | 0.111 | 8 |
| retrieved_tokens@1 | 409 | 57 | 8 |
| retrieved_tokens@10 | 4700 | 137 | 8 |
| retrieved_tokens@20 | 9386 | 137 | 8 |
| retrieved_tokens@3 | 1376 | 70 | 8 |
| retrieved_tokens@5 | 2279 | 90 | 8 |

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.125 | 0.117 | 8 |
| chunk_all_required@20 | 0.250 | 0.153 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@1 | 0.083 | 0.055 | 8 |
| chunk_fact_recall@10 | 0.396 | 0.130 | 8 |
| chunk_fact_recall@20 | 0.500 | 0.134 | 8 |
| chunk_fact_recall@3 | 0.188 | 0.097 | 8 |
| chunk_fact_recall@5 | 0.188 | 0.097 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.375 | 0.171 | 8 |
| chunk_mrr | 0.312 | 0.162 | 8 |
| chunk_ndcg@5 | 0.177 | 0.094 | 8 |
| page_fact_recall@1 | 0.292 | 0.160 | 8 |
| page_fact_recall@10 | 0.688 | 0.162 | 8 |
| page_fact_recall@20 | 0.812 | 0.132 | 8 |
| page_fact_recall@3 | 0.417 | 0.175 | 8 |
| page_fact_recall@5 | 0.479 | 0.165 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.588 | 0.165 | 8 |
| page_ndcg@5 | 0.466 | 0.132 | 8 |
| retrieved_tokens@1 | 467 | 40 | 8 |
| retrieved_tokens@10 | 4586 | 186 | 8 |
| retrieved_tokens@20 | 9553 | 219 | 8 |
| retrieved_tokens@3 | 1414 | 57 | 8 |
| retrieved_tokens@5 | 2320 | 114 | 8 |

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.500 | 0.177 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.583 | 0.175 | 8 |
| chunk_fact_recall@20 | 0.771 | 0.130 | 8 |
| chunk_fact_recall@3 | 0.417 | 0.175 | 8 |
| chunk_fact_recall@5 | 0.542 | 0.177 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.385 | 0.149 | 8 |
| chunk_ndcg@5 | 0.280 | 0.103 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@10 | 0.812 | 0.132 | 8 |
| page_fact_recall@20 | 0.812 | 0.132 | 8 |
| page_fact_recall@3 | 0.479 | 0.165 | 8 |
| page_fact_recall@5 | 0.604 | 0.160 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.542 | 0.143 | 8 |
| page_ndcg@5 | 0.513 | 0.129 | 8 |
| retrieved_tokens@1 | 402 | 60 | 8 |
| retrieved_tokens@10 | 4610 | 162 | 8 |
| retrieved_tokens@20 | 9307 | 178 | 8 |
| retrieved_tokens@3 | 1327 | 70 | 8 |
| retrieved_tokens@5 | 2224 | 101 | 8 |

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.062 | 0.062 | 8 |
| chunk_fact_recall@10 | 0.625 | 0.157 | 8 |
| chunk_fact_recall@20 | 0.688 | 0.162 | 8 |
| chunk_fact_recall@3 | 0.375 | 0.157 | 8 |
| chunk_fact_recall@5 | 0.500 | 0.164 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.302 | 0.120 | 8 |
| chunk_ndcg@5 | 0.197 | 0.071 | 8 |
| page_fact_recall@1 | 0.232 | 0.153 | 8 |
| page_fact_recall@10 | 0.795 | 0.129 | 8 |
| page_fact_recall@20 | 0.795 | 0.129 | 8 |
| page_fact_recall@3 | 0.670 | 0.158 | 8 |
| page_fact_recall@5 | 0.732 | 0.130 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.483 | 0.126 | 8 |
| page_ndcg@5 | 0.393 | 0.105 | 8 |
| retrieved_tokens@1 | 477 | 35 | 8 |
| retrieved_tokens@10 | 4801 | 115 | 8 |
| retrieved_tokens@20 | 9499 | 171 | 8 |
| retrieved_tokens@3 | 1501 | 35 | 8 |
| retrieved_tokens@5 | 2428 | 60 | 8 |

## Lists

- page_hit_no_chunk: 52, 53, 8, 10, 99, 38, 89
- conflict_unscored: 53, 50, 58
- near_ties: none

## answer_only_facts

- row 58 F1
- row 22 F1

## no_retrieval_facts

- 22

## evidence_warnings

none
