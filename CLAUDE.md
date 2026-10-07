# handbook-rag

Senior-engineer portfolio project built over 8 weeks: a permission-aware RAG assistant over the GitLab public handbook. Later weeks add ingestion from the handbook repo's markdown, chunking/embedding experiments, synthetic ACLs enforced as a retrieval pre-filter, hybrid search, reranking, an eval harness, and an agent layer. Production hygiene matters; speculative structure does not.

## Stack

Python 3.12, uv, Postgres + pgvector via docker compose.

## Working rules

- Plan first. Present the full plan (files, contents summary, commands) and WAIT for approval before creating or editing anything.
- Do not add dependencies, tables, frameworks, or files beyond the acceptance criteria. If you think something is missing, ask; don't add it.
- Run `make test` before saying any task is done. Show the actual output.
- When something fails, show the raw error and your diagnosis before fixing it.
- Push only when asked, and always to a new branch with a PR. Never push to main.
- NOTES.md holds decisions, gate catches, limitations, assumptions, and follow-ups only.
- Be terse. No summaries of what you're about to do after the plan is approved.

## Workflow (spec-driven)

1. Write `specs/NNNN-<name>.md` from `specs/0000-template.md`, with numbered AC-n criteria. Open it as its own PR. The human reviews and merges it before any build starts.
2. Build from the merged spec in plan mode. Each plan step cites the AC IDs it covers. Anything not traceable to an AC is scope creep: list it in NOTES.md as a follow-up, and don't build it.
3. Tests reference the AC IDs they cover.
4. Before opening a PR, run `make test`, `make lint`, and `/code-review`. Rank the findings by severity.
   - **Fix by default:** correctness bugs, data integrity or provenance problems, security issues, and anything that breaks an AC.
   - **Lower priority** (simplification, style, minor efficiency, speculative hardening): list them with the reason and wait for the human to confirm before fixing.
   - Record what the review caught in NOTES.md.
5. Clean-room verify from a fresh clone under `$HOME`. Colima only mounts `$HOME`.
6. Set the spec's status to implemented, then push and open the PR.

## Commands

- `make help` — list targets
- `make up` — start DB and wait until healthy
- `make down` — stop DB
- `make corpus` — check out the pinned handbook corpus into `data/handbook`
- `make ingest` — load the corpus into Postgres (needs `make up` and `make corpus`)
- `make test` — unit + integration
- `make test-unit`
- `make test-integration`
- `make lint`
- `make fmt`
- `make db-shell`
