# Eval summary

## Takeaways

- **The prefix helps structural chunks, but v3 still trails.** v3 is v2 plus the title and heading path in the embedded text. Against v2: recall@5 went from 0.375 to 0.422 and page_hit@5 from 0.719 to 0.812, the baseline's level. Paired, it is +0.047 ± 0.047: rows 5, 34, 49, 51 and 58 win, and 88 loses.
- **Against the prefixed baseline (both changes together):** at the matched k=7, recall is 0.469 against 0.531: −0.063, within the SE, so no difference. At k=5, paired, it is −0.109 ± 0.054: rows 35, 44, 58, 88, 89 and 100 lose, and row 8 wins.
- **Row 88 regressed:** v2 found it at rank 4, v3 didn't. With the prefix, the Timeline continuation chunk (504 tokens, same title and path as the first Timeline chunk) and a data-engineering "Quarter calendar" chunk entered the top 5 and pushed out the Cadence chunk that holds the fact.
- **Next:** none for structural chunking (stop rule). The prefix is judged on the fixed comparison.

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: 21334f046d3d073e3387f6c3c131ad1de47e0868
- harness_dirty: False
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- config_id: structural-v3
- chunk_params: {'strategy': 'structural-packed', 'overlap': 64, 'max_tokens': 512, 'embed_prefix': 'title-path', 'tokenizer': 'cl100k_base'}
- embed_model: openai:text-embedding-3-small
- answer_model: None
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- eval_depth: 20
- timestamp: 2026-10-19T14:34:56.210616+00:00
- rows: 33
- mode: retrieval-only
- limit: None
- baseline: 2026-10-19-d2625d91

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.058 | 32 |
| chunk_all_required@10 | 0.438 | 0.088 | 32 |
| chunk_all_required@20 | 0.562 | 0.088 | 32 |
| chunk_all_required@3 | 0.250 | 0.077 | 32 |
| chunk_all_required@5 | 0.312 | 0.082 | 32 |
| chunk_fact_recall@1 | 0.177 | 0.061 | 32 |
| chunk_fact_recall@10 | 0.542 | 0.079 | 32 |
| chunk_fact_recall@20 | 0.659 | 0.075 | 32 |
| chunk_fact_recall@3 | 0.359 | 0.074 | 32 |
| chunk_fact_recall@5 | 0.422 | 0.078 | 32 |
| chunk_hit@1 | 0.250 | 0.077 | 32 |
| chunk_hit@10 | 0.656 | 0.084 | 32 |
| chunk_hit@20 | 0.781 | 0.073 | 32 |
| chunk_hit@3 | 0.500 | 0.088 | 32 |
| chunk_hit@5 | 0.531 | 0.088 | 32 |
| chunk_mrr | 0.367 | 0.073 | 32 |
| chunk_ndcg@5 | 0.309 | 0.061 | 32 |
| page_fact_recall@1 | 0.454 | 0.083 | 32 |
| page_fact_recall@10 | 0.662 | 0.077 | 32 |
| page_fact_recall@20 | 0.779 | 0.065 | 32 |
| page_fact_recall@3 | 0.563 | 0.081 | 32 |
| page_fact_recall@5 | 0.615 | 0.078 | 32 |
| page_hit@1 | 0.594 | 0.087 | 32 |
| page_hit@10 | 0.812 | 0.069 | 32 |
| page_hit@20 | 0.875 | 0.058 | 32 |
| page_hit@3 | 0.750 | 0.077 | 32 |
| page_hit@5 | 0.812 | 0.069 | 32 |
| page_mrr | 0.681 | 0.074 | 32 |
| page_ndcg@5 | 0.549 | 0.063 | 32 |
| retrieved_tokens@1 | 342 | 23 | 32 |
| retrieved_tokens@10 | 3574 | 94 | 32 |
| retrieved_tokens@20 | 7312 | 129 | 32 |
| retrieved_tokens@3 | 1024 | 44 | 32 |
| retrieved_tokens@5 | 1759 | 65 | 32 |

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.688 | 0.132 | 8 |
| chunk_fact_recall@20 | 0.812 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.438 | 0.148 | 8 |
| chunk_fact_recall@5 | 0.500 | 0.134 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.448 | 0.138 | 8 |
| chunk_ndcg@5 | 0.373 | 0.118 | 8 |
| page_fact_recall@1 | 0.420 | 0.168 | 8 |
| page_fact_recall@10 | 0.857 | 0.080 | 8 |
| page_fact_recall@20 | 0.920 | 0.062 | 8 |
| page_fact_recall@3 | 0.670 | 0.158 | 8 |
| page_fact_recall@5 | 0.732 | 0.130 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 1.000 | 0.000 | 8 |
| page_mrr | 0.781 | 0.110 | 8 |
| page_ndcg@5 | 0.630 | 0.094 | 8 |
| retrieved_tokens@1 | 389 | 46 | 8 |
| retrieved_tokens@10 | 3883 | 117 | 8 |
| retrieved_tokens@20 | 7684 | 113 | 8 |
| retrieved_tokens@3 | 1194 | 66 | 8 |
| retrieved_tokens@5 | 1902 | 75 | 8 |

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.250 | 0.153 | 8 |
| chunk_all_required@10 | 0.750 | 0.153 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.625 | 0.171 | 8 |
| chunk_all_required@5 | 0.625 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.250 | 0.164 | 8 |
| chunk_fact_recall@10 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@3 | 0.625 | 0.183 | 8 |
| chunk_fact_recall@5 | 0.625 | 0.183 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.417 | 0.148 | 8 |
| chunk_ndcg@5 | 0.421 | 0.140 | 8 |
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
| page_ndcg@5 | 0.660 | 0.154 | 8 |
| retrieved_tokens@1 | 335 | 40 | 8 |
| retrieved_tokens@10 | 3379 | 203 | 8 |
| retrieved_tokens@20 | 7009 | 340 | 8 |
| retrieved_tokens@3 | 916 | 121 | 8 |
| retrieved_tokens@5 | 1664 | 148 | 8 |

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.250 | 0.153 | 8 |
| chunk_all_required@20 | 0.500 | 0.177 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.354 | 0.156 | 8 |
| chunk_fact_recall@20 | 0.667 | 0.137 | 8 |
| chunk_fact_recall@3 | 0.292 | 0.129 | 8 |
| chunk_fact_recall@5 | 0.354 | 0.156 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.500 | 0.177 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.500 | 0.177 | 8 |
| chunk_mrr | 0.354 | 0.156 | 8 |
| chunk_ndcg@5 | 0.261 | 0.108 | 8 |
| page_fact_recall@1 | 0.417 | 0.175 | 8 |
| page_fact_recall@10 | 0.479 | 0.165 | 8 |
| page_fact_recall@20 | 0.729 | 0.141 | 8 |
| page_fact_recall@3 | 0.479 | 0.165 | 8 |
| page_fact_recall@5 | 0.479 | 0.165 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.604 | 0.160 | 8 |
| page_ndcg@5 | 0.412 | 0.119 | 8 |
| retrieved_tokens@1 | 324 | 54 | 8 |
| retrieved_tokens@10 | 3299 | 200 | 8 |
| retrieved_tokens@20 | 7113 | 234 | 8 |
| retrieved_tokens@3 | 934 | 62 | 8 |
| retrieved_tokens@5 | 1588 | 158 | 8 |

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.250 | 0.153 | 8 |
| chunk_all_required@20 | 0.250 | 0.153 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.083 | 0.055 | 8 |
| chunk_fact_recall@10 | 0.375 | 0.157 | 8 |
| chunk_fact_recall@20 | 0.406 | 0.149 | 8 |
| chunk_fact_recall@3 | 0.083 | 0.055 | 8 |
| chunk_fact_recall@5 | 0.208 | 0.140 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.500 | 0.177 | 8 |
| chunk_hit@20 | 0.625 | 0.171 | 8 |
| chunk_hit@3 | 0.250 | 0.153 | 8 |
| chunk_hit@5 | 0.250 | 0.153 | 8 |
| chunk_mrr | 0.250 | 0.164 | 8 |
| chunk_ndcg@5 | 0.183 | 0.122 | 8 |
| page_fact_recall@1 | 0.354 | 0.156 | 8 |
| page_fact_recall@10 | 0.562 | 0.175 | 8 |
| page_fact_recall@20 | 0.719 | 0.145 | 8 |
| page_fact_recall@3 | 0.354 | 0.156 | 8 |
| page_fact_recall@5 | 0.500 | 0.164 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.650 | 0.172 | 8 |
| page_ndcg@5 | 0.494 | 0.133 | 8 |
| retrieved_tokens@1 | 319 | 45 | 8 |
| retrieved_tokens@10 | 3736 | 164 | 8 |
| retrieved_tokens@20 | 7442 | 269 | 8 |
| retrieved_tokens@3 | 1051 | 66 | 8 |
| retrieved_tokens@5 | 1880 | 109 | 8 |

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.375 | 0.171 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.125 | 0.125 | 8 |
| chunk_fact_recall@10 | 0.479 | 0.165 | 8 |
| chunk_fact_recall@20 | 0.729 | 0.141 | 8 |
| chunk_fact_recall@3 | 0.229 | 0.130 | 8 |
| chunk_fact_recall@5 | 0.354 | 0.156 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.500 | 0.177 | 8 |
| chunk_mrr | 0.260 | 0.125 | 8 |
| chunk_ndcg@5 | 0.265 | 0.130 | 8 |
| page_fact_recall@1 | 0.292 | 0.160 | 8 |
| page_fact_recall@10 | 0.542 | 0.150 | 8 |
| page_fact_recall@20 | 0.729 | 0.141 | 8 |
| page_fact_recall@3 | 0.354 | 0.156 | 8 |
| page_fact_recall@5 | 0.417 | 0.148 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.635 | 0.146 | 8 |
| page_ndcg@5 | 0.494 | 0.127 | 8 |
| retrieved_tokens@1 | 290 | 57 | 8 |
| retrieved_tokens@10 | 3431 | 196 | 8 |
| retrieved_tokens@20 | 7213 | 211 | 8 |
| retrieved_tokens@3 | 946 | 55 | 8 |
| retrieved_tokens@5 | 1579 | 136 | 8 |

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.375 | 0.171 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.250 | 0.134 | 8 |
| chunk_fact_recall@10 | 0.562 | 0.148 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.134 | 8 |
| chunk_fact_recall@3 | 0.500 | 0.134 | 8 |
| chunk_fact_recall@5 | 0.500 | 0.134 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.750 | 0.153 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.542 | 0.150 | 8 |
| chunk_ndcg@5 | 0.368 | 0.093 | 8 |
| page_fact_recall@1 | 0.545 | 0.170 | 8 |
| page_fact_recall@10 | 0.795 | 0.129 | 8 |
| page_fact_recall@20 | 0.920 | 0.062 | 8 |
| page_fact_recall@3 | 0.795 | 0.129 | 8 |
| page_fact_recall@5 | 0.795 | 0.129 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.750 | 0.134 | 8 |
| page_ndcg@5 | 0.549 | 0.101 | 8 |
| retrieved_tokens@1 | 424 | 27 | 8 |
| retrieved_tokens@10 | 3752 | 179 | 8 |
| retrieved_tokens@20 | 7584 | 191 | 8 |
| retrieved_tokens@3 | 1182 | 78 | 8 |
| retrieved_tokens@5 | 1911 | 106 | 8 |

## Token-matched k = 7 (target 2335 tokens)

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_fact_recall | 0.469 | 0.081 | 32 |
| chunk_hit | 0.562 | 0.088 | 32 |
| page_hit | 0.812 | 0.069 | 32 |
| tokens | 2484 | 76 | 32 |

## Lists

- page_hit_no_chunk: 52, 53, 10, 44, 99, 35, 38, 88, 89
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
| chunk_fact_recall@5 | 0.495 ± 0.081 (32) | 0.422 ± 0.078 (32) | -0.073 |
| retrieved_tokens@5 | 2335 ± 45 (32) | 1759 ± 65 (32) | -576 |
| chunk_all_required@1 | 0.125 ± 0.058 (32) | 0.125 ± 0.058 (32) | +0.000 |
| chunk_all_required@10 | 0.469 ± 0.088 (32) | 0.438 ± 0.088 (32) | -0.031 |
| chunk_all_required@20 | 0.562 ± 0.088 (32) | 0.562 ± 0.088 (32) | +0.000 |
| chunk_all_required@3 | 0.312 ± 0.082 (32) | 0.250 ± 0.077 (32) | -0.062 |
| chunk_all_required@5 | 0.406 ± 0.087 (32) | 0.312 ± 0.082 (32) | -0.094 |
| chunk_fact_recall@1 | 0.177 ± 0.061 (32) | 0.177 ± 0.061 (32) | +0.000 |
| chunk_fact_recall@10 | 0.589 ± 0.078 (32) | 0.542 ± 0.079 (32) | -0.047 |
| chunk_fact_recall@20 | 0.677 ± 0.073 (32) | 0.659 ± 0.075 (32) | -0.018 |
| chunk_fact_recall@3 | 0.417 ± 0.078 (32) | 0.359 ± 0.074 (32) | -0.057 |
| chunk_hit@1 | 0.250 ± 0.077 (32) | 0.250 ± 0.077 (32) | +0.000 |
| chunk_hit@10 | 0.688 ± 0.082 (32) | 0.656 ± 0.084 (32) | -0.031 |
| chunk_hit@20 | 0.781 ± 0.073 (32) | 0.781 ± 0.073 (32) | +0.000 |
| chunk_hit@3 | 0.531 ± 0.088 (32) | 0.500 ± 0.088 (32) | -0.031 |
| chunk_hit@5 | 0.594 ± 0.087 (32) | 0.531 ± 0.088 (32) | -0.062 |
| chunk_mrr | 0.380 ± 0.071 (32) | 0.367 ± 0.073 (32) | -0.013 |
| chunk_ndcg@5 | 0.295 ± 0.056 (32) | 0.309 ± 0.061 (32) | +0.014 |
| page_fact_recall@1 | 0.318 ± 0.082 (32) | 0.454 ± 0.083 (32) | +0.135 |
| page_fact_recall@10 | 0.761 ± 0.071 (32) | 0.662 ± 0.077 (32) | -0.099 |
| page_fact_recall@20 | 0.792 ± 0.067 (32) | 0.779 ± 0.065 (32) | -0.013 |
| page_fact_recall@3 | 0.579 ± 0.082 (32) | 0.563 ± 0.081 (32) | -0.016 |
| page_fact_recall@5 | 0.641 ± 0.076 (32) | 0.615 ± 0.078 (32) | -0.026 |
| page_hit@1 | 0.438 ± 0.088 (32) | 0.594 ± 0.087 (32) | +0.156 |
| page_hit@10 | 0.844 ± 0.064 (32) | 0.812 ± 0.069 (32) | -0.031 |
| page_hit@20 | 0.875 ± 0.058 (32) | 0.875 ± 0.058 (32) | +0.000 |
| page_hit@3 | 0.688 ± 0.082 (32) | 0.750 ± 0.077 (32) | +0.062 |
| page_hit@5 | 0.812 ± 0.069 (32) | 0.812 ± 0.069 (32) | +0.000 |
| page_mrr | 0.575 ± 0.072 (32) | 0.681 ± 0.074 (32) | +0.106 |
| page_ndcg@5 | 0.511 ± 0.065 (32) | 0.549 ± 0.063 (32) | +0.038 |
| retrieved_tokens@1 | 444 ± 23 (32) | 342 ± 23 (32) | -102 |
| retrieved_tokens@10 | 4639 ± 78 (32) | 3574 ± 94 (32) | -1065 |
| retrieved_tokens@20 | 9441 ± 100 (32) | 7312 ± 129 (32) | -2130 |
| retrieved_tokens@3 | 1396 ± 31 (32) | 1024 ± 44 (32) | -372 |

### Token-matched k (baseline k=5, this run k=7)

| metric | baseline @5 | this run @matched | delta |
|---|---|---|---|
| tokens | 2335 ± 45 (32) | 2484 ± 76 (32) | +149 |
| chunk_fact_recall | 0.495 ± 0.081 (32) | 0.469 ± 0.081 (32) | -0.026 |
| chunk_hit | 0.594 ± 0.087 (32) | 0.562 ± 0.088 (32) | -0.031 |
| page_hit | 0.812 ± 0.069 (32) | 0.812 ± 0.069 (32) | +0.000 |
| chunk_fact_recall@5 (both at k=5) | 0.495 ± 0.081 (32) | 0.422 ± 0.078 (32) | -0.073 |

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
| 8 | chunk_fact_recall@5 | 0.000 | 0.500 |
| 8 | chunk_hit@5 | 0.000 | 1.000 |
| 8 | page_hit@5 | 1.000 | 1.000 |
| 8 | chunk_fact_recall@matched | 0.000 | 1.000 |
| 8 | best relevant chunk | — | 2 · Expenses > Team Member Reimbursements - Navan > Processing Navan Reports |
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
| 89 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 89 | chunk_hit@5 | 0.000 | 0.000 |
| 89 | page_hit@5 | 1.000 | 1.000 |
| 89 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 89 | best relevant chunk | — | — |
| 11 | chunk_fact_recall@5 | 0.333 | 0.333 |
| 11 | chunk_hit@5 | 1.000 | 1.000 |
| 11 | page_hit@5 | 1.000 | 1.000 |
| 11 | chunk_fact_recall@matched | 0.333 | 0.333 |
| 11 | best relevant chunk | 2 · Shipping Locations | 3 · New Hire Laptop Ordering Process |
| 34 | chunk_fact_recall@5 | 0.667 | 0.667 |
| 34 | chunk_hit@5 | 1.000 | 1.000 |
| 34 | page_hit@5 | 1.000 | 1.000 |
| 34 | chunk_fact_recall@matched | 0.667 | 0.667 |
| 34 | best relevant chunk | 1 · Team Member | 1 · How To Apply for a Long-Term Relocation > Approvals Phase > Relocations To New Country or Different Location Factor |
| 44 | chunk_fact_recall@5 | 1.000 | 0.000 |
| 44 | chunk_hit@5 | 1.000 | 0.000 |
| 44 | page_hit@5 | 1.000 | 1.000 |
| 44 | chunk_fact_recall@matched | 1.000 | 0.000 |
| 44 | best relevant chunk | 3 · Customer Experience | — |
| 49 | chunk_fact_recall@5 | 1.000 | 0.500 |
| 49 | chunk_hit@5 | 1.000 | 1.000 |
| 49 | page_hit@5 | 1.000 | 1.000 |
| 49 | chunk_fact_recall@matched | 1.000 | 0.500 |
| 49 | best relevant chunk | 4 · Shipping Locations | 4 · New Hire Laptop Ordering Process |
| 51 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 51 | chunk_hit@5 | 1.000 | 1.000 |
| 51 | page_hit@5 | 1.000 | 1.000 |
| 51 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 51 | best relevant chunk | 1 · Equipment | 2 · 4. PROCEDURES > 4.1 NON-TRAVEL RELATED EXPENSES > Equipment |
| 58 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 58 | chunk_hit@5 | 1.000 | 1.000 |
| 58 | page_hit@5 | 1.000 | 1.000 |
| 58 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 58 | best relevant chunk | 3 · Time Off Types | 1 · Time Off Types |
| 88 | chunk_fact_recall@5 | 1.000 | 0.000 |
| 88 | chunk_hit@5 | 1.000 | 0.000 |
| 88 | page_hit@5 | 1.000 | 1.000 |
| 88 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 88 | best relevant chunk | 1 · Timeline | — |
| 100 | chunk_fact_recall@5 | 1.000 | 0.500 |
| 100 | chunk_hit@5 | 1.000 | 1.000 |
| 100 | page_hit@5 | 1.000 | 1.000 |
| 100 | chunk_fact_recall@matched | 1.000 | 0.500 |
| 100 | best relevant chunk | 1 · Overview | 3 · Time Off Types |
| 5 | chunk_fact_recall@5 | 0.333 | 1.000 |
| 5 | chunk_hit@5 | 1.000 | 1.000 |
| 5 | page_hit@5 | 1.000 | 1.000 |
| 5 | chunk_fact_recall@matched | 0.333 | 1.000 |
| 5 | best relevant chunk | 1 · Sick Time Eligibility and Coverage | 1 · Sick Time > For Sick Absences 1-5 Consecutive Days |
| 32 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 32 | chunk_hit@5 | 0.000 | 0.000 |
| 32 | page_hit@5 | 0.000 | 0.000 |
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
