# Eval summary

## Takeaways

- **Retrieval-only, rerank (`Qwen/Qwen3-Reranker-4B` over the dense top 50) vs the same run's dense top 5.** chunk_fact_recall@5 0.542 against 0.583: paired −0.041 ± 0.058, mean/SE −0.70, against the bar of +2. Rows: 3 won (52, 53, 8), 6 lost (44, 49, 35, 89, 58, 23), 23 tied. Below dense at every k from 3 to 10. Headroom captured −0.139.
- **Targeted rows:** 8 and 53 gain. Rows 49 and 89 lose a fact from dense rank 3 or 5, and row 55's fact falls from rank 8 to 38. Truncation share 0; rerank p50 4,154 ms against dense 337 ms. Details are in the [journal](../../../journal/2026-11-01-rerank-runs.md).
- **Why:** the dense top 50 is already on topic, and the reranker rates many candidates near 1.0 (5+ at ≥ 0.99 on 8 rows), so fact chunks lose on small margins (row 44: 0.998 against 0.999). It also scores some fact chunks as irrelevant: on row 89 ("whats our exit policy") all 50 score ≤ 0.056. Fixed 512-token windows and colloquial questions fit both patterns, untested. Row 55's reranked #1 names the leader through an optional fact, which the metric doesn't credit.
- **Next:** not adopted under the pre-set rule (below 1 SE). Dense stays the default; `--retriever rerank` stays as a measurement flag.

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: aba4828d890a1a55c28b1932c788f1063169f804
- harness_dirty: False
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- config_id: fixed-512-64
- chunk_params: {'strategy': 'fixed', 'size': 512, 'overlap': 64, 'tokenizer': 'cl100k_base'}
- embed_model: openai:text-embedding-3-large@1536
- answer_model: None
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- eval_depth: 20
- timestamp: 2026-11-01T17:09:40.140238+00:00
- rows: 33
- mode: retrieval-only
- limit: None
- user_id: admin
- policy_version: policy-v1
- policy_sha256: eeb8443f1e3b84718e02a302e6fe5efb43c3386de2050b055d9d0c14aa564cdc
- retriever: rerank
- rerank: {'model': 'deepinfra:Qwen/Qwen3-Reranker-4B', 'depth': 50, 'instruction': 'Given a web search query, retrieve relevant passages that answer the query', 'max_input_tokens': 32768, 'template_tokens': 80, 'token_margin': 1.5, 'truncation': 'none; refuse over limit', 'usd_per_1m': 0.025, 'price_source': 'deepinfra.com/Qwen/Qwen3-Reranker-4B, 2026-10-31', 'input_tokens': 930422}
- baseline: 2026-10-21-d83f3edc
- baseline_change: retriever

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.156 | 0.064 | 32 |
| chunk_all_required@10 | 0.500 | 0.088 | 32 |
| chunk_all_required@20 | 0.688 | 0.082 | 32 |
| chunk_all_required@3 | 0.312 | 0.082 | 32 |
| chunk_all_required@5 | 0.406 | 0.087 | 32 |
| chunk_fact_recall@1 | 0.255 | 0.067 | 32 |
| chunk_fact_recall@10 | 0.664 | 0.071 | 32 |
| chunk_fact_recall@20 | 0.768 | 0.068 | 32 |
| chunk_fact_recall@3 | 0.458 | 0.076 | 32 |
| chunk_fact_recall@5 | 0.542 | 0.079 | 32 |
| chunk_hit@1 | 0.375 | 0.086 | 32 |
| chunk_hit@10 | 0.812 | 0.069 | 32 |
| chunk_hit@20 | 0.844 | 0.064 | 32 |
| chunk_hit@3 | 0.594 | 0.087 | 32 |
| chunk_hit@5 | 0.656 | 0.084 | 32 |
| chunk_mrr | 0.488 | 0.077 | 32 |
| chunk_ndcg@5 | 0.357 | 0.056 | 32 |
| page_fact_recall@1 | 0.411 | 0.083 | 32 |
| page_fact_recall@10 | 0.817 | 0.061 | 32 |
| page_fact_recall@20 | 0.859 | 0.056 | 32 |
| page_fact_recall@3 | 0.660 | 0.076 | 32 |
| page_fact_recall@5 | 0.703 | 0.074 | 32 |
| page_hit@1 | 0.531 | 0.088 | 32 |
| page_hit@10 | 0.938 | 0.043 | 32 |
| page_hit@20 | 0.938 | 0.043 | 32 |
| page_hit@3 | 0.844 | 0.064 | 32 |
| page_hit@5 | 0.875 | 0.058 | 32 |
| page_mrr | 0.673 | 0.067 | 32 |
| page_ndcg@5 | 0.592 | 0.062 | 32 |
| retrieved_tokens@1 | 491 | 11 | 32 |
| retrieved_tokens@10 | 4758 | 62 | 32 |
| retrieved_tokens@20 | 9552 | 89 | 32 |
| retrieved_tokens@3 | 1447 | 30 | 32 |
| retrieved_tokens@5 | 2425 | 38 | 32 |

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.875 | 0.117 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.500 | 0.177 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.091 | 8 |
| chunk_fact_recall@10 | 0.832 | 0.077 | 8 |
| chunk_fact_recall@20 | 0.938 | 0.062 | 8 |
| chunk_fact_recall@3 | 0.438 | 0.148 | 8 |
| chunk_fact_recall@5 | 0.670 | 0.158 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 1.000 | 0.000 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.504 | 0.156 | 8 |
| chunk_ndcg@5 | 0.377 | 0.109 | 8 |
| page_fact_recall@1 | 0.312 | 0.132 | 8 |
| page_fact_recall@10 | 0.895 | 0.063 | 8 |
| page_fact_recall@20 | 0.938 | 0.062 | 8 |
| page_fact_recall@3 | 0.725 | 0.129 | 8 |
| page_fact_recall@5 | 0.895 | 0.063 | 8 |
| page_hit@1 | 0.500 | 0.177 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 1.000 | 0.000 | 8 |
| page_mrr | 0.671 | 0.128 | 8 |
| page_ndcg@5 | 0.603 | 0.112 | 8 |
| retrieved_tokens@1 | 460 | 42 | 8 |
| retrieved_tokens@10 | 4759 | 175 | 8 |
| retrieved_tokens@20 | 9658 | 204 | 8 |
| retrieved_tokens@3 | 1362 | 88 | 8 |
| retrieved_tokens@5 | 2338 | 113 | 8 |

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.375 | 0.171 | 8 |
| chunk_all_required@10 | 0.750 | 0.153 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.625 | 0.171 | 8 |
| chunk_all_required@5 | 0.625 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.375 | 0.183 | 8 |
| chunk_fact_recall@10 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@20 | 0.750 | 0.164 | 8 |
| chunk_fact_recall@3 | 0.688 | 0.162 | 8 |
| chunk_fact_recall@5 | 0.688 | 0.162 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.750 | 0.153 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.750 | 0.153 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.542 | 0.150 | 8 |
| chunk_ndcg@5 | 0.458 | 0.126 | 8 |
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
| page_ndcg@5 | 0.691 | 0.161 | 8 |
| retrieved_tokens@1 | 502 | 10 | 8 |
| retrieved_tokens@10 | 4655 | 108 | 8 |
| retrieved_tokens@20 | 9309 | 232 | 8 |
| retrieved_tokens@3 | 1500 | 26 | 8 |
| retrieved_tokens@5 | 2506 | 28 | 8 |

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.250 | 0.153 | 8 |
| chunk_all_required@10 | 0.625 | 0.171 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.417 | 0.148 | 8 |
| chunk_fact_recall@10 | 0.750 | 0.134 | 8 |
| chunk_fact_recall@20 | 0.812 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.583 | 0.148 | 8 |
| chunk_fact_recall@5 | 0.583 | 0.148 | 8 |
| chunk_hit@1 | 0.625 | 0.171 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.750 | 0.153 | 8 |
| chunk_hit@5 | 0.750 | 0.153 | 8 |
| chunk_mrr | 0.688 | 0.162 | 8 |
| chunk_ndcg@5 | 0.406 | 0.101 | 8 |
| page_fact_recall@1 | 0.583 | 0.175 | 8 |
| page_fact_recall@10 | 0.812 | 0.132 | 8 |
| page_fact_recall@20 | 0.812 | 0.132 | 8 |
| page_fact_recall@3 | 0.688 | 0.162 | 8 |
| page_fact_recall@5 | 0.688 | 0.162 | 8 |
| page_hit@1 | 0.750 | 0.153 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.812 | 0.132 | 8 |
| page_ndcg@5 | 0.625 | 0.112 | 8 |
| retrieved_tokens@1 | 500 | 12 | 8 |
| retrieved_tokens@10 | 4848 | 93 | 8 |
| retrieved_tokens@20 | 9600 | 165 | 8 |
| retrieved_tokens@3 | 1479 | 42 | 8 |
| retrieved_tokens@5 | 2501 | 42 | 8 |

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.125 | 0.117 | 8 |
| chunk_all_required@20 | 0.375 | 0.171 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.042 | 0.042 | 8 |
| chunk_fact_recall@10 | 0.323 | 0.122 | 8 |
| chunk_fact_recall@20 | 0.573 | 0.152 | 8 |
| chunk_fact_recall@3 | 0.125 | 0.088 | 8 |
| chunk_fact_recall@5 | 0.229 | 0.130 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.625 | 0.171 | 8 |
| chunk_hit@20 | 0.750 | 0.153 | 8 |
| chunk_hit@3 | 0.250 | 0.153 | 8 |
| chunk_hit@5 | 0.375 | 0.171 | 8 |
| chunk_mrr | 0.219 | 0.129 | 8 |
| chunk_ndcg@5 | 0.185 | 0.106 | 8 |
| page_fact_recall@1 | 0.125 | 0.125 | 8 |
| page_fact_recall@10 | 0.812 | 0.132 | 8 |
| page_fact_recall@20 | 0.938 | 0.062 | 8 |
| page_fact_recall@3 | 0.479 | 0.165 | 8 |
| page_fact_recall@5 | 0.479 | 0.165 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.875 | 0.117 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.521 | 0.120 | 8 |
| page_ndcg@5 | 0.447 | 0.111 | 8 |
| retrieved_tokens@1 | 501 | 11 | 8 |
| retrieved_tokens@10 | 4769 | 116 | 8 |
| retrieved_tokens@20 | 9642 | 88 | 8 |
| retrieved_tokens@3 | 1448 | 61 | 8 |
| retrieved_tokens@5 | 2356 | 84 | 8 |

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.500 | 0.177 | 8 |
| chunk_all_required@20 | 0.750 | 0.153 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.229 | 0.130 | 8 |
| chunk_fact_recall@10 | 0.725 | 0.129 | 8 |
| chunk_fact_recall@20 | 0.812 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.521 | 0.165 | 8 |
| chunk_fact_recall@5 | 0.521 | 0.165 | 8 |
| chunk_hit@1 | 0.375 | 0.171 | 8 |
| chunk_hit@10 | 0.875 | 0.117 | 8 |
| chunk_hit@20 | 0.875 | 0.117 | 8 |
| chunk_hit@3 | 0.625 | 0.171 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.479 | 0.165 | 8 |
| chunk_ndcg@5 | 0.327 | 0.111 | 8 |
| page_fact_recall@1 | 0.396 | 0.160 | 8 |
| page_fact_recall@10 | 0.787 | 0.129 | 8 |
| page_fact_recall@20 | 0.812 | 0.132 | 8 |
| page_fact_recall@3 | 0.725 | 0.129 | 8 |
| page_fact_recall@5 | 0.787 | 0.129 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 1.000 | 0.000 | 8 |
| page_hit@5 | 1.000 | 0.000 | 8 |
| page_mrr | 0.771 | 0.113 | 8 |
| page_ndcg@5 | 0.659 | 0.096 | 8 |
| retrieved_tokens@1 | 466 | 42 | 8 |
| retrieved_tokens@10 | 4636 | 170 | 8 |
| retrieved_tokens@20 | 9434 | 237 | 8 |
| retrieved_tokens@3 | 1356 | 91 | 8 |
| retrieved_tokens@5 | 2330 | 114 | 8 |

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.625 | 0.171 | 8 |
| chunk_all_required@20 | 0.875 | 0.117 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.500 | 0.177 | 8 |
| chunk_fact_recall@1 | 0.375 | 0.125 | 8 |
| chunk_fact_recall@10 | 0.857 | 0.080 | 8 |
| chunk_fact_recall@20 | 0.938 | 0.062 | 8 |
| chunk_fact_recall@3 | 0.500 | 0.134 | 8 |
| chunk_fact_recall@5 | 0.732 | 0.130 | 8 |
| chunk_hit@1 | 0.625 | 0.171 | 8 |
| chunk_hit@10 | 1.000 | 0.000 | 8 |
| chunk_hit@20 | 1.000 | 0.000 | 8 |
| chunk_hit@3 | 0.750 | 0.153 | 8 |
| chunk_hit@5 | 0.875 | 0.117 | 8 |
| chunk_mrr | 0.713 | 0.148 | 8 |
| chunk_ndcg@5 | 0.456 | 0.093 | 8 |
| page_fact_recall@1 | 0.500 | 0.164 | 8 |
| page_fact_recall@10 | 0.920 | 0.062 | 8 |
| page_fact_recall@20 | 0.938 | 0.062 | 8 |
| page_fact_recall@3 | 0.688 | 0.162 | 8 |
| page_fact_recall@5 | 0.795 | 0.129 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@10 | 1.000 | 0.000 | 8 |
| page_hit@20 | 1.000 | 0.000 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.713 | 0.148 | 8 |
| page_ndcg@5 | 0.569 | 0.124 | 8 |
| retrieved_tokens@1 | 494 | 12 | 8 |
| retrieved_tokens@10 | 4971 | 55 | 8 |
| retrieved_tokens@20 | 9824 | 44 | 8 |
| retrieved_tokens@3 | 1485 | 33 | 8 |
| retrieved_tokens@5 | 2509 | 33 | 8 |

## Token-matched k = 5 (target 2344 tokens)

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_fact_recall | 0.542 | 0.079 | 32 |
| chunk_hit | 0.656 | 0.084 | 32 |
| page_hit | 0.875 | 0.058 | 32 |
| tokens | 2425 | 38 | 32 |

## Lists

- page_hit_no_chunk: 49, 32, 44, 55, 35, 38, 89
- conflict_unscored: 53, 50, 58
- near_ties: none

## answer_only_facts

- row 58 F1
- row 22 F1

## no_retrieval_facts

- 22

## evidence_warnings

none

## Rerank vs in-run dense (spec 0012)

Paired chunk_fact_recall@5, rerank − dense: -0.041 ± 0.058 SE (-0.70 SE), n = 32; won 3, lost 6, tied 23

- Headroom captured (headline, fixed): -0.139 = (rerank@5 0.542 − 0.583) / (0.875 − 0.583)
- Headroom within this run: -0.139 = (rerank@5 0.542 − dense@5 0.583) / (ceiling 0.875 − dense@5 0.583)
- A gap between the two figures is query-vector drift. Neither decides adoption.

| k | dense | rerank |
|---|---|---|
| chunk_fact_recall@3 | 0.510 | 0.458 |
| chunk_fact_recall@4 | 0.552 | 0.484 |
| chunk_fact_recall@5 | 0.583 | 0.542 |
| chunk_fact_recall@6 | 0.651 | 0.567 |
| chunk_fact_recall@7 | 0.682 | 0.578 |
| chunk_fact_recall@8 | 0.744 | 0.609 |
| chunk_fact_recall@9 | 0.744 | 0.640 |
| chunk_fact_recall@10 | 0.744 | 0.664 |

| row | fact | dense rank | rerank rank | in top 5 (dense → rerank) |
|---|---|---|---|---|
| 49 | F1 | 8 | 15 | no → no |
| 49 | F4 | 3 | 10 | yes → no |
| 53 | F1 | 6 | 1 | no → yes |
| 8 | F1 | 6 | 5 | no → yes |
| 8 | F4 | 2 | 1 | yes → yes |
| 55 | F1 | 8 | 38 | no → no |
| 89 | F2 | 5 | 34 | yes → no |
| 89 | F4 | 8 | 40 | no → no |

- Rerank latency p50 / p95: 4154 / 5489 ms; in-run dense search p50: 337 ms (nearest-rank percentiles)
- Truncation share (pairs over the limit): 0.000
- Input tokens per pair: 563.9

## Comparison with baseline 2026-10-21-d83f3edc (change: retriever)

| metric | baseline mean ± SE (n) | this run mean ± SE (n) | delta |
|---|---|---|---|
| chunk_fact_recall@5 | 0.583 ± 0.075 (32) | 0.542 ± 0.079 (32) | -0.041 |
| retrieved_tokens@5 | 2344 ± 51 (32) | 2425 ± 38 (32) | +82 |
| chunk_all_required@1 | 0.188 ± 0.069 (32) | 0.156 ± 0.064 (32) | -0.031 |
| chunk_all_required@10 | 0.625 ± 0.086 (32) | 0.500 ± 0.088 (32) | -0.125 |
| chunk_all_required@20 | 0.719 ± 0.079 (32) | 0.688 ± 0.082 (32) | -0.031 |
| chunk_all_required@3 | 0.312 ± 0.082 (32) | 0.312 ± 0.082 (32) | +0.000 |
| chunk_all_required@5 | 0.406 ± 0.087 (32) | 0.406 ± 0.087 (32) | +0.000 |
| chunk_fact_recall@1 | 0.271 ± 0.070 (32) | 0.255 ± 0.067 (32) | -0.016 |
| chunk_fact_recall@10 | 0.744 ± 0.070 (32) | 0.664 ± 0.071 (32) | -0.081 |
| chunk_fact_recall@20 | 0.819 ± 0.061 (32) | 0.768 ± 0.068 (32) | -0.051 |
| chunk_fact_recall@3 | 0.510 ± 0.075 (32) | 0.458 ± 0.076 (32) | -0.052 |
| chunk_hit@1 | 0.375 ± 0.086 (32) | 0.375 ± 0.086 (32) | +0.000 |
| chunk_hit@10 | 0.812 ± 0.069 (32) | 0.812 ± 0.069 (32) | +0.000 |
| chunk_hit@20 | 0.875 ± 0.058 (32) | 0.844 ± 0.064 (32) | -0.031 |
| chunk_hit@3 | 0.656 ± 0.084 (32) | 0.594 ± 0.087 (32) | -0.062 |
| chunk_hit@5 | 0.719 ± 0.079 (32) | 0.656 ± 0.084 (32) | -0.062 |
| chunk_mrr | 0.504 ± 0.075 (32) | 0.488 ± 0.077 (32) | -0.016 |
| chunk_ndcg@5 | 0.397 ± 0.058 (32) | 0.357 ± 0.056 (32) | -0.041 |
| page_fact_recall@1 | 0.401 ± 0.085 (32) | 0.411 ± 0.083 (32) | +0.010 |
| page_fact_recall@10 | 0.849 ± 0.056 (32) | 0.817 ± 0.061 (32) | -0.031 |
| page_fact_recall@20 | 0.869 ± 0.055 (32) | 0.859 ± 0.056 (32) | -0.009 |
| page_fact_recall@3 | 0.661 ± 0.075 (32) | 0.660 ± 0.076 (32) | -0.001 |
| page_fact_recall@5 | 0.692 ± 0.073 (32) | 0.703 ± 0.074 (32) | +0.010 |
| page_hit@1 | 0.469 ± 0.088 (32) | 0.531 ± 0.088 (32) | +0.062 |
| page_hit@10 | 0.938 ± 0.043 (32) | 0.938 ± 0.043 (32) | +0.000 |
| page_hit@20 | 0.938 ± 0.043 (32) | 0.938 ± 0.043 (32) | +0.000 |
| page_hit@3 | 0.812 ± 0.069 (32) | 0.844 ± 0.064 (32) | +0.031 |
| page_hit@5 | 0.844 ± 0.064 (32) | 0.875 ± 0.058 (32) | +0.031 |
| page_mrr | 0.622 ± 0.069 (32) | 0.673 ± 0.067 (32) | +0.051 |
| page_ndcg@5 | 0.564 ± 0.066 (32) | 0.592 ± 0.062 (32) | +0.027 |
| retrieved_tokens@1 | 445 ± 22 (32) | 491 ± 11 (32) | +46 |
| retrieved_tokens@10 | 4679 ± 82 (32) | 4758 ± 62 (32) | +78 |
| retrieved_tokens@20 | 9406 ± 126 (32) | 9552 ± 89 (32) | +146 |
| retrieved_tokens@3 | 1418 ± 36 (32) | 1447 ± 30 (32) | +29 |

### Token-matched k (baseline k=5, this run k=5)

| metric | baseline @5 | this run @matched | delta |
|---|---|---|---|
| tokens | 2344 ± 51 (32) | 2425 ± 38 (32) | +82 |
| chunk_fact_recall | 0.583 ± 0.075 (32) | 0.542 ± 0.079 (32) | -0.041 |
| chunk_hit | 0.719 ± 0.079 (32) | 0.656 ± 0.084 (32) | -0.062 |
| page_hit | 0.844 ± 0.064 (32) | 0.875 ± 0.058 (32) | +0.031 |
| chunk_fact_recall@5 (both at k=5) | 0.583 ± 0.075 (32) | 0.542 ± 0.079 (32) | -0.041 |

### Paired delta (spec 0008 AC-7)

| comparison | mean delta | paired SE | mean / SE | n |
|---|---|---|---|---|
| chunk_fact_recall @matched k vs baseline @5 | -0.041 | 0.058 | -0.70 | 32 |
| chunk_fact_recall@5 vs @5 | -0.041 | 0.058 | -0.70 | 32 |

Adopt only if mean / SE > 2 on the matched-k row (spec 0008 AC-9).

| row | metric | baseline | this run |
|---|---|---|---|
| 52 | chunk_fact_recall@5 | 0.000 | 0.500 |
| 52 | chunk_hit@5 | 0.000 | 1.000 |
| 52 | page_hit@5 | 1.000 | 1.000 |
| 52 | chunk_fact_recall@matched | 0.000 | 0.500 |
| 52 | best relevant chunk | — | 2 · Access Requests (ARs) |
| 53 | chunk_fact_recall@5 | 0.000 | 1.000 |
| 53 | chunk_hit@5 | 0.000 | 1.000 |
| 53 | page_hit@5 | 0.000 | 1.000 |
| 53 | chunk_fact_recall@matched | 0.000 | 1.000 |
| 53 | best relevant chunk | — | 1 · Access Requests (ARs) |
| 8 | chunk_fact_recall@5 | 0.500 | 1.000 |
| 8 | chunk_hit@5 | 1.000 | 1.000 |
| 8 | page_hit@5 | 1.000 | 1.000 |
| 8 | chunk_fact_recall@matched | 0.500 | 1.000 |
| 8 | best relevant chunk | 2 · Processing Navan Reports | 1 · Processing Navan Reports |
| 10 | chunk_fact_recall@5 | 0.857 | 0.857 |
| 10 | chunk_hit@5 | 1.000 | 1.000 |
| 10 | page_hit@5 | 1.000 | 1.000 |
| 10 | chunk_fact_recall@matched | 0.857 | 0.857 |
| 10 | best relevant chunk | 2 · CREDIT | 5 · CREDIT |
| 99 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 99 | chunk_hit@5 | 1.000 | 1.000 |
| 99 | page_hit@5 | 1.000 | 1.000 |
| 99 | chunk_fact_recall@matched | 0.500 | 0.500 |
| 99 | best relevant chunk | 1 · Payroll & Benefits | 4 · Time Off Types |
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
| 11 | chunk_fact_recall@5 | 0.667 | 0.667 |
| 11 | chunk_hit@5 | 1.000 | 1.000 |
| 11 | page_hit@5 | 1.000 | 1.000 |
| 11 | chunk_fact_recall@matched | 0.667 | 0.667 |
| 11 | best relevant chunk | 2 · Equipment | 1 · Equipment |
| 34 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 34 | chunk_hit@5 | 1.000 | 1.000 |
| 34 | page_hit@5 | 1.000 | 1.000 |
| 34 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 34 | best relevant chunk | 1 · Team Member | 1 · Team Member |
| 44 | chunk_fact_recall@5 | 0.800 | 0.000 |
| 44 | chunk_hit@5 | 1.000 | 0.000 |
| 44 | page_hit@5 | 1.000 | 1.000 |
| 44 | chunk_fact_recall@matched | 0.800 | 0.000 |
| 44 | best relevant chunk | 2 · Role Comparison | — |
| 49 | chunk_fact_recall@5 | 0.500 | 0.000 |
| 49 | chunk_hit@5 | 1.000 | 0.000 |
| 49 | page_hit@5 | 1.000 | 1.000 |
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
| 88 | best relevant chunk | 1 · Timeline | 2 · Timeline |
| 100 | chunk_fact_recall@5 | 1.000 | 1.000 |
| 100 | chunk_hit@5 | 1.000 | 1.000 |
| 100 | page_hit@5 | 1.000 | 1.000 |
| 100 | chunk_fact_recall@matched | 1.000 | 1.000 |
| 100 | best relevant chunk | 1 · Time Off Types | 1 · How to Prepare for PTO |
| 5 | chunk_fact_recall@5 | 0.333 | 0.333 |
| 5 | chunk_hit@5 | 1.000 | 1.000 |
| 5 | page_hit@5 | 1.000 | 1.000 |
| 5 | chunk_fact_recall@matched | 0.333 | 0.333 |
| 5 | best relevant chunk | 1 · Sick Time Eligibility and Coverage | 2 · Sick Time Eligibility and Coverage |
| 32 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 32 | chunk_hit@5 | 0.000 | 0.000 |
| 32 | page_hit@5 | 1.000 | 1.000 |
| 32 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 32 | best relevant chunk | — | — |
| 35 | chunk_fact_recall@5 | 0.500 | 0.000 |
| 35 | chunk_hit@5 | 1.000 | 0.000 |
| 35 | page_hit@5 | 1.000 | 1.000 |
| 35 | chunk_fact_recall@matched | 0.500 | 0.000 |
| 35 | best relevant chunk | 3 · Termination | — |
| 87 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 87 | chunk_hit@5 | 0.000 | 0.000 |
| 87 | page_hit@5 | 1.000 | 0.000 |
| 87 | chunk_fact_recall@matched | 0.000 | 0.000 |
| 87 | best relevant chunk | — | — |

### Top-5 order vs baseline (spec 0007, AC-9)

identical on 0 of 33 rows

differing rows: 5, 8, 9, 10, 11, 13, 22, 23, 26, 32, 34, 35, 38, 44, 46, 48, 49, 50, 51, 52, 53, 55, 58, 59, 65, 87, 88, 89, 92, 93, 96, 99, 100

Continuity only (spec 0012 AC-12): the baseline embedded its questions separately, so its query vectors can differ from this run's (the row 32 and 93 drift). The decision rests on the in-run comparison above.
