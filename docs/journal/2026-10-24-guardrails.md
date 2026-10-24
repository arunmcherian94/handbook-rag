# 2026-10-24: paid-call guardrails, spec 0009

Follow-up to the [accidental paid call](2026-10-22-permissions-build.md#accidental-paid-call) of 22 Oct. Spec and build in one PR (Arun's call, to fit the 45-minute timebox).

## Decisions
- **Hook approval:** `permissionDecision: "ask"`, so every paid command needs a human click. Rejected an approval file holding the session id, because the agent can write that file itself.
- **Runtime agent spend is a different layer** (Arun's question): the hook sees only the coding agent's shell. The product agent's model calls run in-process, so they're approved at the run boundary and bounded by caps inside it. Logged in [follow-ups](../follow-ups.md).

## /code-review catches
- **Fixed (must-fix):**
  - **Hook bypass.** It matched only the exact `CONFIRM=1` and `--confirm`. `CONFIRM="1"` (the shell strips the quotes, so make still sees 1) and `--conf` (argparse abbreviation) would have spent with no prompt. It now matches any `CONFIRM` and any `--conf` prefix. Tests cover both.
  - **Hook failed open.** A malformed payload or a null `tool_input` raised, and Claude Code treats a hook error as non-blocking. It now asks on anything it can't read.
  - The spec was marked implemented before review and clean-room verify; set back to approved.
  - This journal entry was missing although NOTES.md linked to it.
- **Listed for Arun, not fixed:** see the PR description.

## Verification
- Live: a harmless `echo` containing the confirm token raised the approval prompt mid-session, and Arun declined it. `make ask AS=us-ic Q="test"` printed the estimate ($0.0040) and the dry-run line, and no spend log was written.
- Clean room: fresh clone under `$HOME` with its own venv and the pinned corpus linked, run against the existing DB (this PR changes no schema): 433 unit and 62 integration passed, lint clean.

## Limitations
- The hook matches command text, so indirection (a variable holding the flag, a wrapper script) can get past it. It stops accidents, not a determined bypass. The dry-run default and the spend log are the other two layers.
- False positives are by design: any Bash command mentioning the token prompts, including a heredoc that writes docs (it happened once while committing this entry). Doc text goes through the Edit tool, which the hook doesn't watch.
- `est_usd` in the spend log is the dry-run estimate, not the provider's bill.

## Spend
- None.
