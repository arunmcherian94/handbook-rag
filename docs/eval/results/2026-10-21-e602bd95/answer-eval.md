# Answer evaluation: 2026-10-21-e602bd95

## Run

- Run: 2026-10-21-e602bd95 (resolved by rule)
- Answer model: openai:gpt-5.4-mini
- Embed model: openai:text-embedding-3-large@1536
- Config: fixed-512-64
- Eval set: v1.2, sha256 995acb3b974d2c6aa7427fb089d9a9e133ab0aaf7879dff184c83071d6f8e725
- Assertions sha256: 8530e04f95e55eef3da8ff043e15bb93f23065a28255e4e6c6c16b53535a7860

## False-abstention classes

n = 10 false abstentions. generator_refusal: 2, partial_retrieval: 3, retrieval_miss: 4, not_classifiable: 1

| row | type | class | found / total | missing | top-k chunks | conflict_unscored | recency_basis |
|---|---|---|---|---|---|---|---|
| 49 | contradiction | partial_retrieval | 1 / 2 | F1 | 6bdc2a5a []; e369aa2f []; af377eae [F4]; bbf35654 []; 2460cb47 [] | false | history-only |
| 53 | recency | retrieval_miss | 0 / 1 | F1 | e5c2c095 []; 0ad6fd23 []; 2fe037c0 []; fac5d3e5 []; 66e0b05c [] | true | history-only |
| 8 | contradiction | partial_retrieval | 1 / 2 | F1 | 5bca07f3 []; 1c0fcba0 [F4]; 5049607c []; 866b69e6 []; 36e03277 [] | false | in-page |
| 55 | recency | retrieval_miss | 0 / 1 | F1 | fce3e797 []; 8e92cbfa []; 90398fce []; fd2f1d4e []; 14f9533b [] | false | history-only |
| 58 | recency | generator_refusal | 2 / 2 | - | 9c57367a [F2]; bbf1a59b []; cba913e5 [F3]; 607e8730 []; 8fdf558c [] | true | in-page |
| 100 | contradiction | generator_refusal | 2 / 2 | - | 9c57367a [F1]; cba913e5 [F2]; be00284c []; 8d045edf []; 8fdf558c [] | false | in-page |
| 22 | lookup | not_classifiable | 0 / 0 | - | fa5d52ac []; dc2e40b4 []; d9ba21b4 []; e686ee73 []; 81b98874 [] | false | - |
| 65 | lookup | retrieval_miss | 0 / 1 | F1 | 8371a8da []; 14066539 []; 004a6315 []; b496fefc []; 766e4251 [] | false | - |
| 89 | synthesis | partial_retrieval | 1 / 2 | F4 | 9fc4e798 []; 78b12e6b []; ce85f0f5 []; a632b578 []; 3eb825ad [F2] | false | - |
| 92 | lookup | retrieval_miss | 0 / 2 | F1, F4 | ca658fa2 []; 2e8148f0 []; 7202e31b []; 4aae9317 []; e99b52f0 [] | false | - |

## Answer-content check

- answer_content_fact_pass: 0.403 ± 0.079 (n = 31)
- answer_content_row_pass: 0.258 ± 0.079 (n = 31)
- Rows scored: 31
- Expressible facts: 66
- expressible:false facts: 7
- Eligible rows not in the file: none

| row | abstained | fact pass | row pass | facts |
|---|---|---|---|---|
| 11 | false | 0.67 | false | F1 fail, F4 pass, F5 pass |
| 49 | true | 0.00 | false | F1 fail, F4 fail |
| 51 | false | 1.00 | true | F1 pass, F2 pass |
| 52 | false | 0.50 | false | F1 pass, F2 fail |
| 53 | true | 0.00 | false | F1 fail |
| 8 | true | 0.00 | false | F1 fail, F4 fail |
| 32 | false | 0.00 | false | F1 fail, F3 fail, F5 fail, F6 fail |
| 10 | false | 0.86 | false | F1 pass, F2 pass, F3 pass, F4 pass, F5 pass, F6 pass, F8 fail |
| 50 | false | 0.50 | false | F1 n/a, F4 fail, F5 pass |
| 59 | false | 0.00 | false | F1 fail, F2 fail, F3 fail, F4 fail |
| 13 | false | 1.00 | true | F1 n/a, F2 pass |
| 48 | false | 0.00 | false | F1 fail, F5 fail |
| 44 | false | 0.80 | false | F1 fail, F2 pass, F3 pass, F4 pass, F5 pass |
| 55 | true | 0.00 | false | F1 fail |
| 46 | false | 1.00 | true | F1 pass |
| 58 | true | 0.00 | false | F1 n/a, F2 fail, F3 fail |
| 99 | false | 1.00 | true | F1 pass, F2 n/a |
| 100 | true | 0.00 | false | F1 fail, F2 fail |
| 87 | false | 0.00 | false | F1 n/a, F2 fail |
| 5 | false | 0.33 | false | F1 fail, F2 fail, F4 pass |
| 9 | false | 1.00 | true | F1 pass |
| 22 | true | - | - | F1 n/a |
| 23 | false | 0.00 | false | F1 fail, F2 fail |
| 26 | false | - | - | F1 n/a |
| 34 | false | 0.33 | false | F1 pass, F2 fail, F3 fail |
| 35 | false | 0.50 | false | F1 fail, F3 pass |
| 38 | false | 0.00 | false | F1 fail, F2 fail |
| 65 | true | 0.00 | false | F1 fail |
| 88 | false | 1.00 | true | F1 pass |
| 89 | true | 0.00 | false | F2 fail, F4 fail |
| 92 | true | 0.00 | false | F1 fail, F4 fail |
| 93 | false | 1.00 | true | F1 pass |
| 96 | false | 1.00 | true | F1 pass |

Metric definitions: [../metrics.md](../metrics.md)
