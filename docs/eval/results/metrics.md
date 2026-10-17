# Eval metrics

Definitions for every `summary.md` under this folder (spec 0004, AC-3 to AC-5). `@k` means k = 1, 3, 5.

## Retrieval (answerable rows)

A chunk is *relevant* to a fact if it comes from a cited page and contains a cited line.

- `chunk_fact_recall@k`: share of the row's required facts with a relevant chunk in the top k. Headline metric.
- `chunk_all_required@k`: 1 if every required fact has a relevant chunk in the top k, else 0.
- `chunk_hit@k`: 1 if any chunk relevant to a required fact is in the top k.
- `chunk_mrr`: 1 / rank of the first relevant chunk (0 if none retrieved).
- `chunk_ndcg@k`: ranking quality of relevant chunks in the top 5, binary relevance.
- `page_fact_recall@k`: share of required facts with a cited page in the top k. Diagnostic.
- `page_hit@k`: 1 if any expected page is in the top k. Diagnostic.
- `page_mrr`: 1 / rank of the first expected page. Diagnostic.
- `page_ndcg@k`: ranking quality of expected pages in the top 5, each page at its best rank.
- `retrieved_tokens@k`: total tokens in the top k chunks, the context cost of the recall.

## Answers

- `ooc_pass`: out-of-corpus rows answered with exactly the expected abstention string.
- `false_abstention`: answerable rows where the model abstained anyway.
- `code_checks_passed`: answers (answerable, not abstained) passing all four checks below.
- `has_citation`: the answer cites at least one chunk.
- `citations_in_range`: every cited number refers to a retrieved chunk.
- `headings_exist`: every cited chunk's heading exists in its page at the corpus pin.
- `no_url`: the answer contains no URL.
- `truncated`: the answer hit the output token limit.

## Reading the tables

- **± SE** is the standard error of the mean; **n** is the number of rows the metric applies to. With n = 8 per row type, differences between types are directional only.
- **Abstention labels** (no score impact): `abstain+extra` = fixed string plus more text; `wrong-string` = the other fixed string.
- **Lists:**
  - `page_hit_no_chunk`: page found but no relevant chunk at k = 5 (a chunking problem).
  - `conflict_unscored`: contradiction rows whose conflict isn't scored.
- **Notes:**
  - `answer_only_facts`: required facts with no citation, left out of retrieval scores.
  - `no_retrieval_facts`: rows with no cited required fact, so no retrieval score.
  - `evidence_warnings`: optional facts whose cited lines match no stored chunk.
