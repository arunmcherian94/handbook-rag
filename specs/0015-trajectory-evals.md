# 0015: Trajectory evals for the agent

- Status: draft
- Date: 2026-11-25

## Problem

The eval harness scores `ask`: one fixed path (retrieve top 5, answer once), so the answer is the only thing to grade. The agent ([spec 0013](0013-hand-rolled-agent.md), guarded by [spec 0014](0014-guardrails.md)) picks whether to search, what to search for, whether to page, and when to stop. A wrong result can come from a bad query, a skipped search, unused excerpts, a budget stop, a retry or a guardrail block. Output scores can't tell those apart, and a right answer can hide a wasteful path.

The 25 Nov smoke turns showed a case only a trajectory check catches: a conversational follow-up got the exact `OUT_OF_SCOPE` string. It was a valid fixed string, it passed all 14 guardrail checks, and it was the wrong terminal state for the user ([journal](../docs/journal/2026-11-25-retry-smoke-turn.md)).

Nothing measures the agent over the eval set today. This spec adds that measurement: terminal state against each row's label, trajectory checks, and efficiency metrics, recorded against the guardrails policy sha. It gives the baseline that C1 (classifier), C3 (source links) and week 6 compare against ([follow-ups](../docs/follow-ups.md#committed-guardrail-work-arun-25-nov)).

Friday builds and runs it. This spec makes no paid calls.

## Depends on / frozen inputs

| Input it fixes | Open decision that could change it | Handling |
|---|---|---|
| Eval set v1.2: 52 live rows, 33 answerable / 19 out-of-corpus ([CHANGELOG](../docs/eval/CHANGELOG.md)) | D4, decided: all 52, subsets reported separately | **Write as a rule:** the run reads the eval set and records its version; a new version needs a new spec ([ADR-0012](../docs/decisions/0012-eval-versioning.md)) |
| Retriever: dense, `openai:text-embedding-3-large@1536`, `fixed-512-64`, top 5 | None open. Hybrid and rerank were measured in week 3 and not adopted as the agent's default | **Write as a rule:** the run uses the agent's `retrieve` tool as built, and records its retriever config |
| Answer model `openai:gpt-5.4-mini` and the agent prompt | None open | **Write as a rule:** the run records the model from the turn records, and the prompt and tool-schema shas from the session header |
| Agent budgets: 6 model calls, 5 tool calls, 50,000 tokens, 90 s | None open. Constants per 0013 AC-9 | **Write as a rule:** read from `budgets()` at run time and recorded; never a flag |
| Guardrails policy `guardrails-v1`, sha256 `806cc433…4e19` | D1, decided: on only | **Write as a rule:** the run uses the policy as built and records its version and sha on every turn (0014 AC-1); no bypass |
| Identity the quality set runs as | None open | **Write as a rule:** admin, as for every quality-set run (spec 0007 AC-9) |
| Baselines to compare against | Week 4b may change the agent before Friday | **Write as a rule:** a baseline is the latest run on eval set v1.2 with the same model, retriever config and policy sha. Never a run ID |
| What a check asserts, row-specific vs generic, judge, reporting, cost | D2, D3, D5, D6, D7 | **Decide first:** all decided by Arun, 25 Nov (Decisions table) |
| Prices for the cost tally | A price change in `ANSWER_MODELS` / the embedding price table | **Write as a rule:** actual cost uses the price tables in code at run time, recorded with the run |

## Acceptance criteria

Target names (`agent-eval`, `paid-agent-eval`, `agent-eval-report`) follow the existing `eval` / `paid-eval` / `answer-eval` pattern. The paid-guard hook picks up any `paid-*` target from the Makefile.

**Collect (the paid step)**

- AC-1 (D7): `make agent-eval` is a dry run. It makes no API call and saves no turn. It prints the eval version, the row count, the answer and embedding models, the retriever config, the budgets, the guardrails version and sha, the per-turn upper bound from `agent.__main__.estimate()`, the full-run upper bound, and the cap if one is given.
- AC-2 (D7): `make paid-agent-eval CAP=<usd>` spends through the existing paid gate. It refuses to start without `CAP`, or with a `CAP` that isn't a positive number. There is no default.
- AC-3 (D4, D1): the paid run takes every live row of eval set v1.2, in file order, as `admin` (spec 0007 AC-9). Each row is one turn in a fresh session, run through the agent's `run_turn` as built, with the guardrails policy as built.
- AC-4 (D1): nothing disables, skips or swaps the guardrails for the eval: no flag, environment variable or parameter. A test asserts that a turn which reaches an answer carries all 14 checks' events.
- AC-5 (D7): after each turn the runner adds the turn's actual cost: its input and output tokens at the answer model's prices, plus its accepted queries' embedding tokens at the embedding price, from the price tables in code. Before each turn it stops if tally + `estimate()` > `CAP`. A stopped run keeps the rows written so far and records `complete: false` and `stopped: "cap"`.
- AC-6 (D6): the run writes `runs/eval/<date-id>/rows.jsonl` and `runs/eval/<date-id>/run.json`. Each row line holds the row id, its type, the session id and a copy of the redacted turn record that `run_turn` saved, never the unredacted record. The record carries the queries, pages, excerpt numbers and chunk ids, the messages (as saved, redacted), the answer, citations, retries and guardrail events. That makes the run regradable without the DB or a re-run (D5).
- AC-7 (D6, D7): `run.json` holds everything an `ask` eval run records that applies (eval version and sha, harness sha and dirty flag, corpus sha, config id and chunk params, embedding and answer models, `k`, timestamp, `user_id`, the ACL policy version and sha), plus `mode: "agent"`, `guardrails_version`, `guardrails_sha256`, the budgets, the agent prompt and tool-schema shas, `cap_usd`, `actual_usd`, `complete` and `stopped`. The `spend.jsonl` line for the run adds `actual_usd` next to `est_usd`.
- AC-8 (D1, D6): if any turn's `guardrails_sha256` differs from the run's, the run stops with `complete: false` and `stopped: "guardrails_sha"`.

**Score (free: no DB, no API)**

- AC-9 (D6): `make agent-eval-report RUN=<id>` reads only the run directory, the eval set and the files the 0010 assertions need. It imports neither the agent loop nor the DB layer nor a model client. It writes `summary.json` and `summary.md` to `docs/eval/results/<id>/`. Running it twice on the same run gives the same output.
- AC-10 (D2 #1): **terminal state**, pass/fail per row. Answerable rows pass on `answered`; ooc-in-scope rows on `abstained` with exactly `NOT_FOUND`; ooc-off-topic rows on `abstained` with exactly `OUT_OF_SCOPE` (ADR-0014). `budget_exhausted`, `guardrail_blocked` and `error` fail on every row. A turn that retried and ended in a passing state passes. The summary shows a row-type × state table.
- AC-11 (D2 #5): **citation validity**, pass/fail per answered row: at least one citation, and `invalid_citations` empty.
- AC-12 (D2 #2, #3, #4, #6, #7, #5b): reported, not pass/fail:
  - per turn: model calls, accepted tool calls, input and output tokens, latency (mean, SE, max); accepted searches on ooc-off-topic rows;
  - the rejected tool-call rate, and the expected-doc hit rate (answerable rows with a retrieved chunk from `expected_docs`);
  - the share of turns with an accepted page > 1 call, and of those, the share that cited an excerpt from page > 1;
  - the share of answered answerable rows that cite a chunk from `expected_docs`;
  - the retry rate, and the terminal states of turns that retried;
  - per guardrail check, the number of rows with a non-`pass` event.
- AC-13 (D3): **trajectory fact coverage** per answerable row: the share of its required facts (`Row.required`) for which some chunk retrieved by any accepted search in the turn is relevant under the ADR-0015 rule. It reuses the existing relevance code. Reported, not pass/fail.
- AC-14 (D2 #8): the spec 0010 answer-content assertions run on every answered agent answer, using the existing code. Reported, not pass/fail.
- AC-15 (D4): each AC-10 to AC-14 metric is reported pooled, for answerable rows and for out-of-corpus rows (where it applies), each with `metrics.mean_se` and its kind (binary or continuous) set per metric. The by-type breakdown is counts only, without SEs. A run with `complete: false` is labelled at the top of `summary.md`, with n per metric.
- AC-16: comparisons are chosen by rule, never by run ID. (a) `ask`: the latest `ask` answer run on v1.2 with the same answer model, embedding model and config, shown next to AC-10, AC-13 and AC-14 with its run id. (b) Agent baseline: the latest earlier agent run on v1.2 with the same model, retriever config and guardrails sha. If either doesn't exist, the summary says so.
- AC-17: `docs/eval/results/metrics.md` defines every metric in AC-10 to AC-14.

## Out of scope

- LLM judges of any kind (week 6, D5). The stored run is kept judge-ready.
- Changes to the agent, its prompt, budgets or guardrails. Findings go to follow-ups.
- New eval rows. The "+20 cases" roadmap item needs its own spec and Arun's authoring ([ADR-0010](../docs/decisions/0010-eval-questions-human-authored.md)).
- Multi-turn (follow-up) rows. Turn 3's false abstention came from a follow-up; v1.2 has single-turn rows only. Logged as a follow-up.
- Paid runs in this spec.
- An off-guardrails arm (D1). Logged as a follow-up only if Friday's run shows non-zero trips.
- `actual_usd` for paths other than this runner (`ask`, `agent`). The existing spend-log follow-up stays open for those.

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| D1: guardrails on, off, or both (Arun, 25 Nov) | **On only.** The run measures the agent as shipped, at the recorded policy sha. Guardrail trips on these benign rows are reported per check as the false-positive measure (D2). If trips are non-zero, an off-arm comparison is logged as a follow-up | **Off only:** measures a configuration nobody runs, needs a bypass path in production code (the kind of switch 0013 AC-9 avoids for budgets), and its baseline wouldn't match the shipped sha. **Both:** 2× spend plus the bypass; with 52 rows and few expected trips the on/off difference sits in the noise, and removing the excerpt framing changes the prompt, so framing and checks would be mixed in one difference |
| D2: what a trajectory check asserts (Arun, 25 Nov) | **Pass/fail:** (1) terminal state against the row's label: answerable → `answered`; ooc-in-scope → `abstained` with `NOT_FOUND`; ooc-off-topic → `abstained` with `OUT_OF_SCOPE` (exact match, ADR-0014); `budget_exhausted`, `guardrail_blocked` and `error` fail on every row. This is the headline, with a row-type × state table. (5) Citation validity on answered rows: ≥ 1 citation, none out of range. **Reported only:** (2) model calls, tool calls, tokens and latency per turn, plus searches on ooc-off-topic rows; (3) rejected tool calls and expected-doc hit rate (any retrieved chunk from `expected_docs`); (4) page > 1 usage and whether those excerpts were cited; (5b) a cited chunk from `expected_docs`; (6) retry rate and the state after a retry: a retry that ends in the right state counts as correct, since a retry is a cost, not a failure; (7) non-`pass` guardrail events per check, the false-positive rate (D1); (8) spec 0010's deterministic answer-content assertions, so that "answered" is also checked for content and the agent is comparable to `ask` | **(A) Without 8:** a confidently wrong answer passes the terminal-state check. **(C) Strict, failing on any retry, trip or missed expected doc:** punishes harmless behaviour, such as a retry or finding the fact in another doc; that's the brittleness production practice avoids. **(D) Terminal state only:** ignores the trajectory, which is the point of this spec. Asserting query wording was rejected as brittle |
| D3: per-row expected trajectories vs generic invariants (Arun, 25 Nov) | **Generic checks (D2) plus one per-row expectation derived from existing row data, no new authoring:** *trajectory fact coverage*, the share of a row's required facts for which some chunk retrieved by any of the turn's searches holds a cited line (ADR-0015 relevance, ADR-0013 fact recall, taken over the union of searches). Reported by row type, not pass/fail; comparable with `ask`'s top-5 fact recall | **Generic only:** can't tell a multi-part row that found half its evidence from one that found all of it. **Hand-authored per-row paths:** brittle when several paths are valid, costs Arun's authoring time (ADR-0010), and ties expectations to today's tool. Revisit if coverage shows a row type that consistently under-searches. **All `expected_docs` retrieved:** wrong test, because some rows list alternatives |
| D4: row scope (Arun, 25 Nov) | **All 52 v1.2 rows.** Every D2/D3 metric is reported pooled, for answerable rows (n = 33) and for out-of-corpus rows (n = 19), each with an SE. The by-type breakdown (n = 8–10 per type) is shown as counts, without SEs | **One pooled score:** the 63/37 mix hides opposite failures (false abstention vs answering out-of-corpus rows). **Answerable only:** loses the abstention side, where turn 3's failure and `ask`'s known weaknesses are. **Stratified sample:** saves about $0.10 actual and widens every SE |
| D5: deterministic checks only vs an LLM judge (Arun, 25 Nov) | **Deterministic only, with judge-ready output.** Every check is code over the turn record and the row's references (ADR-0016). The run keeps each full trajectory (queries, excerpts seen, answer) so week 6's judge can grade this same run without re-running the agent | **Judge now:** needs a cross-family judge, a rubric and validation against Arun's labels before its numbers mean anything; it's week 6 work, and it would mix two measurement methods into Friday's baseline. **Deterministic, trajectories not kept:** week 6 would need a fresh paid run to have something to grade |
| D6: how results land in the harness (Arun, 25 Nov) | **Collect, then score offline.** The paid step runs the turns and writes `rows.jsonl` and the run metadata to `runs/eval/<id>/` (`mode: agent`). Each row holds its id, type and a **copy of the full redacted turn record**; the DB keeps its own copy, but the run directory must stand alone and survive a DB reset. A separate scoring step (no DB, no API, as `answer_eval`) reads the run and writes `summary.json` and `summary.md`: every D2/D3 metric with an SE (`metrics.mean_se`), pooled and per subset, type counts (D4), and the latest `ask` run on v1.2 with the same model and retriever config for the D2 #8 and D3 comparisons. Run metadata adds agent mode, `guardrails_version`, `guardrails_sha256`, budgets, tool-schema sha and actual cost; the run aborts if any turn's guardrails sha differs from the run's. Definitions go in `docs/eval/results/metrics.md` | **Inline mode of the existing harness:** a check bug would need a new paid run to fix the numbers, and it adds branches to large files. **Separate runner and report:** duplicates the metadata and report plumbing and puts agent runs away from `ask` runs. **DB only, the run file holding just ids:** report and judge would need the DB up, the baseline is lost on a volume reset, and eval sessions mix with real ones. Redaction isn't a reason: the file copies the same redacted record (0014 AC-11) |
| D7: cost: dry-run upper bound and Friday's paid run (Arun, 25 Nov) | **A running actual-cost tally with a hard stop at a cap.** After each turn the runner adds the turn's actual cost; before each turn it stops if tally + one turn's upper bound ($0.2252) > cap, so the run can never pass the cap. The cap is a required argument with no default, recorded in the run metadata. **Friday: one paid run, cap $1.00** (about 5× the expected ≈ $0.20), Arun's OK in that session | **Approve against the worst case ($11.71):** rejected by Arun as too high, and it says nothing about actual spend. **Pilot then full run:** two approvals for the protection B gives in one. **Lower the budgets for the eval:** changes a frozen input, so it measures a different agent |

## Open questions

None. The cap for Friday's run ($1.00) is confirmed when Arun gives the OK for it.

## Test plan

Each test names the ACs it covers. No test makes a paid call; the model and embedder are fakes.

| Test | Kind | ACs |
|---|---|---|
| Dry run prints the listed fields and calls no model, embedder or turn save | unit | AC-1 |
| Paid target refuses without `CAP`, with `CAP=0`, with `CAP=abc` | unit | AC-2 |
| Collector over a 3-row eval set (answerable, ooc-in-scope, ooc-off-topic), fake model, real DB: one fresh admin session per row, `rows.jsonl` holds the redacted records, `run.json` fields present | integration | AC-3, AC-6, AC-7 |
| An answered turn carries all 14 checks' events; no guardrails switch exists in the collector's signature or env reads | unit | AC-4 |
| Fake turns with set token counts: tally matches tokens × prices; stops before the turn that would make tally + bound exceed the cap; `complete: false`, `stopped: "cap"`; rows written so far kept | unit | AC-5 |
| Spend line carries `actual_usd` and `est_usd` | unit | AC-7 |
| A turn with a different guardrails sha stops the run with `stopped: "guardrails_sha"` | unit | AC-8 |
| Scorer imports no agent loop, DB layer or model client; same input gives byte-identical output | unit | AC-9 |
| Terminal state over hand-built records: each row type × each state, the wrong fixed string, curly-apostrophe abstention, retried-then-passed | unit | AC-10 |
| Citation validity: none, out of range, valid | unit | AC-11 |
| Each reported metric on hand-built records with known answers | unit | AC-12 |
| Fact coverage: union over two searches covers a fact neither covers alone; a fact in an uncited doc doesn't count | unit | AC-13 |
| Answer-content assertions applied to agent answers match the 0010 results for the same text | unit | AC-14 |
| Pooled and subset SEs with the right kind; type counts carry no SE; incomplete-run label | unit | AC-15 |
| Comparison picks the latest matching run by rule, ignores non-matching runs, says when none exists | unit | AC-16 |
| `metrics.md` names every metric the summary emits | unit | AC-17 |

## Verification

Friday, after the build is committed:

1. `make agent-eval`: check the printed bounds and fields (AC-1).
2. Arun's OK for the spend, then `make paid-agent-eval CAP=1.00`: one run (AC-2 to AC-8).
3. `make agent-eval-report RUN=<id>`: the summary, with the journal entry recording actual cost and findings (AC-9 to AC-17).

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] docs updated: journal entry, an ADR for any decision, follow-ups
