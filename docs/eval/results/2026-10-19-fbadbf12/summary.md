# Eval summary

## Takeaways

_To fill before committing the run (LLM-drafted, human-approved): what to improve in the next iteration, and whether the previous run's fixes worked._

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: 21334f046d3d073e3387f6c3c131ad1de47e0868
- harness_dirty: False
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- config_id: fixed-512-64-prefixed
- chunk_params: {'strategy': 'fixed', 'size': 512, 'overlap': 64, 'embed_prefix': 'title-path', 'tokenizer': 'cl100k_base'}
- embed_model: openai:text-embedding-3-small
- answer_model: None
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- eval_depth: 20
- timestamp: 2026-10-19T14:39:44.631183+00:00
- rows: 33
- mode: retrieval-only
- limit: None
- baseline: 2026-10-19-d2625d91

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.094 | 0.052 | 32 |
| chunk_all_required@10 | 0.500 | 0.088 | 32 |
| chunk_all_required@20 | 0.594 | 0.087 | 32 |
| chunk_all_required@3 | 0.344 | 0.084 | 32 |
| chunk_all_required@5 | 0.438 | 0.088 | 32 |
| chunk_fact_recall@1 | 0.188 | 0.059 | 32 |
| chunk_fact_recall@10 | 0.589 | 0.080 | 32 |
| chunk_fact_recall@20 | 0.693 | 0.073 | 32 |
| chunk_fact_recall@3 | 0.427 | 0.080 | 32 |
| chunk_fact_recall@5 | 0.531 | 0.081 | 32 |
| chunk_hit@1 | 0.281 | 0.079 | 32 |
| chunk_hit@10 | 0.688 | 0.082 | 32 |
| chunk_hit@20 | 0.781 | 0.073 | 32 |
| chunk_hit@3 | 0.531 | 0.088 | 32 |
| chunk_hit@5 | 0.625 | 0.086 | 32 |
| chunk_mrr | 0.407 | 0.073 | 32 |
| chunk_ndcg@5 | 0.319 | 0.056 | 32 |
| page_fact_recall@1 | 0.386 | 0.083 | 32 |
| page_fact_recall@10 | 0.717 | 0.072 | 32 |
| page_fact_recall@20 | 0.800 | 0.064 | 32 |
| page_fact_recall@3 | 0.615 | 0.078 | 32 |
| page_fact_recall@5 | 0.647 | 0.076 | 32 |
| page_hit@1 | 0.500 | 0.088 | 32 |
| page_hit@10 | 0.844 | 0.064 | 32 |
| page_hit@20 | 0.906 | 0.052 | 32 |
| page_hit@3 | 0.812 | 0.069 | 32 |
| page_hit@5 | 0.812 | 0.069 | 32 |
| page_mrr | 0.635 | 0.071 | 32 |
| page_ndcg@5 | 0.527 | 0.063 | 32 |
| retrieved_tokens@1 | 438 | 24 | 32 |
| retrieved_tokens@10 | 4635 | 83 | 32 |
| retrieved_tokens@20 | 9417 | 120 | 32 |
| retrieved_tokens@3 | 1364 | 41 | 32 |
| retrieved_tokens@5 | 2310 | 51 | 32 |

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.625 | 0.171 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.500 | 0.177 | 8 |
| chunk_fact_recall@1 | 0.125 | 0.082 | 8 |
| chunk_fact_recall@10 | 0.750 | 0.134 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.134 | 8 |
| chunk_fact_recall@3 | 0.500 | 0.164 | 8 |
| chunk_fact_recall@5 | 0.625 | 0.157 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.421 | 0.140 | 8 |
| chunk_ndcg@5 | 0.295 | 0.087 | 8 |
| page_fact_recall@1 | 0.295 | 0.152 | 8 |
| page_fact_recall@10 | 0.920 | 0.062 | 8 |
| page_fact_recall@20 | 0.920 | 0.062 | 8 |
| page_fact_recall@3 | 0.670 | 0.127 | 8 |
| page_fact_recall@5 | 0.795 | 0.088 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 1.000 | 0.000 | 8 |
| page_hit@5 | 1.000 | 0.000 | 8 |
| page_mrr | 0.688 | 0.120 | 8 |
| page_ndcg@5 | 0.553 | 0.085 | 8 |
| retrieved_tokens@1 | 439 | 48 | 8 |
| retrieved_tokens@10 | 4742 | 99 | 8 |
| retrieved_tokens@20 | 9559 | 144 | 8 |
| retrieved_tokens@3 | 1369 | 56 | 8 |
| retrieved_tokens@5 | 2340 | 58 | 8 |

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.250 | 0.153 | 8 |
| chunk_all_required@10 | 0.750 | 0.153 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.625 | 0.171 | 8 |
| chunk_all_required@5 | 0.750 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.312 | 0.162 | 8 |
| chunk_fact_recall@10 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@3 | 0.625 | 0.183 | 8 |
| chunk_fact_recall@5 | 0.750 | 0.164 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.531 | 0.153 | 8 |
| chunk_ndcg@5 | 0.502 | 0.123 | 8 |
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
| page_ndcg@5 | 0.667 | 0.154 | 8 |
| retrieved_tokens@1 | 448 | 54 | 8 |
| retrieved_tokens@10 | 4448 | 245 | 8 |
| retrieved_tokens@20 | 9070 | 362 | 8 |
| retrieved_tokens@3 | 1361 | 79 | 8 |
| retrieved_tokens@5 | 2241 | 114 | 8 |

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.375 | 0.171 | 8 |
| chunk_all_required@20 | 0.500 | 0.177 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.229 | 0.130 | 8 |
| chunk_fact_recall@10 | 0.417 | 0.175 | 8 |
| chunk_fact_recall@20 | 0.646 | 0.156 | 8 |
| chunk_fact_recall@3 | 0.354 | 0.156 | 8 |
| chunk_fact_recall@5 | 0.417 | 0.175 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.500 | 0.177 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.500 | 0.177 | 8 |
| chunk_mrr | 0.417 | 0.175 | 8 |
| chunk_ndcg@5 | 0.255 | 0.104 | 8 |
| page_fact_recall@1 | 0.292 | 0.160 | 8 |
| page_fact_recall@10 | 0.479 | 0.165 | 8 |
| page_fact_recall@20 | 0.812 | 0.132 | 8 |
| page_fact_recall@3 | 0.479 | 0.165 | 8 |
| page_fact_recall@5 | 0.479 | 0.165 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.542 | 0.150 | 8 |
| page_ndcg@5 | 0.384 | 0.116 | 8 |
| retrieved_tokens@1 | 393 | 56 | 8 |
| retrieved_tokens@10 | 4499 | 148 | 8 |
| retrieved_tokens@20 | 9265 | 165 | 8 |
| retrieved_tokens@3 | 1260 | 114 | 8 |
| retrieved_tokens@5 | 2244 | 142 | 8 |

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.250 | 0.153 | 8 |
| chunk_all_required@20 | 0.500 | 0.177 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.083 | 0.083 | 8 |
| chunk_fact_recall@10 | 0.438 | 0.148 | 8 |
| chunk_fact_recall@20 | 0.625 | 0.157 | 8 |
| chunk_fact_recall@3 | 0.229 | 0.130 | 8 |
| chunk_fact_recall@5 | 0.333 | 0.137 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.500 | 0.177 | 8 |
| chunk_mrr | 0.260 | 0.125 | 8 |
| chunk_ndcg@5 | 0.222 | 0.121 | 8 |
| page_fact_recall@1 | 0.333 | 0.167 | 8 |
| page_fact_recall@10 | 0.719 | 0.145 | 8 |
| page_fact_recall@20 | 0.719 | 0.145 | 8 |
| page_fact_recall@3 | 0.562 | 0.175 | 8 |
| page_fact_recall@5 | 0.562 | 0.175 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.625 | 0.157 | 8 |
| page_ndcg@5 | 0.503 | 0.137 | 8 |
| retrieved_tokens@1 | 472 | 40 | 8 |
| retrieved_tokens@10 | 4850 | 123 | 8 |
| retrieved_tokens@20 | 9773 | 185 | 8 |
| retrieved_tokens@3 | 1464 | 72 | 8 |
| retrieved_tokens@5 | 2416 | 75 | 8 |

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.500 | 0.177 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.167 | 0.083 | 8 |
| chunk_fact_recall@10 | 0.542 | 0.177 | 8 |
| chunk_fact_recall@20 | 0.646 | 0.156 | 8 |
| chunk_fact_recall@3 | 0.354 | 0.156 | 8 |
| chunk_fact_recall@5 | 0.479 | 0.165 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.463 | 0.168 | 8 |
| chunk_ndcg@5 | 0.304 | 0.107 | 8 |
| page_fact_recall@1 | 0.229 | 0.130 | 8 |
| page_fact_recall@10 | 0.604 | 0.160 | 8 |
| page_fact_recall@20 | 0.812 | 0.132 | 8 |
| page_fact_recall@3 | 0.417 | 0.148 | 8 |
| page_fact_recall@5 | 0.542 | 0.150 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.688 | 0.132 | 8 |
| page_ndcg@5 | 0.524 | 0.105 | 8 |
| retrieved_tokens@1 | 398 | 61 | 8 |
| retrieved_tokens@10 | 4448 | 122 | 8 |
| retrieved_tokens@20 | 9119 | 103 | 8 |
| retrieved_tokens@3 | 1222 | 106 | 8 |
| retrieved_tokens@5 | 2206 | 134 | 8 |

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.500 | 0.177 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.625 | 0.157 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.134 | 8 |
| chunk_fact_recall@3 | 0.500 | 0.164 | 8 |
| chunk_fact_recall@5 | 0.562 | 0.175 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.375 | 0.147 | 8 |
| chunk_ndcg@5 | 0.247 | 0.083 | 8 |
| page_fact_recall@1 | 0.357 | 0.175 | 8 |
| page_fact_recall@10 | 0.795 | 0.129 | 8 |
| page_fact_recall@20 | 0.920 | 0.062 | 8 |
| page_fact_recall@3 | 0.732 | 0.130 | 8 |
| page_fact_recall@5 | 0.732 | 0.130 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.542 | 0.140 | 8 |
| page_ndcg@5 | 0.414 | 0.104 | 8 |
| retrieved_tokens@1 | 434 | 43 | 8 |
| retrieved_tokens@10 | 4793 | 112 | 8 |
| retrieved_tokens@20 | 9705 | 138 | 8 |
| retrieved_tokens@3 | 1407 | 57 | 8 |
| retrieved_tokens@5 | 2379 | 64 | 8 |

## Token-matched k = 5 (target 2335 tokens)

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_fact_recall | 0.531 | 0.081 | 32 |
| chunk_hit | 0.625 | 0.086 | 32 |
| page_hit | 0.812 | 0.069 | 32 |
| tokens | 2310 | 51 | 32 |

## Lists

- page_hit_no_chunk: 52, 53, 8, 10, 99, 38
- conflict_unscored: 53, 50, 58
- near_ties: none

## answer_only_facts

- row 58 F1
- row 22 F1

## no_retrieval_facts

- 22

## evidence_warnings

none

## Comparison with baseline 2026-10-19-d2625d91

| metric | baseline mean ± SE (n) | this run mean ± SE (n) | delta |
|---|---|---|---|
| chunk_fact_recall@5 | 0.495 ± 0.081 (32) | 0.531 ± 0.081 (32) | +0.036 |
| retrieved_tokens@5 | 2335 ± 45 (32) | 2310 ± 51 (32) | -25 |
| chunk_all_required@1 | 0.125 ± 0.058 (32) | 0.094 ± 0.052 (32) | -0.031 |
| chunk_all_required@10 | 0.469 ± 0.088 (32) | 0.500 ± 0.088 (32) | +0.031 |
| chunk_all_required@20 | 0.562 ± 0.088 (32) | 0.594 ± 0.087 (32) | +0.031 |
| chunk_all_required@3 | 0.312 ± 0.082 (32) | 0.344 ± 0.084 (32) | +0.031 |
| chunk_all_required@5 | 0.406 ± 0.087 (32) | 0.438 ± 0.088 (32) | +0.031 |
| chunk_fact_recall@1 | 0.177 ± 0.061 (32) | 0.188 ± 0.059 (32) | +0.010 |
| chunk_fact_recall@10 | 0.589 ± 0.078 (32) | 0.589 ± 0.080 (32) | +0.000 |
| chunk_fact_recall@20 | 0.677 ± 0.073 (32) | 0.693 ± 0.073 (32) | +0.016 |
| chunk_fact_recall@3 | 0.417 ± 0.078 (32) | 0.427 ± 0.080 (32) | +0.010 |
| chunk_hit@1 | 0.250 ± 0.077 (32) | 0.281 ± 0.079 (32) | +0.031 |
| chunk_hit@10 | 0.688 ± 0.082 (32) | 0.688 ± 0.082 (32) | +0.000 |
| chunk_hit@20 | 0.781 ± 0.073 (32) | 0.781 ± 0.073 (32) | +0.000 |
| chunk_hit@3 | 0.531 ± 0.088 (32) | 0.531 ± 0.088 (32) | +0.000 |
| chunk_hit@5 | 0.594 ± 0.087 (32) | 0.625 ± 0.086 (32) | +0.031 |
| chunk_mrr | 0.380 ± 0.071 (32) | 0.407 ± 0.073 (32) | +0.027 |
| chunk_ndcg@5 | 0.295 ± 0.056 (32) | 0.319 ± 0.056 (32) | +0.023 |
| page_fact_recall@1 | 0.318 ± 0.082 (32) | 0.386 ± 0.083 (32) | +0.068 |
| page_fact_recall@10 | 0.761 ± 0.071 (32) | 0.717 ± 0.072 (32) | -0.044 |
| page_fact_recall@20 | 0.792 ± 0.067 (32) | 0.800 ± 0.064 (32) | +0.008 |
| page_fact_recall@3 | 0.579 ± 0.082 (32) | 0.615 ± 0.078 (32) | +0.036 |
| page_fact_recall@5 | 0.641 ± 0.076 (32) | 0.647 ± 0.076 (32) | +0.005 |
| page_hit@1 | 0.438 ± 0.088 (32) | 0.500 ± 0.088 (32) | +0.062 |
| page_hit@10 | 0.844 ± 0.064 (32) | 0.844 ± 0.064 (32) | +0.000 |
| page_hit@20 | 0.875 ± 0.058 (32) | 0.906 ± 0.052 (32) | +0.031 |
| page_hit@3 | 0.688 ± 0.082 (32) | 0.812 ± 0.069 (32) | +0.125 |
| page_hit@5 | 0.812 ± 0.069 (32) | 0.812 ± 0.069 (32) | +0.000 |
| page_mrr | 0.575 ± 0.072 (32) | 0.635 ± 0.071 (32) | +0.060 |
| page_ndcg@5 | 0.511 ± 0.065 (32) | 0.527 ± 0.063 (32) | +0.015 |
| retrieved_tokens@1 | 444 ± 23 (32) | 438 ± 24 (32) | -6 |
| retrieved_tokens@10 | 4639 ± 78 (32) | 4635 ± 83 (32) | -4 |
| retrieved_tokens@20 | 9441 ± 100 (32) | 9417 ± 120 (32) | -25 |
| retrieved_tokens@3 | 1396 ± 31 (32) | 1364 ± 41 (32) | -33 |

### Token-matched k (baseline k=5, this run k=5)

| metric | baseline @5 | this run @matched | delta |
|---|---|---|---|
| tokens | 2335 ± 45 (32) | 2310 ± 51 (32) | -25 |
| chunk_fact_recall | 0.495 ± 0.081 (32) | 0.531 ± 0.081 (32) | +0.036 |
| chunk_hit | 0.594 ± 0.087 (32) | 0.625 ± 0.086 (32) | +0.031 |
| page_hit | 0.812 ± 0.069 (32) | 0.812 ± 0.069 (32) | +0.000 |
| chunk_fact_recall@5 (both at k=5) | 0.495 ± 0.081 (32) | 0.531 ± 0.081 (32) | +0.036 |

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
| 8 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 8 | chunk_hit@5 | 0.000 | 0.000 |
| 8 | page_hit@5 | 1.000 | 1.000 |
| 8 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 8 | best relevant chunk | — | — |
| 10 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 10 | chunk_hit@5 | 0.000 | 0.000 |
| 10 | page_hit@5 | 1.000 | 1.000 |
| 10 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 10 | best relevant chunk | — | — |
| 99 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 99 | chunk_hit@5 | 0.000 | 0.000 |
| 99 | page_hit@5 | 1.000 | 1.000 |
| 99 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 99 | best relevant chunk | — | — |
| 38 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 38 | chunk_hit@5 | 0.000 | 0.000 |
| 38 | page_hit@5 | 1.000 | 1.000 |
| 38 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 38 | best relevant chunk | — | — |
| 89 | chunk_fact_recall@5 | 0.000 | 0.500 |
| 89 | chunk_hit@5 | 0.000 | 1.000 |
| 89 | page_hit@5 | 1.000 | 1.000 |
| 89 | chunk_fact_recall@matched | 0.000 | 0.500 |
| 89 | best relevant chunk | — | 2 · Voluntary Terminations > Prior to Resignation |
| 11 | chunk_fact_recall@5 | 0.333 | 0.333 |
| 11 | chunk_hit@5 | 1.000 | 1.000 |
| 11 | page_hit@5 | 1.000 | 1.000 |
| 11 | chunk_fact_recall@matched | 0.333 | 0.333 |
| 11 | best relevant chunk | 2 · Shipping Locations | 1 · Shipping Locations |
| 34 | chunk_fact_recall@5 | 0.667 | 0.667 |
| 34 | chunk_hit@5 | 1.000 | 1.000 |
| 34 | page_hit@5 | 1.000 | 1.000 |
| 34 | chunk_fact_recall@matched | 0.667 | 0.667 |
| 34 | best relevant chunk | 1 · Team Member | 3 · How To Apply for a Long-Term Relocation > Team Member |
| 44 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 44 | chunk_hit@5 | 1.000 | 1.000 |
| 44 | page_hit@5 | 1.000 | 1.000 |
| 44 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 44 | best relevant chunk | 3 · Customer Experience | 5 · Customer Experience |
| 49 | chunk_fact_recall@5 | 1.000 | 0.500 |
| 49 | chunk_hit@5 | 1.000 | 1.000 |
| 49 | page_hit@5 | 1.000 | 1.000 |
| 49 | chunk_fact_recall@matched | 1.000 | 0.500 |
| 49 | best relevant chunk | 4 · Shipping Locations | 1 · Shipping Locations |
| 51 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 51 | chunk_hit@5 | 1.000 | 1.000 |
| 51 | page_hit@5 | 1.000 | 1.000 |
| 51 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 51 | best relevant chunk | 1 · Equipment | 1 · 4. PROCEDURES > 4.1 NON-TRAVEL RELATED EXPENSES > Equipment |
| 58 | chunk_fact_recall@5 | 0.500 | 1.000 |
| 58 | chunk_hit@5 | 1.000 | 1.000 |
| 58 | page_hit@5 | 1.000 | 1.000 |
| 58 | chunk_fact_recall@matched | 0.500 | 1.000 |
| 58 | best relevant chunk | 3 · Time Off Types | 3 · Time Off Types |
| 88 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 88 | chunk_hit@5 | 1.000 | 1.000 |
| 88 | page_hit@5 | 1.000 | 1.000 |
| 88 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 88 | best relevant chunk | 1 · Timeline | 2 · FY26 Talent Assessment > Timeline |
| 100 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 100 | chunk_hit@5 | 1.000 | 1.000 |
| 100 | page_hit@5 | 1.000 | 1.000 |
| 100 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 100 | best relevant chunk | 1 · Overview | 1 · Flexible Paid Time Off (PTO) > Overview |
| 5 | chunk_fact_recall@5 | 0.333 | 1.000 |
| 5 | chunk_hit@5 | 1.000 | 1.000 |
| 5 | page_hit@5 | 1.000 | 1.000 |
| 5 | chunk_fact_recall@matched | 0.333 | 1.000 |
| 5 | best relevant chunk | 1 · Sick Time Eligibility and Coverage | 1 · Time Off Policies > Sick Leave Protection |
| 32 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 32 | chunk_hit@5 | 0.000 | 0.000 |
| 32 | page_hit@5 | 0.000 | 0.000 |
| 32 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 32 | best relevant chunk | — | — |
| 35 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 35 | chunk_hit@5 | 1.000 | 1.000 |
| 35 | page_hit@5 | 1.000 | 1.000 |
| 35 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 35 | best relevant chunk | 2 · Termination | 4 · Voluntary Terminations > Termination |
| 87 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 87 | chunk_hit@5 | 0.000 | 0.000 |
| 87 | page_hit@5 | 0.000 | 0.000 |
| 87 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 87 | best relevant chunk | — | — |
