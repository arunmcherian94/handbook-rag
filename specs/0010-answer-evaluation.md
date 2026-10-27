# 0010: Answer evaluation, code-first (false-abstention classes, answer-content assertions)

- Status: implemented
- Date: 2026-10-27

## Problem

The answer side of the harness reports only abstention and code checks. In the baseline full run (`2026-10-21-e602bd95`), 10 of the 33 answerable rows are false abstentions. Nothing says whether the generator refused despite having the evidence, or whether retrieval never delivered it. That split decides Friday's work: prompt or generator first, or retrieval first. For rows that do answer, nothing checks whether the answer contains the required facts.

This spec adds two code-only measures over stored run data. It makes no API calls and does not change retrieval, `ask.py`, the answer model or the prompt.

## Depends on / frozen inputs

| Input it fixes | Open decision that could change it | Handling |
|---|---|---|
| Baseline answer run | A new full answer run, or an answer-model or embed-model change | **Write as a rule** (AC-1). Today it resolves to `2026-10-21-e602bd95`. Without the embed-model filter it would resolve to the Qwen run `2026-10-21-9719cae6`, which is 45 ms newer. |
| Fact lists in eval set v1.2 (`eval_sha256 995acb3b…`) | Arun's hand-check of the 26 auto-reviewed rows (today). Any changed fact means v1.3, done by Arun | **Decided** (Arun, 27 Oct). Assertions only for eligible rows (AC-6). A row Arun changes stays `checked=n` until v1.3 lands. The assertions file pins `eval_sha256`, so a v1.3 bump makes the loader refuse the file until it is re-reviewed (AC-6). |
| Retrieved chunks and their matched facts, per row | None in week 3 (retrieval is frozen for this run) | **Read from the run folder**: `rows.jsonl` → `retrieved[]` (rank, `chunk_id`, `facts`). The harness wrote `facts` at run time with its path + heading + line-range matcher, so nothing is recomputed. |
| Fixed abstention strings | None (`prompts.py` is frozen) | `NOT_FOUND` and `OUT_OF_SCOPE`, imported from `prompts.py`, not copied. **Correction (2026-10-27, Arun):** this row said `checks.FIXED_STRINGS`; `checks.py` imports `ask.py`, which loads the model clients and would break AC-2. `checks.py` takes the same two strings from `prompts.py`. |
| Reference text an assertion must pass on | Eval set v1.2 has no reference-answer field | **Decided** (Arun, 27 Oct): the fact's own statement (Decisions, row 1). |
| Which rows are eligible for assertions | Whether the 23 owner-reviewed answerable rows count as checked | **Decided** (Arun, 27 Oct): owner-reviewed rows are eligible, and auto-reviewed rows become eligible once checked (AC-6). |

## Acceptance criteria

### Shared

- AC-1: **Baseline resolution.** `resolve_baseline(runs_root)` returns the run with the latest `meta.timestamp` among `runs/eval/*` where all of these hold:
  - `mode == "full"`, `limit` is null and `harness_dirty` is false
  - `answer_model == DEFAULT_ANSWER_MODEL`, `embed_model == DEFAULT_EMBED_MODEL` and `config_id == BASELINE_CONFIG`
  - `eval_sha256` equals the current `docs/eval/eval-set-v1.md`

  If no run matches, it fails with a message naming each filter. A unit test builds fixture run folders, including a newer run with another embed model and a newer retrieval-only run, and asserts that the right run is picked. `--run <id>` overrides the rule, and the override is recorded in the output.
- AC-2: **One command, no network.** `make answer-eval` runs `python -m handbook_rag.evaluation.answer_eval`. It needs no DB, no API key and no `.env`, and imports no model client (a unit test asserts this). It writes these files to `docs/eval/results/<run>/`:
  - `false-abstentions.json` (Part A)
  - `answer-content.json` (Part B)
  - `answer-eval.md`: both tables, the resolved run ID, the eval-set version and SHA, and the assertions-file SHA

  It also appends one link line to that run's `summary.md` if the line is missing.

### Part A: false-abstention classification

- AC-3: **Classes.** Each answerable row with `abstention.false_abstention == true` gets one class. `required` means the row's required facts that carry a citation (`Row.required`, the set the retrieval metrics score). `found` means the facts in `required` that appear in `facts` of any `retrieved` chunk with rank ≤ `TOP_K`.
  - `generator_refusal`: found == required
  - `partial_retrieval`: 0 < |found| < |required|
  - `retrieval_miss`: found is empty
  - `not_classifiable`: required is empty (all required facts are answer-only; row 22 today)

  A parametrised unit test covers each class.
- AC-4: **Output.** For each row, the JSON and the md table hold:
  - row ID, type and class
  - found / total, plus the found and missing fact IDs
  - top-k chunk IDs in rank order, and for each chunk the facts it carries
  - `conflict_unscored` and `recency_basis`

  Both also give counts per class, with n = the number of false abstentions. An unknown fact ID in the run data, a row missing `retrieved`, or a run with no false-abstention field is an error, not a silent skip.

### Part B: answer-content assertions

- AC-5: **Schema.** The file is `eval/assertions/assertions-v1.yaml`. Its top-level fields are `eval_version`, `eval_sha256` and `rows`, keyed `row id → fact id → entry`. An entry is one of:
  - `{expressible: true, assert: <node>}`
  - `{expressible: false, reason: <one line>}`

  A node is one of:
  - `number`: value plus an optional unit. Normalisation removes thousands separators, currency symbols and codes (`$`, `€`, `£`, `USD`, `EUR`, `GBP`) and unit words or suffixes (`%`, `days`, `weeks`, `months`, `years`, `hours`). Number words map to digits only where unambiguous: zero–twenty, the tens, "hundred" and "thousand". Numbers compare by value.
  - `term`: text plus `variants: [...]`. Matching is case-insensitive, whitespace-collapsed and on word boundaries.
  - `all_of: [nodes]` or `any_of: [nodes]`, nestable.

  An unknown key or type is a load error naming the row and fact.
- AC-6: **Loader gates.** The loader refuses the whole file, naming the offending row or fact, when any of these holds:
  - `eval_sha256` differs from the current eval set
  - a row is not eligible. Eligible means `ref_source: llm-draft, reviewed`, or `llm-draft, auto-reviewed` with `checked=y` and `changed=n` in `docs/eval/fact-list-review.md`. That allows 23 to 33 rows; 10 alone would give SE ≈ ±0.16, and they are the weaker-checked half
  - a row is ooc
  - a fact ID is not in the row, or is not `[required]`
  - a listed row omits any of its required facts

  Each gate has a unit test. An empty `rows` loads and scores n = 0 without error.
- AC-7: **Self-test.** A parametrised unit test runs over every `expressible: true` entry in the committed file. Each entry must pass on its reference text (Decisions, row 1) and fail on both `FIXED_STRINGS`. With an empty file the test collects 0 cases. Unit tests on synthetic entries cover the number, term, `all_of` and `any_of` matchers, including normalisation.
- AC-8: **Scoring.** The scorer runs every eligible row's assertions against the stored `answer` of the resolved run, abstentions included (an abstention fails every assertion). It reports these metrics:
  - **`answer_content_fact_pass`**: per row, the passed expressible facts / the row's expressible facts. Reported as the mean over rows with ≥ 1 expressible fact, with n and SE from `metrics.mean_se(binary=False)`, the convention `chunk_fact_recall` uses.
  - **`answer_content_row_pass`**: 1 if every expressible fact in the row passes, else 0, with `mean_se(binary=True)`.
  - **Counts**: rows scored, expressible facts, `expressible: false` facts (counted, not dropped; they go to the week 6 judge), and eligible rows not in the file.

  For each row, the output gives the result of each fact.
- AC-9: **Naming.** The output and docs call these metrics an **answer-content check**. A unit test asserts that the words "correctness" and "groundedness" appear nowhere in `answer-eval.md` or `answer-content.json`.
- AC-10: **Metric definitions.** `docs/eval/results/metrics.md` gains an "Answer content" section defining `answer_content_fact_pass` and `answer_content_row_pass`, and the existing test that every metric is defined (`test_every_metric_is_defined_in_metrics_md`) is extended to cover them. The section also says what the metrics do not measure: paraphrase, extra or wrong claims, and support by the citations.
- AC-11: **Review file.** `docs/eval/fact-list-review.md` has one table row for each of the 26 `auto-reviewed` row IDs, in eval-set order, with these columns:
  - row ID and type (answerable or ooc)
  - `checked` (y/n) and `changed` (y/n), both `n` at creation
  - `note`

  The loader parses it, and a unit test checks that the table lists exactly the auto-reviewed IDs in the eval set. Arun fills it in.
- AC-12: **Stage 1 ships an empty assertions file** (`rows: {}`) with the current `eval_version` and `eval_sha256`. Assertions are drafted in Stage 2 only, for eligible rows, from the reference text and the fact list, and Arun reviews each one before it is committed.

## Out of scope

- LLM judge (week 6), evidence-substring assertions, structured output, small-to-big retrieval, saved-query-vector defaults, any retrieval change.
- Any change to `ask.py`, the answer model, the prompt or the eval-set content. A fact change is Arun's v1.3 bump.
- Assertions for `[optional]` facts or ooc rows.
- Re-running retrieval or answers.

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| Reference text an assertion must pass on | The fact's own statement (Arun, 27 Oct) (the text between the `[required]` marker and the `—` citation) in v1.2. The self-test runs on it. It proves the assertion is well-formed and not too strict, not that it accepts every paraphrase. Paraphrase is covered by the reviewed `variants`, and what rules can't express goes to the week 6 judge | Reference answers written by Arun: an eval-set content change (v1.3), not allowed here. Reference answers drafted by Claude: model-written text in the eval set, which breaks the human-authored rule |
| Which facts get assertions | `[required]` facts only, including answer-only ones (22 F1, 58 F1) | Optional facts too: they are credit only, and adding them would mix the measure |
| Where the output goes | new files in the committed `docs/eval/results/<run>/` plus one link line in its `summary.md`. `runs/` is gitignored | Rewriting `summary.md` sections: changes a historical run report. Writing only to `runs/`: not reviewable and lost in a clean clone |
| Part A data source | Stored `retrieved[].facts` | Re-running retrieval or re-matching facts: forbidden, and a second matcher |
| Row 22 (only answer-only required facts) | a fourth class, `not_classifiable` | Forcing it into `retrieval_miss`: a false statement about retrieval |
| SE for fact pass | a mean of per-row fractions, `binary=False`, n = rows (as `chunk_fact_recall`) | Pooled over facts, `binary=True`: treats facts in one row as independent |

## Open questions

None. Eligibility and the reference text were decided by Arun on 27 Oct, and the target name is `make answer-eval`.

## Verification

- Unit tests cite AC-1 to AC-12.
- `make answer-eval` on the real baseline writes the three files and resolves to `2026-10-21-e602bd95`.
- Clean room: a fresh clone under `$HOME` has no `runs/`, so `make test` and `make lint` run there unchanged, and `make answer-eval` runs after copying only `runs/eval/2026-10-21-e602bd95/` in. The outputs must match byte for byte.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] docs updated: journal entry (classification split only), follow-ups
