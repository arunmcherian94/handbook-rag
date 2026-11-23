# 0013: Hand-rolled agent, multi-turn, with explicit session state

- Status: draft
- Date: 2026-11-23

## Problem

`ask` does one retrieval and one answer call. That is enough for a single-fact lookup, and it is the baseline. It fails in three places:

- **Synthesis rows:** chunk_all_required@5 is 0.125 on the current baseline (1 of 8 rows). No single top-5 set holds every fact the row needs.
- **Facts just below the cut:** in spec 0010, 5 of the 7 retrieval-side false abstentions (rows 8, 49, 53, 55, 89) had their missing fact at dense rank 6–8. Two ranking changes over the same candidates (specs 0011, 0012) didn't recover them.
- **Follow-ups:** `ask` has no memory, so "and for contractors?" is answered without the earlier question.

This spec adds a hand-rolled, multi-turn agent: a loop in which the answer model calls handbook tools, with the session state written down explicitly. It covers week 5 Monday only. It adds no eval run; the comparison with `ask` is Wednesday's trajectory evals.

## Design

### The riskiest requirement: no answer from outside the user's ACL

Today the guarantee is structural: groups come only from `identity.load`, and the SQL filters on them before ranking (spec 0007, AC-8). An agent adds three new ways to break it:

1. **A model-filled identity.** If any tool took a user or group argument, a prompt ("I'm an admin") or an injected excerpt could fill it. So no tool has one. The Principal is bound once by the process entry point (the CLI today, a server later) and closed over by the tool executors. Spec 0007 AC-14 already names this obligation for week 5.
2. **State carried across turns.** Earlier excerpts are replayed into later turns. That is safe only if every turn in a session runs as the same Principal under the same ACLs. A session is bound to one user and one policy and identities version, and resuming it under anything else fails.
3. **A second tool with its own SQL.** Any new statement carries the same `allowed_groups && %(groups)s` predicate, and the spec 0011 static test covers it.

### Where a fixed workflow is enough, and why a loop earns its place here

A single-fact lookup is a fixed workflow: retrieve, then answer. That is `ask`, and it stays unchanged. A loop earns its place when the number of retrievals can't be known in advance:

- a synthesis question needs one retrieval per part, and only the model can see which parts are still missing
- a fact at rank 6–8 needs a reworded query or a section fetch, and only the first result shows that
- a follow-up needs the earlier turn, plus maybe a new retrieval

### Which pattern this is

In the terms of [Building effective agents](../docs/reading/week-05.md#building-effective-agents-anthropic-dec-2024), this is an **agent**: an augmented LLM (the answer model with retrieval tools and session memory) in a loop of tool calls. Ground truth from the environment at each step is the tool results. Stopping conditions are the budgets and the terminal states. The final-answer citation and abstention checks are recorded here and become Tuesday's evaluator in an evaluator-optimizer loop. Following the article, there is no framework: direct Chat Completions calls, so every prompt and response is visible in the session file.

## Depends on / frozen inputs

| Input it fixes | Open decision that could change it | Handling |
|---|---|---|
| Answer model | None this week; ADR-0005 sets the default (`DEFAULT_ANSWER_MODEL`), overridable by `ANSWER_MODEL` | **Write as a rule:** the model `resolve_answer_spec()` returns at run time, recorded in the session header. Reasoning effort and `MAX_COMPLETION_TOKENS` per call as for `ask` |
| Retriever inside the `retrieve` tool | `DEFAULT_RETRIEVER` is `dense` (hybrid and rerank not adopted, week 3) | **Write as a rule:** `ask.retrieve`, the dense path the default retriever names, at `TOP_K` |
| Embedding model and chunk config | Week 4's size and overlap sweep could change `BASELINE_CONFIG` | **Write as a rule:** `resolve_embed_spec()` and `BASELINE_CONFIG` at run time, recorded in the session header |
| Baseline the agent must beat | None | **Write as a rule:** `ask` with the default retriever and answer model at run time. No run ID is fixed here; Wednesday's spec picks the runs |
| `ask.py`, `prompts.SYSTEM_PROMPT`, `OpenAIAnswerer.answer` | None | **Frozen:** unchanged (AC-17) |
| Agent system prompt | None | **Decided in the build PR, reviewed by Arun:** a new `AGENT_SYSTEM_PROMPT` that keeps `SYSTEM_PROMPT`'s rules and fixed replies, adapted to excerpts arriving through tools |
| Answer model price for the dry-run estimate | No price constant exists for answer models | **Write as a rule:** read from a new `ANSWER_MODELS` entry (input and output USD per 1M, `price_source`) verified on the vendor's page at build time; an unknown model fails the dry run |
| Loop shape, tool count, state storage, budget values, follow-up handling | Decisions D1–D5 | **Decide first:** Arun fills in the Chosen column before this spec merges. ACs that depend on a choice cite it |
| Guardrails, trajectory evals, modes and checkpointing | Tuesday–Thursday specs | **Accepted risk:** out of scope here, but the ACs keep the hooks they need (Non-goals) |

## Acceptance criteria

Each criterion is testable. Tests and plan steps cite them by ID.

**Model port**

- AC-1: **A tool-calling port beside `Answerer`.**
  - `ChatModel.complete(messages, tools) -> ChatStep`, where `ChatStep` carries the text, a list of tool calls (id, name, raw argument string), input and output tokens, and the finish reason.
  - One OpenAI Chat Completions adapter, built by a `make_chat_model()` factory from `resolve_answer_spec()`. It passes `tools` with strict JSON schemas and the same reasoning effort and completion cap as `ask`; parallel tool calls as D1 decides.
  - No new dependency and no framework.
  - Unit tests use a fake client: request shape, tool-call and usage mapping, `finish_reason == "length"` read as truncated.

**Tools**

- AC-2: **`retrieve(query)`.**
  - Schema: one required string, `query`; `additionalProperties: false`.
  - Description, in the tool definition: searches the GitLab handbook and returns up to 5 numbered excerpts; reword the query rather than repeat it; use one call per part of a multi-part question; an empty result means nothing was found.
  - It calls `ask.retrieve(conn, embedder, query, principal, TOP_K, config_id=BASELINE_CONFIG)` with the bound Principal.
  - The result is plain text, one excerpt per block: `[n] url_path — heading` then the content, as `ask.build_prompt` formats them.
  - An empty result returns "No excerpts found.", the same text whether nothing matched or nothing was visible to the Principal (spec 0007, AC-8).
- AC-3: **`fetch_section(url_path, heading)`, only if D2 picks two tools.**
  - Schema: two required strings; `additionalProperties: false`.
  - It accepts only a (url_path, heading) pair already shown in this session's excerpts. Any other pair returns one fixed error text, the same whether the section doesn't exist, isn't visible to the Principal or wasn't shown yet.
  - It returns the visible chunks of that document whose `COALESCE(heading, title)` equals the heading, in `chunk_index` order, for `BASELINE_CONFIG`, capped at a fixed number of chunks set in `constants.py`.
  - Its SQL carries `allowed_groups && %(groups)s`; the spec 0011 static predicate test covers it.
  - (If D2 picks the neighbour-expansion option instead, the same rules apply to it: no identity argument, only excerpts already shown, the ACL predicate in its SQL.)
- AC-4: **Session-wide excerpt numbers.**
  - Each chunk gets a number the first time any tool returns it in the session, counting up from 1. A chunk returned again keeps its number. Numbers stay valid across turns.
  - More unique excerpts than `MAX_CITATION` in one session ends the turn as `error`, so no excerpt number can be read as a year or amount.

**Identity**

- AC-5: **The Principal can't be set from tool arguments.**
  - No tool schema has a user, group or principal field. A tool call with any argument outside its schema (for example `user_id`, `groups`, `as`) is rejected before execution: the model gets an error tool result, the retriever is not called, and the call counts toward the tool-call budget.
  - Every executed tool receives the Principal bound at session start: the same object, for every call in every turn.
  - A question or excerpt that claims another identity changes nothing: the spec 0007 claimed-identity cases (AC-15) pass when asked through the agent with a fake model that calls `retrieve`.
- AC-6: **A session is bound to one Principal and one ACL state.**
  - The session header records `user_id`, the resolved groups, the policy version and sha256, and the identities fixture version and sha256.
  - Resuming a session as a different user, or after the policy or identities file changed, fails before any model or tool call, with a message to start a new session.
  - Every turn runs `acl.check_stale` first, as `ask` does (spec 0007, AC-5).

**Loop, budgets and terminal states**

- AC-7: **The loop.** Per D1. In the tool-loop shape: call the model with the tools; execute each tool call in order and append its result; repeat until the model replies without tool calls (the final answer) or a budget or error ends the turn.
- AC-8: **Four budgets per turn**, values per D4, set in `constants.py` and recorded in the session header:
  - `max_steps`: model calls
  - `max_tool_calls`: tool calls executed or rejected
  - `max_tokens`: input + output tokens summed over the turn's model calls
  - `timeout_s`: wall-clock time since the turn started, read from an injected clock
  - Each is checked before every model call and every tool call. The remaining time is also passed as the request timeout, so one slow call can't overrun by more than the SDK's own timeout handling.
- AC-9: **Exactly one terminal state per turn**, logged in the turn record:
  - `answered`: a final reply that is not an abstention
  - `abstained`: a final reply that `checks.abstention` marks as abstained (either fixed string)
  - `budget_exhausted`: a budget hit first; the record names it in `budget` (`steps`, `tool_calls`, `tokens` or `timeout`). The user gets a fixed message from `prompts.py`, not a partial answer, and no extra model call is made to summarise
  - `error`: a model API failure after the SDK's retries, a database error, an excerpt-number overflow (AC-4) or a session-file write failure. The record has the exception type and message
  - A malformed tool call (bad JSON, unknown tool, extra argument) is not an error: the model gets an error tool result and may recover within budget.
  - A final reply cut at the completion cap is `answered` or `abstained` with `truncated: true`, as in `ask`.

**Session state**

- AC-10: **What a session stores.**
  - Header: `session_id`, `created_at`, `user_id`, groups, policy and identities versions (AC-6), answer model, embedding model, `config_id`, corpus sha, budgets, the sha256 of `AGENT_SYSTEM_PROMPT` and of the tool definitions.
  - `messages`: the exact list sent to the model, including tool calls and tool results.
  - `excerpts`: the session's numbered excerpts (`n`, `chunk_id`, `url_path`, `heading`, `first_seen_turn`).
  - `turns`, one record per turn: question, start and end time, terminal state, `budget` when hit, every step (model call: tokens, latency, finish reason; each tool call: id, name, raw arguments, accepted or rejected, the excerpt numbers and chunk ids it returned, latency, error), the final text, citations, invalid citations, the abstention result, `truncated`, and token and latency totals.
- AC-11: **Where it lives** (per D3; the AC below is the first option):
  - In memory during a turn, and in `runs/agent/<session_id>.json` (gitignored), written after every step through a temporary file and a rename, so a crash leaves the last complete step.
  - Loading the file gives back the same state that was saved (round-trip test).
- AC-12: **A follow-up turn reuses the session.**
  - `make agent AS=<user> Q="..." SESSION=<id>` (and `paid-agent`) loads the session, checks AC-6, and runs one more turn. Without `SESSION`, a new session starts and its id is printed.
  - What the model sees from earlier turns follows D5. Whatever D5 picks, the model sees the earlier questions and final answers, and excerpt numbers from earlier turns stay valid for citation (AC-4).
  - Budgets are per turn and start fresh each turn.

**Final-answer checks**

- AC-13: **The existing checks run on the final answer.**
  - `ask.parse_citations` over the session's excerpts (AC-4) gives citations and invalid citations, so citing an excerpt from an earlier turn is valid.
  - `checks.abstention(answer, None)` gives `abstained` and its label.
  - Both results are stored in the turn record and printed with the answer, as `ask.format_result` prints them. A failed check doesn't change the terminal state in this spec; Tuesday's retry acts on it.

**Paid calls**

- AC-14: **`make agent` is a dry run.**
  - It verifies the corpus pin, the embeddings for the embedding model, the ACLs and the identity, then prints the models, the budgets and an upper-bound cost for one turn: `max_tool_calls` query embeds at the embedding price + `max_tokens` at the answer model's input price + `max_steps × MAX_COMPLETION_TOKENS` at its output price.
  - It needs no API key and makes no paid call.
- AC-15: **`make paid-agent` spends, through the existing guard.**
  - The recipe sets `HANDBOOK_PAID_RUN=1` and passes `--confirm`; `spend.paid(confirm, "agent")` gates it. The paid-call hook reads `paid-*` names from the Makefile, so it asks before `paid-agent` with no hook change.
  - `log_spend("agent", estimate, run_id=session_id, ...)` runs in a `finally`, once per turn, with `status` set from the terminal state.
- AC-16: **Tests make no API calls.** Unit tests use a fake `ChatModel` that returns scripted steps and fake tool executors; integration tests use the database with a fake embedder.

**Unchanged**

- AC-17: **`ask` is unchanged.** `ask.py`, `prompts.SYSTEM_PROMPT`, `OpenAIAnswerer.answer` and `make ask` keep their behaviour, and their existing tests pass unchanged.

## Non-goals (the design must not block them)

| Later work | What this spec keeps for it |
|---|---|
| **Guardrails (Tue):** retry with feedback when the citation or abstention check fails; the prompt-injection suite | The checks' results are in the turn record (AC-13), and the loop ends in one place where an evaluator can append feedback and continue within the same budgets. Tool results are already treated as data by the prompt |
| **Trajectory evals (Wed):** scoring steps, tool choice and queries; the comparison with `ask` | Every step, raw tool arguments and returned chunk ids are in the session file (AC-10), so trajectories can be scored offline without re-running the model |
| **Orchestration modes and checkpointing (Thu)** | The session file is written after every step with everything needed to continue (AC-11). The loop is a function of (state, model, tools), so a mode can wrap it or resume it from a saved step |

## Out of scope

- Any eval run of the agent, and any claim that it beats `ask`.
- Hybrid or reranked retrieval inside the tools.
- Streaming, a server or a UI. The CLI is the entry point.
- Per-session, per-run and per-day spend caps beyond the per-turn budgets ([follow-ups](../docs/follow-ups.md), weeks 6 and 8).
- Observability beyond the session file (week 6).
- A third tool, or tools that write anything.

## Decisions

Arun fills in **Chosen** before this spec merges. Token figures assume ~560 tokens per excerpt, so one `retrieve` adds ~2.9k tokens, and every step re-sends the history.

| # | Decision | Options: pros / cons | Trade-off | Chosen |
|---|---|---|---|---|
| D1 | Loop shape | **(a) Tool loop:** the model decides each step until it replies without a tool call. *Pros:* the agent pattern itself; handles any number of parts; simplest code. *Cons:* least predictable cost and latency; needs every budget. **(b) Fixed workflow with one reformulation:** retrieve → answer; on an abstention, the model rewrites the query once, then retrieve → answer again. *Pros:* bounded at 2 retrievals; easy to evaluate. *Cons:* can't split a synthesis question; it's a workflow, not an agent, so it skips this week's subject. **(c) Plan then execute:** the model lists queries up front, code runs them all, then one answer call. *Pros:* fixed 2 model calls; retrievals in parallel. *Cons:* no ground truth between steps, so a weak first result can't change the plan. **Sub-choice for (a): parallel tool calls** on (fewer steps, but a burst of calls can spend the tool budget at once) or off (one call per step; simpler logs, more steps) | Adaptivity against predictability. (a) is the only option that uses each tool result to choose the next step | |
| D2 | How many tools | **(a) `retrieve` only.** *Pros:* smallest interface; nothing new to secure. *Cons:* a fact at rank 6–8 is reachable only by rewording. **(b) `retrieve` + `fetch_section(url_path, heading)`.** *Pros:* reads the rest of a section that a 512-token window cut; arguments come from excerpts already shown. *Cons:* a new SQL statement to cover with the ACL test; with fixed windows, `heading` is only the heading at the window's start, so a "section" is approximate. **(c) `retrieve` + `expand(n)`, the neighbouring chunks (`chunk_index ± 1`) of excerpt n.** *Pros:* one integer argument, hard to get wrong; fits fixed windows exactly. *Cons:* a new SQL statement; context grows by two chunks per call. **(d) `retrieve` with a `k` argument.** *Pros:* reaches rank 6–8 directly. *Cons:* the model picks k, which week 4 treats as a measured setting; larger k costs tokens every call | Interface size against reach. Each added tool is one more statement to keep under the ACL predicate | |
| D3 | State storage | **(a) In memory + one JSON file per session, rewritten atomically after every step.** *Pros:* one file holds the whole state; easy to read and diff; Thursday's checkpointing loads it. *Cons:* rewrites the whole file each step (small at our sizes). **(b) An append-only JSONL event log per session, state rebuilt by replay.** *Pros:* never rewrites; a full history of events. *Cons:* a replay function to write and test; two shapes (events and state) to keep in step. **(c) Postgres tables (sessions, turns, steps).** *Pros:* queryable; ready for a server. *Cons:* new tables, migrations and cleanup, which CLAUDE.md asks to avoid unless an AC needs them. **(d) In memory only.** *Pros:* no I/O. *Cons:* no follow-up across CLI invocations, no checkpoint, no offline trajectory evals | Simplicity against queryability. (a) or (b) keeps Thursday's options open; (c) commits to a schema early | |
| D4 | Budget values (per turn) | **(a) Tight:** 4 steps, 4 tool calls, 20k tokens, 60 s. *Pros:* low cost per turn. *Cons:* room for about 3 retrievals before the answer call; a follow-up's replayed history (D5) eats into it. **(b) Medium:** 6 steps, 8 tool calls, 40k tokens, 90 s. *Pros:* 4–5 retrievals plus the answer, enough for a 3-part synthesis with one rewording. *Cons:* about twice (a)'s worst-case cost. **(c) Loose:** 10 steps, 15 tool calls, 100k tokens, 180 s. *Pros:* rarely binds, so it shows natural trajectory lengths for Wednesday. *Cons:* a looping model spends the most before it stops. Cumulative input for r retrieval steps plus the answer is about 0.5k + 3.4k + 6.3k + … (r + 1 terms): ~31k at r = 4 | Coverage against worst-case cost. The dry run (AC-14) shows each option's upper bound in dollars before any paid turn | |
| D5 | How a follow-up turn is handled | **(a) Replay the full message history**, tool results included. *Pros:* exact; earlier excerpts stay in context and citable; no extra code. *Cons:* input grows every turn and counts against the token budget. **(b) Replay questions and final answers only.** *Pros:* small context. *Cons:* earlier excerpts are gone, so citing them needs a new retrieval; the model sees numbers it can't read. **(c) (b) plus a compact excerpt list** (number, url_path, heading; no content). *Pros:* small; the model knows what it saw and can fetch it again (pairs with D2 b or c). *Cons:* citing an excerpt still needs a fetch first. **(d) Condense the follow-up into a standalone question** (one extra model call), then run the turn fresh. *Pros:* a known workflow pattern; each turn's context stays small. *Cons:* an extra call per turn; the rewrite can drop the user's intent; earlier excerpts aren't reused. **(e) A model-written summary of earlier turns.** *Pros:* bounded context. *Cons:* an extra call; lossy; its errors carry forward | Fidelity against context growth. All options are safe for permissions only because a session is bound to one Principal (AC-6) | |

## Open questions

- None beyond D1–D5.

## Verification

- Unit (in memory, fake `ChatModel`, fake tool executors, injected clock; no API calls):
  - the adapter's request shape and response mapping (AC-1)
  - tool schemas and descriptions; empty-result text (AC-2, AC-3)
  - excerpt numbering across tools and turns; overflow at `MAX_CITATION` (AC-4)
  - **the Principal can't be overridden:** a scripted tool call with `user_id`, `groups` or `as` is rejected and never reaches the retriever; every executed call receives the bound Principal object (AC-5)
  - resuming as another user, or after a policy or identities change, fails before any call (AC-6)
  - **budgets terminate the loop:** one scripted model that never stops calling tools, run once per budget (steps, tool calls, tokens, timeout via the fake clock); each ends `budget_exhausted` with the right `budget` and a saved file (AC-8, AC-9)
  - the other terminal states: `answered`, `abstained`, `error` (fake API failure), malformed tool calls recovered within budget, truncation (AC-9)
  - session file contents, atomic write and round trip (AC-10, AC-11)
  - **a follow-up turn sees the earlier turn's state:** turn 2's fake model asserts its messages hold turn 1's question, answer and (per D5) excerpts; it cites an excerpt number from turn 1, and that citation is valid (AC-12, AC-13)
  - the dry run needs no key and prints the estimate; the paid gate; spend logged in `finally` on success and failure (AC-14, AC-15)
- Integration (database, fake embedder, fake `ChatModel`):
  - a restricted chunk never reaches a persona without access through `retrieve` (and `fetch_section` or `expand`, if D2 adds one), and `admin` gets it (AC-2, AC-3, AC-5)
  - the spec 0011 static predicate test covers any new statement (AC-3)
  - the claimed-identity cases through the agent (AC-5)
- `ask` unchanged: existing tests pass (AC-17).
- Free checks: `make agent AS=us-ic Q="..."` prints the models, budgets and estimate and makes no call.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] docs updated: journal entry, an ADR for any decision, follow-ups

## References

- [Reading log, week 5: Building effective agents](../docs/reading/week-05.md#building-effective-agents-anthropic-dec-2024)
- [Spec 0007: permission-aware retrieval](0007-permission-aware-retrieval.md) (AC-8, AC-14, AC-15)
- [Spec 0009: paid-call guardrails](0009-paid-call-guardrails.md)
- [Spec 0010: answer evaluation](0010-answer-evaluation.md) (the rank 6–8 false abstentions)
- [Week 3 summary](../docs/weekly/week-03.md)
- [Follow-ups](../docs/follow-ups.md) (prompt injection beyond retrieval; runtime agent spend controls)
