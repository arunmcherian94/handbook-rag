# handbook-rag

A permission-aware RAG assistant over the [GitLab public handbook](https://handbook.gitlab.com). Answers cite the handbook sections they come from. Retrieval only searches the chunks the asking user is allowed to see. The handbook is public, so the permissions are synthetic.

**Status (end of week 2):** retrieval and permissions are built and measured. Answers are generated, but their correctness isn't scored yet. Week summaries: [week 1](docs/weekly/week-01.md), [week 2](docs/weekly/week-02.md).

## Current configuration

| Part | Setting | Decision |
|---|---|---|
| Corpus | whole handbook at a pinned commit (`5273b21`), 4,088 docs | [ADR-0001](docs/decisions/0001-corpus-scope-and-pin.md) |
| Chunks | `fixed-512-64`: 512 tokens, 64 overlap, 22,378 chunks | [ADR-0003](docs/decisions/0003-baseline-chunking-512-64.md); structure-aware chunking rejected in [ADR-0019](docs/decisions/0019-structural-first-recursive-inside-chunking.md) |
| Embeddings | `openai:text-embedding-3-large@1536` | [ADR-0022](docs/decisions/0022-adopt-text-embedding-3-large-1536.md) |
| Search | exact cosine distance in pgvector, top 5, no ANN index | [ADR-0021](docs/decisions/0021-permission-model.md) |
| Permissions | synthetic group allow-lists, filtered in SQL before ranking | [ADR-0021](docs/decisions/0021-permission-model.md), [spec 0007](specs/0007-permission-aware-retrieval.md) |
| Answers | gpt-5.4-mini, strict grounding prompt, two fixed abstention replies; frozen through week 3 | [ADR-0005](docs/decisions/0005-answer-model-and-api.md), [ADR-0006](docs/decisions/0006-grounding-prompt-fixed-abstentions.md) |

## How it works

- **Corpus:** a blobless sparse clone of the handbook repo at the pin. Ingestion mirrors that snapshot into Postgres, keeping redirect stubs and skipping drafts ([ADR-0002](docs/decisions/0002-ingest-mirrors-snapshot.md)). Other chunk configs live in the same table, keyed by `config_id`, for comparison ([ADR-0020](docs/decisions/0020-chunk-configs-coexist.md)).
- **Permissions:** a synthetic policy, [`acl/policy-v1.yaml`](acl/policy-v1.yaml), maps handbook paths to the groups allowed to see them.
  - `make acl` copies each document's allow-list onto its chunks. Redirect stubs take their target's allow-list.
  - Every search filters on the user's groups in SQL before ranking. There is no unfiltered path.
  - A chunk with no ACL is hidden, never public.
  - The six users are fixtures in [`acl/identities-v1.yaml`](acl/identities-v1.yaml). A typed `Principal` carries their groups, which code resolves from their attributes, never from the question.
- **Evaluation:** a human-authored eval set ([docs/eval/](docs/eval/)) scored by chunk-level fact recall@k ([ADR-0013](docs/decisions/0013-retrieval-metrics.md)). A separate suite, [permissions-v1](docs/eval/permissions-v1.md), measures leak, over-blocking and authorized recall for each user. Its cases were LLM-drafted from the pin and the policy, with outcomes computed by code.

## Headline numbers

The retrieval and answer rows come from the current configuration and are compared with the same pipeline on text-embedding-3-small, the model it replaced, over the same eval rows. The permissions suite has no earlier run to compare with. It checks each persona against entitlements computed by code from the policy, and checks over-blocking against admin's top k (admin's allow-lists cover every chunk, so its results equal an unfiltered search).

| What | Run | Result | Compared with |
|---|---|---|---|
| Retrieval, chunk_fact_recall@5 (n = 32 scored answerable rows) | `2026-10-21-d83f3edc` | 0.583 ± 0.075 | 3-small, `2026-10-19-d2625d91`: 0.495 ± 0.081 (paired +0.088 ± 0.045) |
| Answers, false abstention (n = 33 answerable rows) | `2026-10-21-e602bd95` | 10/33, 0.303 ± 0.080 | 3-small, `2026-10-21-18f10293`: 11/33 (paired −0.030 ± 0.053) |
| Answers, correct out-of-corpus abstention (n = 19) | `2026-10-21-e602bd95` | 17/19 | 3-small, `2026-10-21-18f10293`: 17/19 |
| Permissions, leaked chunks / over-block (n = 50 scored cases, k = 5 and 20) | `2026-10-24-086eca8a` | 0 / 0 | Leak 0 holds by construction under the SQL pre-filter; it is not an empirical result |
| Permissions, authorized recall@5 (n = 26 cases with an authorized target) | `2026-10-24-086eca8a` | 0.878 (1.000 at k = 20) | In the four cases below 1.0, the persona's top 5 equals admin's: the targets rank lower, and nothing was filtered out |

- **The embedding switch is a retrieval gain, not an answer-quality gain.** 3-large was adopted at 1.97 paired SE, just under the pre-set 2-SE bar, as a documented exception.
- **An HNSW path was measured but isn't used.** Spec 0007 Part B measured filtered-HNSW recall starvation on a separate copy (22k chunks, ef_search 40), run `2026-10-24-ddf4a2dc`. Production stays on exact search.

Each committed eval run is in [docs/eval/results/](docs/eval/results/), and [metrics.md](docs/eval/results/metrics.md) defines the metrics. Permissions and ANN runs write to `runs/`, which isn't committed.

## Built vs not yet

**Built:**
- pinned corpus and ingestion
- chunk configs
- embedding with a model comparison
- exact search with the SQL ACL pre-filter
- grounded answers with fixed abstentions
- the retrieval eval harness
- the permissions suite
- the HNSW measurement path
- paid-call guardrails

**Not yet:**
- **answer-correctness scoring:** the harness scores abstention and citation form only
- **an LLM judge**
- **hybrid search** and reranking, in week 3
- an ANN index in production
- the agent layer
- observability
- a service

## Quickstart

Clone under `$HOME` (see Troubleshooting). Copy `.env.example` to `.env`, then add `OPENAI_API_KEY` to it.

```sh
make up                      # Postgres + pgvector
make corpus                  # check out the pinned handbook
make ingest
make chunk
make embed                   # dry run: prints the cost; `make paid-embed` spends
make acl                     # dry run; `make acl CONFIRM=1` writes the ACLs (no spend)
make ask AS=us-ic Q="How many days of PTO do I get?"        # dry run: prints the cost
make paid-ask AS=us-ic Q="How many days of PTO do I get?"   # spends: answers as the us-ic fixture user
make test
```

`make help` lists every target.

**Dry run vs paid:** `make ask`, `make embed`, `make eval`, `make permissions` and `make ann` are dry runs. They print what would run and an estimate, and spend nothing. Their `paid-` twins (`make paid-ask`, `make paid-eval`, …) take the same options and spend. Each paid run appends a line to `runs/spend.jsonl`. In Claude Code, a project hook asks for a human's approval before any `paid-` target runs ([spec 0009](specs/0009-paid-call-guardrails.md)).

## Project notes

[NOTES.md](NOTES.md) is the index of the project notes: decisions (ADRs), the dated journal, follow-ups, the reading log and weekly summaries. Work is spec-driven ([ADR-0009](docs/decisions/0009-spec-driven-workflow.md)). Each change starts as a spec in [specs/](specs/) with numbered acceptance criteria, and that spec is reviewed before the build starts.

## Troubleshooting

- **Cannot connect to the Docker API:** the Colima VM is down. Run `colima start`.
- **`type "vector" does not exist`:** the init SQL did not run. Colima only mounts `$HOME` into its VM, so clone the repo under `$HOME`, not `/tmp`. Init scripts also run only on a fresh volume, so for an existing one run `docker compose down -v` and then `make up`.
