# handbook-rag

Senior-engineer portfolio project built over 8 weeks: a permission-aware RAG assistant over the GitLab public handbook. Later weeks add ingestion from the handbook repo's markdown, chunking/embedding experiments, synthetic ACLs enforced as a retrieval pre-filter, hybrid search, reranking, an eval harness, and an agent layer. Production hygiene matters; speculative structure does not.

## Stack

Python 3.12, uv, Postgres + pgvector via docker compose.

## Working rules

- Plan first. Present the full plan (files, contents summary, commands) and WAIT for approval before creating or editing anything.
- Do not add dependencies, tables, frameworks, or files beyond the acceptance criteria. If you think something is missing, ask; don't add it.
- Run `make test` before saying any task is done. Show the actual output.
- When something fails, show the raw error and your diagnosis before fixing it.
- Don't run `git push` or create remote repos. The user does that.
- Be terse. No summaries of what you're about to do after the plan is approved.

## Commands

- `make help` — list targets
- `make up` — start DB and wait until healthy
- `make down` — stop DB
- `make test` — unit + integration
- `make test-unit`
- `make test-integration`
- `make lint`
- `make fmt`
- `make db-shell`
