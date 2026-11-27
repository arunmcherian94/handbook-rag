# 0026. Agent eval references are computed at collect time; the scorer stays DB-free

- **Status:** accepted (2026-11-27, decided by Arun at the spec 0015 build plan)
- **Date:** 2026-11-27
- **Journal:** [2026-11-27 trajectory eval run](../journal/2026-11-27-trajectory-eval-run.md)
- **Spec:** [0015](../../specs/0015-trajectory-evals.md), AC-9, AC-12, AC-13

## Context
- AC-13 (trajectory fact coverage) must reuse the ADR-0015 relevance code. AC-9 says the scorer reads only the run directory, the eval set and the assertion files, with no DB.
- The relevance code (`evidence.check`) needs chunk content from the DB. The agent's turn record has only chunk ids, `url_path` and heading for each excerpt.
- AC-12's expected-doc metrics compare `expected_docs` (repo paths) with `url_path`. The path converter (`ingest.derive_url_path`) is in a module that imports the DB layer.

## Decision
The collector computes the references once, before the first turn (free: DB and corpus, no API), and writes them into `run.json` under `refs`: for each row, the expected docs as `url_path`s and, for each required fact, the sorted relevant chunk ids. The scorer intersects these with the chunk ids from the turn's accepted searches and citations.

| Option | Pros | Cons |
|---|---|---|
| **Collector stores the sets (chosen)** | Reuses `evidence.check` unchanged; the scorer stays DB-free; the run directory stands alone | Relevance is frozen at collect time: a change to the rule means recomputing `refs` (free, DB), not just re-scoring |
| Rows store chunk text and line ranges; the scorer runs the matcher on the checkout | Relevance can be recomputed offline | The scorer reads the corpus checkout (not in AC-9's list); rows.jsonl grows to about 3 MB; reuses the matcher but not `relevant_chunks` as written |
| Reuse the latest `ask` run's per-chunk facts | No new data | The agent retrieves chunks `ask` never saw (other queries, page 2), so coverage is undercounted |

## Consequences
- An agent run is regradable without the DB, and survives a volume reset (D6).
- The relevance sets are tied to the config's chunk ids at the corpus pin. Both are recorded in `run.json`.
