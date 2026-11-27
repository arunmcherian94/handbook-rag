# 2026-11-27: trajectory evals, build and first agent baseline (spec 0015)

Built [spec 0015](../../specs/0015-trajectory-evals.md) on `build-0015-trajectory-evals` and ran it once, paid, with Arun's OK. This is the first agent baseline on eval set v1.2: n = 52 (33 answerable, 19 out-of-corpus), one run. Numbers are mean ± SE. By-type figures are counts only (n = 8–10 per type).

## What ran
- **Dry run** (`make agent-eval CAP=1.00`): 52 live rows, admin. `openai:gpt-5.4-mini`, `openai:text-embedding-3-large@1536`, dense, `fixed-512-64`, k 5, 4 pages. Budgets 6 steps / 5 tool calls / 50,000 tokens / 90 s. `guardrails-v1`, sha256 `806cc433…4e19`. Upper bound $0.2252 a turn, $11.7087 for the run.
- **Paid run** (`make paid-agent-eval CAP=1.00`): run `2026-11-27-92d57d39`, at harness commit `9a2e9ca`. 52/52 turns, `complete: true`, `stopped: null`. Every turn recorded the run's guardrails sha.
- **Report** (`make agent-eval-report RUN=2026-11-27-92d57d39`): [summary.md](../eval/results/2026-11-27-92d57d39/summary.md). A second run gave byte-identical files (AC-9).

## Cost
- **Actual: $0.1750** (205,396 input + 4,640 output tokens; query embeds $0.00005). Expected ≈ $0.20; cap $1.00.
- **Bound vs actual:** the most expensive turn cost $0.0168, 13× below the $0.2252 per-turn bound. The full-run bound ($11.71) was 67× the actual. The cap never came close to binding.
- `runs/spend.jsonl` has `est_usd` 11.7087 (the dry-run bound, spec 0009's definition) and `actual_usd` 0.1750.

## Results (pass/fail, D2)

| Metric | Pooled (n = 52) | Answerable (n = 33) | Out-of-corpus (n = 19) |
|---|---|---|---|
| Terminal state | 0.846 ± 0.050 | 0.788 ± 0.071 | 0.947 ± 0.051 |
| Citation validity (answered rows) | 1.000 (n = 26) | 1.000 (n = 26) | — |

- **Terminal states:** answered 26, abstained 26. No `budget_exhausted`, `guardrail_blocked` or `error`.
- **Answerable rows that abstained (7):** 53, 58 (recency); 100 (contradiction); 87 (synthesis); 65, 92, 96 (lookup). Rows 58 and 100 are also in spec 0010's generator-refusal list for `ask`.
- **Out-of-corpus failure (1):** row 111 (ooc-in-scope, "who else is starting in my onboarding cohort this month?") got `OUT_OF_SCOPE` instead of `NOT_FOUND`. It's the 25 Nov turn-3 pattern again, on a single-turn row: a valid fixed string, but the wrong one.

## Results (reported only)

| Metric | Value |
|---|---|
| Model calls per turn | 1.92 ± 0.09 (max 4) |
| Accepted tool calls per turn | 0.88 ± 0.08 (max 3); answerable 1.09, ooc 0.53 |
| Input / output tokens per turn | 3,950 ± 413 (max 18,281) / 89 ± 15 (max 683) |
| Latency per turn | 4.5 s ± 1.7 (max 91.8 s; answerable 3.3 s ± 0.4) |
| Searches on ooc-off-topic rows | 0.00 (n = 9) |
| Rejected tool-call share | 0.00 (n = 41 turns with a tool call) |
| Expected-doc hit (answerable) | 0.818 ± 0.067 |
| Page > 1 use | 0.00: no turn asked for page 2 |
| Answered rows citing an expected doc | 0.885 ± 0.063 (n = 26) |
| Retry rate | 0.038 ± 0.027 (2 of 52) |
| Trajectory fact coverage (answerable) | 0.552 ± 0.074 (n = 32) |
| Answer content, fact pass | 0.479 ± 0.088 (n = 24) |
| Answer content, row pass | 0.292 ± 0.093 (n = 24) |

## Against `ask` (AC-16 a: run `2026-10-21-e602bd95`)

| Metric | Agent | `ask` |
|---|---|---|
| Terminal state, pooled | 0.846 ± 0.050 | 0.769 ± 0.058 |
| Terminal state, answerable | 0.788 ± 0.071 | 0.697 ± 0.080 |
| Terminal state, out-of-corpus | 0.947 ± 0.051 | 0.895 ± 0.070 |
| Fact coverage (agent: all searches; `ask`: top 5) | 0.552 ± 0.074 | 0.583 ± 0.075 |
| Answer content, fact pass | 0.479 ± 0.088 (n = 24) | 0.568 ± 0.089 (n = 22) |
| Answer content, row pass | 0.292 ± 0.093 (n = 24) | 0.364 ± 0.103 (n = 22) |

- These are unpaired differences from different runs, and each sits within about 1 to 1.5 combined SEs. This run doesn't show the agent better or worse than `ask` on any of them. A paired per-row comparison was not part of the spec.
- `e602bd95` predates the ACLs (spec 0007), so it ran unfiltered. Admin sees every document, so the retrievable set is the same.
- No earlier agent run exists. This run is the agent baseline for C1, C3 and week 6 (AC-16 b).

## Guardrail trips on benign rows (D1)
- **`excerpt_invisible` on 1 row (row 10):** invisible characters stripped from a retrieved handbook excerpt (`redact`). The excerpt still reached the model, and the row was answered.
- **`output_citation` on 2 rows (47, 112):** the retry path (below).
- No other check tripped. Input checks and output PII and link checks: 0 of 52 rows.
- Trips are non-zero, so the guardrails-off arm is logged as a follow-up, as D1 says. Neither trip type blocked a turn.

## Retry firings
- **The first natural retries against the real model.** The 25 Nov probe got none in 4 turns. Rows 47 and 112 (both ooc-in-scope) searched, then replied with no citation (`citation_missing`). After the feedback, both retried to exactly `NOT_FOUND`, which passes. Under D2, a retry that ends in the right state counts as correct.

## Surprises
- **Row 71 took 91.8 s, past the 90 s budget, without ending as `budget_exhausted`.** It was one model call and no tools, and it abstained correctly with `OUT_OF_SCOPE`. The timeout budget is checked only before each call, and the call is given the time left as its request timeout. This one returned 1.8 s past it and was kept. Why the client didn't time out is not investigated. It inflates the ooc latency mean (6.7 s ± 4.7). Logged as a follow-up.
- **No turn used page 2,** so the page > 1 metrics have no data on this run.
- **The agent never searched on ooc-off-topic rows** (0 of 9). It searched on 9 of 10 ooc-in-scope rows and 32 of 33 answerable rows.

## Build and review
- Two parallel slices (collector, scorer) on a written run-directory contract. One decision taken at the plan gate: references are computed at collect time, so the scorer stays DB-free ([ADR-0026](../decisions/0026-agent-eval-references-at-collect.md)).
- **Review catches, fixed with regression tests:**
  - **Collector:** `QueryCounter` encoded queries with tiktoken's default `disallowed_special`. A query with special-token text that the tool accepts would have raised, ending the turn as `error`.
  - **Scorer:** the ask comparison could pick a hybrid or rerank `ask` run. It now requires a dense run (runs from before spec 0011 have no retriever key and count as dense).
- **Lower priority, Arun picked the recommended set:**
  - Fixed: a post-turn stop if a turn ever costs more than the bound (the cap guarantee rests on it); summary.md cost formatting; the Makefile `RUN` quoting; the ask column relabelled `chunk_fact_recall@5`.
  - Skipped: scoring a row from a mismatched-sha turn (can't happen in one process); `est_usd` capped at the cap.
  - Kept as built: the agent baseline must be complete; the ask run must have a clean harness.
- **Caught on the real run, after review:** the scorer read ask rows' abstention from a top-level `abstained` key. Ask rows store it at `abstention.abstained`, so every ask answerable row counted as answered (1.000) and abstained answers entered its answer-content n (31). The unit fixtures had the same wrong shape. Fixed: the scorer now raises on a missing flag, and the fixtures use the real shape. A regression test fails on the old read. The tables above are after the fix.
- **Clean room:** a fresh clone under `$HOME` with its own DB on port 5434, no API keys, ingest, all five chunk configs, `make acl`. 1026 unit and 121 integration tests pass, lint clean. Working copy after the scorer fix: 1027 unit and 121 integration tests pass, lint clean.

## Limitations
- One run, n = 52. Model sampling noise between runs is not measured.
- Trajectory fact coverage counts a fact as covered when a relevant chunk was retrieved, not when the answer used it.
- The answer-content assertions are tuned to gpt-5.4-mini's phrasing in `ask` answers (spec 0010). Agent answers may phrase facts differently.
