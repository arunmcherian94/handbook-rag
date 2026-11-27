# Agent trajectory evaluation: 2026-11-27-92d57d39

## Run

- Eval set: v1.2, sha256 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- Answer model: openai:gpt-5.4-mini; retriever: {"kind": "dense", "embed_model": "openai:text-embedding-3-large@1536", "config_id": "fixed-512-64", "k": 5, "pages": 4}
- Guardrails: guardrails-v1, sha256 806cc433ebd4111317fcb078f06aefe01de1bd8e5f79c4f139597a3deccd4e19
- Turns scored: 52 of 52; cost $0.1750 (cap $1.0000)
- Assertions sha256: 8530e04f95e55eef3da8ff043e15bb93f23065a28255e4e6c6c16b53535a7860

## Terminal state by row type (counts)

| type | answered | abstained | budget_exhausted | guardrail_blocked | error |
|---|---|---|---|---|---|
| contradiction | 7 | 1 | 0 | 0 | 0 |
| lookup | 6 | 3 | 0 | 0 | 0 |
| ooc-in-scope | 0 | 10 | 0 | 0 | 0 |
| ooc-off-topic | 0 | 9 | 0 | 0 | 0 |
| recency | 6 | 2 | 0 | 0 | 0 |
| synthesis | 7 | 1 | 0 | 0 | 0 |

## Metrics (mean ± SE, n)

| metric | kind | pooled | answerable | ooc |
|---|---|---|---|---|
| `terminal_state_pass` | binary | 0.846 ± 0.050 (n = 52) | 0.788 ± 0.071 (n = 33) | 0.947 ± 0.051 (n = 19) |
| `citation_valid` | binary | 1.000 ± 0.000 (n = 26) | 1.000 ± 0.000 (n = 26) | n = 0 |
| `model_calls` | continuous | 1.923 ± 0.090 (n = 52), max 4.0 | 2.091 ± 0.080 (n = 33), max 4.0 | 1.632 ± 0.191 (n = 19), max 4.0 |
| `tool_calls_accepted` | continuous | 0.885 ± 0.081 (n = 52), max 3.0 | 1.091 ± 0.080 (n = 33), max 3.0 | 0.526 ± 0.140 (n = 19), max 2.0 |
| `input_tokens` | continuous | 3949.923 ± 413.392 (n = 52), max 18281.0 | 4602.788 ± 499.945 (n = 33), max 18281.0 | 2816.000 ± 663.968 (n = 19), max 11267.0 |
| `output_tokens` | continuous | 89.231 ± 14.737 (n = 52), max 683.0 | 122.333 ± 20.983 (n = 33), max 683.0 | 31.737 ± 5.925 (n = 19), max 105.0 |
| `latency_ms` | continuous | 4546.966 ± 1730.216 (n = 52), max 91798.1 | 3285.594 ± 352.501 (n = 33), max 12279.2 | 6737.771 ± 4733.925 (n = 19), max 91798.1 |
| `ooc_offtopic_searches` | continuous | 0.000 ± 0.000 (n = 9) | n = 0 | 0.000 ± 0.000 (n = 9) |
| `rejected_tool_call_share` | continuous | 0.000 ± 0.000 (n = 41) | 0.000 ± 0.000 (n = 32) | 0.000 ± 0.000 (n = 9) |
| `expected_doc_hit` | binary | 0.818 ± 0.067 (n = 33) | 0.818 ± 0.067 (n = 33) | n = 0 |
| `page2_use` | binary | 0.000 ± 0.000 (n = 52) | 0.000 ± 0.000 (n = 33) | 0.000 ± 0.000 (n = 19) |
| `page2_cited` | binary | n = 0 | n = 0 | n = 0 |
| `cited_expected_doc` | binary | 0.885 ± 0.063 (n = 26) | 0.885 ± 0.063 (n = 26) | n = 0 |
| `retry_rate` | binary | 0.038 ± 0.027 (n = 52) | 0.000 ± 0.000 (n = 33) | 0.105 ± 0.070 (n = 19) |
| `trajectory_fact_coverage` | continuous | 0.552 ± 0.074 (n = 32) | 0.552 ± 0.074 (n = 32) | n = 0 |
| `answer_content_fact_pass` | continuous | 0.479 ± 0.088 (n = 24) | 0.479 ± 0.088 (n = 24) | n = 0 |
| `answer_content_row_pass` | binary | 0.292 ± 0.093 (n = 24) | 0.292 ± 0.093 (n = 24) | n = 0 |

## Counts

- Rows by type: {"contradiction": 8, "lookup": 9, "ooc-in-scope": 10, "ooc-off-topic": 9, "recency": 8, "synthesis": 8}
- Terminal states of retried turns: {"abstained": 2}

Rows with a non-pass guardrail event, per check:

| check | rows |
|---|---|
| excerpt_delimiter | 0 |
| excerpt_injection | 0 |
| excerpt_invisible | 1 |
| input_empty | 0 |
| input_garbage | 0 |
| input_injection | 0 |
| input_invisible | 0 |
| input_length | 0 |
| input_pii | 0 |
| output_citation | 2 |
| output_image | 0 |
| output_link | 0 |
| output_pii | 0 |
| persist_pii | 0 |

## Comparisons

### ask: 2026-10-21-e602bd95

| metric | pooled | answerable | ooc |
|---|---|---|---|
| `terminal_state_pass` | 0.769 ± 0.058 (n = 52) | 0.697 ± 0.080 (n = 33) | 0.895 ± 0.070 (n = 19) |
| `chunk_fact_recall@5` | 0.583 ± 0.075 (n = 32) | 0.583 ± 0.075 (n = 32) | n = 0 |
| `answer_content_fact_pass` | 0.568 ± 0.089 (n = 22) | 0.568 ± 0.089 (n = 22) | n = 0 |
| `answer_content_row_pass` | 0.364 ± 0.103 (n = 22) | 0.364 ± 0.103 (n = 22) | n = 0 |

### Earlier agent run: no earlier agent run

Metric definitions: [../metrics.md](../metrics.md)
