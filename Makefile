.DEFAULT_GOAL := help
.PHONY: help up down corpus ingest chunk embed acl ask eval permissions test test-unit test-integration lint fmt db-shell

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-18s %s\n", $$1, $$2}'

up: ## Start DB and wait until healthy
	docker compose up -d --wait

down: ## Stop DB (keeps data volume)
	docker compose down

corpus: ## Check out pinned handbook corpus into data/handbook
	PYTHONPATH=src uv run python -m handbook_rag.corpus

ingest: ## Load pinned corpus markdown into Postgres (needs `make up`, `make corpus`)
	PYTHONPATH=src uv run --env-file .env python -m handbook_rag.ingest

chunk: ## Chunk documents under CONFIG (default the baseline, fixed-512-64); FORCE=1 ignores the early exit
	PYTHONPATH=src uv run --env-file .env python -m handbook_rag.chunk $(if $(CONFIG),--config $(CONFIG)) $(if $(FORCE),--force)

embed: ## Embed CONFIG's chunks with no embedding for EMBED_MODEL: dry run unless CONFIRM=1, LIMIT=n
	PYTHONPATH=src uv run --env-file .env python -m handbook_rag.embed \
		$(if $(CONFIG),--config $(CONFIG)) $(if $(filter 1,$(CONFIRM)),--confirm) $(if $(LIMIT),--limit $(LIMIT))

acl: ## Resolve acl/policy-v1.yaml onto documents and every config's chunks: dry run unless CONFIRM=1
	PYTHONPATH=src uv run --env-file .env python -m handbook_rag.acl $(if $(filter 1,$(CONFIRM)),--confirm)

ask: ## Answer a question as a fixture user: make ask AS=us-ic Q="...", dry run unless CONFIRM=1
	@test -n "$$Q" -a -n "$(AS)" || { echo 'usage: make ask AS=<user id> Q="your question"'; exit 2; }
	PYTHONPATH=src uv run --env-file .env python -m handbook_rag.ask --as "$(AS)" $(if $(filter 1,$(CONFIRM)),--confirm) "$$Q"

eval: ## Run the eval set: CONFIRM=1 to spend (only 1 counts), LIMIT=n, RETRIEVAL_ONLY=1, CONFIG=, BASELINE=<run id>
	PYTHONPATH=src uv run --env-file .env python -m handbook_rag.evaluation.run \
		$(if $(filter 1,$(CONFIRM)),--confirm) $(if $(LIMIT),--limit $(LIMIT)) $(if $(filter 1,$(RETRIEVAL_ONLY)),--retrieval-only) \
		$(if $(CONFIG),--config $(CONFIG)) $(if $(BASELINE),--baseline $(BASELINE))

permissions: ## Run permissions-v1, retrieval-only: dry run unless CONFIRM=1, CONFIG=
	PYTHONPATH=src uv run --env-file .env python -m handbook_rag.evaluation.permissions \
		$(if $(filter 1,$(CONFIRM)),--confirm) $(if $(CONFIG),--config $(CONFIG))

test: test-unit test-integration ## Run unit + integration tests

test-unit: ## Run unit tests
	uv run pytest -m "not integration"

test-integration: ## Run integration tests (needs `make up`)
	uv run --env-file .env pytest -m integration

lint: ## Ruff check + format check
	uv run ruff check .
	uv run ruff format --check .

fmt: ## Ruff autofix + format
	uv run ruff check --fix .
	uv run ruff format .

db-shell: ## psql into the DB container
	docker compose exec db sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'
