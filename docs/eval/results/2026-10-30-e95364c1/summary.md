# Eval summary

## Takeaways

- **Retrieval-only, FTS-only (OR of lexemes, `ts_rank_cd`), for diagnosis.** chunk_fact_recall@5 0.148, against 0.583 for dense (`2026-10-21-d83f3edc`) and 0.521 for hybrid (`2026-10-30-e1e47d72`). No `BASELINE`, so there is no comparison section.
- **Why low:** the OR query matches a median of 51% of chunks, so common words such as `need`, `pleas` and `us` set the ranking. FTS ranks 1–5 carry a fact 4.4% of the time. Details are in the [journal](../../../journal/2026-10-30-hybrid-runs.md).
- **Next:** no adoption decision rests on this run.

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
- timestamp: 2026-10-30T11:53:02.442007+00:00
- rows: 33
- mode: retrieval-only
- limit: None
- user_id: admin
- policy_version: policy-v1
- policy_sha256: eeb8443f1e3b84718e02a302e6fe5efb43c3386de2050b055d9d0c14aa564cdc
- retriever: fts
- fts: {'config': 'english', 'normalization': 0, 'query': 'or-of-lexemes'}

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.031 | 0.031 | 32 |
| chunk_all_required@10 | 0.156 | 0.064 | 32 |
| chunk_all_required@20 | 0.281 | 0.079 | 32 |
| chunk_all_required@3 | 0.062 | 0.043 | 32 |
| chunk_all_required@5 | 0.094 | 0.052 | 32 |
| chunk_fact_recall@1 | 0.031 | 0.031 | 32 |
| chunk_fact_recall@10 | 0.216 | 0.066 | 32 |
| chunk_fact_recall@20 | 0.357 | 0.078 | 32 |
| chunk_fact_recall@3 | 0.078 | 0.046 | 32 |
| chunk_fact_recall@5 | 0.148 | 0.056 | 32 |
| chunk_hit@1 | 0.031 | 0.031 | 32 |
| chunk_hit@10 | 0.312 | 0.082 | 32 |
| chunk_hit@20 | 0.469 | 0.088 | 32 |
| chunk_hit@3 | 0.094 | 0.052 | 32 |
| chunk_hit@5 | 0.219 | 0.073 | 32 |
| chunk_mrr | 0.084 | 0.036 | 32 |
| chunk_ndcg@5 | 0.070 | 0.028 | 32 |
| page_fact_recall@1 | 0.078 | 0.046 | 32 |
| page_fact_recall@10 | 0.339 | 0.079 | 32 |
| page_fact_recall@20 | 0.522 | 0.083 | 32 |
| page_fact_recall@3 | 0.156 | 0.061 | 32 |
| page_fact_recall@5 | 0.234 | 0.071 | 32 |
| page_hit@1 | 0.125 | 0.058 | 32 |
| page_hit@10 | 0.406 | 0.087 | 32 |
| page_hit@20 | 0.594 | 0.087 | 32 |
| page_hit@3 | 0.219 | 0.073 | 32 |
| page_hit@5 | 0.312 | 0.082 | 32 |
| page_mrr | 0.192 | 0.061 | 32 |
| page_ndcg@5 | 0.141 | 0.043 | 32 |
| retrieved_tokens@1 | 512 | 0 | 32 |
| retrieved_tokens@10 | 5003 | 112 | 32 |
| retrieved_tokens@20 | 9896 | 270 | 32 |
| retrieved_tokens@3 | 1536 | 0 | 32 |
| retrieved_tokens@5 | 2525 | 32 | 32 |

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.000 | 0.000 | 8 |
| chunk_all_required@20 | 0.375 | 0.171 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@1 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@10 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@20 | 0.375 | 0.183 | 8 |
| chunk_fact_recall@3 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@5 | 0.000 | 0.000 | 8 |
| chunk_hit@1 | 0.000 | 0.000 | 8 |
| chunk_hit@10 | 0.000 | 0.000 | 8 |
| chunk_hit@20 | 0.375 | 0.171 | 8 |
| chunk_hit@3 | 0.000 | 0.000 | 8 |
| chunk_hit@5 | 0.000 | 0.000 | 8 |
| chunk_mrr | 0.000 | 0.000 | 8 |
| chunk_ndcg@5 | 0.000 | 0.000 | 8 |
| page_fact_recall@1 | 0.000 | 0.000 | 8 |
| page_fact_recall@10 | 0.062 | 0.062 | 8 |
| page_fact_recall@20 | 0.607 | 0.179 | 8 |
| page_fact_recall@3 | 0.062 | 0.062 | 8 |
| page_fact_recall@5 | 0.062 | 0.062 | 8 |
| page_hit@1 | 0.000 | 0.000 | 8 |
| page_hit@10 | 0.125 | 0.117 | 8 |
| page_hit@20 | 0.625 | 0.171 | 8 |
| page_hit@3 | 0.125 | 0.117 | 8 |
| page_hit@5 | 0.125 | 0.117 | 8 |
| page_mrr | 0.062 | 0.062 | 8 |
| page_ndcg@5 | 0.048 | 0.048 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 5120 | 0 | 8 |
| retrieved_tokens@20 | 10224 | 12 | 8 |
| retrieved_tokens@3 | 1536 | 0 | 8 |
| retrieved_tokens@5 | 2560 | 0 | 8 |

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@10 | 0.375 | 0.171 | 8 |
| chunk_all_required@20 | 0.500 | 0.177 | 8 |
| chunk_all_required@3 | 0.250 | 0.153 | 8 |
| chunk_all_required@5 | 0.375 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.125 | 0.125 | 8 |
| chunk_fact_recall@10 | 0.438 | 0.175 | 8 |
| chunk_fact_recall@20 | 0.500 | 0.189 | 8 |
| chunk_fact_recall@3 | 0.250 | 0.164 | 8 |
| chunk_fact_recall@5 | 0.438 | 0.175 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@10 | 0.500 | 0.177 | 8 |
| chunk_hit@20 | 0.500 | 0.177 | 8 |
| chunk_hit@3 | 0.250 | 0.153 | 8 |
| chunk_hit@5 | 0.500 | 0.177 | 8 |
| chunk_mrr | 0.244 | 0.125 | 8 |
| chunk_ndcg@5 | 0.204 | 0.090 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@10 | 0.625 | 0.183 | 8 |
| page_fact_recall@20 | 0.625 | 0.183 | 8 |
| page_fact_recall@3 | 0.250 | 0.164 | 8 |
| page_fact_recall@5 | 0.500 | 0.189 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@10 | 0.625 | 0.171 | 8 |
| page_hit@20 | 0.625 | 0.171 | 8 |
| page_hit@3 | 0.250 | 0.153 | 8 |
| page_hit@5 | 0.500 | 0.177 | 8 |
| page_mrr | 0.306 | 0.155 | 8 |
| page_ndcg@5 | 0.286 | 0.127 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 5103 | 11 | 8 |
| retrieved_tokens@20 | 10093 | 50 | 8 |
| retrieved_tokens@3 | 1536 | 0 | 8 |
| retrieved_tokens@5 | 2550 | 10 | 8 |

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.125 | 0.117 | 8 |
| chunk_all_required@20 | 0.125 | 0.117 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@1 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@10 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@20 | 0.250 | 0.134 | 8 |
| chunk_fact_recall@3 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@5 | 0.062 | 0.062 | 8 |
| chunk_hit@1 | 0.000 | 0.000 | 8 |
| chunk_hit@10 | 0.250 | 0.153 | 8 |
| chunk_hit@20 | 0.375 | 0.171 | 8 |
| chunk_hit@3 | 0.000 | 0.000 | 8 |
| chunk_hit@5 | 0.125 | 0.117 | 8 |
| chunk_mrr | 0.025 | 0.025 | 8 |
| chunk_ndcg@5 | 0.023 | 0.023 | 8 |
| page_fact_recall@1 | 0.000 | 0.000 | 8 |
| page_fact_recall@10 | 0.188 | 0.132 | 8 |
| page_fact_recall@20 | 0.312 | 0.162 | 8 |
| page_fact_recall@3 | 0.000 | 0.000 | 8 |
| page_fact_recall@5 | 0.062 | 0.062 | 8 |
| page_hit@1 | 0.000 | 0.000 | 8 |
| page_hit@10 | 0.250 | 0.153 | 8 |
| page_hit@20 | 0.375 | 0.171 | 8 |
| page_hit@3 | 0.125 | 0.117 | 8 |
| page_hit@5 | 0.250 | 0.153 | 8 |
| page_mrr | 0.087 | 0.064 | 8 |
| page_ndcg@5 | 0.067 | 0.044 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 5118 | 2 | 8 |
| retrieved_tokens@20 | 10184 | 42 | 8 |
| retrieved_tokens@3 | 1536 | 0 | 8 |
| retrieved_tokens@5 | 2558 | 2 | 8 |

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.125 | 0.117 | 8 |
| chunk_all_required@20 | 0.125 | 0.117 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@1 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@10 | 0.240 | 0.121 | 8 |
| chunk_fact_recall@20 | 0.302 | 0.120 | 8 |
| chunk_fact_recall@3 | 0.062 | 0.062 | 8 |
| chunk_fact_recall@5 | 0.094 | 0.066 | 8 |
| chunk_hit@1 | 0.000 | 0.000 | 8 |
| chunk_hit@10 | 0.500 | 0.177 | 8 |
| chunk_hit@20 | 0.625 | 0.171 | 8 |
| chunk_hit@3 | 0.125 | 0.117 | 8 |
| chunk_hit@5 | 0.250 | 0.153 | 8 |
| chunk_mrr | 0.067 | 0.045 | 8 |
| chunk_ndcg@5 | 0.055 | 0.039 | 8 |
| page_fact_recall@1 | 0.062 | 0.062 | 8 |
| page_fact_recall@10 | 0.479 | 0.165 | 8 |
| page_fact_recall@20 | 0.542 | 0.150 | 8 |
| page_fact_recall@3 | 0.312 | 0.162 | 8 |
| page_fact_recall@5 | 0.312 | 0.162 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@10 | 0.625 | 0.171 | 8 |
| page_hit@20 | 0.750 | 0.153 | 8 |
| page_hit@3 | 0.375 | 0.171 | 8 |
| page_hit@5 | 0.375 | 0.171 | 8 |
| page_mrr | 0.312 | 0.162 | 8 |
| page_ndcg@5 | 0.164 | 0.084 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 4672 | 448 | 8 |
| retrieved_tokens@20 | 9082 | 1079 | 8 |
| retrieved_tokens@3 | 1536 | 0 | 8 |
| retrieved_tokens@5 | 2432 | 128 | 8 |

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.125 | 0.117 | 8 |
| chunk_all_required@20 | 0.375 | 0.171 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@1 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@10 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@20 | 0.438 | 0.175 | 8 |
| chunk_fact_recall@3 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@5 | 0.062 | 0.062 | 8 |
| chunk_hit@1 | 0.000 | 0.000 | 8 |
| chunk_hit@10 | 0.250 | 0.153 | 8 |
| chunk_hit@20 | 0.500 | 0.177 | 8 |
| chunk_hit@3 | 0.000 | 0.000 | 8 |
| chunk_hit@5 | 0.125 | 0.117 | 8 |
| chunk_mrr | 0.025 | 0.025 | 8 |
| chunk_ndcg@5 | 0.023 | 0.023 | 8 |
| page_fact_recall@1 | 0.000 | 0.000 | 8 |
| page_fact_recall@10 | 0.188 | 0.132 | 8 |
| page_fact_recall@20 | 0.438 | 0.175 | 8 |
| page_fact_recall@3 | 0.000 | 0.000 | 8 |
| page_fact_recall@5 | 0.062 | 0.062 | 8 |
| page_hit@1 | 0.000 | 0.000 | 8 |
| page_hit@10 | 0.250 | 0.153 | 8 |
| page_hit@20 | 0.500 | 0.177 | 8 |
| page_hit@3 | 0.125 | 0.117 | 8 |
| page_hit@5 | 0.250 | 0.153 | 8 |
| page_mrr | 0.087 | 0.064 | 8 |
| page_ndcg@5 | 0.067 | 0.044 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 5120 | 0 | 8 |
| retrieved_tokens@20 | 10228 | 12 | 8 |
| retrieved_tokens@3 | 1536 | 0 | 8 |
| retrieved_tokens@5 | 2560 | 0 | 8 |

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@10 | 0.000 | 0.000 | 8 |
| chunk_all_required@20 | 0.125 | 0.117 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@1 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@10 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@20 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@5 | 0.000 | 0.000 | 8 |
| chunk_hit@1 | 0.000 | 0.000 | 8 |
| chunk_hit@10 | 0.000 | 0.000 | 8 |
| chunk_hit@20 | 0.250 | 0.153 | 8 |
| chunk_hit@3 | 0.000 | 0.000 | 8 |
| chunk_hit@5 | 0.000 | 0.000 | 8 |
| chunk_mrr | 0.000 | 0.000 | 8 |
| chunk_ndcg@5 | 0.000 | 0.000 | 8 |
| page_fact_recall@1 | 0.000 | 0.000 | 8 |
| page_fact_recall@10 | 0.062 | 0.062 | 8 |
| page_fact_recall@20 | 0.482 | 0.183 | 8 |
| page_fact_recall@3 | 0.062 | 0.062 | 8 |
| page_fact_recall@5 | 0.062 | 0.062 | 8 |
| page_hit@1 | 0.000 | 0.000 | 8 |
| page_hit@10 | 0.125 | 0.117 | 8 |
| page_hit@20 | 0.500 | 0.177 | 8 |
| page_hit@3 | 0.125 | 0.117 | 8 |
| page_hit@5 | 0.125 | 0.117 | 8 |
| page_mrr | 0.062 | 0.062 | 8 |
| page_ndcg@5 | 0.048 | 0.048 | 8 |
| retrieved_tokens@1 | 512 | 0 | 8 |
| retrieved_tokens@10 | 5118 | 2 | 8 |
| retrieved_tokens@20 | 10180 | 41 | 8 |
| retrieved_tokens@3 | 1536 | 0 | 8 |
| retrieved_tokens@5 | 2558 | 2 | 8 |

## Lists

- page_hit_no_chunk: 53, 8, 87
- conflict_unscored: 53, 50, 58
- near_ties: none

## answer_only_facts

- row 58 F1
- row 22 F1

## no_retrieval_facts

- 22

## evidence_warnings

none
