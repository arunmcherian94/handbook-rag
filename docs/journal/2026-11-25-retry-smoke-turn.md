# 2026-11-25: retry-path smoke turns (the retry didn't fire in 4 attempts)

A paid smoke test of the [spec 0014](../../specs/0014-guardrails.md) guardrails against the real model, at main `40677a7`. The goal was to exercise the citation-check retry (AC-7, AC-8) once. Four turns in one session, each approved by Arun. Turns 3 and 4 were chosen deliberately to provoke a failure (below). n = 1 session.

## Choosing the trigger
- **No eval row reliably triggers a retry.** Across 260 past eval answers (the `ask` pipeline, five runs), 2 would have failed the agent's check: rows 11 and 55 each answered once with "I don’t know based on the provided handbook excerpts." using a curly apostrophe. That doesn't match the fixed string, and it has no citation. Under 1%, and from a different prompt.
- **The follow-up case was the likelier natural trigger** (0014 D6). A follow-up replays the earlier answer with `[n]` stripped, and each turn starts with zero excerpts. A model that answers straight from that history has no valid citation, which fails as `citation_missing`.
- Prompt and model unchanged. Nothing was rigged.

## What ran
- **Persona:** `us-ic`. Session `c75113a2-fd71-4c77-894f-974eb33a2e55`, a fresh session, so its header records the post-0014 prompt and tool hashes.
- **Turn 1:** eval set v1.2 row 26, "do i have to turn on disk encryption on my laptop".
- **Turn 2:** a follow-up whose answer was already in turn 1, "and on linux, when do i have to turn it on?"
- **Config:** `openai:gpt-5.4-mini`, `openai:text-embedding-3-large@1536`, `fixed-512-64`, budgets 6 steps / 5 tool calls / 50,000 tokens / 90 s.
- **Policy:** `guardrails-v1`, sha256 `806cc433ebd4111317fcb078f06aefe01de1bd8e5f79c4f139597a3deccd4e19`, recorded on both turns.

| | Turn 1 | Turn 2 |
|---|---|---|
| Terminal state | `answered` | `answered` |
| Retry fired | no (`retries` 0) | no (`retries` 0) |
| Steps | model → `retrieve` → model | model → `retrieve` → model |
| Query | "disk encryption laptop required handbook" | "Linux onboarding disk encryption when enable it" |
| Citations | [1], [4]; none invalid | [1], [3]; none invalid |
| Guardrail events | 14, all `pass` | 14, all `pass` |
| Tokens (turn record) | 4,135 in / 97 out | 4,423 in / 76 out |
| Actual cost (from tokens × `ANSWER_MODELS` prices) | ≈ $0.0035 | ≈ $0.0037 |
| Estimate in `runs/spend.jsonl` | $0.2252 (upper bound) | $0.2252 (upper bound) |
| Latency | 9.2 s | 4.1 s |

Total actual ≈ $0.0072 of the $0.4504 approved upper bound. Query embeddings are about $0.000001 each.

## Turns 3 and 4: follow-ups chosen to provoke the failure
After turns 1–2, Arun asked for a follow-up that would trigger the retry. Only the question was chosen to provoke it: prompt and model unchanged.

| | Turn 3 | Turn 4 |
|---|---|---|
| Question | "thanks — can you put that in one short sentence?" | "what exactly does source [3] from your last answer say?" |
| Expected failure | Answers from history, no citation → `citation_missing` | Cites `[3]` with no excerpts this turn → `citation_out_of_range` |
| What happened | One call, no search; replied with the exact `OUT_OF_SCOPE` string | Searched again, then quoted the right sentence from linux-onboarding101, now excerpt [4] |
| Terminal state | `abstained` | `answered` |
| Retry fired | no | no |
| Guardrail events | 14, all `pass` | 14, all `pass` |
| Tokens (turn record) | 944 in / 19 out | 4,495 in / 65 out |
| Actual cost | ≈ $0.0008 | ≈ $0.0037 |
| Estimate in `runs/spend.jsonl` | $0.2252 | $0.2252 |

Session total actual ≈ $0.0117 over 4 turns. Approved upper bounds: $0.4504 for turns 1–2, plus $0.2252 each for turns 3 and 4.

**Finding: false out-of-scope abstention on a conversational follow-up (turn 3).** The model read "put that in one short sentence" as outside the handbook (rule 7) and returned `OUT_OF_SCOPE`. That's a valid fixed string, so the citation check correctly passed it. For the user, though, it's a wrong refusal. It isn't a guardrail problem, but trajectory evals should catch it: terminal state against the row's label.

## What it shows and doesn't
- **Shows:**
  - All 14 checks run, and record a `pass` event, on a real-model turn.
  - Every turn records the policy version and sha.
  - Resuming a session after 0014 works.
  - On a follow-up, the model searched again rather than answering from history: rule 4 (cite every claim) held.
- **Doesn't show:** the retry path against the real model. In 4 attempts, 2 of them built to provoke it, the model either searched and cited correctly or abstained with an exact fixed string. That's good news about the model, but the path is still untested against the real API. It's still covered only by unit tests and the fake-model injection suite (AC-8, AC-14).
- **n = 1 session:** 4 turns without a retry isn't a rate. The trajectory evals (spec 0015) will give retry occurrence over the eval set.
- **Spend log:** `runs/spend.jsonl` still records only the estimate. Actual cost is computed from the turn record (known follow-up).

## Observation
The curly-apostrophe abstention (rows 11 and 55 in `ask` runs) would trip `citation_missing` and get a retry whose feedback restates the exact string. That's probably the right outcome, but it would count as a retry, not an abstention, in trajectory metrics. Worth deciding in spec 0015 how retries are scored.
