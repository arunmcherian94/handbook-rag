---
name: orchestrate
description: Split approved work into file-disjoint slices, run them as parallel subagent waves from a dependency graph, checkpoint progress, integrate and verify. Use for the build after plan approval, code-review fixes, and read-only research during planning.
---

# Orchestrate subagents

The main session is the orchestrator. It writes the contracts, launches the agents, integrates their work and verifies it. It never hands off `make test`, `make lint`, `/code-review`, commits or pushes.

## When to use it
- **Use it** for two or more slices that touch disjoint files.
- **Don't use it** for:
  - a quick edit or a single file
  - work so coupled that it needs back-and-forth
  - a strict sequence where each step needs the previous result

## Plan phase (read-only)
- Up to 3 Explore or general-purpose agents, each with its own question.
- Each returns a digest of at most 400 words with sources or `file:line` references, not raw dumps.
- No edits.

## Slice table (goes in the approved plan)

| id | owns | reads | depends on | ACs | model | done when | status |
|---|---|---|---|---|---|---|---|

- A file appears in only one `owns` list.
- Tests go in the same slice as their module.
- Slice 0 holds the contracts (dataclasses, typed stubs, constants) and is written by the orchestrator before any agent starts.
- Coupled changes go in one slice. When in doubt, merge the slices.
- **Waves:** a slice is in wave 1 if it has no dependencies. Otherwise it is one wave after its latest dependency. Slices in the same wave run in parallel. A dependency cycle means the plan is wrong, so fix the plan.
- At most 4 agents per wave.

## Model per slice (the orchestrator's call)
Set the Agent `model` param and record it in the table.
- **Main model:** planning, contracts, integration, research that needs judgment.
- **`sonnet` (Sonnet 5.5):** a well-defined coding slice, where the contracts are written and "done when" is clear.
- **`haiku` (Haiku 5.5):** mechanical fixes, such as message text, a one-line guard or a test tweak.
- **On failure:** if an agent returns `blocked` or a wrong diff, re-run the slice one model up instead of patching around it.

## Brief (each agent starts cold)
- the goal and the AC text
- the files it **owns** (it edits only these) and the files it **reads**
- the contract paths it builds on
- the repo rules:
  - match the surrounding style
  - tests cite AC IDs
  - no new dependencies
  - no git operations
- **Stop rule:** if it needs to edit a file outside its slice or change a contract, it stops and reports why.
- **Done when:** its own tests and `uv run ruff check` pass.
- **Report, at most 200 words:**
  - files changed
  - tests run, with their output
  - assumptions
  - open questions

## Checkpoints (resume without redoing work)
- **Status values:** `todo`, `running <agentId>`, `done`, or `blocked: <why>`.
- The orchestrator updates the status column in the plan file at every launch and every return. The plan file survives the session; the agents' memory doesn't.
- A slice becomes `done` only after the orchestrator has read its diff and its tests pass.
- **On resume** (after a usage limit or in a new session):
  1. Re-read the table and `git status`.
  2. Re-run the tests of the `done` slices.
  3. For each `running` slice, continue the agent by ID with `SendMessage`. Explore and Plan agents can't be continued. If continuing fails, relaunch with the same brief plus: "Files may be partly written. Read them first and finish; don't restart."
- No commits per slice. The working tree plus the table are the checkpoint, and the PR gets one clean commit.

## Integrate
1. Read every diff.
2. Run the full `make test` and `make lint` on the combined tree. A slice passing its own tests doesn't mean the combined tree does.
3. Resolve conflicting decisions yourself, and record any real decision as an ADR in `docs/decisions/`.

## Review-fix phase
- Group the `/code-review` findings by the file they touch. Each file group is one slice, so two fixes to the same file always go in the same slice.
- The same brief, checkpoints and integration steps apply.
- Re-review only the changed diff, once. Don't loop.
