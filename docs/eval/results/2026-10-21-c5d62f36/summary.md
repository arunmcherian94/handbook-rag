# Eval summary

## Takeaways

- **Retrieval-only, Qwen3-Embedding-8B@1536 vs baseline `2026-10-19-d2625d91`.** recall@5 0.586 against 0.495: paired +0.091 ± 0.076, mean/SE 1.20. No difference under AC-9. Rows: 7 won, 2 lost (44 and 49, each −1.0), 23 tied.
- **Why the SE is larger than 3-large's:** same mean gain, but the two lost rows lose a full 1.0 each, and some wins are +1.0 (rows 8, 10, 99).
- **Next:** the full answer run is `2026-10-21-9719cae6`; the decision is in ADR-0022.

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: 7a8c798fcb99bf8d09df693cb40940198a6b00e9
- harness_dirty: False
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- config_id: fixed-512-64
- chunk_params: {'strategy': 'fixed', 'size': 512, 'overlap': 64, 'tokenizer': 'cl100k_base'}
- embed_model: deepinfra:Qwen/Qwen3-Embedding-8B@1536
- answer_model: None
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- eval_depth: 20
- timestamp: 2026-10-21T09:14:06.193549+00:00
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
| chunk_all_required@10 | 0.656 | 0.084 | 32 |
| chunk_all_required@20 | 0.719 | 0.079 | 32 |
| chunk_all_required@3 | 0.406 | 0.087 | 32 |
| chunk_all_required@5 | 0.500 | 0.088 | 32 |
| chunk_fact_recall@1 | 0.281 | 0.070 | 32 |
| chunk_fact_recall@10 | 0.734 | 0.071 | 32 |
| chunk_fact_recall@20 | 0.797 | 0.063 | 32 |
| chunk_fact_recall@3 | 0.497 | 0.080 | 32 |
| chunk_fact_recall@5 | 0.586 | 0.082 | 32 |
| chunk_hit@1 | 0.406 | 0.087 | 32 |
| chunk_hit@10 | 0.812 | 0.069 | 32 |
| chunk_hit@20 | 0.875 | 0.058 | 32 |
| chunk_hit@3 | 0.625 | 0.086 | 32 |
| chunk_hit@5 | 0.656 | 0.084 | 32 |
| chunk_mrr | 0.522 | 0.078 | 32 |
| chunk_ndcg@5 | 0.456 | 0.070 | 32 |
| page_fact_recall@1 | 0.421 | 0.084 | 32 |
| page_fact_recall@10 | 0.844 | 0.061 | 32 |
| page_fact_recall@20 | 0.859 | 0.056 | 32 |
| page_fact_recall@3 | 0.667 | 0.080 | 32 |
| page_fact_recall@5 | 0.698 | 0.078 | 32 |
| page_hit@1 | 0.594 | 0.087 | 32 |
| page_hit@10 | 0.875 | 0.058 | 32 |
| page_hit@20 | 0.938 | 0.043 | 32 |
| page_hit@3 | 0.781 | 0.073 | 32 |
| page_hit@5 | 0.844 | 0.064 | 32 |
| page_mrr | 0.691 | 0.071 | 32 |
| page_ndcg@5 | 0.604 | 0.063 | 32 |
| retrieved_tokens@1 | 469 | 18 | 32 |
| retrieved_tokens@10 | 4657 | 64 | 32 |
| retrieved_tokens@20 | 9247 | 138 | 32 |
| retrieved_tokens@3 | 1374 | 40 | 32 |
| retrieved_tokens@5 | 2308 | 40 | 32 |

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.750 | 0.153 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.625 | 0.171 | 8 |
| chunk_all_required@5 | 0.625 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.289 | 0.137 | 8 |
| chunk_fact_recall@10 | 0.812 | 0.132 | 8 |
| chunk_fact_recall@20 | 0.875 | 0.082 | 8 |
| chunk_fact_recall@3 | 0.625 | 0.183 | 8 |
| chunk_fact_recall@5 | 0.688 | 0.162 | 8 |
| chunk_hit@1 | 0.500 | 0.177 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.588 | 0.165 | 8 |
| chunk_ndcg@5 | 0.585 | 0.162 | 8 |
| page_fact_recall@1 | 0.455 | 0.170 | 8 |
| page_fact_recall@10 | 0.812 | 0.132 | 8 |
| page_fact_recall@20 | 0.875 | 0.082 | 8 |
| page_fact_recall@3 | 0.688 | 0.162 | 8 |
| page_fact_recall@5 | 0.688 | 0.162 | 8 |
| page_hit@1 | 0.750 | 0.153 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.792 | 0.140 | 8 |
| page_ndcg@5 | 0.703 | 0.139 | 8 |
| retrieved_tokens@1 | 451 | 43 | 8 |
| retrieved_tokens@10 | 4715 | 116 | 8 |
| retrieved_tokens@20 | 9617 | 135 | 8 |
| retrieved_tokens@3 | 1420 | 62 | 8 |
| retrieved_tokens@5 | 2328 | 58 | 8 |

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.625 | 0.171 | 8 |
| chunk_all_required@10 | 0.750 | 0.153 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.625 | 0.171 | 8 |
| chunk_all_required@5 | 0.750 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.625 | 0.183 | 8 |
| chunk_fact_recall@10 | 0.812 | 0.132 | 8 |
| chunk_fact_recall@20 | 0.812 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.688 | 0.162 | 8 |
| chunk_fact_recall@5 | 0.750 | 0.164 | 8 |
| chunk_hit@1 | 0.625 | 0.171 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.750 | 0.153 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.688 | 0.162 | 8 |
| chunk_ndcg@5 | 0.597 | 0.147 | 8 |
| page_fact_recall@1 | 0.625 | 0.183 | 8 |
| page_fact_recall@10 | 0.875 | 0.125 | 8 |
| page_fact_recall@20 | 0.875 | 0.125 | 8 |
| page_fact_recall@3 | 0.750 | 0.164 | 8 |
| page_fact_recall@5 | 0.750 | 0.164 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.719 | 0.145 | 8 |
| page_ndcg@5 | 0.696 | 0.137 | 8 |
| retrieved_tokens@1 | 466 | 37 | 8 |
| retrieved_tokens@10 | 4496 | 132 | 8 |
| retrieved_tokens@20 | 9194 | 225 | 8 |
| retrieved_tokens@3 | 1318 | 104 | 8 |
| retrieved_tokens@5 | 2242 | 96 | 8 |

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.625 | 0.171 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.062 | 0.062 | 8 |
| chunk_fact_recall@10 | 0.688 | 0.162 | 8 |
| chunk_fact_recall@20 | 0.812 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.292 | 0.129 | 8 |
| chunk_fact_recall@5 | 0.458 | 0.177 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.500 | 0.177 | 8 |
| chunk_mrr | 0.312 | 0.132 | 8 |
| chunk_ndcg@5 | 0.235 | 0.096 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@10 | 0.812 | 0.132 | 8 |
| page_fact_recall@20 | 0.812 | 0.132 | 8 |
| page_fact_recall@3 | 0.562 | 0.175 | 8 |
| page_fact_recall@5 | 0.562 | 0.175 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.542 | 0.150 | 8 |
| page_ndcg@5 | 0.398 | 0.097 | 8 |
| retrieved_tokens@1 | 492 | 20 | 8 |
| retrieved_tokens@10 | 4616 | 149 | 8 |
| retrieved_tokens@20 | 8799 | 335 | 8 |
| retrieved_tokens@3 | 1316 | 91 | 8 |
| retrieved_tokens@5 | 2236 | 87 | 8 |

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.146 | 0.073 | 8 |
| chunk_fact_recall@10 | 0.625 | 0.157 | 8 |
| chunk_fact_recall@20 | 0.688 | 0.162 | 8 |
| chunk_fact_recall@3 | 0.385 | 0.149 | 8 |
| chunk_fact_recall@5 | 0.448 | 0.153 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.500 | 0.164 | 8 |
| chunk_ndcg@5 | 0.406 | 0.131 | 8 |
| page_fact_recall@1 | 0.354 | 0.156 | 8 |
| page_fact_recall@10 | 0.875 | 0.125 | 8 |
| page_fact_recall@20 | 0.875 | 0.125 | 8 |
| page_fact_recall@3 | 0.667 | 0.167 | 8 |
| page_fact_recall@5 | 0.792 | 0.140 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.713 | 0.148 | 8 |
| page_ndcg@5 | 0.617 | 0.123 | 8 |
| retrieved_tokens@1 | 467 | 45 | 8 |
| retrieved_tokens@10 | 4803 | 111 | 8 |
| retrieved_tokens@20 | 9380 | 325 | 8 |
| retrieved_tokens@3 | 1441 | 63 | 8 |
| retrieved_tokens@5 | 2424 | 67 | 8 |

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.083 | 0.083 | 8 |
| chunk_fact_recall@10 | 0.562 | 0.175 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.134 | 8 |
| chunk_fact_recall@3 | 0.229 | 0.130 | 8 |
| chunk_fact_recall@5 | 0.333 | 0.167 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.375 | 0.171 | 8 |
| chunk_mrr | 0.250 | 0.134 | 8 |
| chunk_ndcg@5 | 0.239 | 0.131 | 8 |
| page_fact_recall@1 | 0.125 | 0.125 | 8 |
| page_fact_recall@10 | 0.688 | 0.162 | 8 |
| page_fact_recall@20 | 0.750 | 0.134 | 8 |
| page_fact_recall@3 | 0.438 | 0.175 | 8 |
| page_fact_recall@5 | 0.438 | 0.175 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.542 | 0.150 | 8 |
| page_ndcg@5 | 0.446 | 0.121 | 8 |
| retrieved_tokens@1 | 451 | 43 | 8 |
| retrieved_tokens@10 | 4584 | 150 | 8 |
| retrieved_tokens@20 | 8853 | 361 | 8 |
| retrieved_tokens@3 | 1321 | 95 | 8 |
| retrieved_tokens@5 | 2250 | 83 | 8 |

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.875 | 0.117 | 8 |
| chunk_all_required@20 | 0.875 | 0.117 | 8 |
| chunk_all_required@3 | 0.625 | 0.171 | 8 |
| chunk_all_required@5 | 0.750 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.268 | 0.130 | 8 |
| chunk_fact_recall@10 | 0.938 | 0.062 | 8 |
| chunk_fact_recall@20 | 0.938 | 0.062 | 8 |
| chunk_fact_recall@3 | 0.688 | 0.162 | 8 |
| chunk_fact_recall@5 | 0.812 | 0.132 | 8 |
| chunk_hit@1 | 0.500 | 0.177 | 8 |
| chunk_hit@10 | 1.000 | 0.000 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.750 | 0.153 | 8 |
| chunk_hit@5 | 0.875 | 0.117 | 8 |
| chunk_mrr | 0.650 | 0.144 | 8 |
| chunk_ndcg@5 | 0.580 | 0.136 | 8 |
| page_fact_recall@1 | 0.580 | 0.168 | 8 |
| page_fact_recall@10 | 0.938 | 0.062 | 8 |
| page_fact_recall@20 | 0.938 | 0.062 | 8 |
| page_fact_recall@3 | 0.812 | 0.132 | 8 |
| page_fact_recall@5 | 0.812 | 0.132 | 8 |
| page_hit@1 | 0.750 | 0.153 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.792 | 0.140 | 8 |
| page_ndcg@5 | 0.655 | 0.132 | 8 |
| retrieved_tokens@1 | 492 | 20 | 8 |
| retrieved_tokens@10 | 4748 | 110 | 8 |
| retrieved_tokens@20 | 9563 | 109 | 8 |
| retrieved_tokens@3 | 1415 | 58 | 8 |
| retrieved_tokens@5 | 2314 | 65 | 8 |

## Token-matched k = 5 (target 2335 tokens)

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_fact_recall | 0.586 | 0.082 | 32 |
| chunk_hit | 0.656 | 0.084 | 32 |
| page_hit | 0.844 | 0.064 | 32 |
| tokens | 2308 | 40 | 32 |

## Lists

- page_hit_no_chunk: 52, 53, 44, 38, 89, 92
- conflict_unscored: 53, 50, 58
- near_ties: 11, 51, 5, 35, 65, 88, 93

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
| chunk_fact_recall@5 | 0.495 ± 0.081 (32) | 0.586 ± 0.082 (32) | +0.091 |
| retrieved_tokens@5 | 2335 ± 45 (32) | 2308 ± 40 (32) | -28 |
| chunk_all_required@1 | 0.125 ± 0.058 (32) | 0.188 ± 0.069 (32) | +0.062 |
| chunk_all_required@10 | 0.469 ± 0.088 (32) | 0.656 ± 0.084 (32) | +0.188 |
| chunk_all_required@20 | 0.562 ± 0.088 (32) | 0.719 ± 0.079 (32) | +0.156 |
| chunk_all_required@3 | 0.312 ± 0.082 (32) | 0.406 ± 0.087 (32) | +0.094 |
| chunk_all_required@5 | 0.406 ± 0.087 (32) | 0.500 ± 0.088 (32) | +0.094 |
| chunk_fact_recall@1 | 0.177 ± 0.061 (32) | 0.281 ± 0.070 (32) | +0.103 |
| chunk_fact_recall@10 | 0.589 ± 0.078 (32) | 0.734 ± 0.071 (32) | +0.146 |
| chunk_fact_recall@20 | 0.677 ± 0.073 (32) | 0.797 ± 0.063 (32) | +0.120 |
| chunk_fact_recall@3 | 0.417 ± 0.078 (32) | 0.497 ± 0.080 (32) | +0.081 |
| chunk_hit@1 | 0.250 ± 0.077 (32) | 0.406 ± 0.087 (32) | +0.156 |
| chunk_hit@10 | 0.688 ± 0.082 (32) | 0.812 ± 0.069 (32) | +0.125 |
| chunk_hit@20 | 0.781 ± 0.073 (32) | 0.875 ± 0.058 (32) | +0.094 |
| chunk_hit@3 | 0.531 ± 0.088 (32) | 0.625 ± 0.086 (32) | +0.094 |
| chunk_hit@5 | 0.594 ± 0.087 (32) | 0.656 ± 0.084 (32) | +0.062 |
| chunk_mrr | 0.380 ± 0.071 (32) | 0.522 ± 0.078 (32) | +0.142 |
| chunk_ndcg@5 | 0.295 ± 0.056 (32) | 0.456 ± 0.070 (32) | +0.161 |
| page_fact_recall@1 | 0.318 ± 0.082 (32) | 0.421 ± 0.084 (32) | +0.103 |
| page_fact_recall@10 | 0.761 ± 0.071 (32) | 0.844 ± 0.061 (32) | +0.083 |
| page_fact_recall@20 | 0.792 ± 0.067 (32) | 0.859 ± 0.056 (32) | +0.067 |
| page_fact_recall@3 | 0.579 ± 0.082 (32) | 0.667 ± 0.080 (32) | +0.088 |
| page_fact_recall@5 | 0.641 ± 0.076 (32) | 0.698 ± 0.078 (32) | +0.057 |
| page_hit@1 | 0.438 ± 0.088 (32) | 0.594 ± 0.087 (32) | +0.156 |
| page_hit@10 | 0.844 ± 0.064 (32) | 0.875 ± 0.058 (32) | +0.031 |
| page_hit@20 | 0.875 ± 0.058 (32) | 0.938 ± 0.043 (32) | +0.062 |
| page_hit@3 | 0.688 ± 0.082 (32) | 0.781 ± 0.073 (32) | +0.094 |
| page_hit@5 | 0.812 ± 0.069 (32) | 0.844 ± 0.064 (32) | +0.031 |
| page_mrr | 0.575 ± 0.072 (32) | 0.691 ± 0.071 (32) | +0.116 |
| page_ndcg@5 | 0.511 ± 0.065 (32) | 0.604 ± 0.063 (32) | +0.092 |
| retrieved_tokens@1 | 444 ± 23 (32) | 469 ± 18 (32) | +25 |
| retrieved_tokens@10 | 4639 ± 78 (32) | 4657 ± 64 (32) | +19 |
| retrieved_tokens@20 | 9441 ± 100 (32) | 9247 ± 138 (32) | -194 |
| retrieved_tokens@3 | 1396 ± 31 (32) | 1374 ± 40 (32) | -23 |

### Token-matched k (baseline k=5, this run k=5)

| metric | baseline @5 | this run @matched | delta |
|---|---|---|---|
| tokens | 2335 ± 45 (32) | 2308 ± 40 (32) | -28 |
| chunk_fact_recall | 0.495 ± 0.081 (32) | 0.586 ± 0.082 (32) | +0.091 |
| chunk_hit | 0.594 ± 0.087 (32) | 0.656 ± 0.084 (32) | +0.062 |
| page_hit | 0.812 ± 0.069 (32) | 0.844 ± 0.064 (32) | +0.031 |
| chunk_fact_recall@5 (both at k=5) | 0.495 ± 0.081 (32) | 0.586 ± 0.082 (32) | +0.091 |

### Paired delta (spec 0008 AC-7)

| comparison | mean delta | paired SE | mean / SE | n |
|---|---|---|---|---|
| chunk_fact_recall @matched k vs baseline @5 | +0.091 | 0.076 | 1.20 | 32 |
| chunk_fact_recall@5 vs @5 | +0.091 | 0.076 | 1.20 | 32 |

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
| 53 | page_hit@5 | 1.000 | 1.000 |
| 53 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 53 | best relevant chunk | — | — |
| 8 | chunk_fact_recall@5 | 0.000 | 1.000 |
| 8 | chunk_hit@5 | 0.000 | 1.000 |
| 8 | page_hit@5 | 1.000 | 1.000 |
| 8 | chunk_fact_recall@matched | 0.000 | 1.000 |
| 8 | best relevant chunk | — | 2 · Processing Navan Reports |
| 10 | chunk_fact_recall@5 | 0.000 | 1.000 |
| 10 | chunk_hit@5 | 0.000 | 1.000 |
| 10 | page_hit@5 | 1.000 | 1.000 |
| 10 | chunk_fact_recall@matched | 0.000 | 1.000 |
| 10 | best relevant chunk | — | 1 · Customer Outcomes |
| 99 | chunk_fact_recall@5 | 0.000 | 1.000 |
| 99 | chunk_hit@5 | 0.000 | 1.000 |
| 99 | page_hit@5 | 1.000 | 1.000 |
| 99 | chunk_fact_recall@matched | 0.000 | 1.000 |
| 99 | best relevant chunk | — | 1 · Payroll & Benefits |
| 38 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 38 | chunk_hit@5 | 0.000 | 0.000 |
| 38 | page_hit@5 | 1.000 | 1.000 |
| 38 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 38 | best relevant chunk | — | — |
| 89 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 89 | chunk_hit@5 | 0.000 | 0.000 |
| 89 | page_hit@5 | 1.000 | 1.000 |
| 89 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 89 | best relevant chunk | — | — |
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
| 44 | chunk_fact_recall@5 | 1.000 | 0.000 |
| 44 | chunk_hit@5 | 1.000 | 0.000 |
| 44 | page_hit@5 | 1.000 | 1.000 |
| 44 | chunk_fact_recall@matched | 1.000 | 0.000 |
| 44 | best relevant chunk | 3 · Customer Experience | — |
| 49 | chunk_fact_recall@5 | 1.000 | 0.000 |
| 49 | chunk_hit@5 | 1.000 | 0.000 |
| 49 | page_hit@5 | 1.000 | 0.000 |
| 49 | chunk_fact_recall@matched | 1.000 | 0.000 |
| 49 | best relevant chunk | 4 · Shipping Locations | — |
| 51 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 51 | chunk_hit@5 | 1.000 | 1.000 |
| 51 | page_hit@5 | 1.000 | 1.000 |
| 51 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 51 | best relevant chunk | 1 · Equipment | 2 · Equipment |
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
| 32 | chunk_fact_recall@5 | 0.000 | 0.750 |
| 32 | chunk_hit@5 | 0.000 | 1.000 |
| 32 | page_hit@5 | 0.000 | 1.000 |
| 32 | chunk_fact_recall@matched | 0.000 | 0.750 |
| 32 | best relevant chunk | — | 2 · Legal entities |
| 35 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 35 | chunk_hit@5 | 1.000 | 1.000 |
| 35 | page_hit@5 | 1.000 | 1.000 |
| 35 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 35 | best relevant chunk | 2 · Termination | 2 · Termination |
| 87 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 87 | chunk_hit@5 | 0.000 | 0.000 |
| 87 | page_hit@5 | 0.000 | 0.000 |
| 87 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 87 | best relevant chunk | — | — |
