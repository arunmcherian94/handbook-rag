.DEFAULT_GOAL := help
.PHONY: help up down corpus ingest chunk embed paid-embed acl ask paid-ask eval paid-eval answer-eval permissions paid-permissions ann-build ann paid-ann test test-unit test-integration lint fmt db-shell

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

# Spec 0009: a plain target only dry-runs; its paid-<target> twin spends. The paid mains need both
# --confirm and this env var, so a direct `python -m` call can't spend without the hook seeing it.
SPEND = HANDBOOK_PAID_RUN=1
EMBED = PYTHONPATH=src uv run --env-file .env python -m handbook_rag.embed \
	$(if $(CONFIG),--config $(CONFIG)) $(if $(LIMIT),--limit $(LIMIT))
ASK = PYTHONPATH=src uv run --env-file .env python -m handbook_rag.ask --as "$(AS)" "$$Q"
EVAL = PYTHONPATH=src uv run --env-file .env python -m handbook_rag.evaluation.run \
	$(if $(LIMIT),--limit $(LIMIT)) $(if $(filter 1,$(RETRIEVAL_ONLY)),--retrieval-only) \
	$(if $(CONFIG),--config $(CONFIG)) $(if $(BASELINE),--baseline $(BASELINE)) \
	$(if $(RETRIEVER),--retriever $(RETRIEVER))
PERMISSIONS = PYTHONPATH=src uv run --env-file .env python -m handbook_rag.evaluation.permissions \
	$(if $(CONFIG),--config $(CONFIG)) $(if $(RETRIEVER),--retriever $(RETRIEVER))
ANN = PYTHONPATH=src uv run --env-file .env python -m handbook_rag.evaluation.ann
ASK_USAGE = @test -n "$$Q" -a -n "$(AS)" || { echo 'usage: make ask AS=<user id> Q="your question"'; exit 2; }

embed: ## Dry run: chunks of CONFIG with no embedding for EMBED_MODEL, and the cost; LIMIT=n
	$(EMBED)

paid-embed: ## Spend: embed as `make embed` estimates
	$(SPEND) $(EMBED) --confirm

acl: ## Resolve acl/policy-v1.yaml onto documents and every config's chunks: dry run unless CONFIRM=1 (no spend)
	PYTHONPATH=src uv run --env-file .env python -m handbook_rag.acl $(if $(filter 1,$(CONFIRM)),--confirm)

ask: ## Dry run: the cost of answering as a fixture user, make ask AS=us-ic Q="..."
	$(ASK_USAGE)
	$(ASK)

paid-ask: ## Spend: answer as a fixture user, AS= Q= as for `make ask`
	$(ASK_USAGE)
	$(SPEND) $(ASK) --confirm

eval: ## Dry run: the eval set's rows and cost; LIMIT=n, RETRIEVAL_ONLY=1, CONFIG=, BASELINE=<run id>, RETRIEVER=dense|fts|hybrid|rerank
	$(EVAL)

paid-eval: ## Spend: run the eval set, same options as `make eval`
	$(SPEND) $(EVAL) --confirm

answer-eval: ## Answer-content check + false-abstention classes over the baseline run (no spend); RUN=<id>
	PYTHONPATH=src uv run python -m handbook_rag.evaluation.answer_eval $(if $(RUN),--run $(RUN))

permissions: ## Dry run: permissions-v1 cases and cost (retrieval-only); CONFIG=, RETRIEVER=
	$(PERMISSIONS)

paid-permissions: ## Spend: run permissions-v1, same options as `make permissions`
	$(SPEND) $(PERMISSIONS) --confirm

ann-build: ## Copy fixed-512-64 3-large vectors into ann.hnsw_chunks + HNSW index: dry run unless CONFIRM=1 (no spend)
	$(ANN) build $(if $(filter 1,$(CONFIRM)),--confirm)

ann: ## Dry run: exact vs HNSW recall-starvation run, saved/missing query vectors and cost
	$(ANN) run

paid-ann: ## Spend: embed missing query vectors, then run as `make ann` describes
	$(SPEND) $(ANN) run --confirm

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
