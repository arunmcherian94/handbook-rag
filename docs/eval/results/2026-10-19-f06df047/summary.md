# Eval summary

## Takeaways

- **structural-v1 re-scored at depth 20, to compare at a matched token budget.** recall@5 0.358 is unchanged from 62a52a83. At the matched k=13 (2,284 tokens) it is 0.421 against the baseline's 0.495: −0.074, within the SE (0.081), so "no difference" under the spec 0006 rule. (The 19 Oct preview's 0.442 cut by a token budget, not by k.)
- At k=5, paired over the same rows, it is −0.136 ± 0.059: 8 rows lose (11, 34, 44, 49, 51, 58, 88, 100) and only row 8 wins.
- Row 52 is a near-tie: the k=5 and depth-20 lists disagree on the top 5, so its @5 and @10 metrics come from different lists.
- **Next:** none. v1 is superseded by v2 and v3, and structural chunking is not adopted ([ADR-0019](../../../decisions/0019-structural-first-recursive-inside-chunking.md)).

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: 21334f046d3d073e3387f6c3c131ad1de47e0868
- harness_dirty: False
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- config_id: structural-v1
- chunk_params: {'strategy': 'structural', 'overlap': 64, 'max_tokens': 512, 'min_tokens': 64, 'tokenizer': 'cl100k_base'}
- embed_model: openai:text-embedding-3-small
- answer_model: None
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- eval_depth: 20
- timestamp: 2026-10-19T14:31:27.611136+00:00
- rows: 33
- mode: retrieval-only
- limit: None
- baseline: 2026-10-19-d2625d91

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.058 | 32 |
| chunk_all_required@10 | 0.250 | 0.077 | 32 |
| chunk_all_required@20 | 0.375 | 0.086 | 32 |
| chunk_all_required@3 | 0.156 | 0.064 | 32 |
| chunk_all_required@5 | 0.250 | 0.077 | 32 |
| chunk_fact_recall@1 | 0.161 | 0.061 | 32 |
| chunk_fact_recall@10 | 0.410 | 0.074 | 32 |
| chunk_fact_recall@20 | 0.499 | 0.079 | 32 |
| chunk_fact_recall@3 | 0.255 | 0.067 | 32 |
| chunk_fact_recall@5 | 0.358 | 0.076 | 32 |
| chunk_hit@1 | 0.219 | 0.073 | 32 |
| chunk_hit@10 | 0.562 | 0.088 | 32 |
| chunk_hit@20 | 0.625 | 0.086 | 32 |
| chunk_hit@3 | 0.375 | 0.086 | 32 |
| chunk_hit@5 | 0.469 | 0.088 | 32 |
| chunk_mrr | 0.308 | 0.072 | 32 |
| chunk_ndcg@5 | 0.247 | 0.057 | 32 |
| page_fact_recall@1 | 0.334 | 0.081 | 32 |
| page_fact_recall@10 | 0.647 | 0.079 | 32 |
| page_fact_recall@20 | 0.761 | 0.071 | 32 |
| page_fact_recall@3 | 0.459 | 0.083 | 32 |
| page_fact_recall@5 | 0.563 | 0.081 | 32 |
| page_hit@1 | 0.375 | 0.086 | 32 |
| page_hit@10 | 0.719 | 0.079 | 32 |
| page_hit@20 | 0.875 | 0.058 | 32 |
| page_hit@3 | 0.562 | 0.088 | 32 |
| page_hit@5 | 0.688 | 0.082 | 32 |
| page_mrr | 0.486 | 0.077 | 32 |
| page_ndcg@5 | 0.425 | 0.068 | 32 |
| retrieved_tokens@1 | 133 | 23 | 32 |
| retrieved_tokens@10 | 1737 | 120 | 32 |
| retrieved_tokens@20 | 3684 | 187 | 32 |
| retrieved_tokens@3 | 476 | 52 | 32 |
| retrieved_tokens@5 | 815 | 70 | 32 |

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.250 | 0.153 | 8 |
| chunk_all_required@20 | 0.375 | 0.171 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.475 | 0.154 | 8 |
| chunk_fact_recall@20 | 0.537 | 0.168 | 8 |
| chunk_fact_recall@3 | 0.250 | 0.134 | 8 |
| chunk_fact_recall@5 | 0.475 | 0.154 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.625 | 0.171 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.369 | 0.150 | 8 |
| chunk_ndcg@5 | 0.309 | 0.122 | 8 |
| page_fact_recall@1 | 0.295 | 0.152 | 8 |
| page_fact_recall@10 | 0.732 | 0.130 | 8 |
| page_fact_recall@20 | 0.795 | 0.129 | 8 |
| page_fact_recall@3 | 0.482 | 0.157 | 8 |
| page_fact_recall@5 | 0.732 | 0.130 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.573 | 0.137 | 8 |
| page_ndcg@5 | 0.491 | 0.105 | 8 |
| retrieved_tokens@1 | 222 | 63 | 8 |
| retrieved_tokens@10 | 2041 | 197 | 8 |
| retrieved_tokens@20 | 3932 | 370 | 8 |
| retrieved_tokens@3 | 664 | 104 | 8 |
| retrieved_tokens@5 | 1012 | 143 | 8 |

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.250 | 0.153 | 8 |
| chunk_all_required@10 | 0.625 | 0.171 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.625 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.250 | 0.164 | 8 |
| chunk_fact_recall@10 | 0.625 | 0.183 | 8 |
| chunk_fact_recall@20 | 0.625 | 0.183 | 8 |
| chunk_fact_recall@3 | 0.438 | 0.175 | 8 |
| chunk_fact_recall@5 | 0.625 | 0.183 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.625 | 0.171 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.385 | 0.149 | 8 |
| chunk_ndcg@5 | 0.392 | 0.147 | 8 |
| page_fact_recall@1 | 0.625 | 0.183 | 8 |
| page_fact_recall@10 | 0.750 | 0.164 | 8 |
| page_fact_recall@20 | 0.875 | 0.125 | 8 |
| page_fact_recall@3 | 0.750 | 0.164 | 8 |
| page_fact_recall@5 | 0.750 | 0.164 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.688 | 0.162 | 8 |
| page_ndcg@5 | 0.638 | 0.156 | 8 |
| retrieved_tokens@1 | 102 | 37 | 8 |
| retrieved_tokens@10 | 1726 | 229 | 8 |
| retrieved_tokens@20 | 3652 | 343 | 8 |
| retrieved_tokens@3 | 483 | 67 | 8 |
| retrieved_tokens@5 | 788 | 102 | 8 |

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.125 | 0.117 | 8 |
| chunk_all_required@20 | 0.375 | 0.171 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.125 | 0.125 | 8 |
| chunk_fact_recall@10 | 0.292 | 0.129 | 8 |
| chunk_fact_recall@20 | 0.479 | 0.165 | 8 |
| chunk_fact_recall@3 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@5 | 0.188 | 0.132 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.500 | 0.177 | 8 |
| chunk_hit@20 | 0.625 | 0.171 | 8 |
| chunk_hit@3 | 0.250 | 0.153 | 8 |
| chunk_hit@5 | 0.250 | 0.153 | 8 |
| chunk_mrr | 0.167 | 0.126 | 8 |
| chunk_ndcg@5 | 0.115 | 0.081 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@10 | 0.562 | 0.175 | 8 |
| page_fact_recall@20 | 0.562 | 0.175 | 8 |
| page_fact_recall@3 | 0.312 | 0.162 | 8 |
| page_fact_recall@5 | 0.479 | 0.165 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@10 | 0.625 | 0.171 | 8 |
| page_hit@20 | 0.750 | 0.153 | 8 |
| page_hit@3 | 0.375 | 0.171 | 8 |
| page_hit@5 | 0.625 | 0.171 | 8 |
| page_mrr | 0.348 | 0.149 | 8 |
| page_ndcg@5 | 0.302 | 0.128 | 8 |
| retrieved_tokens@1 | 69 | 18 | 8 |
| retrieved_tokens@10 | 1594 | 244 | 8 |
| retrieved_tokens@20 | 3584 | 223 | 8 |
| retrieved_tokens@3 | 406 | 99 | 8 |
| retrieved_tokens@5 | 769 | 162 | 8 |

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.000 | 0.000 | 8 |
| chunk_all_required@20 | 0.125 | 0.117 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@1 | 0.083 | 0.055 | 8 |
| chunk_fact_recall@10 | 0.250 | 0.100 | 8 |
| chunk_fact_recall@20 | 0.354 | 0.124 | 8 |
| chunk_fact_recall@3 | 0.146 | 0.073 | 8 |
| chunk_fact_recall@5 | 0.146 | 0.073 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.500 | 0.177 | 8 |
| chunk_hit@20 | 0.625 | 0.171 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.375 | 0.171 | 8 |
| chunk_mrr | 0.312 | 0.162 | 8 |
| chunk_ndcg@5 | 0.174 | 0.090 | 8 |
| page_fact_recall@1 | 0.167 | 0.126 | 8 |
| page_fact_recall@10 | 0.542 | 0.177 | 8 |
| page_fact_recall@20 | 0.812 | 0.132 | 8 |
| page_fact_recall@3 | 0.292 | 0.160 | 8 |
| page_fact_recall@5 | 0.292 | 0.160 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@10 | 0.625 | 0.171 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.375 | 0.171 | 8 |
| page_hit@5 | 0.500 | 0.177 | 8 |
| page_mrr | 0.338 | 0.157 | 8 |
| page_ndcg@5 | 0.269 | 0.132 | 8 |
| retrieved_tokens@1 | 138 | 46 | 8 |
| retrieved_tokens@10 | 1586 | 294 | 8 |
| retrieved_tokens@20 | 3568 | 553 | 8 |
| retrieved_tokens@3 | 350 | 119 | 8 |
| retrieved_tokens@5 | 692 | 145 | 8 |

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.125 | 0.117 | 8 |
| chunk_all_required@20 | 0.375 | 0.171 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.125 | 0.125 | 8 |
| chunk_fact_recall@10 | 0.392 | 0.135 | 8 |
| chunk_fact_recall@20 | 0.579 | 0.153 | 8 |
| chunk_fact_recall@3 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@5 | 0.287 | 0.148 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.250 | 0.153 | 8 |
| chunk_hit@5 | 0.375 | 0.171 | 8 |
| chunk_mrr | 0.192 | 0.124 | 8 |
| chunk_ndcg@5 | 0.186 | 0.123 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@10 | 0.688 | 0.162 | 8 |
| page_fact_recall@20 | 0.688 | 0.162 | 8 |
| page_fact_recall@3 | 0.312 | 0.162 | 8 |
| page_fact_recall@5 | 0.604 | 0.160 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.750 | 0.153 | 8 |
| page_hit@3 | 0.500 | 0.177 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.390 | 0.141 | 8 |
| page_ndcg@5 | 0.395 | 0.141 | 8 |
| retrieved_tokens@1 | 163 | 54 | 8 |
| retrieved_tokens@10 | 1887 | 166 | 8 |
| retrieved_tokens@20 | 3643 | 251 | 8 |
| retrieved_tokens@3 | 604 | 101 | 8 |
| retrieved_tokens@5 | 931 | 125 | 8 |

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.250 | 0.153 | 8 |
| chunk_all_required@20 | 0.375 | 0.171 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.375 | 0.157 | 8 |
| chunk_fact_recall@20 | 0.438 | 0.175 | 8 |
| chunk_fact_recall@3 | 0.250 | 0.134 | 8 |
| chunk_fact_recall@5 | 0.375 | 0.157 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.500 | 0.177 | 8 |
| chunk_hit@20 | 0.500 | 0.177 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.500 | 0.177 | 8 |
| chunk_mrr | 0.344 | 0.156 | 8 |
| chunk_ndcg@5 | 0.237 | 0.093 | 8 |
| page_fact_recall@1 | 0.295 | 0.152 | 8 |
| page_fact_recall@10 | 0.607 | 0.152 | 8 |
| page_fact_recall@20 | 0.670 | 0.158 | 8 |
| page_fact_recall@3 | 0.482 | 0.157 | 8 |
| page_fact_recall@5 | 0.607 | 0.152 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.531 | 0.153 | 8 |
| page_ndcg@5 | 0.397 | 0.100 | 8 |
| retrieved_tokens@1 | 128 | 55 | 8 |
| retrieved_tokens@10 | 1748 | 289 | 8 |
| retrieved_tokens@20 | 3872 | 358 | 8 |
| retrieved_tokens@3 | 466 | 118 | 8 |
| retrieved_tokens@5 | 850 | 186 | 8 |

## Token-matched k = 13 (target 2335 tokens)

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_fact_recall | 0.421 | 0.076 | 32 |
| chunk_hit | 0.562 | 0.088 | 32 |
| page_hit | 0.750 | 0.077 | 32 |
| tokens | 2284 | 142 | 32 |

## Lists

- page_hit_no_chunk: 11, 52, 53, 10, 100, 38, 88
- conflict_unscored: 53, 50, 58
- near_ties: 52

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
| chunk_fact_recall@5 | 0.495 ± 0.081 (32) | 0.358 ± 0.076 (32) | -0.136 |
| retrieved_tokens@5 | 2335 ± 45 (32) | 815 ± 70 (32) | -1520 |
| chunk_all_required@1 | 0.125 ± 0.058 (32) | 0.125 ± 0.058 (32) | +0.000 |
| chunk_all_required@10 | 0.469 ± 0.088 (32) | 0.250 ± 0.077 (32) | -0.219 |
| chunk_all_required@20 | 0.562 ± 0.088 (32) | 0.375 ± 0.086 (32) | -0.188 |
| chunk_all_required@3 | 0.312 ± 0.082 (32) | 0.156 ± 0.064 (32) | -0.156 |
| chunk_all_required@5 | 0.406 ± 0.087 (32) | 0.250 ± 0.077 (32) | -0.156 |
| chunk_fact_recall@1 | 0.177 ± 0.061 (32) | 0.161 ± 0.061 (32) | -0.016 |
| chunk_fact_recall@10 | 0.589 ± 0.078 (32) | 0.410 ± 0.074 (32) | -0.178 |
| chunk_fact_recall@20 | 0.677 ± 0.073 (32) | 0.499 ± 0.079 (32) | -0.178 |
| chunk_fact_recall@3 | 0.417 ± 0.078 (32) | 0.255 ± 0.067 (32) | -0.161 |
| chunk_hit@1 | 0.250 ± 0.077 (32) | 0.219 ± 0.073 (32) | -0.031 |
| chunk_hit@10 | 0.688 ± 0.082 (32) | 0.562 ± 0.088 (32) | -0.125 |
| chunk_hit@20 | 0.781 ± 0.073 (32) | 0.625 ± 0.086 (32) | -0.156 |
| chunk_hit@3 | 0.531 ± 0.088 (32) | 0.375 ± 0.086 (32) | -0.156 |
| chunk_hit@5 | 0.594 ± 0.087 (32) | 0.469 ± 0.088 (32) | -0.125 |
| chunk_mrr | 0.380 ± 0.071 (32) | 0.308 ± 0.072 (32) | -0.072 |
| chunk_ndcg@5 | 0.295 ± 0.056 (32) | 0.247 ± 0.057 (32) | -0.048 |
| page_fact_recall@1 | 0.318 ± 0.082 (32) | 0.334 ± 0.081 (32) | +0.016 |
| page_fact_recall@10 | 0.761 ± 0.071 (32) | 0.647 ± 0.079 (32) | -0.115 |
| page_fact_recall@20 | 0.792 ± 0.067 (32) | 0.761 ± 0.071 (32) | -0.031 |
| page_fact_recall@3 | 0.579 ± 0.082 (32) | 0.459 ± 0.083 (32) | -0.120 |
| page_fact_recall@5 | 0.641 ± 0.076 (32) | 0.563 ± 0.081 (32) | -0.078 |
| page_hit@1 | 0.438 ± 0.088 (32) | 0.375 ± 0.086 (32) | -0.062 |
| page_hit@10 | 0.844 ± 0.064 (32) | 0.719 ± 0.079 (32) | -0.125 |
| page_hit@20 | 0.875 ± 0.058 (32) | 0.875 ± 0.058 (32) | +0.000 |
| page_hit@3 | 0.688 ± 0.082 (32) | 0.562 ± 0.088 (32) | -0.125 |
| page_hit@5 | 0.812 ± 0.069 (32) | 0.688 ± 0.082 (32) | -0.125 |
| page_mrr | 0.575 ± 0.072 (32) | 0.486 ± 0.077 (32) | -0.089 |
| page_ndcg@5 | 0.511 ± 0.065 (32) | 0.425 ± 0.068 (32) | -0.087 |
| retrieved_tokens@1 | 444 ± 23 (32) | 133 ± 23 (32) | -311 |
| retrieved_tokens@10 | 4639 ± 78 (32) | 1737 ± 120 (32) | -2902 |
| retrieved_tokens@20 | 9441 ± 100 (32) | 3684 ± 187 (32) | -5758 |
| retrieved_tokens@3 | 1396 ± 31 (32) | 476 ± 52 (32) | -920 |

### Token-matched k (baseline k=5, this run k=13)

| metric | baseline @5 | this run @matched | delta |
|---|---|---|---|
| tokens | 2335 ± 45 (32) | 2284 ± 142 (32) | -51 |
| chunk_fact_recall | 0.495 ± 0.081 (32) | 0.421 ± 0.076 (32) | -0.074 |
| chunk_hit | 0.594 ± 0.087 (32) | 0.562 ± 0.088 (32) | -0.031 |
| page_hit | 0.812 ± 0.069 (32) | 0.750 ± 0.077 (32) | -0.062 |
| chunk_fact_recall@5 (both at k=5) | 0.495 ± 0.081 (32) | 0.358 ± 0.076 (32) | -0.136 |

| row | metric | baseline | this run |
|---|---|---|---|
| 52 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 52 | chunk_hit@5 | 0.000 | 0.000 |
| 52 | page_hit@5 | 1.000 | 1.000 |
| 52 | chunk_fact_recall@matched | 0.000 | 0.500 |
| 52 | best relevant chunk | — | — |
| 53 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 53 | chunk_hit@5 | 0.000 | 0.000 |
| 53 | page_hit@5 | 1.000 | 1.000 |
| 53 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 53 | best relevant chunk | — | — |
| 8 | chunk_fact_recall@5 | 0.000 | 0.500 |
| 8 | chunk_hit@5 | 0.000 | 1.000 |
| 8 | page_hit@5 | 1.000 | 1.000 |
| 8 | chunk_fact_recall@matched | 0.000 | 0.500 |
| 8 | best relevant chunk | — | 2 · Approved Office Supplies List > 4.4 Reimbursement Payout Timelines > Legal entities |
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
| 38 | chunk_fact_recall@matched | 0.000 | 0.500 |
| 38 | best relevant chunk | — | — |
| 89 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 89 | chunk_hit@5 | 0.000 | 0.000 |
| 89 | page_hit@5 | 1.000 | 0.000 |
| 89 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 89 | best relevant chunk | — | — |
| 11 | chunk_fact_recall@5 | 0.333 | 0.000 |
| 11 | chunk_hit@5 | 1.000 | 0.000 |
| 11 | page_hit@5 | 1.000 | 1.000 |
| 11 | chunk_fact_recall@matched | 0.333 | 0.333 |
| 11 | best relevant chunk | 2 · Shipping Locations | — |
| 34 | chunk_fact_recall@5 | 0.667 | 0.333 |
| 34 | chunk_hit@5 | 1.000 | 1.000 |
| 34 | page_hit@5 | 1.000 | 1.000 |
| 34 | chunk_fact_recall@matched | 0.667 | 1.000 |
| 34 | best relevant chunk | 1 · Team Member | 1 · How To Apply for a Long-Term Relocation > Approvals Phase > Relocations To New Country or Different Location Factor |
| 44 | chunk_fact_recall@5 | 1.000 | 0.800 |
| 44 | chunk_hit@5 | 1.000 | 1.000 |
| 44 | page_hit@5 | 1.000 | 1.000 |
| 44 | chunk_fact_recall@matched | 1.000 | 0.800 |
| 44 | best relevant chunk | 3 · Customer Experience | 5 · North Star Metrics > Customer Experience Teams |
| 49 | chunk_fact_recall@5 | 1.000 | 0.000 |
| 49 | chunk_hit@5 | 1.000 | 0.000 |
| 49 | page_hit@5 | 1.000 | 0.000 |
| 49 | chunk_fact_recall@matched | 1.000 | 0.000 |
| 49 | best relevant chunk | 4 · Shipping Locations | — |
| 51 | chunk_fact_recall@5 | 1.000 | 0.500 |
| 51 | chunk_hit@5 | 1.000 | 1.000 |
| 51 | page_hit@5 | 1.000 | 1.000 |
| 51 | chunk_fact_recall@matched | 1.000 | 0.500 |
| 51 | best relevant chunk | 1 · Equipment | 3 · 4. PROCEDURES > 4.1 NON-TRAVEL RELATED EXPENSES > Equipment |
| 58 | chunk_fact_recall@5 | 0.500 | 0.000 |
| 58 | chunk_hit@5 | 1.000 | 0.000 |
| 58 | page_hit@5 | 1.000 | 0.000 |
| 58 | chunk_fact_recall@matched | 0.500 | 0.000 |
| 58 | best relevant chunk | 3 · Time Off Types | — |
| 88 | chunk_fact_recall@5 | 1.000 | 0.000 |
| 88 | chunk_hit@5 | 1.000 | 0.000 |
| 88 | page_hit@5 | 1.000 | 1.000 |
| 88 | chunk_fact_recall@matched | 1.000 | 0.000 |
| 88 | best relevant chunk | 1 · Timeline | — |
| 100 | chunk_fact_recall@5 | 1.000 | 0.000 |
| 100 | chunk_hit@5 | 1.000 | 0.000 |
| 100 | page_hit@5 | 1.000 | 1.000 |
| 100 | chunk_fact_recall@matched | 1.000 | 0.000 |
| 100 | best relevant chunk | 1 · Overview | — |
| 5 | chunk_fact_recall@5 | 0.333 | 0.333 |
| 5 | chunk_hit@5 | 1.000 | 1.000 |
| 5 | page_hit@5 | 1.000 | 1.000 |
| 5 | chunk_fact_recall@matched | 0.333 | 0.333 |
| 5 | best relevant chunk | 1 · Sick Time Eligibility and Coverage | 1 · Sick Time > For Sick Absences 1-5 Consecutive Days |
| 32 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 32 | chunk_hit@5 | 0.000 | 0.000 |
| 32 | page_hit@5 | 0.000 | 0.000 |
| 32 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 32 | best relevant chunk | — | — |
| 35 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 35 | chunk_hit@5 | 1.000 | 1.000 |
| 35 | page_hit@5 | 1.000 | 1.000 |
| 35 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 35 | best relevant chunk | 2 · Termination | 2 · Voluntary Terminations > Offboarding |
| 87 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 87 | chunk_hit@5 | 0.000 | 0.000 |
| 87 | page_hit@5 | 0.000 | 0.000 |
| 87 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 87 | best relevant chunk | — | — |
