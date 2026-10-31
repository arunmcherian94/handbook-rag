# Eval summary

## Takeaways

- **Retrieval-only, hybrid (FTS + dense, RRF k=60, depth 50) vs `2026-10-21-d83f3edc`.** chunk_fact_recall@5 0.521 against 0.583: paired −0.062 ± 0.057, mean/SE −1.08, against the bar of +2. Rows: 3 won (52, 53, 44), 7 lost (10, 8, 49, 89, 35, 58, 11), 22 tied. @20: +0.025.
- **Why:** FTS adds no fact chunks beyond dense's top 50, and equal-weight RRF ranks chunks found by both lists above good dense-only ones. Rows 65 and 92 are not reached via FTS. Details are in the [journal](../../../journal/2026-10-30-hybrid-runs.md).
- **Next:** not adopted (Arun, 31 Oct). Dense stays the default. Re-test once the eval set has keyword-heavy questions ([follow-ups](../../../follow-ups.md)).

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: cd22409bd6b77aafadfef6bf2e09f16f1d914907
- harness_dirty: False
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- config_id: fixed-512-64
- chunk_params: {'strategy': 'fixed', 'size': 512, 'overlap': 64, 'tokenizer': 'cl100k_base'}
- embed_model: openai:text-embedding-3-large@1536
- answer_model: None
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- eval_depth: 20
- timestamp: 2026-10-30T11:51:59.485028+00:00
- rows: 33
- mode: retrieval-only
- limit: None
- user_id: admin
- policy_version: policy-v1
- policy_sha256: eeb8443f1e3b84718e02a302e6fe5efb43c3386de2050b055d9d0c14aa564cdc
- retriever: hybrid
- rrf_k: 60
- fusion_depth: 50
- fts: {'config': 'english', 'normalization': 0, 'query': 'or-of-lexemes'}
- baseline: 2026-10-21-d83f3edc
- baseline_change: retriever

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.094 | 0.052 | 32 |
| chunk_all_required@10 | 0.469 | 0.088 | 32 |
| chunk_all_required@20 | 0.750 | 0.077 | 32 |
| chunk_all_required@3 | 0.250 | 0.077 | 32 |
| chunk_all_required@5 | 0.438 | 0.088 | 32 |
| chunk_fact_recall@1 | 0.161 | 0.056 | 32 |
| chunk_fact_recall@10 | 0.626 | 0.072 | 32 |
| chunk_fact_recall@20 | 0.844 | 0.056 | 32 |
| chunk_fact_recall@3 | 0.365 | 0.074 | 32 |
| chunk_fact_recall@5 | 0.521 | 0.081 | 32 |
| chunk_hit@1 | 0.250 | 0.077 | 32 |
| chunk_hit@10 | 0.781 | 0.073 | 32 |
| chunk_hit@20 | 0.906 | 0.052 | 32 |
| chunk_hit@3 | 0.500 | 0.088 | 32 |
| chunk_hit@5 | 0.625 | 0.086 | 32 |
| chunk_mrr | 0.393 | 0.071 | 32 |
| chunk_ndcg@5 | 0.295 | 0.054 | 32 |
| page_fact_recall@1 | 0.397 | 0.084 | 32 |
| page_fact_recall@10 | 0.751 | 0.065 | 32 |
| page_fact_recall@20 | 0.886 | 0.049 | 32 |
| page_fact_recall@3 | 0.563 | 0.078 | 32 |
| page_fact_recall@5 | 0.657 | 0.074 | 32 |
| page_hit@1 | 0.500 | 0.088 | 32 |
| page_hit@10 | 0.875 | 0.058 | 32 |
| page_hit@20 | 0.938 | 0.043 | 32 |
| page_hit@3 | 0.750 | 0.077 | 32 |
| page_hit@5 | 0.812 | 0.069 | 32 |
| page_mrr | 0.629 | 0.072 | 32 |
| page_ndcg@5 | 0.505 | 0.060 | 32 |
| retrieved_tokens@1 | 510 | 2 | 32 |
| retrieved_tokens@10 | 4996 | 37 | 32 |
| retrieved_tokens@20 | 9877 | 69 | 32 |
| retrieved_tokens@3 | 1520 | 10 | 32 |
| retrieved_tokens@5 | 2524 | 15 | 32 |

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.500 | 0.177 | 8 |
| chunk_fact_recall@1 | 0.125 | 0.125 | 8 |
| chunk_fact_recall@10 | 0.732 | 0.130 | 8 |
| chunk_fact_recall@20 | 0.920 | 0.062 | 8 |
| chunk_fact_recall@3 | 0.375 | 0.157 | 8 |
| chunk_fact_recall@5 | 0.562 | 0.175 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.323 | 0.122 | 8 |
| chunk_ndcg@5 | 0.270 | 0.118 | 8 |
| page_fact_recall@1 | 0.232 | 0.153 | 8 |
| page_fact_recall@10 | 0.795 | 0.088 | 8 |
| page_fact_recall@20 | 0.920 | 0.062 | 8 |
| page_fact_recall@3 | 0.607 | 0.152 | 8 |
| page_fact_recall@5 | 0.732 | 0.130 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.510 | 0.122 | 8 |
| page_ndcg@5 | 0.412 | 0.077 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 4968 | 101 | 8 |
| retrieved_tokens@20 | 9846 | 194 | 8 |
| retrieved_tokens@3 | 1536 | 0 | 8 |
| retrieved_tokens@5 | 2560 | 0 | 8 |

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.250 | 0.153 | 8 |
| chunk_all_required@10 | 0.750 | 0.153 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.750 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.312 | 0.162 | 8 |
| chunk_fact_recall@10 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@3 | 0.438 | 0.175 | 8 |
| chunk_fact_recall@5 | 0.750 | 0.164 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.487 | 0.160 | 8 |
| chunk_ndcg@5 | 0.401 | 0.117 | 8 |
| page_fact_recall@1 | 0.625 | 0.183 | 8 |
| page_fact_recall@10 | 0.750 | 0.164 | 8 |
| page_fact_recall@20 | 0.750 | 0.164 | 8 |
| page_fact_recall@3 | 0.625 | 0.183 | 8 |
| page_fact_recall@5 | 0.750 | 0.164 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 0.750 | 0.153 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.650 | 0.172 | 8 |
| page_ndcg@5 | 0.632 | 0.158 | 8 |
| retrieved_tokens@1 | 502 | 10 | 8 |
| retrieved_tokens@10 | 5007 | 70 | 8 |
| retrieved_tokens@20 | 9870 | 129 | 8 |
| retrieved_tokens@3 | 1491 | 35 | 8 |
| retrieved_tokens@5 | 2484 | 42 | 8 |

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.375 | 0.171 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.125 | 0.082 | 8 |
| chunk_fact_recall@10 | 0.542 | 0.150 | 8 |
| chunk_fact_recall@20 | 0.896 | 0.070 | 8 |
| chunk_fact_recall@3 | 0.417 | 0.148 | 8 |
| chunk_fact_recall@5 | 0.542 | 0.150 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.448 | 0.138 | 8 |
| chunk_ndcg@5 | 0.277 | 0.082 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@10 | 0.604 | 0.160 | 8 |
| page_fact_recall@20 | 0.938 | 0.062 | 8 |
| page_fact_recall@3 | 0.479 | 0.165 | 8 |
| page_fact_recall@5 | 0.604 | 0.160 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 0.750 | 0.153 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.542 | 0.150 | 8 |
| page_ndcg@5 | 0.409 | 0.121 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 5013 | 45 | 8 |
| retrieved_tokens@20 | 9793 | 128 | 8 |
| retrieved_tokens@3 | 1515 | 14 | 8 |
| retrieved_tokens@5 | 2536 | 13 | 8 |

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.250 | 0.153 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.083 | 0.055 | 8 |
| chunk_fact_recall@10 | 0.479 | 0.135 | 8 |
| chunk_fact_recall@20 | 0.812 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.229 | 0.130 | 8 |
| chunk_fact_recall@5 | 0.229 | 0.130 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.375 | 0.171 | 8 |
| chunk_mrr | 0.312 | 0.162 | 8 |
| chunk_ndcg@5 | 0.234 | 0.123 | 8 |
| page_fact_recall@1 | 0.479 | 0.165 | 8 |
| page_fact_recall@10 | 0.854 | 0.097 | 8 |
| page_fact_recall@20 | 0.938 | 0.062 | 8 |
| page_fact_recall@3 | 0.542 | 0.150 | 8 |
| page_fact_recall@5 | 0.542 | 0.150 | 8 |
| page_hit@1 | 0.750 | 0.153 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.812 | 0.132 | 8 |
| page_ndcg@5 | 0.568 | 0.110 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 4997 | 86 | 8 |
| retrieved_tokens@20 | 9998 | 98 | 8 |
| retrieved_tokens@3 | 1536 | 0 | 8 |
| retrieved_tokens@5 | 2518 | 42 | 8 |

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.500 | 0.177 | 8 |
| chunk_fact_recall@1 | 0.062 | 0.062 | 8 |
| chunk_fact_recall@10 | 0.667 | 0.137 | 8 |
| chunk_fact_recall@20 | 0.896 | 0.070 | 8 |
| chunk_fact_recall@3 | 0.354 | 0.156 | 8 |
| chunk_fact_recall@5 | 0.604 | 0.160 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.333 | 0.112 | 8 |
| chunk_ndcg@5 | 0.243 | 0.077 | 8 |
| page_fact_recall@1 | 0.125 | 0.125 | 8 |
| page_fact_recall@10 | 0.667 | 0.137 | 8 |
| page_fact_recall@20 | 0.938 | 0.062 | 8 |
| page_fact_recall@3 | 0.354 | 0.156 | 8 |
| page_fact_recall@5 | 0.604 | 0.160 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.427 | 0.139 | 8 |
| page_ndcg@5 | 0.379 | 0.119 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 4882 | 95 | 8 |
| retrieved_tokens@20 | 9586 | 171 | 8 |
| retrieved_tokens@3 | 1536 | 0 | 8 |
| retrieved_tokens@5 | 2557 | 3 | 8 |

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.375 | 0.171 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@10 | 0.607 | 0.152 | 8 |
| chunk_fact_recall@20 | 0.920 | 0.062 | 8 |
| chunk_fact_recall@3 | 0.438 | 0.148 | 8 |
| chunk_fact_recall@5 | 0.500 | 0.164 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.438 | 0.148 | 8 |
| chunk_ndcg@5 | 0.303 | 0.120 | 8 |
| page_fact_recall@1 | 0.357 | 0.175 | 8 |
| page_fact_recall@10 | 0.732 | 0.130 | 8 |
| page_fact_recall@20 | 0.920 | 0.062 | 8 |
| page_fact_recall@3 | 0.732 | 0.130 | 8 |
| page_fact_recall@5 | 0.732 | 0.130 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@10 | 0.875 | 0.117 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.625 | 0.125 | 8 |
| page_ndcg@5 | 0.443 | 0.079 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 5099 | 14 | 8 |
| retrieved_tokens@20 | 10053 | 96 | 8 |
| retrieved_tokens@3 | 1515 | 14 | 8 |
| retrieved_tokens@5 | 2539 | 14 | 8 |

## Token-matched k = 5 (target 2344 tokens)

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_fact_recall | 0.521 | 0.081 | 32 |
| chunk_hit | 0.625 | 0.086 | 32 |
| page_hit | 0.812 | 0.069 | 32 |
| tokens | 2524 | 15 | 32 |

## Lists

- page_hit_no_chunk: 8, 32, 10, 87, 38, 89
- conflict_unscored: 53, 50, 58
- near_ties: none

## answer_only_facts

- row 58 F1
- row 22 F1

## no_retrieval_facts

- 22

## evidence_warnings

none

## Comparison with baseline 2026-10-21-d83f3edc (change: retriever)

| metric | baseline mean ± SE (n) | this run mean ± SE (n) | delta |
|---|---|---|---|
| chunk_fact_recall@5 | 0.583 ± 0.075 (32) | 0.521 ± 0.081 (32) | -0.062 |
| retrieved_tokens@5 | 2344 ± 51 (32) | 2524 ± 15 (32) | +181 |
| chunk_all_required@1 | 0.188 ± 0.069 (32) | 0.094 ± 0.052 (32) | -0.094 |
| chunk_all_required@10 | 0.625 ± 0.086 (32) | 0.469 ± 0.088 (32) | -0.156 |
| chunk_all_required@20 | 0.719 ± 0.079 (32) | 0.750 ± 0.077 (32) | +0.031 |
| chunk_all_required@3 | 0.312 ± 0.082 (32) | 0.250 ± 0.077 (32) | -0.062 |
| chunk_all_required@5 | 0.406 ± 0.087 (32) | 0.438 ± 0.088 (32) | +0.031 |
| chunk_fact_recall@1 | 0.271 ± 0.070 (32) | 0.161 ± 0.056 (32) | -0.109 |
| chunk_fact_recall@10 | 0.744 ± 0.070 (32) | 0.626 ± 0.072 (32) | -0.119 |
| chunk_fact_recall@20 | 0.819 ± 0.061 (32) | 0.844 ± 0.056 (32) | +0.025 |
| chunk_fact_recall@3 | 0.510 ± 0.075 (32) | 0.365 ± 0.074 (32) | -0.146 |
| chunk_hit@1 | 0.375 ± 0.086 (32) | 0.250 ± 0.077 (32) | -0.125 |
| chunk_hit@10 | 0.812 ± 0.069 (32) | 0.781 ± 0.073 (32) | -0.031 |
| chunk_hit@20 | 0.875 ± 0.058 (32) | 0.906 ± 0.052 (32) | +0.031 |
| chunk_hit@3 | 0.656 ± 0.084 (32) | 0.500 ± 0.088 (32) | -0.156 |
| chunk_hit@5 | 0.719 ± 0.079 (32) | 0.625 ± 0.086 (32) | -0.094 |
| chunk_mrr | 0.504 ± 0.075 (32) | 0.393 ± 0.071 (32) | -0.111 |
| chunk_ndcg@5 | 0.397 ± 0.058 (32) | 0.295 ± 0.054 (32) | -0.102 |
| page_fact_recall@1 | 0.401 ± 0.085 (32) | 0.397 ± 0.084 (32) | -0.004 |
| page_fact_recall@10 | 0.849 ± 0.056 (32) | 0.751 ± 0.065 (32) | -0.098 |
| page_fact_recall@20 | 0.869 ± 0.055 (32) | 0.886 ± 0.049 (32) | +0.017 |
| page_fact_recall@3 | 0.661 ± 0.075 (32) | 0.563 ± 0.078 (32) | -0.098 |
| page_fact_recall@5 | 0.692 ± 0.073 (32) | 0.657 ± 0.074 (32) | -0.035 |
| page_hit@1 | 0.469 ± 0.088 (32) | 0.500 ± 0.088 (32) | +0.031 |
| page_hit@10 | 0.938 ± 0.043 (32) | 0.875 ± 0.058 (32) | -0.062 |
| page_hit@20 | 0.938 ± 0.043 (32) | 0.938 ± 0.043 (32) | +0.000 |
| page_hit@3 | 0.812 ± 0.069 (32) | 0.750 ± 0.077 (32) | -0.062 |
| page_hit@5 | 0.844 ± 0.064 (32) | 0.812 ± 0.069 (32) | -0.031 |
| page_mrr | 0.622 ± 0.069 (32) | 0.629 ± 0.072 (32) | +0.006 |
| page_ndcg@5 | 0.564 ± 0.066 (32) | 0.505 ± 0.060 (32) | -0.059 |
| retrieved_tokens@1 | 445 ± 22 (32) | 510 ± 2 (32) | +64 |
| retrieved_tokens@10 | 4679 ± 82 (32) | 4996 ± 37 (32) | +317 |
| retrieved_tokens@20 | 9406 ± 126 (32) | 9877 ± 69 (32) | +470 |
| retrieved_tokens@3 | 1418 ± 36 (32) | 1520 ± 10 (32) | +101 |

### Token-matched k (baseline k=5, this run k=5)

| metric | baseline @5 | this run @matched | delta |
|---|---|---|---|
| tokens | 2344 ± 51 (32) | 2524 ± 15 (32) | +181 |
| chunk_fact_recall | 0.583 ± 0.075 (32) | 0.521 ± 0.081 (32) | -0.062 |
| chunk_hit | 0.719 ± 0.079 (32) | 0.625 ± 0.086 (32) | -0.094 |
| page_hit | 0.844 ± 0.064 (32) | 0.812 ± 0.069 (32) | -0.031 |
| chunk_fact_recall@5 (both at k=5) | 0.583 ± 0.075 (32) | 0.521 ± 0.081 (32) | -0.062 |

### Paired delta (spec 0008 AC-7)

| comparison | mean delta | paired SE | mean / SE | n |
|---|---|---|---|---|
| chunk_fact_recall @matched k vs baseline @5 | -0.062 | 0.057 | -1.08 | 32 |
| chunk_fact_recall@5 vs @5 | -0.062 | 0.057 | -1.08 | 32 |

Adopt only if mean / SE > 2 on the matched-k row (spec 0008 AC-9).

| row | metric | baseline | this run |
|---|---|---|---|
| 52 | chunk_fact_recall@5 | 0.000 | 0.500 |
| 52 | chunk_hit@5 | 0.000 | 1.000 |
| 52 | page_hit@5 | 1.000 | 1.000 |
| 52 | chunk_fact_recall@matched | 0.000 | 0.500 |
| 52 | best relevant chunk | — | 3 · Access Requests (ARs) |
| 53 | chunk_fact_recall@5 | 0.000 | 1.000 |
| 53 | chunk_hit@5 | 0.000 | 1.000 |
| 53 | page_hit@5 | 0.000 | 1.000 |
| 53 | chunk_fact_recall@matched | 0.000 | 1.000 |
| 53 | best relevant chunk | — | 4 · Access Requests (ARs) |
| 8 | chunk_fact_recall@5 | 0.500 | 0.000 |
| 8 | chunk_hit@5 | 1.000 | 0.000 |
| 8 | page_hit@5 | 1.000 | 1.000 |
| 8 | chunk_fact_recall@matched | 0.500 | 0.000 |
| 8 | best relevant chunk | 2 · Processing Navan Reports | — |
| 10 | chunk_fact_recall@5 | 0.857 | 0.000 |
| 10 | chunk_hit@5 | 1.000 | 0.000 |
| 10 | page_hit@5 | 1.000 | 1.000 |
| 10 | chunk_fact_recall@matched | 0.857 | 0.000 |
| 10 | best relevant chunk | 2 · CREDIT | — |
| 99 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 99 | chunk_hit@5 | 1.000 | 1.000 |
| 99 | page_hit@5 | 1.000 | 1.000 |
| 99 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 99 | best relevant chunk | 1 · Payroll & Benefits | 2 · Time Off Types |
| 38 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 38 | chunk_hit@5 | 0.000 | 0.000 |
| 38 | page_hit@5 | 1.000 | 1.000 |
| 38 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 38 | best relevant chunk | — | — |
| 89 | chunk_fact_recall@5 | 0.500 | 0.000 |
| 89 | chunk_hit@5 | 1.000 | 0.000 |
| 89 | page_hit@5 | 1.000 | 1.000 |
| 89 | chunk_fact_recall@matched | 0.500 | 0.000 |
| 89 | best relevant chunk | 5 · GitLab Offboarding | — |
| 11 | chunk_fact_recall@5 | 0.667 | 0.333 |
| 11 | chunk_hit@5 | 1.000 | 1.000 |
| 11 | page_hit@5 | 1.000 | 1.000 |
| 11 | chunk_fact_recall@matched | 0.667 | 0.333 |
| 11 | best relevant chunk | 2 · Equipment | 2 · Shipping Locations |
| 34 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 34 | chunk_hit@5 | 1.000 | 1.000 |
| 34 | page_hit@5 | 1.000 | 1.000 |
| 34 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 34 | best relevant chunk | 1 · Team Member | 1 · Relocation Within Same Country and Same Location Factor |
| 44 | chunk_fact_recall@5 | 0.800 | 1.000 |
| 44 | chunk_hit@5 | 1.000 | 1.000 |
| 44 | page_hit@5 | 1.000 | 1.000 |
| 44 | chunk_fact_recall@matched | 0.800 | 1.000 |
| 44 | best relevant chunk | 2 · Role Comparison | 3 · Customer Experience |
| 49 | chunk_fact_recall@5 | 0.500 | 0.000 |
| 49 | chunk_hit@5 | 1.000 | 0.000 |
| 49 | page_hit@5 | 1.000 | 0.000 |
| 49 | chunk_fact_recall@matched | 0.500 | 0.000 |
| 49 | best relevant chunk | 3 · Equipment | — |
| 51 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 51 | chunk_hit@5 | 1.000 | 1.000 |
| 51 | page_hit@5 | 1.000 | 1.000 |
| 51 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 51 | best relevant chunk | 1 · Equipment | 1 · Equipment |
| 58 | chunk_fact_recall@5 | 1.000 | 0.500 |
| 58 | chunk_hit@5 | 1.000 | 1.000 |
| 58 | page_hit@5 | 1.000 | 1.000 |
| 58 | chunk_fact_recall@matched | 1.000 | 0.500 |
| 58 | best relevant chunk | 1 · Time Off Types | 1 · Time Off Types |
| 88 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 88 | chunk_hit@5 | 1.000 | 1.000 |
| 88 | page_hit@5 | 1.000 | 1.000 |
| 88 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 88 | best relevant chunk | 1 · Timeline | 5 · Timeline |
| 100 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 100 | chunk_hit@5 | 1.000 | 1.000 |
| 100 | page_hit@5 | 1.000 | 1.000 |
| 100 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 100 | best relevant chunk | 1 · Time Off Types | 2 · Time Off Types |
| 5 | chunk_fact_recall@5 | 0.333 | 0.333 |
| 5 | chunk_hit@5 | 1.000 | 1.000 |
| 5 | page_hit@5 | 1.000 | 1.000 |
| 5 | chunk_fact_recall@matched | 0.333 | 0.333 |
| 5 | best relevant chunk | 1 · Sick Time Eligibility and Coverage | 1 · Sick Time Eligibility and Coverage |
| 32 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 32 | chunk_hit@5 | 0.000 | 0.000 |
| 32 | page_hit@5 | 1.000 | 1.000 |
| 32 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 32 | best relevant chunk | — | — |
| 35 | chunk_fact_recall@5 | 0.500 | 0.000 |
| 35 | chunk_hit@5 | 1.000 | 0.000 |
| 35 | page_hit@5 | 1.000 | 0.000 |
| 35 | chunk_fact_recall@matched | 0.500 | 0.000 |
| 35 | best relevant chunk | 3 · Termination | — |
| 87 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 87 | chunk_hit@5 | 0.000 | 0.000 |
| 87 | page_hit@5 | 1.000 | 1.000 |
| 87 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 87 | best relevant chunk | — | — |

### Top-5 order vs baseline (spec 0007, AC-9)

identical on 0 of 33 rows

differing rows: 5, 8, 9, 10, 11, 13, 22, 23, 26, 32, 34, 35, 38, 44, 46, 48, 49, 50, 51, 52, 53, 55, 58, 59, 65, 87, 88, 89, 92, 93, 96, 99, 100
