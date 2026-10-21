# Eval summary

## Takeaways

- **Heading-path prefix on 3-large@1536 (spec 0008 AC-8 step 4), against `d83f3edc`: no difference on the headline, so not adopted (Arun, 21 Oct).** chunk_fact_recall@5 0.583 → 0.614, paired +0.031 ± 0.059 (0.51 SE), bootstrap 95% [−0.08, +0.15]. Rows 53, 59, 5 won; 10, 48, 34 lost; 26 tied.
- **It sharpens the top and costs depth.** page_hit@1 +0.156 (2.40 SE), page_mrr +0.088 (1.91), chunk_mrr +0.049 (1.14); chunk_fact_recall@10 −0.062 (−1.68) and @20 −0.051.
- **Losses are same-page crowding, as predicted.** Row 10: four of the top 5 are other `values/_index.md` windows (Mission, Transparency, Why have values) and the CREDIT window with six facts leaves the top 20. Row 48: windows whose path says "invoice" rise and the Fiscal Year window falls out. Row 34: the right page fills the top 5 with less relevant sections.
- **Next:** re-test prefixed vs unprefixed after the week-3 reranker (retrieve ~50, rerank to 5), which needs depth and supplies its own top ordering. The vectors are stored, so it costs one eval.

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: 779c86a3f19dda7a1b5450fc28fe49021c33e349
- harness_dirty: False
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- config_id: fixed-512-64-prefixed
- chunk_params: {'strategy': 'fixed', 'size': 512, 'overlap': 64, 'embed_prefix': 'title-path', 'tokenizer': 'cl100k_base'}
- embed_model: openai:text-embedding-3-large@1536
- answer_model: None
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- eval_depth: 20
- timestamp: 2026-10-21T11:22:56.099177+00:00
- rows: 33
- mode: retrieval-only
- limit: None
- baseline: 2026-10-21-d83f3edc
- baseline_change: chunk config

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.219 | 0.073 | 32 |
| chunk_all_required@10 | 0.562 | 0.088 | 32 |
| chunk_all_required@20 | 0.625 | 0.086 | 32 |
| chunk_all_required@3 | 0.406 | 0.087 | 32 |
| chunk_all_required@5 | 0.469 | 0.088 | 32 |
| chunk_fact_recall@1 | 0.328 | 0.072 | 32 |
| chunk_fact_recall@10 | 0.682 | 0.076 | 32 |
| chunk_fact_recall@20 | 0.768 | 0.064 | 32 |
| chunk_fact_recall@3 | 0.504 | 0.083 | 32 |
| chunk_fact_recall@5 | 0.614 | 0.076 | 32 |
| chunk_hit@1 | 0.469 | 0.088 | 32 |
| chunk_hit@10 | 0.750 | 0.077 | 32 |
| chunk_hit@20 | 0.875 | 0.058 | 32 |
| chunk_hit@3 | 0.562 | 0.088 | 32 |
| chunk_hit@5 | 0.719 | 0.079 | 32 |
| chunk_mrr | 0.553 | 0.079 | 32 |
| chunk_ndcg@5 | 0.448 | 0.065 | 32 |
| page_fact_recall@1 | 0.464 | 0.083 | 32 |
| page_fact_recall@10 | 0.771 | 0.070 | 32 |
| page_fact_recall@20 | 0.833 | 0.061 | 32 |
| page_fact_recall@3 | 0.661 | 0.079 | 32 |
| page_fact_recall@5 | 0.739 | 0.070 | 32 |
| page_hit@1 | 0.625 | 0.086 | 32 |
| page_hit@10 | 0.875 | 0.058 | 32 |
| page_hit@20 | 0.906 | 0.052 | 32 |
| page_hit@3 | 0.750 | 0.077 | 32 |
| page_hit@5 | 0.875 | 0.058 | 32 |
| page_mrr | 0.710 | 0.070 | 32 |
| page_ndcg@5 | 0.615 | 0.065 | 32 |
| retrieved_tokens@1 | 469 | 19 | 32 |
| retrieved_tokens@10 | 4705 | 73 | 32 |
| retrieved_tokens@20 | 9425 | 119 | 32 |
| retrieved_tokens@3 | 1416 | 34 | 32 |
| retrieved_tokens@5 | 2402 | 42 | 32 |

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.250 | 0.153 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.375 | 0.157 | 8 |
| chunk_fact_recall@10 | 0.770 | 0.126 | 8 |
| chunk_fact_recall@20 | 0.895 | 0.063 | 8 |
| chunk_fact_recall@3 | 0.537 | 0.168 | 8 |
| chunk_fact_recall@5 | 0.600 | 0.150 | 8 |
| chunk_hit@1 | 0.500 | 0.177 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.588 | 0.165 | 8 |
| chunk_ndcg@5 | 0.424 | 0.125 | 8 |
| page_fact_recall@1 | 0.545 | 0.170 | 8 |
| page_fact_recall@10 | 0.895 | 0.063 | 8 |
| page_fact_recall@20 | 0.895 | 0.063 | 8 |
| page_fact_recall@3 | 0.645 | 0.152 | 8 |
| page_fact_recall@5 | 0.770 | 0.083 | 8 |
| page_hit@1 | 0.750 | 0.153 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 1.000 | 0.000 | 8 |
| page_mrr | 0.806 | 0.127 | 8 |
| page_ndcg@5 | 0.638 | 0.102 | 8 |
| retrieved_tokens@1 | 418 | 62 | 8 |
| retrieved_tokens@10 | 4694 | 168 | 8 |
| retrieved_tokens@20 | 9612 | 204 | 8 |
| retrieved_tokens@3 | 1395 | 69 | 8 |
| retrieved_tokens@5 | 2378 | 93 | 8 |

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.500 | 0.177 | 8 |
| chunk_all_required@10 | 0.750 | 0.153 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.625 | 0.171 | 8 |
| chunk_all_required@5 | 0.750 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.500 | 0.189 | 8 |
| chunk_fact_recall@10 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@3 | 0.625 | 0.183 | 8 |
| chunk_fact_recall@5 | 0.750 | 0.164 | 8 |
| chunk_hit@1 | 0.500 | 0.177 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.594 | 0.163 | 8 |
| chunk_ndcg@5 | 0.567 | 0.145 | 8 |
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
| page_ndcg@5 | 0.662 | 0.168 | 8 |
| retrieved_tokens@1 | 466 | 37 | 8 |
| retrieved_tokens@10 | 4668 | 163 | 8 |
| retrieved_tokens@20 | 9276 | 318 | 8 |
| retrieved_tokens@3 | 1465 | 46 | 8 |
| retrieved_tokens@5 | 2489 | 47 | 8 |

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.625 | 0.171 | 8 |
| chunk_all_required@20 | 0.625 | 0.171 | 8 |
| chunk_all_required@3 | 0.500 | 0.177 | 8 |
| chunk_all_required@5 | 0.625 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.292 | 0.129 | 8 |
| chunk_fact_recall@10 | 0.708 | 0.160 | 8 |
| chunk_fact_recall@20 | 0.771 | 0.130 | 8 |
| chunk_fact_recall@3 | 0.583 | 0.175 | 8 |
| chunk_fact_recall@5 | 0.708 | 0.160 | 8 |
| chunk_hit@1 | 0.500 | 0.177 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.594 | 0.163 | 8 |
| chunk_ndcg@5 | 0.467 | 0.125 | 8 |
| page_fact_recall@1 | 0.458 | 0.177 | 8 |
| page_fact_recall@10 | 0.812 | 0.132 | 8 |
| page_fact_recall@20 | 0.812 | 0.132 | 8 |
| page_fact_recall@3 | 0.812 | 0.132 | 8 |
| page_fact_recall@5 | 0.812 | 0.132 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.667 | 0.137 | 8 |
| page_ndcg@5 | 0.569 | 0.118 | 8 |
| retrieved_tokens@1 | 480 | 22 | 8 |
| retrieved_tokens@10 | 4587 | 147 | 8 |
| retrieved_tokens@20 | 9133 | 211 | 8 |
| retrieved_tokens@3 | 1312 | 97 | 8 |
| retrieved_tokens@5 | 2264 | 112 | 8 |

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.375 | 0.171 | 8 |
| chunk_all_required@20 | 0.500 | 0.177 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.146 | 0.073 | 8 |
| chunk_fact_recall@10 | 0.500 | 0.164 | 8 |
| chunk_fact_recall@20 | 0.656 | 0.141 | 8 |
| chunk_fact_recall@3 | 0.271 | 0.141 | 8 |
| chunk_fact_recall@5 | 0.396 | 0.130 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.438 | 0.169 | 8 |
| chunk_ndcg@5 | 0.333 | 0.135 | 8 |
| page_fact_recall@1 | 0.229 | 0.130 | 8 |
| page_fact_recall@10 | 0.625 | 0.183 | 8 |
| page_fact_recall@20 | 0.875 | 0.125 | 8 |
| page_fact_recall@3 | 0.438 | 0.175 | 8 |
| page_fact_recall@5 | 0.625 | 0.183 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.681 | 0.158 | 8 |
| page_ndcg@5 | 0.592 | 0.146 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 4871 | 104 | 8 |
| retrieved_tokens@20 | 9680 | 184 | 8 |
| retrieved_tokens@3 | 1494 | 42 | 8 |
| retrieved_tokens@5 | 2477 | 54 | 8 |

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.500 | 0.177 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.292 | 0.129 | 8 |
| chunk_fact_recall@10 | 0.683 | 0.155 | 8 |
| chunk_fact_recall@20 | 0.746 | 0.126 | 8 |
| chunk_fact_recall@3 | 0.496 | 0.156 | 8 |
| chunk_fact_recall@5 | 0.621 | 0.149 | 8 |
| chunk_hit@1 | 0.500 | 0.177 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.594 | 0.163 | 8 |
| chunk_ndcg@5 | 0.439 | 0.130 | 8 |
| page_fact_recall@1 | 0.396 | 0.160 | 8 |
| page_fact_recall@10 | 0.787 | 0.129 | 8 |
| page_fact_recall@20 | 0.787 | 0.129 | 8 |
| page_fact_recall@3 | 0.725 | 0.129 | 8 |
| page_fact_recall@5 | 0.725 | 0.129 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 0.875 | 0.117 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.729 | 0.141 | 8 |
| page_ndcg@5 | 0.652 | 0.129 | 8 |
| retrieved_tokens@1 | 451 | 43 | 8 |
| retrieved_tokens@10 | 4440 | 181 | 8 |
| retrieved_tokens@20 | 9012 | 196 | 8 |
| retrieved_tokens@3 | 1331 | 99 | 8 |
| retrieved_tokens@5 | 2252 | 123 | 8 |

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.250 | 0.153 | 8 |
| chunk_all_required@10 | 0.625 | 0.171 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.625 | 0.171 | 8 |
| chunk_all_required@5 | 0.625 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.375 | 0.157 | 8 |
| chunk_fact_recall@10 | 0.795 | 0.129 | 8 |
| chunk_fact_recall@20 | 0.920 | 0.062 | 8 |
| chunk_fact_recall@3 | 0.625 | 0.183 | 8 |
| chunk_fact_recall@5 | 0.688 | 0.162 | 8 |
| chunk_hit@1 | 0.500 | 0.177 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.588 | 0.165 | 8 |
| chunk_ndcg@5 | 0.452 | 0.120 | 8 |
| page_fact_recall@1 | 0.607 | 0.179 | 8 |
| page_fact_recall@10 | 0.920 | 0.062 | 8 |
| page_fact_recall@20 | 0.920 | 0.062 | 8 |
| page_fact_recall@3 | 0.732 | 0.161 | 8 |
| page_fact_recall@5 | 0.857 | 0.080 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 1.000 | 0.000 | 8 |
| page_mrr | 0.744 | 0.129 | 8 |
| page_ndcg@5 | 0.555 | 0.085 | 8 |
| retrieved_tokens@1 | 448 | 52 | 8 |
| retrieved_tokens@10 | 4841 | 79 | 8 |
| retrieved_tokens@20 | 9734 | 163 | 8 |
| retrieved_tokens@3 | 1376 | 70 | 8 |
| retrieved_tokens@5 | 2391 | 75 | 8 |

## Token-matched k = 5 (target 2344 tokens)

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_fact_recall | 0.614 | 0.076 | 32 |
| chunk_hit | 0.719 | 0.079 | 32 |
| page_hit | 0.875 | 0.058 | 32 |
| tokens | 2402 | 42 | 32 |

## Lists

- page_hit_no_chunk: 52, 10, 48, 87, 38
- conflict_unscored: 53, 50, 58
- near_ties: none

## answer_only_facts

- row 58 F1
- row 22 F1

## no_retrieval_facts

- 22

## evidence_warnings

none

## Comparison with baseline 2026-10-21-d83f3edc (change: chunk config)

| metric | baseline mean ± SE (n) | this run mean ± SE (n) | delta |
|---|---|---|---|
| chunk_fact_recall@5 | 0.583 ± 0.075 (32) | 0.614 ± 0.076 (32) | +0.031 |
| retrieved_tokens@5 | 2344 ± 51 (32) | 2402 ± 42 (32) | +58 |
| chunk_all_required@1 | 0.188 ± 0.069 (32) | 0.219 ± 0.073 (32) | +0.031 |
| chunk_all_required@10 | 0.625 ± 0.086 (32) | 0.562 ± 0.088 (32) | -0.062 |
| chunk_all_required@20 | 0.719 ± 0.079 (32) | 0.625 ± 0.086 (32) | -0.094 |
| chunk_all_required@3 | 0.312 ± 0.082 (32) | 0.406 ± 0.087 (32) | +0.094 |
| chunk_all_required@5 | 0.406 ± 0.087 (32) | 0.469 ± 0.088 (32) | +0.062 |
| chunk_fact_recall@1 | 0.271 ± 0.070 (32) | 0.328 ± 0.072 (32) | +0.057 |
| chunk_fact_recall@10 | 0.744 ± 0.070 (32) | 0.682 ± 0.076 (32) | -0.062 |
| chunk_fact_recall@20 | 0.819 ± 0.061 (32) | 0.768 ± 0.064 (32) | -0.051 |
| chunk_fact_recall@3 | 0.510 ± 0.075 (32) | 0.504 ± 0.083 (32) | -0.006 |
| chunk_hit@1 | 0.375 ± 0.086 (32) | 0.469 ± 0.088 (32) | +0.094 |
| chunk_hit@10 | 0.812 ± 0.069 (32) | 0.750 ± 0.077 (32) | -0.062 |
| chunk_hit@20 | 0.875 ± 0.058 (32) | 0.875 ± 0.058 (32) | +0.000 |
| chunk_hit@3 | 0.656 ± 0.084 (32) | 0.562 ± 0.088 (32) | -0.094 |
| chunk_hit@5 | 0.719 ± 0.079 (32) | 0.719 ± 0.079 (32) | +0.000 |
| chunk_mrr | 0.504 ± 0.075 (32) | 0.553 ± 0.079 (32) | +0.049 |
| chunk_ndcg@5 | 0.397 ± 0.058 (32) | 0.448 ± 0.065 (32) | +0.051 |
| page_fact_recall@1 | 0.401 ± 0.085 (32) | 0.464 ± 0.083 (32) | +0.063 |
| page_fact_recall@10 | 0.849 ± 0.056 (32) | 0.771 ± 0.070 (32) | -0.078 |
| page_fact_recall@20 | 0.869 ± 0.055 (32) | 0.833 ± 0.061 (32) | -0.036 |
| page_fact_recall@3 | 0.661 ± 0.075 (32) | 0.661 ± 0.079 (32) | +0.000 |
| page_fact_recall@5 | 0.692 ± 0.073 (32) | 0.739 ± 0.070 (32) | +0.047 |
| page_hit@1 | 0.469 ± 0.088 (32) | 0.625 ± 0.086 (32) | +0.156 |
| page_hit@10 | 0.938 ± 0.043 (32) | 0.875 ± 0.058 (32) | -0.062 |
| page_hit@20 | 0.938 ± 0.043 (32) | 0.906 ± 0.052 (32) | -0.031 |
| page_hit@3 | 0.812 ± 0.069 (32) | 0.750 ± 0.077 (32) | -0.062 |
| page_hit@5 | 0.844 ± 0.064 (32) | 0.875 ± 0.058 (32) | +0.031 |
| page_mrr | 0.622 ± 0.069 (32) | 0.710 ± 0.070 (32) | +0.088 |
| page_ndcg@5 | 0.564 ± 0.066 (32) | 0.615 ± 0.065 (32) | +0.051 |
| retrieved_tokens@1 | 445 ± 22 (32) | 469 ± 19 (32) | +24 |
| retrieved_tokens@10 | 4679 ± 82 (32) | 4705 ± 73 (32) | +25 |
| retrieved_tokens@20 | 9406 ± 126 (32) | 9425 ± 119 (32) | +19 |
| retrieved_tokens@3 | 1418 ± 36 (32) | 1416 ± 34 (32) | -2 |

### Token-matched k (baseline k=5, this run k=5)

| metric | baseline @5 | this run @matched | delta |
|---|---|---|---|
| tokens | 2344 ± 51 (32) | 2402 ± 42 (32) | +58 |
| chunk_fact_recall | 0.583 ± 0.075 (32) | 0.614 ± 0.076 (32) | +0.031 |
| chunk_hit | 0.719 ± 0.079 (32) | 0.719 ± 0.079 (32) | +0.000 |
| page_hit | 0.844 ± 0.064 (32) | 0.875 ± 0.058 (32) | +0.031 |
| chunk_fact_recall@5 (both at k=5) | 0.583 ± 0.075 (32) | 0.614 ± 0.076 (32) | +0.031 |

### Paired delta (spec 0008 AC-7)

| comparison | mean delta | paired SE | mean / SE | n |
|---|---|---|---|---|
| chunk_fact_recall @matched k vs baseline @5 | +0.031 | 0.059 | 0.51 | 32 |
| chunk_fact_recall@5 vs @5 | +0.031 | 0.059 | 0.51 | 32 |

Adopt only if mean / SE > 2 on the matched-k row (spec 0008 AC-9).

| row | metric | baseline | this run |
|---|---|---|---|
| 52 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 52 | chunk_hit@5 | 0.000 | 0.000 |
| 52 | page_hit@5 | 1.000 | 1.000 |
| 52 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 52 | best relevant chunk | — | — |
| 53 | chunk_fact_recall@5 | 0.000 | 1.000 |
| 53 | chunk_hit@5 | 0.000 | 1.000 |
| 53 | page_hit@5 | 0.000 | 1.000 |
| 53 | chunk_fact_recall@matched | 0.000 | 1.000 |
| 53 | best relevant chunk | — | 4 · Overview |
| 8 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 8 | chunk_hit@5 | 1.000 | 1.000 |
| 8 | page_hit@5 | 1.000 | 1.000 |
| 8 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 8 | best relevant chunk | 2 · Processing Navan Reports | 5 · Expenses > Team Member Reimbursements - Navan > Processing Navan Reports |
| 10 | chunk_fact_recall@5 | 0.857 | 0.000 |
| 10 | chunk_hit@5 | 1.000 | 0.000 |
| 10 | page_hit@5 | 1.000 | 1.000 |
| 10 | chunk_fact_recall@matched | 0.857 | 0.000 |
| 10 | best relevant chunk | 2 · CREDIT | — |
| 99 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 99 | chunk_hit@5 | 1.000 | 1.000 |
| 99 | page_hit@5 | 1.000 | 1.000 |
| 99 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 99 | best relevant chunk | 1 · Payroll & Benefits | 1 · Your Onboarding Journey > Payroll & Benefits |
| 38 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 38 | chunk_hit@5 | 0.000 | 0.000 |
| 38 | page_hit@5 | 1.000 | 1.000 |
| 38 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 38 | best relevant chunk | — | — |
| 89 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 89 | chunk_hit@5 | 1.000 | 1.000 |
| 89 | page_hit@5 | 1.000 | 1.000 |
| 89 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 89 | best relevant chunk | 5 · GitLab Offboarding | 4 · Voluntary Terminations > Offboarding |
| 11 | chunk_fact_recall@5 | 0.667 | 0.667 |
| 11 | chunk_hit@5 | 1.000 | 1.000 |
| 11 | page_hit@5 | 1.000 | 1.000 |
| 11 | chunk_fact_recall@matched | 0.667 | 0.667 |
| 11 | best relevant chunk | 2 · Equipment | 1 · 4. PROCEDURES > 4.1 NON-TRAVEL RELATED EXPENSES > Equipment |
| 34 | chunk_fact_recall@5 | 1.000 | 0.667 |
| 34 | chunk_hit@5 | 1.000 | 1.000 |
| 34 | page_hit@5 | 1.000 | 1.000 |
| 34 | chunk_fact_recall@matched | 1.000 | 0.667 |
| 34 | best relevant chunk | 1 · Team Member | 1 · How To Apply for a Long-Term Relocation > Team Member |
| 44 | chunk_fact_recall@5 | 0.800 | 0.800 |
| 44 | chunk_hit@5 | 1.000 | 1.000 |
| 44 | page_hit@5 | 1.000 | 1.000 |
| 44 | chunk_fact_recall@matched | 0.800 | 0.800 |
| 44 | best relevant chunk | 2 · Role Comparison | 2 · CS & SA Roles Overview |
| 49 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 49 | chunk_hit@5 | 1.000 | 1.000 |
| 49 | page_hit@5 | 1.000 | 1.000 |
| 49 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 49 | best relevant chunk | 3 · Equipment | 1 · 4. PROCEDURES > 4.1 NON-TRAVEL RELATED EXPENSES > Equipment |
| 51 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 51 | chunk_hit@5 | 1.000 | 1.000 |
| 51 | page_hit@5 | 1.000 | 1.000 |
| 51 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 51 | best relevant chunk | 1 · Equipment | 1 · 4. PROCEDURES > 4.1 NON-TRAVEL RELATED EXPENSES > Equipment |
| 58 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 58 | chunk_hit@5 | 1.000 | 1.000 |
| 58 | page_hit@5 | 1.000 | 1.000 |
| 58 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 58 | best relevant chunk | 1 · Time Off Types | 1 · Flexible Paid Time Off (PTO) > Overview |
| 88 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 88 | chunk_hit@5 | 1.000 | 1.000 |
| 88 | page_hit@5 | 1.000 | 1.000 |
| 88 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 88 | best relevant chunk | 1 · Timeline | 1 · FY26 Talent Assessment > Timeline |
| 100 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 100 | chunk_hit@5 | 1.000 | 1.000 |
| 100 | page_hit@5 | 1.000 | 1.000 |
| 100 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 100 | best relevant chunk | 1 · Time Off Types | 1 · Flexible Paid Time Off (PTO) > Overview |
| 5 | chunk_fact_recall@5 | 0.333 | 1.000 |
| 5 | chunk_hit@5 | 1.000 | 1.000 |
| 5 | page_hit@5 | 1.000 | 1.000 |
| 5 | chunk_fact_recall@matched | 0.333 | 1.000 |
| 5 | best relevant chunk | 1 · Sick Time Eligibility and Coverage | 1 · Sick Time > Sick Time Eligibility and Coverage |
| 32 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 32 | chunk_hit@5 | 0.000 | 0.000 |
| 32 | page_hit@5 | 1.000 | 0.000 |
| 32 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 32 | best relevant chunk | — | — |
| 35 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 35 | chunk_hit@5 | 1.000 | 1.000 |
| 35 | page_hit@5 | 1.000 | 1.000 |
| 35 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 35 | best relevant chunk | 3 · Termination | 4 · Voluntary Terminations > Termination |
| 87 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 87 | chunk_hit@5 | 0.000 | 0.000 |
| 87 | page_hit@5 | 1.000 | 1.000 |
| 87 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 87 | best relevant chunk | — | — |
