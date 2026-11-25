# 0025. Deterministic agent guardrails with a versioned policy in code

- **Status:** accepted (2026-11-24, decided by Arun in the spec 0014 review, #61)
- **Date:** 2026-11-24
- **Journal:** [2026-11-24 guardrails spec](../journal/2026-11-24-guardrails-spec.md), [2026-11-24 guardrails build](../journal/2026-11-24-guardrails-build.md)
- **Spec:** [0014](../../specs/0014-guardrails.md), Decisions D1–D8

## Context
- The spec 0013 agent had one structural guarantee: the ACL is a SQL pre-filter on a Principal bound in code. Nothing checked the question, marked where an excerpt ended, acted on a bad citation, or kept the user's personal data out of `agent_turns`.
- Of the lethal trifecta's three legs, private data and untrusted content are present. External communication is cut: the only tool is a read-only `retrieve`, and the CLI renders nothing.

## Decision
The options, pros and cons are in spec 0014's Decisions table. In short:

| # | Decision |
|---|---|
| D1 | Deterministic rules only (regex, token counts, Unicode classes, checksums); no LLM classifier |
| D2 | Structural input failures (empty, too long, garbage) are blocked. Injection-pattern hits are flagged and logged, and the turn proceeds |
| D3 | Excerpts are wrapped in per-turn nonce delimiters, with delimiter look-alikes neutralised and invisible characters stripped. No datamarking yet |
| D4 | PII by regex plus Luhn and mod-97: email, phone, card, US SSN, IBAN. Redacted in the answer (handbook values kept), before every save, and before the model call (apart from `@gitlab.com` emails) |
| D5 | A fifth terminal state, `guardrail_blocked`, with a reason from a closed set |
| D6 | One retry with specific feedback, inside the existing budgets; tools stay available |
| D7 | No URLs or images in answers; removals logged by host and count only |
| D8 | The policy is a frozen dataclass in code (`guardrails-v1` plus a sha256), recorded per turn and in the session header, not bound to the session |

## Consequences
- The controls that hold against an adaptive attacker don't depend on the model obeying: no outbound tool (a static test), no URLs in answers, citation checks in code. Pattern detection is a signal that feeds week 6 tracing.
- Every check writes an event, passes included, so a trip rate per check is a SQL query over `agent_turns.record->'guardrail_events'`.
- Stored turns hold no raw question PII. A follow-up replays a redacted question, so a personal email typed in turn 1 isn't available in turn 2.
- A rule change needs a PR and a version bump. A test pins the policy sha to its version, so an edit without a bump fails.
- The `make paid-agent` upper bound is unchanged ($0.2252): a retry runs inside the existing budgets.

## Policy versions
Only the current version is in the tree; earlier ones are in git history. A turn's `guardrails_sha256` identifies the exact rules that ran.

| Version | sha256 (prefix) | Introduced | Change |
|---|---|---|---|
| `guardrails-v1` | `806cc433` | spec 0014 build | First version |
