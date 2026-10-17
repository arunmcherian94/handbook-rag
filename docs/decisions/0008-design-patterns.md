# 0008. Ports and adapters, DI, functional core

- **Status:** accepted
- **Date:** 2026-10-13
- **Journal:** [2026-10-13 baseline build](../journal/2026-10-13-baseline-build.md)

## Context
Design patterns (AC-11) for the baseline build: a model or provider change shouldn't touch pipeline code (AC-10), and tests should run at zero cost without network mocking.

## Decision
- **Ports and adapters (Strategy).** `Embedder` / `Answerer` are Protocols in `models/base.py`. Adapters sit one file per provider under `models/embedders/` and `models/answerers/` (`OpenAIEmbedder`, `OpenAIAnswerer`), grouped by role because embedding and answer providers differ (PR #8 review). `chunk`, `embed` and `ask` import only the Protocols, so a model or provider change doesn't touch pipeline code (AC-10). Protocols, not ABCs: fakes satisfy them structurally without inheriting anything.
- **Factory on `provider:model` strings.** `make_embedder` / `make_answerer` read `EMBED_MODEL` / `ANSWER_MODEL`. The string is also the stored `chunk_embeddings.model` key, so config, data and traces name a model the same way. A provider registry (`EMBEDDERS` / `ANSWERERS` in `models/factory.py`) replaces an if-chain: a new provider means one adapter file plus one registry entry, and the lookup never changes.
- **Dependency injection.** Clients go into adapters; `sleep` and `rand` go into `embed.run`; `clock` goes into `ask`. Tests then check request shapes, backoff timing and latency fields with fakes, at zero cost and without network mocking. An autouse fixture deletes `OPENAI_API_KEY` to prove it.
- **Functional core, imperative shell.** `chunk_doc`, `build_prompt`, `parse_citations` and the retry/split logic in `embed_with_retry` / `embed_batch` are pure and unit-tested. `run` / `ask` own SQL and commits.
- **Schema as a seam.** The untyped `vector` column plus `(chunk_id, model)` PK let models of any dimension coexist. Deterministic `chunk_id`s make re-runs idempotent and resumable.
- **Settings in `constants.py`, prompt in `prompts.py`** (PR #8 review). Paths, chunk parameters, embedding limits and retry policy, model defaults, reasoning effort, output cap and k live in one file. The system prompt and its two fixed replies live in `prompts.py`, so prompt versions diff on their own for the eval harness. Regexes and SQL stay beside the one function that uses them.

## Consequences
Adding a provider is one adapter file plus one registry entry. See [ADR-0004](0004-embedding-model-and-schema.md) for the schema seam and [ADR-0006](0006-grounding-prompt-fixed-abstentions.md) for the prompt.
