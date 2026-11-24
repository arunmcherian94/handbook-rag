# 2026-11-24: first paid agent turn

The first paid turn of the [spec 0013](../../specs/0013-hand-rolled-agent.md) agent, at main `acd5ae1`. It was a smoke test of the paid path (real adapter, strict tool schema, spend log, turn persistence), not an eval. One run, approved by Arun.

## The turn
- **Row:** eval set v1.2 row 26 (lookup · single-fact), "do i have to turn on disk encryption on my laptop", as `us-ic`. It was picked because it should need one retrieval.
- **Command:** `make paid-agent AS=us-ic Q="…"`, session `dc50bd66-9f2b-4eac-8ba1-63f2e7b80d60`, turn 1.
- **Config:** `openai:gpt-5.4-mini`, `openai:text-embedding-3-large@1536`, `fixed-512-64`. Budgets: 6 steps, 5 tool calls, 50,000 tokens, 90 s.

| | |
|---|---|
| Terminal state | `answered` (not forced-final, not truncated) |
| Model calls | 2: `tool_calls` (635 in / 26 out, 3.3 s), then `stop` (3,234 in / 88 out, 1.8 s) |
| Tool calls | 1: `retrieve {"query": "disk encryption laptop required employee handbook", "page": 1}` → excerpts 1–5 |
| Pages returned | laptop-security/encryption (Overview), people-group/acceptable-use-policy, onboarding101/linux-onboarding101 (Security Requirements), laptop-security/management (MDM), security/corporate/systems |
| Tokens | 3,869 in / 114 out |
| Cost | ≈ $0.0034 (answer model $0.0029 in + $0.0005 out; query embedding ≈ $0.000001), about 1.5% of the $0.2252 upper bound |
| Latency | 9.0 s total; the `retrieve` step took 3.9 s, longer than either model call |
| Citations | [1] encryption Overview, [3] linux-onboarding101. `invalid_citations` empty, so the citation check passed |

**Answer quality (read by hand):** it states required fact F1 ("Yes, all laptops are required…") and optional variants F2 (macOS, Jamf) and F4 (Linux, enable at OS setup). Each claim is in its cited excerpt. The expected doc is excerpt 1.

## Limitations
- **The spend log records the estimate, not the actual cost.** `runs/spend.jsonl` stores `est_usd` (the $0.2252 bound). The actual cost above is worked out from the turn record's tokens and the `ANSWER_MODELS` prices.
- **One turn on one easy row.** It shows the paid path works end to end. It says nothing about synthesis or rank 6–8 rows, which are left to Wednesday's trajectory evals.
