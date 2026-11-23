# 2026-11-23: hand-rolled agent build, spec 0013

The build of [spec 0013](../../specs/0013-hand-rolled-agent.md) ([ADR-0024](../decisions/0024-hand-rolled-agent.md)). No paid calls: every test uses a fake model, a fake retriever or a fake embedder.

## D6 framework behaviour, checked
The [spec review](2026-11-23-agent-spec.md#assumptions) left D6's framework citations to be checked before the build.

| Framework | Spec said | Docs say |
|---|---|---|
| OpenAI Agents SDK | raises `MaxTurnsExceeded` | correct ([running agents](https://openai.github.io/openai-agents-python/running_agents/)) |
| Claude Agent SDK | returns an `error_max_turns` result | correct, and a single-shot `query()` also raises after yielding it ([agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)) |
| LangChain | `early_stopping_method` `"force"` / `"generate"` | both in the v0.3 source; `AgentExecutor` is deprecated, and the current docs no longer list it |

None of these change D6. The spec's D6 row is corrected.

## Interpretations made in the build (approved with the plan)
- **AC-3 static test scope.** Older modules the agent imports already read `chunks` for other purposes: `acl.check_stale` counts them, and `evaluation.checks` imports `chunk`. Neither returns chunk text to the model. The test checks the modules this spec adds (the `agent/` package and `models/chat/`), and that the tool's default retriever is `ask.retrieve`.
- **Session tables on an existing volume.** `db/init/` only runs on a fresh volume. As `ingest` and `chunk` do, the paid path runs `004_agent_sessions.sql` (idempotent). The dry run writes nothing; when the tables are missing it says the first `make paid-agent` creates them.
- **Answer price.** gpt-5.4-mini is $0.75 in / $4.50 out per 1M tokens (standard tier, OpenAI pricing page, 23 Nov), in `ANSWER_MODELS`. The dry run's upper bound is $0.2252 a turn.

## Clean room
- **Setup:** a fresh clone under `$HOME` with its own DB on port 5434, the pinned corpus linked, and no API keys in its `.env`. Then ingest, chunk all five configs and `make acl`.
- **Result:** initdb created `agent_sessions` and `agent_turns` on the fresh volume. All unit and integration tests pass and lint is clean, the same as the working copy. Re-run after the lower-priority fixes.

## Limitations
- The token projection counts the request JSON with cl100k, an estimate of the provider's count, and reserves the full `MAX_COMPLETION_TOKENS` for each call.
- A model call that times out at the request timeout (the turn's remaining time) ends the turn as `error`, not `budget_exhausted/timeout`: the timeout budget is checked before each call.
- The query embedder is built as `ask` builds it (`make_embedder(spec)`, document kind). It sends the same text for the OpenAI default, so it changes nothing today.

## Review
`/code-review` (medium) found nine issues. Three were fixed, each with a regression test:
- **A stale reader could overwrite a finished turn (data integrity, AC-13).** `save_turn` and `release` left the version alone. A run that loaded the session during another turn could claim it once that turn released, then upsert over the same `turn_no`. Now every `save_turn` bumps the version.
- **A database error mid-turn left the connection in a failed transaction.** The `error` record's save and the lease release then both failed, and the lease held until it expired. `save_turn` and `release` now roll back first; every store write commits, so this only ends reads.
- **A failure building the models after the claim skipped the release.** The model and tool are now built inside the `try` whose `finally` releases the lease and logs spend.

The test agent also caught the AC-3 static test pattern being too broad: it flagged the dry run's `chunk_embeddings` presence check, copied from `ask.main`, which reads no chunk. The test now forbids reading `chunks` and allows `chunk_embeddings` only in that statement.

Lower priority, all three fixed at Arun's request, each with a regression test:
- **Tool execution had no deadline.** A query-embed retry storm could run a turn past `timeout_s` + the lease margin. The tool now hands `ask.retrieve` a `sleep` that raises `ToolTimeout` instead of waiting past the turn's remaining time, and the turn ends `budget_exhausted/timeout`. A single slow embed or search call is still bounded only by its own client timeout.
- **A forced final call with tool calls and no text stored `""` as the answer.** It now ends like a token or time stop: no answer, the fixed message, replayed as the question only.
- **An empty reply (e.g. `finish_reason` `content_filter`) ended as `answered`.** It is now `error` (`EmptyReply`, with the finish reason).

Not fixed:
- `tool._format` copies `ask.build_prompt`'s excerpt format; a unit test pins the two together, and `ask.py` stays unchanged (AC-18).
- The token estimate re-encodes the whole request each step. That is at most 6 steps a turn.
- Two first-ever paid runs at once can race on `CREATE TABLE IF NOT EXISTS`. A fresh clone gets the tables from initdb.
