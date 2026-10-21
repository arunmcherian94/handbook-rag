# Eval summary

## Takeaways

- **Retrieval-only, 3-large@1536 vs baseline `2026-10-19-d2625d91`.** recall@5 0.583 against 0.495: paired +0.088 ± 0.045, mean/SE 1.97, just under the AC-9 bar of 2. Rows: 7 won (10, 8, 58, 89, 99, 11, 34), 2 lost (49 −0.5, 44 −0.2), 23 tied.
- **Provenance:** `harness_dirty: True` with `harness_sha` ca41978 because the run started before the build was committed. The tree that ran is commit `6095a08` (files last changed 13:21 IST, run at 13:37 IST, nothing uncommitted afterwards). Not re-run: retrieval is exact search. See the [journal](../../../journal/2026-10-21-embedding-comparison.md).
- **Next:** this run never called the answer model. The full answer run is `2026-10-21-e602bd95`; the decision is in ADR-0022.

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: ca41978e09aa096f7650a511aa32183cd35eb229
- harness_dirty: True
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- config_id: fixed-512-64
- chunk_params: {'strategy': 'fixed', 'size': 512, 'overlap': 64, 'tokenizer': 'cl100k_base'}
- embed_model: openai:text-embedding-3-large@1536
- answer_model: None
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- eval_depth: 20
- timestamp: 2026-10-21T08:07:23.287713+00:00
- rows: 33
- mode: retrieval-only
- limit: None
- baseline: 2026-10-19-d2625d91
- baseline_change: embed model

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.188 | 0.069 | 32 |
| chunk_all_required@10 | 0.625 | 0.086 | 32 |
| chunk_all_required@20 | 0.719 | 0.079 | 32 |
| chunk_all_required@3 | 0.312 | 0.082 | 32 |
| chunk_all_required@5 | 0.406 | 0.087 | 32 |
| chunk_fact_recall@1 | 0.271 | 0.070 | 32 |
| chunk_fact_recall@10 | 0.744 | 0.070 | 32 |
| chunk_fact_recall@20 | 0.819 | 0.061 | 32 |
| chunk_fact_recall@3 | 0.510 | 0.075 | 32 |
| chunk_fact_recall@5 | 0.583 | 0.075 | 32 |
| chunk_hit@1 | 0.375 | 0.086 | 32 |
| chunk_hit@10 | 0.812 | 0.069 | 32 |
| chunk_hit@20 | 0.875 | 0.058 | 32 |
| chunk_hit@3 | 0.656 | 0.084 | 32 |
| chunk_hit@5 | 0.719 | 0.079 | 32 |
| chunk_mrr | 0.504 | 0.075 | 32 |
| chunk_ndcg@5 | 0.397 | 0.058 | 32 |
| page_fact_recall@1 | 0.401 | 0.085 | 32 |
| page_fact_recall@10 | 0.849 | 0.056 | 32 |
| page_fact_recall@20 | 0.869 | 0.055 | 32 |
| page_fact_recall@3 | 0.661 | 0.075 | 32 |
| page_fact_recall@5 | 0.692 | 0.073 | 32 |
| page_hit@1 | 0.469 | 0.088 | 32 |
| page_hit@10 | 0.938 | 0.043 | 32 |
| page_hit@20 | 0.938 | 0.043 | 32 |
| page_hit@3 | 0.812 | 0.069 | 32 |
| page_hit@5 | 0.844 | 0.064 | 32 |
| page_mrr | 0.622 | 0.069 | 32 |
| page_ndcg@5 | 0.564 | 0.066 | 32 |
| retrieved_tokens@1 | 445 | 22 | 32 |
| retrieved_tokens@10 | 4679 | 82 | 32 |
| retrieved_tokens@20 | 9406 | 126 | 32 |
| retrieved_tokens@3 | 1418 | 36 | 32 |
| retrieved_tokens@5 | 2344 | 51 | 32 |

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.625 | 0.171 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.895 | 0.063 | 8 |
| chunk_fact_recall@20 | 0.912 | 0.064 | 8 |
| chunk_fact_recall@3 | 0.770 | 0.083 | 8 |
| chunk_fact_recall@5 | 0.770 | 0.083 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 1.000 | 0.000 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 1.000 | 0.000 | 8 |
| chunk_hit@5 | 1.000 | 0.000 | 8 |
| chunk_mrr | 0.562 | 0.099 | 8 |
| chunk_ndcg@5 | 0.444 | 0.060 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@10 | 0.895 | 0.063 | 8 |
| page_fact_recall@20 | 0.912 | 0.064 | 8 |
| page_fact_recall@3 | 0.770 | 0.083 | 8 |
| page_fact_recall@5 | 0.770 | 0.083 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 1.000 | 0.000 | 8 |
| page_hit@5 | 1.000 | 0.000 | 8 |
| page_mrr | 0.625 | 0.112 | 8 |
| page_ndcg@5 | 0.557 | 0.110 | 8 |
| retrieved_tokens@1 | 471 | 41 | 8 |
| retrieved_tokens@10 | 4630 | 217 | 8 |
| retrieved_tokens@20 | 9376 | 250 | 8 |
| retrieved_tokens@3 | 1452 | 55 | 8 |
| retrieved_tokens@5 | 2336 | 130 | 8 |

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.500 | 0.177 | 8 |
| chunk_all_required@10 | 0.750 | 0.153 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.500 | 0.177 | 8 |
| chunk_all_required@5 | 0.750 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.500 | 0.189 | 8 |
| chunk_fact_recall@10 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@3 | 0.562 | 0.175 | 8 |
| chunk_fact_recall@5 | 0.750 | 0.164 | 8 |
| chunk_hit@1 | 0.500 | 0.177 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.573 | 0.166 | 8 |
| chunk_ndcg@5 | 0.538 | 0.148 | 8 |
| page_fact_recall@1 | 0.625 | 0.183 | 8 |
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
| page_ndcg@5 | 0.685 | 0.162 | 8 |
| retrieved_tokens@1 | 502 | 10 | 8 |
| retrieved_tokens@10 | 4663 | 173 | 8 |
| retrieved_tokens@20 | 9308 | 250 | 8 |
| retrieved_tokens@3 | 1489 | 37 | 8 |
| retrieved_tokens@5 | 2362 | 90 | 8 |

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.750 | 0.153 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.250 | 0.134 | 8 |
| chunk_fact_recall@10 | 0.833 | 0.126 | 8 |
| chunk_fact_recall@20 | 0.896 | 0.070 | 8 |
| chunk_fact_recall@3 | 0.458 | 0.177 | 8 |
| chunk_fact_recall@5 | 0.458 | 0.177 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.500 | 0.177 | 8 |
| chunk_mrr | 0.438 | 0.175 | 8 |
| chunk_ndcg@5 | 0.298 | 0.119 | 8 |
| page_fact_recall@1 | 0.375 | 0.183 | 8 |
| page_fact_recall@10 | 0.938 | 0.062 | 8 |
| page_fact_recall@20 | 0.938 | 0.062 | 8 |
| page_fact_recall@3 | 0.562 | 0.175 | 8 |
| page_fact_recall@5 | 0.562 | 0.175 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.625 | 0.171 | 8 |
| page_mrr | 0.500 | 0.164 | 8 |
| page_ndcg@5 | 0.395 | 0.132 | 8 |
| retrieved_tokens@1 | 374 | 53 | 8 |
| retrieved_tokens@10 | 4642 | 117 | 8 |
| retrieved_tokens@20 | 9342 | 309 | 8 |
| retrieved_tokens@3 | 1314 | 92 | 8 |
| retrieved_tokens@5 | 2274 | 108 | 8 |

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.375 | 0.171 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.146 | 0.073 | 8 |
| chunk_fact_recall@10 | 0.500 | 0.164 | 8 |
| chunk_fact_recall@20 | 0.719 | 0.160 | 8 |
| chunk_fact_recall@3 | 0.250 | 0.100 | 8 |
| chunk_fact_recall@5 | 0.354 | 0.124 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.442 | 0.169 | 8 |
| chunk_ndcg@5 | 0.309 | 0.121 | 8 |
| page_fact_recall@1 | 0.354 | 0.156 | 8 |
| page_fact_recall@10 | 0.812 | 0.132 | 8 |
| page_fact_recall@20 | 0.875 | 0.125 | 8 |
| page_fact_recall@3 | 0.562 | 0.175 | 8 |
| page_fact_recall@5 | 0.688 | 0.162 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 1.000 | 0.000 | 8 |
| page_mrr | 0.677 | 0.124 | 8 |
| page_ndcg@5 | 0.620 | 0.124 | 8 |
| retrieved_tokens@1 | 434 | 51 | 8 |
| retrieved_tokens@10 | 4783 | 159 | 8 |
| retrieved_tokens@20 | 9600 | 230 | 8 |
| retrieved_tokens@3 | 1418 | 85 | 8 |
| retrieved_tokens@5 | 2402 | 86 | 8 |

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.625 | 0.171 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.808 | 0.124 | 8 |
| chunk_fact_recall@20 | 0.871 | 0.069 | 8 |
| chunk_fact_recall@3 | 0.496 | 0.156 | 8 |
| chunk_fact_recall@5 | 0.496 | 0.156 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.417 | 0.148 | 8 |
| chunk_ndcg@5 | 0.323 | 0.108 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@10 | 0.912 | 0.064 | 8 |
| page_fact_recall@20 | 0.912 | 0.064 | 8 |
| page_fact_recall@3 | 0.600 | 0.150 | 8 |
| page_fact_recall@5 | 0.600 | 0.150 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.542 | 0.150 | 8 |
| page_ndcg@5 | 0.519 | 0.144 | 8 |
| retrieved_tokens@1 | 345 | 58 | 8 |
| retrieved_tokens@10 | 4426 | 200 | 8 |
| retrieved_tokens@20 | 9020 | 340 | 8 |
| retrieved_tokens@3 | 1251 | 88 | 8 |
| retrieved_tokens@5 | 2123 | 130 | 8 |

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.750 | 0.153 | 8 |
| chunk_all_required@20 | 0.875 | 0.117 | 8 |
| chunk_all_required@3 | 0.500 | 0.177 | 8 |
| chunk_all_required@5 | 0.500 | 0.177 | 8 |
| chunk_fact_recall@1 | 0.250 | 0.134 | 8 |
| chunk_fact_recall@10 | 0.920 | 0.062 | 8 |
| chunk_fact_recall@20 | 0.938 | 0.062 | 8 |
| chunk_fact_recall@3 | 0.732 | 0.130 | 8 |
| chunk_fact_recall@5 | 0.732 | 0.130 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 1.000 | 0.000 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.875 | 0.117 | 8 |
| chunk_hit@5 | 0.875 | 0.117 | 8 |
| chunk_mrr | 0.583 | 0.134 | 8 |
| chunk_ndcg@5 | 0.419 | 0.083 | 8 |
| page_fact_recall@1 | 0.375 | 0.183 | 8 |
| page_fact_recall@10 | 0.920 | 0.062 | 8 |
| page_fact_recall@20 | 0.938 | 0.062 | 8 |
| page_fact_recall@3 | 0.732 | 0.130 | 8 |
| page_fact_recall@5 | 0.732 | 0.130 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.583 | 0.134 | 8 |
| page_ndcg@5 | 0.434 | 0.102 | 8 |
| retrieved_tokens@1 | 500 | 12 | 8 |
| retrieved_tokens@10 | 4845 | 92 | 8 |
| retrieved_tokens@20 | 9698 | 99 | 8 |
| retrieved_tokens@3 | 1515 | 14 | 8 |
| retrieved_tokens@5 | 2487 | 51 | 8 |

## Token-matched k = 5 (target 2335 tokens)

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_fact_recall | 0.583 | 0.075 | 32 |
| chunk_hit | 0.719 | 0.079 | 32 |
| page_hit | 0.844 | 0.064 | 32 |
| tokens | 2344 | 51 | 32 |

## Lists

- page_hit_no_chunk: 52, 32, 87, 38
- conflict_unscored: 53, 50, 58
- near_ties: none

## answer_only_facts

- row 58 F1
- row 22 F1

## no_retrieval_facts

- 22

## evidence_warnings

none

## Comparison with baseline 2026-10-19-d2625d91 (change: embed model)

| metric | baseline mean ± SE (n) | this run mean ± SE (n) | delta |
|---|---|---|---|
| chunk_fact_recall@5 | 0.495 ± 0.081 (32) | 0.583 ± 0.075 (32) | +0.088 |
| retrieved_tokens@5 | 2335 ± 45 (32) | 2344 ± 51 (32) | +9 |
| chunk_all_required@1 | 0.125 ± 0.058 (32) | 0.188 ± 0.069 (32) | +0.062 |
| chunk_all_required@10 | 0.469 ± 0.088 (32) | 0.625 ± 0.086 (32) | +0.156 |
| chunk_all_required@20 | 0.562 ± 0.088 (32) | 0.719 ± 0.079 (32) | +0.156 |
| chunk_all_required@3 | 0.312 ± 0.082 (32) | 0.312 ± 0.082 (32) | +0.000 |
| chunk_all_required@5 | 0.406 ± 0.087 (32) | 0.406 ± 0.087 (32) | +0.000 |
| chunk_fact_recall@1 | 0.177 ± 0.061 (32) | 0.271 ± 0.070 (32) | +0.094 |
| chunk_fact_recall@10 | 0.589 ± 0.078 (32) | 0.744 ± 0.070 (32) | +0.156 |
| chunk_fact_recall@20 | 0.677 ± 0.073 (32) | 0.819 ± 0.061 (32) | +0.142 |
| chunk_fact_recall@3 | 0.417 ± 0.078 (32) | 0.510 ± 0.075 (32) | +0.093 |
| chunk_hit@1 | 0.250 ± 0.077 (32) | 0.375 ± 0.086 (32) | +0.125 |
| chunk_hit@10 | 0.688 ± 0.082 (32) | 0.812 ± 0.069 (32) | +0.125 |
| chunk_hit@20 | 0.781 ± 0.073 (32) | 0.875 ± 0.058 (32) | +0.094 |
| chunk_hit@3 | 0.531 ± 0.088 (32) | 0.656 ± 0.084 (32) | +0.125 |
| chunk_hit@5 | 0.594 ± 0.087 (32) | 0.719 ± 0.079 (32) | +0.125 |
| chunk_mrr | 0.380 ± 0.071 (32) | 0.504 ± 0.075 (32) | +0.123 |
| chunk_ndcg@5 | 0.295 ± 0.056 (32) | 0.397 ± 0.058 (32) | +0.102 |
| page_fact_recall@1 | 0.318 ± 0.082 (32) | 0.401 ± 0.085 (32) | +0.083 |
| page_fact_recall@10 | 0.761 ± 0.071 (32) | 0.849 ± 0.056 (32) | +0.088 |
| page_fact_recall@20 | 0.792 ± 0.067 (32) | 0.869 ± 0.055 (32) | +0.076 |
| page_fact_recall@3 | 0.579 ± 0.082 (32) | 0.661 ± 0.075 (32) | +0.082 |
| page_fact_recall@5 | 0.641 ± 0.076 (32) | 0.692 ± 0.073 (32) | +0.051 |
| page_hit@1 | 0.438 ± 0.088 (32) | 0.469 ± 0.088 (32) | +0.031 |
| page_hit@10 | 0.844 ± 0.064 (32) | 0.938 ± 0.043 (32) | +0.094 |
| page_hit@20 | 0.875 ± 0.058 (32) | 0.938 ± 0.043 (32) | +0.062 |
| page_hit@3 | 0.688 ± 0.082 (32) | 0.812 ± 0.069 (32) | +0.125 |
| page_hit@5 | 0.812 ± 0.069 (32) | 0.844 ± 0.064 (32) | +0.031 |
| page_mrr | 0.575 ± 0.072 (32) | 0.622 ± 0.069 (32) | +0.047 |
| page_ndcg@5 | 0.511 ± 0.065 (32) | 0.564 ± 0.066 (32) | +0.053 |
| retrieved_tokens@1 | 444 ± 23 (32) | 445 ± 22 (32) | +2 |
| retrieved_tokens@10 | 4639 ± 78 (32) | 4679 ± 82 (32) | +40 |
| retrieved_tokens@20 | 9441 ± 100 (32) | 9406 ± 126 (32) | -35 |
| retrieved_tokens@3 | 1396 ± 31 (32) | 1418 ± 36 (32) | +22 |

### Token-matched k (baseline k=5, this run k=5)

| metric | baseline @5 | this run @matched | delta |
|---|---|---|---|
| tokens | 2335 ± 45 (32) | 2344 ± 51 (32) | +9 |
| chunk_fact_recall | 0.495 ± 0.081 (32) | 0.583 ± 0.075 (32) | +0.088 |
| chunk_hit | 0.594 ± 0.087 (32) | 0.719 ± 0.079 (32) | +0.125 |
| page_hit | 0.812 ± 0.069 (32) | 0.844 ± 0.064 (32) | +0.031 |
| chunk_fact_recall@5 (both at k=5) | 0.495 ± 0.081 (32) | 0.583 ± 0.075 (32) | +0.088 |

### Paired delta (spec 0008 AC-7)

| comparison | mean delta | paired SE | mean / SE | n |
|---|---|---|---|---|
| chunk_fact_recall @matched k vs baseline @5 | +0.088 | 0.045 | 1.97 | 32 |
| chunk_fact_recall@5 vs @5 | +0.088 | 0.045 | 1.97 | 32 |

Adopt only if mean / SE > 2 on the matched-k row (spec 0008 AC-9).

| row | metric | baseline | this run |
|---|---|---|---|
| 52 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 52 | chunk_hit@5 | 0.000 | 0.000 |
| 52 | page_hit@5 | 1.000 | 1.000 |
| 52 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 52 | best relevant chunk | — | — |
| 53 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 53 | chunk_hit@5 | 0.000 | 0.000 |
| 53 | page_hit@5 | 1.000 | 0.000 |
| 53 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 53 | best relevant chunk | — | — |
| 8 | chunk_fact_recall@5 | 0.000 | 0.500 |
| 8 | chunk_hit@5 | 0.000 | 1.000 |
| 8 | page_hit@5 | 1.000 | 1.000 |
| 8 | chunk_fact_recall@matched | 0.000 | 0.500 |
| 8 | best relevant chunk | — | 2 · Processing Navan Reports |
| 10 | chunk_fact_recall@5 | 0.000 | 0.857 |
| 10 | chunk_hit@5 | 0.000 | 1.000 |
| 10 | page_hit@5 | 1.000 | 1.000 |
| 10 | chunk_fact_recall@matched | 0.000 | 0.857 |
| 10 | best relevant chunk | — | 2 · CREDIT |
| 99 | chunk_fact_recall@5 | 0.000 | 0.500 |
| 99 | chunk_hit@5 | 0.000 | 1.000 |
| 99 | page_hit@5 | 1.000 | 1.000 |
| 99 | chunk_fact_recall@matched | 0.000 | 0.500 |
| 99 | best relevant chunk | — | 1 · Payroll & Benefits |
| 38 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 38 | chunk_hit@5 | 0.000 | 0.000 |
| 38 | page_hit@5 | 1.000 | 1.000 |
| 38 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 38 | best relevant chunk | — | — |
| 89 | chunk_fact_recall@5 | 0.000 | 0.500 |
| 89 | chunk_hit@5 | 0.000 | 1.000 |
| 89 | page_hit@5 | 1.000 | 1.000 |
| 89 | chunk_fact_recall@matched | 0.000 | 0.500 |
| 89 | best relevant chunk | — | 5 · GitLab Offboarding |
| 11 | chunk_fact_recall@5 | 0.333 | 0.667 |
| 11 | chunk_hit@5 | 1.000 | 1.000 |
| 11 | page_hit@5 | 1.000 | 1.000 |
| 11 | chunk_fact_recall@matched | 0.333 | 0.667 |
| 11 | best relevant chunk | 2 · Shipping Locations | 2 · Equipment |
| 34 | chunk_fact_recall@5 | 0.667 | 1.000 |
| 34 | chunk_hit@5 | 1.000 | 1.000 |
| 34 | page_hit@5 | 1.000 | 1.000 |
| 34 | chunk_fact_recall@matched | 0.667 | 1.000 |
| 34 | best relevant chunk | 1 · Team Member | 1 · Team Member |
| 44 | chunk_fact_recall@5 | 1.000 | 0.800 |
| 44 | chunk_hit@5 | 1.000 | 1.000 |
| 44 | page_hit@5 | 1.000 | 1.000 |
| 44 | chunk_fact_recall@matched | 1.000 | 0.800 |
| 44 | best relevant chunk | 3 · Customer Experience | 2 · Role Comparison |
| 49 | chunk_fact_recall@5 | 1.000 | 0.500 |
| 49 | chunk_hit@5 | 1.000 | 1.000 |
| 49 | page_hit@5 | 1.000 | 1.000 |
| 49 | chunk_fact_recall@matched | 1.000 | 0.500 |
| 49 | best relevant chunk | 4 · Shipping Locations | 3 · Equipment |
| 51 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 51 | chunk_hit@5 | 1.000 | 1.000 |
| 51 | page_hit@5 | 1.000 | 1.000 |
| 51 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 51 | best relevant chunk | 1 · Equipment | 1 · Equipment |
| 58 | chunk_fact_recall@5 | 0.500 | 1.000 |
| 58 | chunk_hit@5 | 1.000 | 1.000 |
| 58 | page_hit@5 | 1.000 | 1.000 |
| 58 | chunk_fact_recall@matched | 0.500 | 1.000 |
| 58 | best relevant chunk | 3 · Time Off Types | 1 · Time Off Types |
| 88 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 88 | chunk_hit@5 | 1.000 | 1.000 |
| 88 | page_hit@5 | 1.000 | 1.000 |
| 88 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 88 | best relevant chunk | 1 · Timeline | 1 · Timeline |
| 100 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 100 | chunk_hit@5 | 1.000 | 1.000 |
| 100 | page_hit@5 | 1.000 | 1.000 |
| 100 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 100 | best relevant chunk | 1 · Overview | 1 · Time Off Types |
| 5 | chunk_fact_recall@5 | 0.333 | 0.333 |
| 5 | chunk_hit@5 | 1.000 | 1.000 |
| 5 | page_hit@5 | 1.000 | 1.000 |
| 5 | chunk_fact_recall@matched | 0.333 | 0.333 |
| 5 | best relevant chunk | 1 · Sick Time Eligibility and Coverage | 1 · Sick Time Eligibility and Coverage |
| 32 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 32 | chunk_hit@5 | 0.000 | 0.000 |
| 32 | page_hit@5 | 0.000 | 1.000 |
| 32 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 32 | best relevant chunk | — | — |
| 35 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 35 | chunk_hit@5 | 1.000 | 1.000 |
| 35 | page_hit@5 | 1.000 | 1.000 |
| 35 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 35 | best relevant chunk | 2 · Termination | 3 · Termination |
| 87 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 87 | chunk_hit@5 | 0.000 | 0.000 |
| 87 | page_hit@5 | 0.000 | 1.000 |
| 87 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 87 | best relevant chunk | — | — |
