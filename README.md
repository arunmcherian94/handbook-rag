# handbook-rag

A permission-aware RAG assistant over the [GitLab public handbook](https://handbook.gitlab.com). Answers cite the handbook sections they come from. Retrieval only searches the chunks the asking user is allowed to see.

**Status:** a pinned corpus, ingestion, chunking experiments, the embedding model choice, an eval harness, and permission-aware retrieval (spec 0007 Part A) are all built. Hybrid search, reranking, an agent layer and observability come in later weeks.

## How it works

- **Corpus:** the whole handbook at a pinned commit, fetched as a blobless sparse clone ([ADR-0001](docs/decisions/0001-corpus-scope-and-pin.md)). Ingestion mirrors that snapshot into Postgres, keeping redirect stubs and skipping drafts ([ADR-0002](docs/decisions/0002-ingest-mirrors-snapshot.md)).
- **Chunks:** fixed 512-token chunks with 64-token overlap ([ADR-0003](docs/decisions/0003-baseline-chunking-512-64.md)). Other chunk configs live in the same table, keyed by `config_id`, for comparison ([ADR-0020](docs/decisions/0020-chunk-configs-coexist.md)).
- **Embeddings and search:** `text-embedding-3-large` at 1,536 dims, searched by exact cosine distance in pgvector ([ADR-0022](docs/decisions/0022-adopt-text-embedding-3-large-1536.md)).
- **Answers:** gpt-5.4-mini, using a strict grounding prompt that gives a fixed reply when the excerpts don't hold the answer ([ADR-0005](docs/decisions/0005-answer-model-and-api.md), [ADR-0006](docs/decisions/0006-grounding-prompt-fixed-abstentions.md)).
- **Permissions:** [`acl/policy-v1.yaml`](acl/policy-v1.yaml) maps handbook paths to the groups allowed to see them ([ADR-0021](docs/decisions/0021-permission-model.md), [spec 0007](specs/0007-permission-aware-retrieval.md)).
  - `make acl` copies each document's allow-list onto its chunks. Redirect stubs take their target's allow-list.
  - Search filters on the user's groups in SQL before ranking. A chunk with no ACL is hidden, never public.
  - The six users are fixtures in [`acl/identities-v1.yaml`](acl/identities-v1.yaml). Their groups are resolved in code from their attributes.
- **Evaluation:** a human-authored eval set ([docs/eval/](docs/eval/)) scored by chunk-level fact recall@k ([ADR-0013](docs/decisions/0013-retrieval-metrics.md)). A separate suite, [permissions-v1](docs/eval/permissions-v1.md), measures leak and over-blocking for each user.

## Quickstart

Clone under `$HOME` (see Troubleshooting). Copy `.env.example` to `.env`, then add `OPENAI_API_KEY` to it.

```sh
make up                      # Postgres + pgvector
make corpus                  # check out the pinned handbook
make ingest
make chunk
make embed                   # dry run: prints the estimate; `make paid-embed` spends
make acl                     # dry run; CONFIRM=1 to write the ACLs
make paid-ask AS=us-ic Q="How many days of PTO do I get?"
make test
```

`make help` lists every target.

**Costs:** `make ask`, `make embed`, `make eval` and `make permissions` are dry runs that print an estimate. Their `paid-` twins (`make paid-ask`, …) take the same options and spend. Each paid run appends a line to `runs/spend.jsonl`. In Claude Code, a project hook asks for a human's approval before any paid target runs ([spec 0009](specs/0009-paid-call-guardrails.md)).

## Results

Each eval run is written to [docs/eval/results/](docs/eval/results/). [metrics.md](docs/eval/results/metrics.md) defines the metrics. The decisions in [docs/decisions/](docs/decisions/) record which run settled what.

## Project notes

[NOTES.md](NOTES.md) is the index of the project notes: decisions (ADRs), the dated journal, follow-ups and the reading log. Work is spec-driven ([ADR-0009](docs/decisions/0009-spec-driven-workflow.md)): each change starts as a spec in [specs/](specs/) with numbered acceptance criteria, and that spec is reviewed before the build starts.

## Troubleshooting

- **Cannot connect to the Docker API:** the Colima VM is down. Run `colima start`.
- **`type "vector" does not exist`:** the init SQL did not run. Colima only mounts `$HOME` into its VM, so clone the repo under `$HOME`, not `/tmp`. Init scripts also run only on a fresh volume, so for an existing one run `docker compose down -v` and then `make up`.
