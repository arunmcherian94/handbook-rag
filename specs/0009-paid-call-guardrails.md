# 0009: Guardrails against unapproved paid calls

- Status: implemented
- Date: 2026-10-24

## Problem

On 22 Oct an agent ran `make ask` without approval ([journal](../docs/journal/2026-10-22-permissions-build.md#accidental-paid-call)). `make ask` was the only paid target with no dry run, nothing mechanical stopped a paid command, and spend was not logged anywhere. The rule is that every paid call traces to an explicit decision by Arun.

Spec and build ship in one PR (Arun, 24 Oct), to fit the 45-minute timebox.

## Acceptance criteria

- AC-1: **`make ask` dry-runs by default.** Without `CONFIRM=1` it prints the estimated cost (query-embed tokens at the model's price, plus `EST_ANSWER_USD_PER_ROW`) and `Dry run: add CONFIRM=1 to spend.` It builds no embedder or answerer (no API key needed) and writes no trace and no spend line. The corpus, embeddings and stale-ACL checks still run first.
- AC-2: **Hook.** A Claude Code PreToolUse hook on Bash (`.claude/hooks/paid_guard.py`, registered in `.claude/settings.json`): any command containing `CONFIRM` (any value, quoted or not) or a `--conf` prefix (argparse accepts abbreviations), or a payload the hook can't read, returns `permissionDecision: "ask"`, so a human approves each paid command in every permission mode. Other commands pass silently.
- AC-3: **Spend log.** Every confirmed paid run (`ask`, `embed`, `eval`, `permissions`) appends exactly one JSON line to `runs/spend.jsonl`: `timestamp`, `target`, `run_id` (null for `ask` and `embed`), `embed_model`, `answer_model`, `est_usd`, `status` (`ok` / `failed`). It is written in a `finally`, so a run that fails after spending is still logged.

## Out of scope

- Actual cost from provider usage; the log records the dry-run estimate.
- Budgets and caps; an LLM gateway (week 7 follow-up).
- Runtime agent spend controls: per-request step and token caps, a per-run cost cap, a daily ceiling and alerts (weeks 6 and 8). The hook guards only the coding agent's shell. The product agent's calls run in-process, are approved at the run boundary and are then bounded by a budget ([follow-ups](../docs/follow-ups.md)).

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| How the hook gets approval | `permissionDecision: "ask"`: a human click per paid command | An approval file holding the session id: the agent can write that file itself |
| What the hook matches | Any `CONFIRM` and any `--conf` prefix, broadly | Exact `CONFIRM=1` / `--confirm`: quoting (`CONFIRM="1"`) and argparse abbreviations (`--conf`) slipped past it (review catch). A list of target names: drifts as targets are added |

Accepted risk: the hook matches command text, so indirection (a variable holding the flag, a script that sets it) can still get past it. It stops accidents, not a determined bypass; the dry-run default and the spend log are the other two layers.

## Verification

- `tests/unit/test_ask.py` (AC-1, AC-3), `tests/unit/test_paid_guard.py` (AC-2), `tests/unit/test_spend.py` (AC-3). No test calls an API.
- Live: `make ask AS=us-ic Q="test" CONFIRM=1` raises the approval prompt and is declined; `make ask AS=us-ic Q="test"` prints the estimate and the dry-run line, and `runs/spend.jsonl` is unchanged.

Before the implementation PR:

- [x] `make test` and `make lint` pass
- [x] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [x] Clean-room verified
- [x] docs updated: journal entry, an ADR for any decision, follow-ups
