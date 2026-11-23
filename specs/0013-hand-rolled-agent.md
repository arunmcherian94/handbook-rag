# 0013: Hand-rolled agent, multi-turn, with explicit session state

- Status: draft
- Date: 2026-11-23

## Problem

`ask` does one retrieval and one answer call. That is enough for a single-fact lookup, and it is the baseline. It fails in three places:

- **Synthesis rows:** chunk_all_required@5 is 0.125 on the current baseline (1 of 8 rows). No single top-5 set holds every fact the row needs. Row 32 ("walk me through expenses end to end, from submitting a receipt to getting paid") needs four required facts from two pages: submission, deadline, approval and payout.
- **Facts just below the cut:** in spec 0010, 5 of the 7 retrieval-side false abstentions (rows 8, 49, 53, 55, 89) had their missing fact at dense rank 6–8. Two ranking changes over the same candidates (specs 0011, 0012) didn't recover them.
- **Follow-ups:** `ask` has no memory, so "and for contractors?" is answered without the earlier question.

This spec adds a hand-rolled, multi-turn agent: a loop in which the answer model calls a retrieval tool, with the session state stored explicitly. It covers week 5 Monday only. It adds no eval run; the comparison with `ask` is Wednesday's trajectory evals.

## Design

### The riskiest requirement: no answer from outside the user's ACL

Today the guarantee is structural: groups come only from `identity.load`, and the SQL filters on them before ranking (spec 0007, AC-8). An agent adds three new ways to break it:

1. **A model-filled identity.** If the tool took a user or group argument, a prompt ("I'm an admin") or an injected excerpt could fill it. So it has none. The Principal is bound once by the process entry point (the CLI today, a server later) and closed over by the tool executor. Spec 0007 AC-14 already names this obligation for week 5.
2. **State carried across turns.** Earlier answers are replayed into later turns. That is safe only if every turn in a session runs as the same Principal under the same ACLs. A session is bound to one user and one policy and identities version, and resuming it under anything else fails.
3. **A new path to chunks.** Every chunk reaches the model through `ask.search`, whose SQL predicate is the verification and which the spec 0007 tests cover. The agent adds no SQL that reads chunks, so no second check is needed. A later tool with its own data source must add a code-side re-check in its own spec (AC-3).

### Where a fixed workflow is enough, and why a loop earns its place here

A single-fact lookup is a fixed workflow: retrieve, then answer. That is `ask`, and it stays unchanged. A loop earns its place when the number of retrievals can't be known in advance:

- a synthesis question needs one retrieval per part, and only the model can see which parts are still missing
- a fact at rank 6–8 needs the next page of results or a reworded query, and only the first page shows that
- a follow-up needs the earlier turn, plus maybe a new retrieval

### Which pattern this is

In the terms of [Building effective agents](../docs/reading/week-05.md#building-effective-agents-anthropic-dec-2024), this is an **agent**: an augmented LLM (the answer model with a retrieval tool and session memory) in a loop of tool calls. Ground truth from the environment at each step is the tool result. Stopping conditions are the budgets and the terminal states. The final-answer citation and abstention checks are recorded here and become Tuesday's evaluator in an evaluator-optimizer loop. Following the article, there is no framework: direct Chat Completions calls, so every prompt and response is visible in the session record.

## Depends on / frozen inputs

| Input it fixes | Open decision that could change it | Handling |
|---|---|---|
| Answer model | None this week; ADR-0005 sets the default (`DEFAULT_ANSWER_MODEL`), overridable by `ANSWER_MODEL` | **Write as a rule:** the model `resolve_answer_spec()` returns at run time, recorded in the session header. Reasoning effort and `MAX_COMPLETION_TOKENS` per call as for `ask` |
| Retriever inside the `retrieve` tool | `DEFAULT_RETRIEVER` is `dense` (hybrid and rerank not adopted, week 3) | **Write as a rule:** `ask.retrieve`, the dense path the default retriever names, at `TOP_K` per page |
| Embedding model and chunk config | Week 4's size and overlap sweep could change `BASELINE_CONFIG` | **Write as a rule:** `resolve_embed_spec()` and `BASELINE_CONFIG` at run time, recorded in the session header |
| Baseline the agent must beat | None | **Write as a rule:** `ask` with the default retriever and answer model at run time. No run ID is fixed here; Wednesday's spec picks the runs |
| `ask.py`, `prompts.SYSTEM_PROMPT`, `OpenAIAnswerer.answer` | None | **Frozen:** unchanged (AC-18) |
| Agent system prompt | None | **Decided in the build PR, reviewed by Arun:** a new `AGENT_SYSTEM_PROMPT` that keeps `SYSTEM_PROMPT`'s rules and fixed replies, adapted to excerpts arriving through a tool |
| Answer model price for the dry-run estimate | No price constant exists for answer models | **Write as a rule:** read from a new `ANSWER_MODELS` entry (input and output USD per 1M, `price_source`), verified on the vendor's page at build time; an unknown model fails the dry run |
| Loop shape, tool count, state storage, budget values, follow-up handling, budget exhaustion, excerpt numbering | Decisions D1–D7 | **Decided** (Arun, 23 Nov) |
| Guardrails, trajectory evals, modes and checkpointing | Tuesday–Thursday specs | **Accepted risk:** out of scope here, but the ACs keep the hooks they need (Non-goals) |

## Acceptance criteria

Each criterion is testable. Tests and plan steps cite them by ID.

**Model port**

- AC-1: **A tool-calling port beside `Answerer`.**
  - `ChatModel.complete(messages, tools, tool_choice) -> ChatStep`, where `ChatStep` carries the text, a list of tool calls (id, name, raw argument string), input and output tokens, and the finish reason.
  - One OpenAI Chat Completions adapter, built by a `make_chat_model()` factory from `resolve_answer_spec()`. It passes `tools` with strict JSON schemas, `parallel_tool_calls: false`, `tool_choice` (`"auto"`, or `"none"` for the final call in AC-10), and the same reasoning effort and completion cap as `ask`.
  - No new dependency and no framework.
  - Unit tests use a fake client: request shape, tool-call and usage mapping, `finish_reason == "length"` read as truncated.

**The tool**

- AC-2: **`retrieve(query, page)`, the only tool.**
  - Schema: `query`, a string, and `page`, an integer from 1 to 4; both required; `additionalProperties: false`.
  - The description says: it searches the GitLab handbook and returns 5 numbered excerpts per page; start at page 1; ask for the next page only when the results are on-topic but miss the detail; if they are off-topic, reword the query instead; use one search per part of a multi-part question. It gives one example (`{"query": "expense report approval by manager", "page": 1}`).
  - Page p calls `ask.retrieve(conn, embedder, query, principal, k=TOP_K × p, config_id=BASELINE_CONFIG)` with the bound Principal and returns ranks 5(p − 1) + 1 to 5p. The deepest it reaches is rank 20.
  - The result is plain text, one excerpt per block: `[n] url_path — heading` then the content, as `ask.build_prompt` formats them.
  - Rejected before any embedding, each with an error text that says what to do next: an empty query; a query over `AGENT_MAX_QUERY_TOKENS` cl100k tokens (set in `constants.py`, well under the embedder's limit); a (query, page) pair already returned in this turn ("already shown; use the excerpts above, or reword the query").
  - An empty page returns "No excerpts found.", the same text whether nothing matched or nothing was visible to the Principal (spec 0007, AC-8).
- AC-3: **Chunks reach the model only through `ask.search`.**
  - The agent module contains no SQL. A static test fails if it, or any module it imports apart from `ask`, adds a statement that reads `chunks`.
  - A future tool with its own data source must add a code-side ACL re-check on its results, in its own spec.
- AC-4: **Excerpt numbers are per turn.**
  - In each turn, each chunk gets a number the first time the tool returns it, counting from 1. A chunk returned again in the same turn keeps its number. Numbers restart at 1 in the next turn.
  - A turn shows at most 5 tool calls × 5 excerpts = 25 excerpts, so a number never reaches `MAX_CITATION`.

**Identity**

- AC-5: **The Principal can't be set from tool arguments.**
  - The tool schema has no user, group or principal field. A tool call with any argument outside its schema (for example `user_id`, `groups`, `as`) is rejected before execution: the model gets an error tool result, the retriever is not called, and the call counts toward the tool-call budget.
  - Every executed call receives the Principal bound at session start: the same object, for every call in every turn.
  - A question or excerpt that claims another identity changes nothing: the spec 0007 claimed-identity cases pass when asked through the agent with a fake model that calls `retrieve`.
- AC-6: **A session is bound to one Principal and one ACL state.**
  - The session header records `user_id`, the resolved groups, the policy version and sha256, and the identities fixture version and sha256.
  - Resuming a session as a different user, or after the policy or identities file changed, fails before any model or tool call, with a message to start a new session.
  - Every turn runs `acl.check_stale` first, as `ask` does (spec 0007, AC-5).

**Loop, budgets and terminal states**

- AC-7: **The loop.** Call the model with the tool; execute the tool call, if any, and append its result; repeat until the model replies without a tool call (the final answer), or a budget or an error ends the turn. One tool call per step (`parallel_tool_calls: false`).
- AC-8: **Four budgets per turn**, set in `constants.py`:
  - `max_steps = 6`: model calls, including the final answer call
  - `max_tool_calls = 5`: tool calls executed or rejected. With one call per step it equals `max_steps − 1`; it stays a separate check so it still binds if parallel calls are turned on later
  - `max_tokens = 50_000`: input + output tokens summed over the turn's model calls. Before each model call, the projected total (tokens so far + the call's input, counted with cl100k + `MAX_COMPLETION_TOKENS`) must fit, so the cap is a ceiling, not a trigger after the overshoot
  - `timeout_s = 90`: wall-clock time since the turn started, read from an injected clock. The remaining time is passed as the request timeout
  - The arithmetic behind the values is in the [journal, 23 Nov](../docs/journal/2026-11-23-agent-spec.md#budgets).
- AC-9: **Budgets can't be overridden by the user.** No CLI flag, Make variable or environment variable sets them; only a code change to `constants.py` does. Each turn record stores the budgets it ran with. A resumed session uses the current constants, never values read from the stored session.
- AC-10: **What happens when a budget runs out.**
  - **Steps or tool calls:** when the next model call would be the last one allowed (step 6), or the tool-call budget is spent, that call is made with `tool_choice: "none"`. The model answers from the excerpts it already has; the final-answer checks (AC-15) run on it as usual.
  - **Tokens or time:** the turn stops before the next call, with a fixed message from `prompts.py` and no partial answer.
  - Both end the turn as `budget_exhausted` (AC-11). The session continues; the next turn starts with fresh budgets.
- AC-11: **Exactly one terminal state per turn**, logged in the turn record:
  - `answered`: a final reply from a normal step, not an abstention
  - `abstained`: a final reply from a normal step that `checks.abstention` marks as abstained (either fixed string)
  - `budget_exhausted`: the record names the budget in `budget` (`steps`, `tool_calls`, `tokens` or `timeout`) and has `forced_final: true` with the answer and its checks when the final call was made (AC-10)
  - `error`: a model API failure after the SDK's retries, a database error or a session-store write failure. The record has the exception type and message
  - A malformed tool call (bad JSON, an unknown tool, an extra argument, a rejected query) is not an error: the model gets an error tool result and may recover within budget.
  - A final reply cut at the completion cap is `answered` or `abstained` with `truncated: true`, as in `ask`.

**Session state**

- AC-12: **What a session stores.**
  - Header: `session_id`, `created_at`, `user_id`, groups, policy and identities versions (AC-6), answer model, embedding model, `config_id`, corpus sha, the sha256 of `AGENT_SYSTEM_PROMPT` and of the tool definition.
  - One record per turn: question, start and end time, the budgets (AC-9), the exact messages sent in the turn (tool calls and results included), the turn's excerpts (`n`, `chunk_id`, `url_path`, `heading`), every step (model call: tokens, latency, finish reason, `tool_choice`; tool call: id, name, raw arguments, accepted or rejected, the excerpt numbers and chunk ids it returned, latency, error), the terminal state, `budget` and `forced_final`, the final text, citations, invalid citations, the abstention result, `truncated`, and token and latency totals.
- AC-13: **Where it lives: Postgres.**
  - `db/init/004_agent_sessions.sql` adds two tables: `agent_sessions` (`session_id` uuid key, `user_id`, `header` jsonb, `version` integer, `lease_until` timestamptz, `created_at`, `updated_at`) and `agent_turns` (`session_id`, `turn_no`, `record` jsonb; key on both).
  - **Claiming a turn:** one `UPDATE agent_sessions SET version = version + 1, lease_until = now() + timeout_s + margin WHERE session_id = … AND version = <version read> AND (lease_until IS NULL OR lease_until < now())`. No row updated means another turn is running, or the session changed since it was read: the command fails with "session busy; retry" and makes no model call. No transaction stays open across model calls.
  - The turn record is upserted after every step, so a crash leaves the last complete step. The terminal state clears `lease_until`. A lease left by a crash expires after `timeout_s` + margin.
  - Loading a session gives back the same state that was saved (round-trip test).
- AC-14: **A follow-up turn reuses the session.**
  - `make agent AS=<user> Q="..." SESSION=<id>` (and `paid-agent`) loads the session, checks AC-6, claims the turn (AC-13) and runs one more turn. Without `SESSION`, a new session starts and its id is printed.
  - Earlier turns are replayed as the question and the final answer only, with no tool calls or tool results. `[n]` markers are stripped from the replayed answers, and the cited sources are appended as plain text (`Sources: url_path — heading`). The model can retrieve again for anything it needs to quote.
  - Turns ended by tokens or time (no answer) are replayed as the question alone.

**Final-answer checks**

- AC-15: **The existing checks run on the final answer.**
  - `ask.parse_citations` over this turn's excerpts (AC-4) gives citations and invalid citations. Only excerpts in the turn's context count, so a citation can't point at text the model can't see.
  - `checks.abstention(answer, None)` gives `abstained` and its label.
  - Both are stored in the turn record and printed with the answer, as `ask.format_result` prints them. A failed check doesn't change the terminal state in this spec; Tuesday's retry acts on it.

**Paid calls**

- AC-16: **`make agent` is a dry run.**
  - It verifies the corpus pin, the embeddings for the embedding model, the ACLs, the identity and that the session tables exist. It then prints the models, the budgets and an upper-bound cost for one turn: `max_tool_calls` query embeds at the embedding price + `max_tokens` at the answer model's output price (an upper bound, since every token is priced at the higher rate).
  - It needs no API key, makes no paid call and writes nothing.
- AC-17: **`make paid-agent` spends, through the existing guard.**
  - The recipe sets `HANDBOOK_PAID_RUN=1` and passes `--confirm`; `spend.paid(confirm, "agent")` gates it. The paid-call hook reads `paid-*` names from the Makefile, so it asks before `paid-agent` with no hook change.
  - `log_spend("agent", estimate, run_id=session_id, ...)` runs in a `finally`, once per turn, with `status` set from the terminal state.
  - Tests make no API calls. Unit tests use a fake `ChatModel` that returns scripted steps and a fake retriever; integration tests use the database with a fake embedder.

**Unchanged**

- AC-18: **`ask` is unchanged.** `ask.py`, `prompts.SYSTEM_PROMPT`, `OpenAIAnswerer.answer` and `make ask` keep their behaviour, and their existing tests pass unchanged.

## Non-goals (the design must not block them)

| Later work | What this spec keeps for it |
|---|---|
| **Guardrails (Tue):** retry with feedback when the citation or abstention check fails; the prompt-injection suite | The checks' results are in the turn record (AC-15), and the loop ends in one place where an evaluator can append feedback and continue within the same budgets. Tool results are already treated as data by the prompt |
| **Trajectory evals (Wed):** scoring steps, tool choice, queries and pages; the comparison with `ask` | Every step, raw tool arguments and returned chunk ids are in the turn record (AC-12), so trajectories can be scored offline without re-running the model |
| **Orchestration modes and checkpointing (Thu)** | The turn record is saved after every step with everything needed to continue (AC-13). The loop is a function of (state, model, tool), so a mode can wrap it or resume it from a saved step |

## Out of scope

- Any eval run of the agent, and any claim that it beats `ask`.
- Hybrid or reranked retrieval inside the tool.
- A second tool, or a tool that writes anything.
- Streaming, a server or a UI. The CLI is the entry point.
- Session compaction, session expiry, multi-device sessions, a Redis cache, and observability beyond the turn records ([follow-ups](../docs/follow-ups.md#from-the-spec-0013-review-2026-11-23)).
- Spend caps per session, run or day ([follow-ups](../docs/follow-ups.md), weeks 6 and 8).

## Decisions

Decided by Arun, 23 Nov. The review questions, the adjacency check and the budget arithmetic are in the [journal](../docs/journal/2026-11-23-agent-spec.md).

| # | Decision | Options: pros / cons | Chosen |
|---|---|---|---|
| D1 | Loop shape | **(a) Tool loop:** the model decides each step until it replies without a tool call. *Pros:* uses each tool result to choose the next step; handles any number of parts; simplest code. *Cons:* least predictable cost and latency; needs every budget. **(b) Fixed workflow with one reformulation:** retrieve → answer; on an abstention, reword once and repeat. *Pros:* bounded; easy to evaluate. *Cons:* can't split a synthesis question. **(c) Plan then execute:** the model lists queries up front, code runs them, one answer call. *Pros:* two model calls. *Cons:* no ground truth between steps. **Parallel tool calls:** on (fewer steps; a burst can spend the tool budget at once) or off (one call per step; simpler logs) | **(a), parallel calls off** |
| D2 | How many tools | **(a) `retrieve(query)` only.** *Pros:* smallest interface. *Cons:* rank 6–8 reachable only by rewording. **(b) + `fetch_section(url_path, heading)`.** *Cons:* new SQL; with fixed windows a "section" is approximate. **(c) + `expand(n)`, the neighbouring chunks.** *Pros:* one integer argument; the standard sentence-window / parent-document idea. *Cons:* new SQL; and it would reach none of the 5 missing rank 6–8 facts, which are not next to any top-5 chunk ([journal](../docs/journal/2026-11-23-agent-spec.md#would-expand-reach-the-rank-68-facts)). **(d) `retrieve(query, k)`.** *Cons:* the model picks k freely; larger k costs tokens on every call. **(e) `retrieve(query, page)`, page 1–4.** *Pros:* goes straight at rank 6–8; one tool and one SQL path; depth bounded at 20; the model reads deeper only when page 1 is on-topic. *Cons:* the model may page when it should reword; Wednesday measures it | **(e)** |
| D3 | State storage | **(a) In memory + a JSON file per session.** *Pros:* simplest. *Cons:* two turns on one session race (last write wins) without a lock; not how a server would store it. **(b) An append-only JSONL event log.** *Cons:* a replay function; two shapes to keep in step. **(c) Postgres tables.** *Pros:* already running; durable; one `UPDATE` gives the concurrency check; queryable for evals and audit; the production shape. *Cons:* a schema file and integration tests. **(d) Redis.** *Pros:* sub-millisecond reads; built-in expiry. *Cons:* a new service; durability depends on its persistence settings; no SQL next to `chunks`. Storage latency is irrelevant beside a ~1.9 s model call. **(e) In memory only.** *Cons:* no follow-up across CLI calls | **(c)**, with a version check and a lease (AC-13) |
| D4 | Budget values (per turn) | **(a) Tight:** 4 steps, 4 tool calls, 20k tokens, 60 s. **(b) Medium:** 6 steps, 5 tool calls, 50k tokens, 90 s. **(c) Loose:** 10 steps, 15 tool calls, 100k tokens, 180 s. Tool calls above steps − 1 can never bind with parallel calls off, so (b) uses 5, not the 8 first drafted. Tokens are 50k, not 40k, so that a turn which spends all 5 tool calls still fits the forced final answer (D6) | **(b)** |
| D5 | How a follow-up turn is handled | **(a) Replay the full history.** *Pros:* exact. *Cons:* turn 1 leaves ~12k tokens of tool results, re-sent at every step of turn 2, so a follow-up gets one retrieval at most. **(b) Question + final answer only.** *Pros:* ~0.5k tokens per turn; deterministic; no extra call. *Cons:* an earlier excerpt must be retrieved again to be quoted. **(c) (b) plus a list of earlier excerpts.** *Cons:* invites citing text the model can't see. **(d) Condense the follow-up into a standalone question.** *Cons:* an extra call; the rewrite can drop intent. **(e) Last N turns in full + an LLM summary of older turns.** *Pros:* the standard long-session pattern. *Cons:* the "in full" part has (a)'s cost even at N = 1; the summary is an extra, lossy call | **(b)**; summarising older turns is a follow-up (session compaction) |
| D6 | When a budget runs out | **(a) Stop with a fixed message** (LangChain `early_stopping_method="force"`; the OpenAI Agents SDK raises `MaxTurnsExceeded`; the Claude Agent SDK returns an `error_max_turns` result). *Pros:* simplest; no extra cost. *Cons:* discards the excerpts already gathered. **(b) One final call with tools off** (LangChain `"generate"`). *Pros:* a cited answer from ACL-filtered excerpts; the checks still apply. *Cons:* needs headroom in the budget. **(c) (b) for steps and tool calls, (a) for tokens and time** | **(c)** (AC-10). Framework behaviour as recalled on 23 Nov; checked against their docs before the build |
| D7 | Excerpt numbering | **(a) Session-wide.** *Cons:* reaches `MAX_CITATION` (99) after about 3 turns; with (D5 b) old numbers would point at text no longer in context. **(b) Per turn**, `[n]` stripped from replayed answers. *Pros:* at most 25 per turn, so no overflow; every valid number points at visible text. *Cons:* a chunk can get different numbers in different turns (the record keys on `chunk_id`). **(c) Per retrieval call, prefixed (`[r2.3]`).** *Cons:* breaks `parse_citations` | **(b)** (AC-4) |
| D8 | Code-side ACL re-check on tool results | **(a) Re-check every result in code.** *Pros:* defence in depth. *Cons:* redundant when every chunk already comes through the verified `ask.search` predicate. **(b) Only where data isn't already verified** | **(b)** (Arun): no re-check now; AC-3 keeps every chunk on the verified path, and a future tool with its own source adds one |

## Open questions

None.

## Verification

- Unit (in memory, fake `ChatModel`, fake retriever, injected clock; no API calls):
  - the adapter's request shape (`parallel_tool_calls`, `tool_choice`) and response mapping (AC-1)
  - the tool schema and description; paging slices; the rejected queries and their texts; the empty-page text (AC-2)
  - per-turn numbering; a repeated chunk keeps its number; numbers restart next turn (AC-4)
  - **the Principal can't be overridden:** a scripted tool call with `user_id`, `groups` or `as` is rejected and never reaches the retriever; every executed call receives the bound Principal object (AC-5)
  - resuming as another user, or after a policy or identities change, fails before any call (AC-6)
  - **budgets terminate the loop:** a scripted model that never stops calling tools ends at step 6 with a forced final call (`tool_choice: "none"`), `budget_exhausted`, `budget: "steps"`; the same for tool calls with rejected calls; tokens and timeout (fake clock) stop before the next call with the fixed message (AC-8, AC-10, AC-11)
  - no flag or environment variable changes a budget; a resumed session uses the current constants (AC-9)
  - the other terminal states: `answered`, `abstained`, `error` (fake API failure), malformed calls recovered within budget, truncation (AC-11)
  - **a follow-up turn sees the earlier turn's state:** turn 2's fake model asserts its messages hold turn 1's question and final answer, with `[n]` stripped and sources appended, and no turn 1 tool results (AC-14)
  - citations checked against this turn's excerpts only (AC-15)
  - the dry run needs no key, prints the estimate and writes nothing; the paid gate; spend logged in `finally` on success and failure (AC-16, AC-17)
- Integration (database, fake embedder, fake `ChatModel`):
  - a restricted chunk never reaches a persona without access through `retrieve` at any page, and `admin` gets it (AC-2, AC-5)
  - the static test: no chunk-reading SQL outside `ask` (AC-3)
  - the claimed-identity cases through the agent (AC-5)
  - session round trip; two claims on one version, only one wins; an expired lease can be claimed; a record saved after each step survives a simulated crash (AC-13)
- `ask` unchanged: existing tests pass (AC-18).
- Free checks: `make agent AS=us-ic Q="..."` prints the models, budgets and estimate and makes no call.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] docs updated: journal entry, an ADR for any decision, follow-ups

## References

- [Reading log, week 5: Building effective agents](../docs/reading/week-05.md#building-effective-agents-anthropic-dec-2024)
- [Journal, 23 Nov: agent spec review](../docs/journal/2026-11-23-agent-spec.md)
- [Spec 0007: permission-aware retrieval](0007-permission-aware-retrieval.md) (AC-8, AC-14, AC-15)
- [Spec 0009: paid-call guardrails](0009-paid-call-guardrails.md)
- [Spec 0010: answer evaluation](0010-answer-evaluation.md) (the rank 6–8 false abstentions)
- [Week 3 summary](../docs/weekly/week-03.md)
- [Follow-ups](../docs/follow-ups.md)
