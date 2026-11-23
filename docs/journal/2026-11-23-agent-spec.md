# 2026-11-23: hand-rolled agent spec review, spec 0013

Arun's review of the [spec 0013](../../specs/0013-hand-rolled-agent.md) draft (#59): a free check that changed the tool choice, the budget arithmetic, and the decisions. No paid calls.

## Reading-log correction
The draft reading note said synthesis chunk_all_required@5 was 0.00 at baseline. On the current baseline (`e602bd95` / `d83f3edc`) it is 0.125 (1 of 8 rows); 0.00 was the 17 Oct baseline. Corrected in [week 5 reading](../reading/week-05.md). The rank 6–8 figure (5 of 7) was right.

## Would expand reach the rank 6–8 facts?
The first draft recommended a second tool, `expand(n)`, returning a chunk's neighbours. The check: in `d83f3edc`'s depth-20 lists, is each fact chunk at rank 6–8 next to (`chunk_index ± 1`, same doc) a top-5 chunk?

| row | fact chunk at rank 6–8 | next to a top-5 chunk? |
|---|---|---|
| 8 | `finance/expenses`, chunk 26 | no; that doc has no chunk in the top 5 |
| 49 | `laptop-ordering`, chunk 0 | no; another doc |
| 53 | `lumos/ar`, chunk 0 | no |
| 55 | `eba`, chunk 2 | no |
| 89 | `offboarding`, chunk 5 | no; its top-5 chunks are 0, 14 and 17 |

`expand` reaches none of them. They are separate chunks ranked just below the cut, so the tool became `retrieve(query, page)` instead (D2).

## Budgets
**Measured inputs** (13 paid `ask` calls in `runs/ask.jsonl`; small n): answer input 2,952 tokens at p50 (system prompt + 5 excerpts), so one retrieval adds ~2.5–2.9k tokens. Answer call latency p50 1.9 s, p95 3.3 s. Retrieve (query embed + search) p50 0.9 s, p95 3.2 s.

**Arithmetic.** The full turn history is re-sent at every step. With r retrieval steps and a final answer call, total input is about (r + 1) × 0.5k + 2.9k × r(r + 1)/2:
- r = 4: ~31.5k
- r = 5 (all 5 tool calls, then the forced final answer): ~46.5k, plus ~1.5k output, ~48k. Hence **50k tokens**, not the 40k first drafted.
- **6 steps** = 5 tool steps + the answer. With parallel tool calls off, **5 tool calls** is the real ceiling; the drafted 8 could never bind.
- **Timeout:** 6 × 3.3 s + 5 × 3.2 s ≈ 36 s at p95; **90 s** gives ~2.5× headroom.
- These are back-of-envelope safety rails, not measured trajectory lengths. Wednesday's trajectory evals give the real distribution.

**How production would set them:**
1. Run representative traffic or an eval set with generous caps.
2. Set step and tool-call caps near p95–p99 of the trajectories that end well.
3. Set the token cap from a target cost per request (USD per query ÷ price per token).
4. Set the timeout from the latency target promised to users, minus overhead.
5. Monitor the `budget_exhausted` rate and the quality of those answers.
6. Re-derive after any model or retriever change. Caps per session, per day and per user or plan sit on top.

## Decisions (Arun)
Recorded with alternatives in [spec 0013's Decisions table](../../specs/0013-hand-rolled-agent.md#decisions):
- **D1:** tool loop, parallel tool calls off.
- **D2:** one tool, `retrieve(query, page)`, page 1–4 (ranks up to 20).
- **D3:** Postgres tables, with a version check and a lease for two turns on one session. Redis rejected: a new service, and storage latency is irrelevant beside a ~1.9 s model call.
- **D4:** medium: 6 steps, 5 tool calls, 50k tokens, 90 s. Tokens raised for the forced final answer.
- **D5:** earlier turns replayed as question + final answer only. Full replay would leave a follow-up one retrieval; last-N-in-full plus a summary has the same cost at N = 1. Summarising long sessions is a follow-up.
- **D6:** on the step or tool-call budget, one final call with tools off; on tokens or time, stop with a fixed message.
- **D7:** excerpts numbered per turn, `[n]` stripped from replayed answers. No overflow, and no citation to text out of context.
- **D8:** no code-side ACL re-check: every chunk comes through `ask.search`'s verified predicate. A future tool with its own data source adds one.
- Agreed spec changes: query length cap and empty-query rejection; error texts that say what to do next; budgets not overridable by the user and recorded per turn.

## Assumptions
- The framework behaviour cited in D6 (LangChain `early_stopping_method`, OpenAI Agents SDK `MaxTurnsExceeded`, Claude Agent SDK `error_max_turns`) was from memory. Checked before the build: see the [build journal](2026-11-23-agent-build.md#d6-framework-behaviour-checked).
