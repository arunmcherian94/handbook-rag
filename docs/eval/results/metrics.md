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

## Answer content (spec 0010)

An answer-content check: per-fact must-contain assertions (numbers, terms) run against the stored answer, for eligible rows only. It does not measure paraphrase the rules miss, extra or wrong claims, or whether the cited chunks support the answer. Facts the rules can't express are counted as `expressible: false` and left to the week 6 judge. Results are in each run's `answer-eval.md`.

- `answer_content_fact_pass`: per row, the share of expressible required facts whose assertion passes; the mean over rows with at least one, n = rows.
- `answer_content_row_pass`: 1 if every expressible required fact in the row passes, else 0.

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

## Agent trajectory (spec 0015)

Scored offline by `make agent-eval-report RUN=<id>` from the stored run (no DB, no API). One turn per eval row. Each metric is shown pooled, for answerable rows and for out-of-corpus (ooc) rows where it applies, as mean ± SE and n; the kind is fixed per metric (binary: SE = sqrt(p(1-p)/n); continuous: sample sd / sqrt(n)). The by-type tables are counts only. "Accepted" tool steps are those the tool did not reject; page > 1 means the call's `page` argument. A run with `complete: false` is labelled at the top of `summary.md`.

Pass/fail:

- `terminal_state_pass` (binary, all rows): answerable rows pass on state `answered`; ooc-in-scope rows on `abstained` with the answer, stripped, exactly equal to the expected `NOT_FOUND` string; ooc-off-topic rows on `abstained` with exactly `OUT_OF_SCOPE`. `budget_exhausted`, `guardrail_blocked` and `error` fail on every row. Retries are ignored: a retried turn is judged on its end state. A curly-apostrophe variant fails.
- `citation_valid` (binary, answered rows): at least one citation and an empty `invalid_citations`.

Reported only:

- `model_calls`, `tool_calls_accepted`, `input_tokens`, `output_tokens`, `latency_ms` (continuous, per turn): model steps, accepted tool steps, tokens and latency from the turn record. The summary adds the maximum.
- `ooc_offtopic_searches` (continuous, ooc-off-topic rows only): accepted tool calls in the turn.
- `rejected_tool_call_share` (continuous, turns with at least one tool call): rejected tool steps / all tool steps in the turn.
- `expected_doc_hit` (binary, answerable rows): some excerpt the turn retrieved has a `url_path` in the row's expected docs.
- `page2_use` (binary, all turns): any accepted tool step with page > 1.
- `page2_cited` (binary, turns with `page2_use`): a cited excerpt number is among the excerpt numbers returned by an accepted page > 1 step.
- `cited_expected_doc` (binary, answered answerable rows): some citation's `url_path` is in the row's expected docs.
- `retry_rate` (binary, all turns): `retries` > 0. The terminal states of retried turns are listed as counts.
- Guardrail non-pass rows (counts, per check, not a metric): rows with at least one event for that check whose action is not `pass`.
- `trajectory_fact_coverage` (continuous, answerable rows with at least one required fact): share of the row's required facts whose relevant chunks (ADR-0015, stored in the run's `refs`) intersect the chunk ids of all accepted tool steps in the turn. Comparable with `ask`'s top-5 required fact recall, shown as `chunk_fact_recall@5` in the ask comparison.
- `answer_content_fact_pass`, `answer_content_row_pass`: the spec 0010 assertions (above) run on the answers of turns that ended `answered`; other rows are left out, not failed.

Comparisons are chosen by rule: the latest full `ask` run on the same eval set, answer model, embedding model and config (terminal state, fact coverage at top 5, answer content; for `ask`, an answerable row passes terminal state when it did not abstain), and the latest earlier complete agent run with the same eval set, answer model, retriever and guardrails sha.
