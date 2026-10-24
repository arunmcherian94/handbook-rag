# 0009: Guardrails against unapproved paid calls

- Status: approved
- Date: 2026-10-24

## Problem

On 22 Oct an agent ran `make ask` without approval ([journal](../docs/journal/2026-10-22-permissions-build.md#accidental-paid-call)). `make ask` was the only paid target with no dry run, nothing mechanical stopped a paid command, and spend was not logged anywhere. The rule is that every paid call traces to an explicit decision by Arun.

Spec and build ship in one PR (Arun, 24 Oct), to fit the 45-minute timebox.

## Acceptance criteria

- AC-1: **Spending has its own names.** `make ask`, `make embed`, `make eval` and `make permissions` only dry-run: each prints its estimate and `Dry run: \`make paid-<target>\` spends.` `make ask`'s estimate is the query-embed tokens at the model's price plus `EST_ANSWER_USD_PER_ROW`. A dry run builds no embedder or answerer (no API key needed) and writes no trace and no spend line. `make paid-ask`, `paid-embed`, `paid-eval` and `paid-permissions` take the same options and spend. `CONFIRM=1` no longer spends; `make acl CONFIRM=1` keeps it, since acl writes the DB and spends nothing.
- AC-2: **Hook and gate.** The paid mains spend only with `--confirm` *and* `HANDBOOK_PAID_RUN=1`, which only the `paid-*` recipes set. `--confirm` alone exits, naming the paid target. A Claude Code PreToolUse hook on Bash (`.claude/hooks/paid_guard.py`, registered in `.claude/settings.json`) returns `permissionDecision: "ask"` in three cases. First, any `paid-*` target name read from the Makefile appears anywhere in the command; matching the exact name anywhere means continuations, separators inside quotes and `gmake` can't hide it, and a new paid target is guarded without editing the hook. Second, `HANDBOOK_PAID_RUN` is assigned with any shell or make operator (`=`, `:=`, `?=`, `+=`, …). Third, the hook can't read the payload or the Makefile. A human therefore approves each paid run in every permission mode. Every other command passes silently, including `grep CONFIRM`, docs heredocs and `make acl CONFIRM=1`.
- AC-3: **Spend log.** Every paid run (`ask`, `embed`, `eval`, `permissions`) appends exactly one JSON line to `runs/spend.jsonl`: `timestamp`, `target`, `run_id` (null for `ask` and `embed`), `embed_model`, `answer_model`, `est_usd`, `status` (`ok` / `failed`). It is written in a `finally`, so a run that fails after spending is still logged.

## Out of scope

- Actual cost from provider usage; the log records the dry-run estimate.
- Budgets and caps; an LLM gateway (week 7 follow-up).
- Runtime agent spend controls: per-request step and token caps, a per-run cost cap, a daily ceiling and alerts (weeks 6 and 8). The hook guards only the coding agent's shell. The product agent's calls run in-process, are approved at the run boundary and are then bounded by a budget ([follow-ups](../docs/follow-ups.md)).

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| How the hook gets approval | `permissionDecision: "ask"`: a human click per paid run | An approval file holding the session id: the agent can write that file itself |
| What the hook matches | Exact names: the Makefile's `paid-*` targets anywhere in the command, and any `HANDBOOK_PAID_RUN` assignment (Arun, 24 Oct). Second review: a `make …` context match missed continuations, `&` in a quoted Q, `gmake` and `:=` | Any `CONFIRM` / `--conf` text: no gaps, but it prompted on docs heredocs and greps, which was annoying and blurred real prompts. Exact `CONFIRM=1` / `--confirm`: quoting and argparse abbreviations slipped past it (review catch) |
| How a direct `python -m` call is covered | The mains also require the env var | Matching Python command lines in the hook: more patterns, more gaps |
| Hook vs native permission rules | The hook | `"ask": ["Bash(make paid-*)"]` needs no script, but it's prefix-only (it misses `cd … && make paid-eval`) and has no tests |

Accepted risk: the hook matches command text, so indirection (a wrapper script, the env var set in `.env`) can still get past it. It stops accidents, not a determined bypass. The dry-run default and the spend log are the other two layers.

## Verification

- `tests/unit/test_ask.py` (AC-1 to AC-3), `tests/unit/test_spend.py` (AC-1 to AC-3), `tests/unit/test_paid_guard.py` (AC-2). No test calls an API.
- Live: the hook prompts on a paid target and is declined. `make ask AS=us-ic Q="test"` prints the estimate and the dry-run line, and `runs/spend.jsonl` is unchanged.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] docs updated: journal entry, an ADR for any decision, follow-ups
