# Eval summary

## Takeaways

- **structural-v1 retrieves worse than the baseline at k=5.** chunk_fact_recall@5 fell from 0.495 to 0.358 (−0.14) and page_hit@5 from 0.81 to 0.69. Of the 32 scored rows, 8 got worse, 1 got better (row 8) and 23 didn't change. It sends a third of the tokens (2,335 → 815 in the top 5).
- **The main cause is heading-only chunks crowding the top 5.** 2,433 structural chunks are just a heading line: a parent heading followed directly by a child heading, which AC-8 won't merge with the child. They match a question's wording closely and carry no facts.
  - 39 of the 165 chunks retrieved for answerable rows are under 32 tokens.
  - Row 58's top 5 is five copies of "Time Off Policies" from five entity benefit pages.
  - Rows 49, 100, 11 and 34 each lose a slot or more to a 5–16 token heading chunk.
  - The build review noted this as a follow-up. The run shows it's the first thing to fix.
- **Where it helped:** row 8 now finds its fact at rank 2. The other target rows from the baseline (52, 53, 10, 99, 38, 89) still get 0, and 99 and 89 also lose the page.
- **Answers:** ooc_pass fell from 0.89 to 0.74. On 5 of the 6 OOC rows that changed, the model still abstained in both runs; the only change is whether the check accepted the wording, and it went both ways. Row 112 answered instead of abstaining. With n=19–20, the answer metrics move by about one SE.
- **Previous fix:** the AC-10 relevance fix left the baseline unchanged. The re-run 2026-10-19-287181bb has the same top-5 ids and metrics on all 33 answerable rows.
- **Next iteration:** keep a heading with no body out of the chunks. Carry it into its first child's heading path instead of making it a chunk (this needs an AC-8 amendment in a spec). Then re-run against the same baseline. The min-size sweep waits until after that.

## Run

- eval_version: v1.2
- eval_sha256: 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- harness_sha: e1abbc03357c6c495eb2e91b514ff64adbf04738
- harness_dirty: False
- corpus_sha: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- config_id: structural-v1
- chunk_params: {'strategy': 'structural', 'overlap': 64, 'max_tokens': 512, 'min_tokens': 64, 'tokenizer': 'cl100k_base'}
- embed_model: openai:text-embedding-3-small
- answer_model: openai:gpt-5.4-mini
- system_prompt_sha256: deebd6f367e33132316ef082b903808e5c892714e35a5ebcd0bfedfbec9316f2
- k: 5
- timestamp: 2026-10-19T12:10:12.683892+00:00
- rows: 52
- mode: full
- limit: None
- baseline: 2026-10-17-3748df5b

Metric definitions: [../metrics.md](../metrics.md)

## overall

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.058 | 32 |
| chunk_all_required@3 | 0.156 | 0.064 | 32 |
| chunk_all_required@5 | 0.250 | 0.077 | 32 |
| chunk_fact_recall@1 | 0.161 | 0.061 | 32 |
| chunk_fact_recall@3 | 0.255 | 0.067 | 32 |
| chunk_fact_recall@5 | 0.358 | 0.076 | 32 |
| chunk_hit@1 | 0.219 | 0.073 | 32 |
| chunk_hit@3 | 0.375 | 0.086 | 32 |
| chunk_hit@5 | 0.469 | 0.088 | 32 |
| chunk_mrr | 0.308 | 0.072 | 32 |
| chunk_ndcg@5 | 0.247 | 0.057 | 32 |
| page_fact_recall@1 | 0.334 | 0.081 | 32 |
| page_fact_recall@3 | 0.459 | 0.083 | 32 |
| page_fact_recall@5 | 0.563 | 0.081 | 32 |
| page_hit@1 | 0.375 | 0.086 | 32 |
| page_hit@3 | 0.562 | 0.088 | 32 |
| page_hit@5 | 0.688 | 0.082 | 32 |
| page_mrr | 0.486 | 0.077 | 32 |
| page_ndcg@5 | 0.425 | 0.068 | 32 |
| retrieved_tokens@1 | 133 | 23 | 32 |
| retrieved_tokens@3 | 476 | 52 | 32 |
| retrieved_tokens@5 | 815 | 70 | 32 |
| ooc_pass | 0.737 | 0.101 | 19 |
| false_abstention | 0.424 | 0.086 | 33 |
| code_checks_passed | 0.947 | 0.051 | 19 |
| has_citation | 0.947 | 0.051 | 19 |
| citations_in_range | 1.000 | 0.000 | 19 |
| headings_exist | 1.000 | 0.000 | 19 |
| no_url | 1.000 | 0.000 | 19 |
| truncated | 0.000 | 0.000 | 52 |

Abstention labels: wrong-string 4

## by_type: contradiction

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.250 | 0.134 | 8 |
| chunk_fact_recall@5 | 0.475 | 0.154 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.369 | 0.150 | 8 |
| chunk_ndcg@5 | 0.309 | 0.122 | 8 |
| page_fact_recall@1 | 0.295 | 0.152 | 8 |
| page_fact_recall@3 | 0.482 | 0.157 | 8 |
| page_fact_recall@5 | 0.732 | 0.130 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.875 | 0.117 | 8 |
| page_mrr | 0.573 | 0.137 | 8 |
| page_ndcg@5 | 0.491 | 0.105 | 8 |
| retrieved_tokens@1 | 222 | 63 | 8 |
| retrieved_tokens@3 | 664 | 104 | 8 |
| retrieved_tokens@5 | 1012 | 143 | 8 |
| false_abstention | 0.250 | 0.153 | 8 |
| code_checks_passed | 1.000 | 0.000 | 6 |
| has_citation | 1.000 | 0.000 | 6 |
| citations_in_range | 1.000 | 0.000 | 6 |
| headings_exist | 1.000 | 0.000 | 6 |
| no_url | 1.000 | 0.000 | 6 |
| truncated | 0.000 | 0.000 | 8 |

Abstention labels: none

## by_type: lookup

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.250 | 0.153 | 8 |
| chunk_all_required@3 | 0.375 | 0.171 | 8 |
| chunk_all_required@5 | 0.625 | 0.171 | 8 |
| chunk_fact_recall@1 | 0.250 | 0.164 | 8 |
| chunk_fact_recall@3 | 0.438 | 0.175 | 8 |
| chunk_fact_recall@5 | 0.625 | 0.183 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@3 | 0.500 | 0.177 | 8 |
| chunk_hit@5 | 0.625 | 0.171 | 8 |
| chunk_mrr | 0.385 | 0.149 | 8 |
| chunk_ndcg@5 | 0.392 | 0.147 | 8 |
| page_fact_recall@1 | 0.625 | 0.183 | 8 |
| page_fact_recall@3 | 0.750 | 0.164 | 8 |
| page_fact_recall@5 | 0.750 | 0.164 | 8 |
| page_hit@1 | 0.625 | 0.171 | 8 |
| page_hit@3 | 0.750 | 0.153 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.688 | 0.162 | 8 |
| page_ndcg@5 | 0.638 | 0.156 | 8 |
| retrieved_tokens@1 | 102 | 37 | 8 |
| retrieved_tokens@3 | 483 | 67 | 8 |
| retrieved_tokens@5 | 788 | 102 | 8 |
| false_abstention | 0.444 | 0.166 | 9 |
| code_checks_passed | 1.000 | 0.000 | 5 |
| has_citation | 1.000 | 0.000 | 5 |
| citations_in_range | 1.000 | 0.000 | 5 |
| headings_exist | 1.000 | 0.000 | 5 |
| no_url | 1.000 | 0.000 | 5 |
| truncated | 0.000 | 0.000 | 9 |

Abstention labels: none

## by_type: ooc-in-scope

| metric | mean | ± SE | n |
|---|---|---|---|
| ooc_pass | 0.900 | 0.095 | 10 |
| truncated | 0.000 | 0.000 | 10 |

Abstention labels: none

## by_type: ooc-off-topic

| metric | mean | ± SE | n |
|---|---|---|---|
| ooc_pass | 0.556 | 0.166 | 9 |
| truncated | 0.000 | 0.000 | 9 |

Abstention labels: wrong-string 4

## by_type: recency

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.125 | 0.125 | 8 |
| chunk_fact_recall@3 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@5 | 0.188 | 0.132 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@3 | 0.250 | 0.153 | 8 |
| chunk_hit@5 | 0.250 | 0.153 | 8 |
| chunk_mrr | 0.167 | 0.126 | 8 |
| chunk_ndcg@5 | 0.115 | 0.081 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@3 | 0.312 | 0.162 | 8 |
| page_fact_recall@5 | 0.479 | 0.165 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@3 | 0.375 | 0.171 | 8 |
| page_hit@5 | 0.625 | 0.171 | 8 |
| page_mrr | 0.348 | 0.149 | 8 |
| page_ndcg@5 | 0.302 | 0.128 | 8 |
| retrieved_tokens@1 | 69 | 18 | 8 |
| retrieved_tokens@3 | 406 | 99 | 8 |
| retrieved_tokens@5 | 769 | 162 | 8 |
| false_abstention | 0.500 | 0.177 | 8 |
| code_checks_passed | 0.750 | 0.217 | 4 |
| has_citation | 0.750 | 0.217 | 4 |
| citations_in_range | 1.000 | 0.000 | 4 |
| headings_exist | 1.000 | 0.000 | 4 |
| no_url | 1.000 | 0.000 | 4 |
| truncated | 0.000 | 0.000 | 8 |

Abstention labels: none

## by_type: synthesis

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.000 | 0.000 | 8 |
| chunk_all_required@3 | 0.000 | 0.000 | 8 |
| chunk_all_required@5 | 0.000 | 0.000 | 8 |
| chunk_fact_recall@1 | 0.083 | 0.055 | 8 |
| chunk_fact_recall@3 | 0.146 | 0.073 | 8 |
| chunk_fact_recall@5 | 0.146 | 0.073 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.375 | 0.171 | 8 |
| chunk_mrr | 0.312 | 0.162 | 8 |
| chunk_ndcg@5 | 0.174 | 0.090 | 8 |
| page_fact_recall@1 | 0.167 | 0.126 | 8 |
| page_fact_recall@3 | 0.292 | 0.160 | 8 |
| page_fact_recall@5 | 0.292 | 0.160 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@3 | 0.375 | 0.171 | 8 |
| page_hit@5 | 0.500 | 0.177 | 8 |
| page_mrr | 0.338 | 0.157 | 8 |
| page_ndcg@5 | 0.269 | 0.132 | 8 |
| retrieved_tokens@1 | 138 | 46 | 8 |
| retrieved_tokens@3 | 350 | 119 | 8 |
| retrieved_tokens@5 | 692 | 145 | 8 |
| false_abstention | 0.500 | 0.177 | 8 |
| code_checks_passed | 1.000 | 0.000 | 4 |
| has_citation | 1.000 | 0.000 | 4 |
| citations_in_range | 1.000 | 0.000 | 4 |
| headings_exist | 1.000 | 0.000 | 4 |
| no_url | 1.000 | 0.000 | 4 |
| truncated | 0.000 | 0.000 | 8 |

Abstention labels: none

## by_recency_basis: history-only

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.125 | 0.117 | 8 |
| chunk_fact_recall@1 | 0.125 | 0.125 | 8 |
| chunk_fact_recall@3 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@5 | 0.287 | 0.148 | 8 |
| chunk_hit@1 | 0.125 | 0.117 | 8 |
| chunk_hit@3 | 0.250 | 0.153 | 8 |
| chunk_hit@5 | 0.375 | 0.171 | 8 |
| chunk_mrr | 0.192 | 0.124 | 8 |
| chunk_ndcg@5 | 0.186 | 0.123 | 8 |
| page_fact_recall@1 | 0.250 | 0.164 | 8 |
| page_fact_recall@3 | 0.312 | 0.162 | 8 |
| page_fact_recall@5 | 0.604 | 0.160 | 8 |
| page_hit@1 | 0.250 | 0.153 | 8 |
| page_hit@3 | 0.500 | 0.177 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.390 | 0.141 | 8 |
| page_ndcg@5 | 0.395 | 0.141 | 8 |
| retrieved_tokens@1 | 163 | 54 | 8 |
| retrieved_tokens@3 | 604 | 101 | 8 |
| retrieved_tokens@5 | 931 | 125 | 8 |
| false_abstention | 0.500 | 0.177 | 8 |
| code_checks_passed | 0.750 | 0.217 | 4 |
| has_citation | 0.750 | 0.217 | 4 |
| citations_in_range | 1.000 | 0.000 | 4 |
| headings_exist | 1.000 | 0.000 | 4 |
| no_url | 1.000 | 0.000 | 4 |
| truncated | 0.000 | 0.000 | 8 |

Abstention labels: none

## by_recency_basis: in-page

| metric | mean | ± SE | n |
|---|---|---|---|
| chunk_all_required@1 | 0.125 | 0.117 | 8 |
| chunk_all_required@3 | 0.125 | 0.117 | 8 |
| chunk_all_required@5 | 0.250 | 0.153 | 8 |
| chunk_fact_recall@1 | 0.188 | 0.132 | 8 |
| chunk_fact_recall@3 | 0.250 | 0.134 | 8 |
| chunk_fact_recall@5 | 0.375 | 0.157 | 8 |
| chunk_hit@1 | 0.250 | 0.153 | 8 |
| chunk_hit@3 | 0.375 | 0.171 | 8 |
| chunk_hit@5 | 0.500 | 0.177 | 8 |
| chunk_mrr | 0.344 | 0.156 | 8 |
| chunk_ndcg@5 | 0.237 | 0.093 | 8 |
| page_fact_recall@1 | 0.295 | 0.152 | 8 |
| page_fact_recall@3 | 0.482 | 0.157 | 8 |
| page_fact_recall@5 | 0.607 | 0.152 | 8 |
| page_hit@1 | 0.375 | 0.171 | 8 |
| page_hit@3 | 0.625 | 0.171 | 8 |
| page_hit@5 | 0.750 | 0.153 | 8 |
| page_mrr | 0.531 | 0.153 | 8 |
| page_ndcg@5 | 0.397 | 0.100 | 8 |
| retrieved_tokens@1 | 128 | 55 | 8 |
| retrieved_tokens@3 | 466 | 118 | 8 |
| retrieved_tokens@5 | 850 | 186 | 8 |
| false_abstention | 0.250 | 0.153 | 8 |
| code_checks_passed | 1.000 | 0.000 | 6 |
| has_citation | 1.000 | 0.000 | 6 |
| citations_in_range | 1.000 | 0.000 | 6 |
| headings_exist | 1.000 | 0.000 | 6 |
| no_url | 1.000 | 0.000 | 6 |
| truncated | 0.000 | 0.000 | 8 |

Abstention labels: none

## Lists

- page_hit_no_chunk: 11, 52, 53, 10, 100, 38, 88
- conflict_unscored: 53, 50, 58

## answer_only_facts

- row 58 F1
- row 22 F1

## no_retrieval_facts

- 22

## evidence_warnings

none

## Comparison with baseline 2026-10-17-3748df5b

| metric | baseline mean ± SE (n) | this run mean ± SE (n) | delta |
|---|---|---|---|
| chunk_fact_recall@5 | 0.495 ± 0.081 (32) | 0.358 ± 0.076 (32) | -0.136 |
| retrieved_tokens@5 | 2335 ± 45 (32) | 815 ± 70 (32) | -1520 |
| chunk_all_required@1 | 0.125 ± 0.058 (32) | 0.125 ± 0.058 (32) | +0.000 |
| chunk_all_required@3 | 0.312 ± 0.082 (32) | 0.156 ± 0.064 (32) | -0.156 |
| chunk_all_required@5 | 0.406 ± 0.087 (32) | 0.250 ± 0.077 (32) | -0.156 |
| chunk_fact_recall@1 | 0.177 ± 0.061 (32) | 0.161 ± 0.061 (32) | -0.016 |
| chunk_fact_recall@3 | 0.417 ± 0.078 (32) | 0.255 ± 0.067 (32) | -0.161 |
| chunk_hit@1 | 0.250 ± 0.077 (32) | 0.219 ± 0.073 (32) | -0.031 |
| chunk_hit@3 | 0.531 ± 0.088 (32) | 0.375 ± 0.086 (32) | -0.156 |
| chunk_hit@5 | 0.594 ± 0.087 (32) | 0.469 ± 0.088 (32) | -0.125 |
| chunk_mrr | 0.380 ± 0.071 (32) | 0.308 ± 0.072 (32) | -0.072 |
| chunk_ndcg@5 | 0.295 ± 0.056 (32) | 0.247 ± 0.057 (32) | -0.048 |
| citations_in_range | 1.000 ± 0.000 (20) | 1.000 ± 0.000 (19) | +0.000 |
| code_checks_passed | 0.950 ± 0.049 (20) | 0.947 ± 0.051 (19) | -0.003 |
| false_abstention | 0.394 ± 0.085 (33) | 0.424 ± 0.086 (33) | +0.030 |
| has_citation | 0.950 ± 0.049 (20) | 0.947 ± 0.051 (19) | -0.003 |
| headings_exist | 1.000 ± 0.000 (20) | 1.000 ± 0.000 (19) | +0.000 |
| no_url | 1.000 ± 0.000 (20) | 1.000 ± 0.000 (19) | +0.000 |
| ooc_pass | 0.895 ± 0.070 (19) | 0.737 ± 0.101 (19) | -0.158 |
| page_fact_recall@1 | 0.318 ± 0.082 (32) | 0.334 ± 0.081 (32) | +0.016 |
| page_fact_recall@3 | 0.579 ± 0.082 (32) | 0.459 ± 0.083 (32) | -0.120 |
| page_fact_recall@5 | 0.641 ± 0.076 (32) | 0.563 ± 0.081 (32) | -0.078 |
| page_hit@1 | 0.438 ± 0.088 (32) | 0.375 ± 0.086 (32) | -0.062 |
| page_hit@3 | 0.688 ± 0.082 (32) | 0.562 ± 0.088 (32) | -0.125 |
| page_hit@5 | 0.812 ± 0.069 (32) | 0.688 ± 0.082 (32) | -0.125 |
| page_mrr | 0.575 ± 0.072 (32) | 0.486 ± 0.077 (32) | -0.089 |
| page_ndcg@5 | 0.511 ± 0.065 (32) | 0.425 ± 0.068 (32) | -0.087 |
| retrieved_tokens@1 | 444 ± 23 (32) | 133 ± 23 (32) | -311 |
| retrieved_tokens@3 | 1396 ± 31 (32) | 476 ± 52 (32) | -920 |
| truncated | 0.000 ± 0.000 (52) | 0.000 ± 0.000 (52) | +0.000 |

| row | metric | baseline | this run |
|---|---|---|---|
| 52 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 52 | chunk_hit@5 | 0.000 | 0.000 |
| 52 | page_hit@5 | 1.000 | 1.000 |
| 52 | best relevant chunk | — | — |
| 53 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 53 | chunk_hit@5 | 0.000 | 0.000 |
| 53 | page_hit@5 | 1.000 | 1.000 |
| 53 | best relevant chunk | — | — |
| 8 | chunk_fact_recall@5 | 0.000 | 0.500 |
| 8 | chunk_hit@5 | 0.000 | 1.000 |
| 8 | page_hit@5 | 1.000 | 1.000 |
| 8 | best relevant chunk | — | 2 · Approved Office Supplies List > 4.4 Reimbursement Payout Timelines > Legal entities |
| 10 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 10 | chunk_hit@5 | 0.000 | 0.000 |
| 10 | page_hit@5 | 1.000 | 1.000 |
| 10 | best relevant chunk | — | — |
| 99 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 99 | chunk_hit@5 | 0.000 | 0.000 |
| 99 | page_hit@5 | 1.000 | 0.000 |
| 99 | best relevant chunk | — | — |
| 38 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 38 | chunk_hit@5 | 0.000 | 0.000 |
| 38 | page_hit@5 | 1.000 | 1.000 |
| 38 | best relevant chunk | — | — |
| 89 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 89 | chunk_hit@5 | 0.000 | 0.000 |
| 89 | page_hit@5 | 1.000 | 0.000 |
| 89 | best relevant chunk | — | — |
| 5 | chunk_fact_recall@5 | 0.333 | 0.333 |
| 5 | chunk_hit@5 | 1.000 | 1.000 |
| 5 | page_hit@5 | 1.000 | 1.000 |
| 5 | best relevant chunk | 1 · Sick Time Eligibility and Coverage | 1 · Sick Time > For Sick Absences 1-5 Consecutive Days |
| 32 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 32 | chunk_hit@5 | 0.000 | 0.000 |
| 32 | page_hit@5 | 0.000 | 0.000 |
| 32 | best relevant chunk | — | — |
| 34 | chunk_fact_recall@5 | 0.667 | 0.333 |
| 34 | chunk_hit@5 | 1.000 | 1.000 |
| 34 | page_hit@5 | 1.000 | 1.000 |
| 34 | best relevant chunk | 1 · Team Member | 1 · How To Apply for a Long-Term Relocation > Approvals Phase > Relocations To New Country or Different Location Factor |
| 35 | chunk_fact_recall@5 | 0.500 | 0.500 |
| 35 | chunk_hit@5 | 1.000 | 1.000 |
| 35 | page_hit@5 | 1.000 | 1.000 |
| 35 | best relevant chunk | 2 · Termination | 2 · Voluntary Terminations > Offboarding |
| 87 | chunk_fact_recall@5 | 0.000 | 0.000 |
| 87 | chunk_hit@5 | 0.000 | 0.000 |
| 87 | page_hit@5 | 0.000 | 0.000 |
| 87 | best relevant chunk | — | — |
