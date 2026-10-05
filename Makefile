.DEFAULT_GOAL := help
.PHONY: help up down test test-unit test-integration lint fmt db-shell

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-18s %s\n", $$1, $$2}'

up: ## Start DB and wait until healthy
	docker compose up -d --wait

down: ## Stop DB (keeps data volume)
	docker compose down

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
