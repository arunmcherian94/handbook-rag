# Eval summary

## Takeaways

_To fill before committing the run (LLM-drafted, human-approved): what to improve in the next iteration, and whether the previous run's fixes worked._

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: 21334f046d3d073e3387f6c3c131ad1de47e0868
- harness_dirty: False
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- config_id: structural-v2
- chunk_params: {'strategy': 'structural-packed', 'overlap': 64, 'max_tokens': 512, 'tokenizer': 'cl100k_base'}
- embed_model: openai:text-embedding-3-small
- answer_model: None
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- eval_depth: 20
- timestamp: 2026-10-19T14:33:53.662831+00:00
- rows: 33
- mode: retrieval-only
- limit: None
- baseline: 2026-10-19-d2625d91

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.156 | 0.064 | 32 |
| chunk_all_required@10 | 0.438 | 0.088 | 32 |
| chunk_all_required@20 | 0.500 | 0.088 | 32 |
| chunk_all_required@3 | 0.250 | 0.077 | 32 |
| chunk_all_required@5 | 0.281 | 0.079 | 32 |
| chunk_fact_recall@1 | 0.193 | 0.066 | 32 |
| chunk_fact_recall@10 | 0.521 | 0.081 | 32 |
| chunk_fact_recall@20 | 0.620 | 0.075 | 32 |
| chunk_fact_recall@3 | 0.318 | 0.076 | 32 |
| chunk_fact_recall@5 | 0.375 | 0.077 | 32 |
| chunk_hit@1 | 0.250 | 0.077 | 32 |
| chunk_hit@10 | 0.625 | 0.086 | 32 |
| chunk_hit@20 | 0.750 | 0.077 | 32 |
| chunk_hit@3 | 0.406 | 0.087 | 32 |
| chunk_hit@5 | 0.500 | 0.088 | 32 |
| chunk_mrr | 0.336 | 0.074 | 32 |
| chunk_ndcg@5 | 0.276 | 0.059 | 32 |
| page_fact_recall@1 | 0.292 | 0.077 | 32 |
| page_fact_recall@10 | 0.657 | 0.077 | 32 |
| page_fact_recall@20 | 0.756 | 0.068 | 32 |
| page_fact_recall@3 | 0.428 | 0.082 | 32 |
| page_fact_recall@5 | 0.563 | 0.081 | 32 |
| page_hit@1 | 0.375 | 0.086 | 32 |
| page_hit@10 | 0.812 | 0.069 | 32 |
| page_hit@20 | 0.875 | 0.058 | 32 |
| page_hit@3 | 0.531 | 0.088 | 32 |
| page_hit@5 | 0.719 | 0.079 | 32 |
| page_mrr | 0.492 | 0.076 | 32 |
| page_ndcg@5 | 0.436 | 0.067 | 32 |
| retrieved_tokens@1 | 321 | 24 | 32 |
| retrieved_tokens@10 | 3553 | 89 | 32 |
| retrieved_tokens@20 | 7246 | 120 | 32 |
| retrieved_tokens@3 | 1011 | 37 | 32 |
| retrieved_tokens@5 | 1714 | 47 | 32 |

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.625 | 0.171 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.750 | 0.134 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.134 | 8 |
| chunk_fact_recall@3 | 0.375 | 0.157 | 8 |
| chunk_fact_recall@5 | 0.438 | 0.148 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.385 | 0.149 | 8 |
| chunk_ndcg@5 | 0.326 | 0.127 | 8 |
| page_fact_recall@1 | 0.250 | 0.134 | 8 |
| page_fact_recall@10 | 0.920 | 0.062 | 8 |
| page_fact_recall@20 | 0.920 | 0.062 | 8 |
| page_fact_recall@3 | 0.482 | 0.157 | 8 |
| page_fact_recall@5 | 0.670 | 0.158 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.542 | 0.143 | 8 |
| page_ndcg@5 | 0.474 | 0.118 | 8 |
| retrieved_tokens@1 | 412 | 28 | 8 |
| retrieved_tokens@10 | 3757 | 140 | 8 |
| retrieved_tokens@20 | 7526 | 173 | 8 |
| retrieved_tokens@3 | 1172 | 57 | 8 |
| retrieved_tokens@5 | 1855 | 75 | 8 |

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
| chunk_fact_recall@3 | 0.625 | 0.183 | 8 |
| chunk_fact_recall@5 | 0.750 | 0.164 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.510 | 0.155 | 8 |
| chunk_ndcg@5 | 0.491 | 0.136 | 8 |
| page_fact_recall@1 | 0.500 | 0.189 | 8 |
| page_fact_recall@10 | 0.750 | 0.164 | 8 |
| page_fact_recall@20 | 0.750 | 0.164 | 8 |
| page_fact_recall@3 | 0.750 | 0.164 | 8 |
| page_fact_recall@5 | 0.750 | 0.164 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.750 | 0.153 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.625 | 0.157 | 8 |
| page_ndcg@5 | 0.639 | 0.156 | 8 |
| retrieved_tokens@1 | 290 | 56 | 8 |
| retrieved_tokens@10 | 3447 | 208 | 8 |
| retrieved_tokens@20 | 7004 | 286 | 8 |
| retrieved_tokens@3 | 857 | 72 | 8 |
| retrieved_tokens@5 | 1590 | 103 | 8 |

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.250 | 0.153 | 8 |
| chunk_all_required@20 | 0.375 | 0.171 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.125 | 0.125 | 8 |
| chunk_fact_recall@10 | 0.417 | 0.148 | 8 |
| chunk_fact_recall@20 | 0.542 | 0.150 | 8 |
| chunk_fact_recall@3 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@5 | 0.229 | 0.130 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.250 | 0.153 | 8 |
| chunk_hit@5 | 0.375 | 0.171 | 8 |
| chunk_mrr | 0.198 | 0.124 | 8 |
| chunk_ndcg@5 | 0.140 | 0.079 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@10 | 0.479 | 0.165 | 8 |
| page_fact_recall@20 | 0.604 | 0.160 | 8 |
| page_fact_recall@3 | 0.250 | 0.164 | 8 |
| page_fact_recall@5 | 0.354 | 0.156 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.750 | 0.153 | 8 |
| page_hit@3 | 0.250 | 0.153 | 8 |
| page_hit@5 | 0.500 | 0.177 | 8 |
| page_mrr | 0.312 | 0.155 | 8 |
| page_ndcg@5 | 0.250 | 0.124 | 8 |
| retrieved_tokens@1 | 302 | 51 | 8 |
| retrieved_tokens@10 | 3417 | 123 | 8 |
| retrieved_tokens@20 | 7180 | 176 | 8 |
| retrieved_tokens@3 | 1016 | 49 | 8 |
| retrieved_tokens@5 | 1747 | 71 | 8 |

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.125 | 0.117 | 8 |
| chunk_all_required@20 | 0.250 | 0.153 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@1 | 0.083 | 0.055 | 8 |
| chunk_fact_recall@10 | 0.167 | 0.126 | 8 |
| chunk_fact_recall@20 | 0.438 | 0.148 | 8 |
| chunk_fact_recall@3 | 0.083 | 0.055 | 8 |
| chunk_fact_recall@5 | 0.083 | 0.055 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.250 | 0.153 | 8 |
| chunk_hit@20 | 0.625 | 0.171 | 8 |
| chunk_hit@3 | 0.250 | 0.153 | 8 |
| chunk_hit@5 | 0.250 | 0.153 | 8 |
| chunk_mrr | 0.250 | 0.164 | 8 |
| chunk_ndcg@5 | 0.146 | 0.096 | 8 |
| page_fact_recall@1 | 0.167 | 0.126 | 8 |
| page_fact_recall@10 | 0.479 | 0.165 | 8 |
| page_fact_recall@20 | 0.750 | 0.134 | 8 |
| page_fact_recall@3 | 0.229 | 0.130 | 8 |
| page_fact_recall@5 | 0.479 | 0.165 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.500 | 0.177 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.487 | 0.160 | 8 |
| page_ndcg@5 | 0.382 | 0.120 | 8 |
| retrieved_tokens@1 | 278 | 49 | 8 |
| retrieved_tokens@10 | 3590 | 228 | 8 |
| retrieved_tokens@20 | 7274 | 300 | 8 |
| retrieved_tokens@3 | 998 | 83 | 8 |
| retrieved_tokens@5 | 1664 | 107 | 8 |

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.125 | 0.125 | 8 |
| chunk_fact_recall@10 | 0.604 | 0.160 | 8 |
| chunk_fact_recall@20 | 0.729 | 0.141 | 8 |
| chunk_fact_recall@3 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@5 | 0.229 | 0.130 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.250 | 0.153 | 8 |
| chunk_hit@5 | 0.375 | 0.171 | 8 |
| chunk_mrr | 0.198 | 0.124 | 8 |
| chunk_ndcg@5 | 0.189 | 0.123 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@10 | 0.604 | 0.160 | 8 |
| page_fact_recall@20 | 0.729 | 0.141 | 8 |
| page_fact_recall@3 | 0.250 | 0.164 | 8 |
| page_fact_recall@5 | 0.354 | 0.156 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.250 | 0.153 | 8 |
| page_hit@5 | 0.625 | 0.171 | 8 |
| page_mrr | 0.344 | 0.149 | 8 |
| page_ndcg@5 | 0.341 | 0.149 | 8 |
| retrieved_tokens@1 | 379 | 53 | 8 |
| retrieved_tokens@10 | 3544 | 137 | 8 |
| retrieved_tokens@20 | 7259 | 178 | 8 |
| retrieved_tokens@3 | 1070 | 60 | 8 |
| retrieved_tokens@5 | 1743 | 72 | 8 |

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.375 | 0.171 | 8 |
| chunk_all_required@20 | 0.375 | 0.171 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.562 | 0.148 | 8 |
| chunk_fact_recall@20 | 0.562 | 0.148 | 8 |
| chunk_fact_recall@3 | 0.375 | 0.157 | 8 |
| chunk_fact_recall@5 | 0.438 | 0.148 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.385 | 0.149 | 8 |
| chunk_ndcg@5 | 0.278 | 0.096 | 8 |
| page_fact_recall@1 | 0.250 | 0.134 | 8 |
| page_fact_recall@10 | 0.795 | 0.129 | 8 |
| page_fact_recall@20 | 0.795 | 0.129 | 8 |
| page_fact_recall@3 | 0.482 | 0.157 | 8 |
| page_fact_recall@5 | 0.670 | 0.158 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.510 | 0.155 | 8 |
| page_ndcg@5 | 0.382 | 0.102 | 8 |
| retrieved_tokens@1 | 335 | 37 | 8 |
| retrieved_tokens@10 | 3630 | 154 | 8 |
| retrieved_tokens@20 | 7446 | 188 | 8 |
| retrieved_tokens@3 | 1118 | 60 | 8 |
| retrieved_tokens@5 | 1859 | 73 | 8 |

## Token-matched k = 7 (target 2335 tokens)

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_fact_recall | 0.417 | 0.078 | 32 |
| chunk_hit | 0.531 | 0.088 | 32 |
| page_hit | 0.781 | 0.073 | 32 |
| tokens | 2431 | 62 | 32 |

## Lists

- page_hit_no_chunk: 52, 32, 10, 44, 35, 38, 89
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
| chunk_fact_recall@5 | 0.495 ± 0.081 (32) | 0.375 ± 0.077 (32) | -0.120 |
| retrieved_tokens@5 | 2335 ± 45 (32) | 1714 ± 47 (32) | -621 |
| chunk_all_required@1 | 0.125 ± 0.058 (32) | 0.156 ± 0.064 (32) | +0.031 |
| chunk_all_required@10 | 0.469 ± 0.088 (32) | 0.438 ± 0.088 (32) | -0.031 |
| chunk_all_required@20 | 0.562 ± 0.088 (32) | 0.500 ± 0.088 (32) | -0.062 |
| chunk_all_required@3 | 0.312 ± 0.082 (32) | 0.250 ± 0.077 (32) | -0.062 |
| chunk_all_required@5 | 0.406 ± 0.087 (32) | 0.281 ± 0.079 (32) | -0.125 |
| chunk_fact_recall@1 | 0.177 ± 0.061 (32) | 0.193 ± 0.066 (32) | +0.016 |
| chunk_fact_recall@10 | 0.589 ± 0.078 (32) | 0.521 ± 0.081 (32) | -0.068 |
| chunk_fact_recall@20 | 0.677 ± 0.073 (32) | 0.620 ± 0.075 (32) | -0.057 |
| chunk_fact_recall@3 | 0.417 ± 0.078 (32) | 0.318 ± 0.076 (32) | -0.099 |
| chunk_hit@1 | 0.250 ± 0.077 (32) | 0.250 ± 0.077 (32) | +0.000 |
| chunk_hit@10 | 0.688 ± 0.082 (32) | 0.625 ± 0.086 (32) | -0.062 |
| chunk_hit@20 | 0.781 ± 0.073 (32) | 0.750 ± 0.077 (32) | -0.031 |
| chunk_hit@3 | 0.531 ± 0.088 (32) | 0.406 ± 0.087 (32) | -0.125 |
| chunk_hit@5 | 0.594 ± 0.087 (32) | 0.500 ± 0.088 (32) | -0.094 |
| chunk_mrr | 0.380 ± 0.071 (32) | 0.336 ± 0.074 (32) | -0.044 |
| chunk_ndcg@5 | 0.295 ± 0.056 (32) | 0.276 ± 0.059 (32) | -0.019 |
| page_fact_recall@1 | 0.318 ± 0.082 (32) | 0.292 ± 0.077 (32) | -0.027 |
| page_fact_recall@10 | 0.761 ± 0.071 (32) | 0.657 ± 0.077 (32) | -0.104 |
| page_fact_recall@20 | 0.792 ± 0.067 (32) | 0.756 ± 0.068 (32) | -0.036 |
| page_fact_recall@3 | 0.579 ± 0.082 (32) | 0.428 ± 0.082 (32) | -0.151 |
| page_fact_recall@5 | 0.641 ± 0.076 (32) | 0.563 ± 0.081 (32) | -0.078 |
| page_hit@1 | 0.438 ± 0.088 (32) | 0.375 ± 0.086 (32) | -0.062 |
| page_hit@10 | 0.844 ± 0.064 (32) | 0.812 ± 0.069 (32) | -0.031 |
| page_hit@20 | 0.875 ± 0.058 (32) | 0.875 ± 0.058 (32) | +0.000 |
| page_hit@3 | 0.688 ± 0.082 (32) | 0.531 ± 0.088 (32) | -0.156 |
| page_hit@5 | 0.812 ± 0.069 (32) | 0.719 ± 0.079 (32) | -0.094 |
| page_mrr | 0.575 ± 0.072 (32) | 0.492 ± 0.076 (32) | -0.083 |
| page_ndcg@5 | 0.511 ± 0.065 (32) | 0.436 ± 0.067 (32) | -0.075 |
| retrieved_tokens@1 | 444 ± 23 (32) | 321 ± 24 (32) | -123 |
| retrieved_tokens@10 | 4639 ± 78 (32) | 3553 ± 89 (32) | -1086 |
| retrieved_tokens@20 | 9441 ± 100 (32) | 7246 ± 120 (32) | -2195 |
| retrieved_tokens@3 | 1396 ± 31 (32) | 1011 ± 37 (32) | -385 |

### Token-matched k (baseline k=5, this run k=7)

| metric | baseline @5 | this run @matched | delta |
|---|---|---|---|
| tokens | 2335 ± 45 (32) | 2431 ± 62 (32) | +96 |
| chunk_fact_recall | 0.495 ± 0.081 (32) | 0.417 ± 0.078 (32) | -0.078 |
| chunk_hit | 0.594 ± 0.087 (32) | 0.531 ± 0.088 (32) | -0.062 |
| page_hit | 0.812 ± 0.069 (32) | 0.781 ± 0.073 (32) | -0.031 |
| chunk_fact_recall@5 (both at k=5) | 0.495 ± 0.081 (32) | 0.375 ± 0.077 (32) | -0.120 |

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
| 8 | best relevant chunk | — | 3 · Approved Office Supplies List > Legal entities |
| 10 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 10 | chunk_hit@5 | 0.000 | 0.000 |
| 10 | page_hit@5 | 1.000 | 1.000 |
| 10 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 10 | best relevant chunk | — | — |
| 99 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 99 | chunk_hit@5 | 0.000 | 0.000 |
| 99 | page_hit@5 | 1.000 | 0.000 |
| 99 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 99 | best relevant chunk | — | — |
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
| 11 | chunk_fact_recall@5 | 0.333 | 0.333 |
| 11 | chunk_hit@5 | 1.000 | 1.000 |
| 11 | page_hit@5 | 1.000 | 1.000 |
| 11 | chunk_fact_recall@matched | 0.333 | 0.333 |
| 11 | best relevant chunk | 2 · Shipping Locations | 4 · New Hire Laptop Ordering Process |
| 34 | chunk_fact_recall@5 | 0.667 | 0.333 |
| 34 | chunk_hit@5 | 1.000 | 1.000 |
| 34 | page_hit@5 | 1.000 | 1.000 |
| 34 | chunk_fact_recall@matched | 0.667 | 0.667 |
| 34 | best relevant chunk | 1 · Team Member | 1 · How To Apply for a Long-Term Relocation > Approvals Phase > Relocations To New Country or Different Location Factor |
| 44 | chunk_fact_recall@5 | 1.000 | 0.000 |
| 44 | chunk_hit@5 | 1.000 | 0.000 |
| 44 | page_hit@5 | 1.000 | 1.000 |
| 44 | chunk_fact_recall@matched | 1.000 | 0.000 |
| 44 | best relevant chunk | 3 · Customer Experience | — |
| 49 | chunk_fact_recall@5 | 1.000 | 0.000 |
| 49 | chunk_hit@5 | 1.000 | 0.000 |
| 49 | page_hit@5 | 1.000 | 0.000 |
| 49 | chunk_fact_recall@matched | 1.000 | 0.500 |
| 49 | best relevant chunk | 4 · Shipping Locations | — |
| 51 | chunk_fact_recall@5 | 1.000 | 0.500 |
| 51 | chunk_hit@5 | 1.000 | 1.000 |
| 51 | page_hit@5 | 1.000 | 1.000 |
| 51 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 51 | best relevant chunk | 1 · Equipment | 3 · 4. PROCEDURES > 4.1 NON-TRAVEL RELATED EXPENSES > Equipment |
| 58 | chunk_fact_recall@5 | 0.500 | 0.000 |
| 58 | chunk_hit@5 | 1.000 | 0.000 |
| 58 | page_hit@5 | 1.000 | 0.000 |
| 58 | chunk_fact_recall@matched | 0.500 | 0.000 |
| 58 | best relevant chunk | 3 · Time Off Types | — |
| 88 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 88 | chunk_hit@5 | 1.000 | 1.000 |
| 88 | page_hit@5 | 1.000 | 1.000 |
| 88 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 88 | best relevant chunk | 1 · Timeline | 4 · FY26 Talent Assessment > Cadence |
| 100 | chunk_fact_recall@5 | 1.000 | 0.500 |
| 100 | chunk_hit@5 | 1.000 | 1.000 |
| 100 | page_hit@5 | 1.000 | 1.000 |
| 100 | chunk_fact_recall@matched | 1.000 | 0.500 |
| 100 | best relevant chunk | 1 · Overview | 4 · Time Off Types |
| 5 | chunk_fact_recall@5 | 0.333 | 0.333 |
| 5 | chunk_hit@5 | 1.000 | 1.000 |
| 5 | page_hit@5 | 1.000 | 1.000 |
| 5 | chunk_fact_recall@matched | 0.333 | 0.333 |
| 5 | best relevant chunk | 1 · Sick Time Eligibility and Coverage | 1 · Sick Time > For Sick Absences 1-5 Consecutive Days |
| 32 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 32 | chunk_hit@5 | 0.000 | 0.000 |
| 32 | page_hit@5 | 0.000 | 1.000 |
| 32 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 32 | best relevant chunk | — | — |
| 35 | chunk_fact_recall@5 | 0.500 | 0.000 |
| 35 | chunk_hit@5 | 1.000 | 0.000 |
| 35 | page_hit@5 | 1.000 | 1.000 |
| 35 | chunk_fact_recall@matched | 0.500 | 0.000 |
| 35 | best relevant chunk | 2 · Termination | — |
| 87 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 87 | chunk_hit@5 | 0.000 | 0.000 |
| 87 | page_hit@5 | 0.000 | 0.000 |
| 87 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 87 | best relevant chunk | — | — |
