# 0018. Subagents on file-disjoint slices via the orchestrate skill

- **Status:** accepted
- **Date:** 2026-10-17
- **Journal:** [2026-10-17 subagent orchestration](../journal/2026-10-17-subagent-orchestration.md)

## Context
Research takeaways:
- **File ownership:** split work by which files each agent owns; agents that edit the same file overwrite each other. Contracts are written first, by one owner. ([agent teams](https://code.claude.com/docs/en/agent-teams), [Cognition](https://cognition.com/blog/multi-agents-working))
- **Waves:** run slices in waves taken from the dependency graph. A cycle means the plan is wrong.
- **Checkpoints:** keep progress on disk, not in agent memory, and continue an interrupted agent by its ID. ([Anthropic: long-running harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), [subagents](https://code.claude.com/docs/en/sub-agents))
- **Final check:** each slice passing its own tests doesn't mean the combined tree passes, so run the full suite once at the end.
- **Cost and risks:** about 3–4× the tokens of a single agent. Agents slow down sequential or coupled work. Failure modes are conflicting implicit decisions and stopping early. ([Anthropic: multi-agent research](https://www.anthropic.com/engineering/multi-agent-research-system), [Cognition](https://cognition.com/blog/dont-build-multi-agents))

## Decision
Use subagents whenever the work splits cleanly: read-only research while planning, and the build and review fixes after approval.
- **Where it lives:** the procedure is in `.claude/skills/orchestrate/SKILL.md`, and CLAUDE.md has a one-line pointer to it.
- **Why:** parallel slices finish faster and keep the main context clean.
- **Why a skill:** only the skill's description is always loaded, so CLAUDE.md stays small.
- **How:**
  - The plan carries a slice table: what each slice owns, reads and depends on, its model, when it's done, and its status.
  - The orchestrator writes the contracts, integrates and verifies.
  - **Models (the orchestrator decides per slice):** Sonnet 5.5 for well-defined coding slices, Haiku 5.5 for mechanical fixes.
  - The status column is the checkpoint. There are no per-slice commits.
- **Not doing:** custom agent definitions, worktrees, a status file in the repo, scripts.

## Consequences
**Limitation:** Explore and Plan agents can't be continued after an interruption, so they're relaunched.
