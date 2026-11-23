# 0024. Hand-rolled tool-loop agent with Postgres session state

- **Status:** accepted (2026-11-23, decided by Arun in the spec 0013 review, #59)
- **Date:** 2026-11-23
- **Journal:** [2026-11-23 agent spec review](../journal/2026-11-23-agent-spec.md), [2026-11-23 agent build](../journal/2026-11-23-agent-build.md)
- **Spec:** [0013](../../specs/0013-hand-rolled-agent.md), Decisions D1–D8

## Context
- `ask` does one retrieval and one answer call. It misses synthesis rows (chunk_all_required@5 0.125, 1 of 8), facts at dense rank 6–8 (5 of 7 retrieval-side false abstentions), and follow-ups.
- The riskiest requirement is that no answer comes from outside the user's ACL.

## Decision
The options, pros and cons are in spec 0013's Decisions table. In short:

| # | Decision |
|---|---|
| D1 | A tool loop on direct Chat Completions calls, no framework; parallel tool calls off |
| D2 | One tool, `retrieve(query, page)`, page 1–4 (ranks up to 20) |
| D3 | Sessions in Postgres (`agent_sessions`, `agent_turns`); a turn is claimed by one `UPDATE` with a version check and a lease |
| D4 | Per turn: 6 steps, 5 tool calls, 50k tokens (a projected ceiling), 90 s; constants only, never user-set |
| D5 | Earlier turns replayed as question + final answer only |
| D6 | Steps or tool calls spent: one final call with tools off. Tokens or time spent: stop with a fixed message |
| D7 | Excerpts numbered per turn; `[n]` stripped from replayed answers |
| D8 | No code-side ACL re-check: every chunk comes through `ask.search`'s verified predicate. A tool with its own data source adds one |

## Consequences
- The Principal is bound by the CLI and closed over by the tool, so identity can't be set by the model.
- Every prompt, response, tool call and returned chunk id is in the turn record, so Wednesday's trajectory evals can score offline.
- A follow-up must retrieve again to quote an earlier excerpt (D5). Long sessions grow by about 0.5k tokens per turn until session compaction (a follow-up).
- `make paid-agent` costs at most ~$0.23 a turn at current prices (upper bound: 50k tokens at the output rate).
