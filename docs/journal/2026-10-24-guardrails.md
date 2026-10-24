# 2026-10-24: paid-call guardrails, spec 0009

Follow-up to the [accidental paid call](2026-10-22-permissions-build.md#accidental-paid-call) of 22 Oct. Spec and build in one PR (Arun's call, to fit the 45-minute timebox).

## Decisions
- **Hook approval:** `permissionDecision: "ask"`, so every paid run needs a human click. Rejected an approval file holding the session id, because the agent can write that file itself.
- **Spending has its own names (Arun, after the first version):** the first hook matched any `CONFIRM` / `--conf` text. It had no gaps, but it prompted on docs heredocs. Arun found that annoying and asked for exact names.
  - Plain targets now only dry-run, and `make paid-<target>` spends.
  - The Python mains also require `HANDBOOK_PAID_RUN=1`, which only those recipes set, so a direct `python -m … --confirm` can't spend.
  - The hook matches the Makefile's `paid-*` names and any assignment of that env var.
  - `make acl CONFIRM=1` keeps its flag, since it writes the DB and spends nothing.
- **Runtime agent spend is a different layer** (Arun's question): the hook sees only the coding agent's shell. The product agent's model calls run in-process, so they're approved at the run boundary and bounded by caps inside it. Logged in [follow-ups](../follow-ups.md).

## /code-review catches
- **First review (broad-match hook), fixed:**
  - **Bypass:** exact `CONFIRM=1` / `--confirm` missed `CONFIRM="1"` and the argparse abbreviation `--conf`.
  - **Failed open:** the hook raised on a null `tool_input`, and Claude Code treats a hook error as non-blocking. It now asks on anything it can't read.
  - The spec status was set to implemented too early, and this entry was missing.
- **Second review (exact names), fixed:**
  - **Bypass:** a `make …` context match missed `HANDBOOK_PAID_RUN:=1` (and `?=`, `+=`), a backslash continuation, a `&` inside a quoted `Q`, and `gmake`. The hook now matches the target names anywhere in the command, and the env var with any assignment operator.
  - **Duplication:** the hook hard-coded the target list. It now reads `paid-*` from the Makefile and fails closed if there are none.
  - **Stale hints:** "no embeddings" errors still said `make embed`, which no longer spends. They now point at `make paid-embed`.
- **Listed for Arun, not fixed:** see the PR description.

## Verification
- `make ask AS=us-ic Q="test"` printed the estimate ($0.0040) and the dry-run line, and no spend log was written.
- The live hook prompt was seen on the first version: Arun declined it, and a later heredoc false positive showed the same hook was live. The final version is checked live before merge (see the PR).
- Clean room: see the PR.

## Limitations
- The hook matches command text. Indirection (a wrapper script, the env var set in `.env`) can get past it. It stops accidents, not a determined bypass. The dry-run default and the spend log are the other two layers.
- A command that merely mentions an exact paid target name (`paid-eval` in a heredoc, say) still prompts. Doc text goes through Edit and Write, which the hook doesn't watch.
- `est_usd` in the spend log is the dry-run estimate, not the provider's bill.

## Spend
- None.
