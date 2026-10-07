# NOTES

Working notes on building this with a coding agent. One bullet per entry: what happened → what I did or learned.

## 2026-10-05 (scaffold)

- Colima was not running, so `make up` failed with a Docker API socket error → the agent showed the raw error and its diagnosis, asked before running `colima start`, then re-ran.
- `brew install uv` timed out compiling cmake from source → the agent killed it and used the standalone uv installer instead.
- Clean-room check in `/tmp` failed with `type "vector" does not exist` → Colima mounts only `$HOME`, so the init SQL bind mount was empty. Re-ran from a clone under `~/tmp`. Documented in the README.
- `git commit` failed with "Author identity unknown" → the agent asked instead of guessing, then set a repo-local identity.
- The plan gate and scope rules held. The agent presented the plan, waited for approval, and left out Alembic, a settings framework, CI and pre-commit hooks, which were all explicitly out of scope.

## 2026-10-07

- Colima was down again → another `colima start`. This is a recurring failure, so the environment check is the first step of every build block.
