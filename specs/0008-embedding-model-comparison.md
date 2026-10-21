# 0008: Embedding model comparison (week 2)

- Status: draft
- Date: 2026-10-21
- Depends on: 0006, eval set v1.2, baseline run `2026-10-19-d2625d91`, [prep journal, 20 Oct](../docs/journal/2026-10-20-embedding-comparison-prep.md)

## Problem

Every run so far has used `text-embedding-3-small`. Chunking work is closed: spec 0006 kept `fixed-512-64`, and the heading prefix tied. The embedding model is the next single change. On MTEB(eng, v2) retrieval, the candidates step up clearly over ours (3-small 53.5, 3-large 58.0, gemini-embedding-001 64.4, Qwen3-Embedding-8B 69.4; snapshot of 20 Oct). That gap is large enough to test on 32 rows, but leaderboard scores don't transfer to a corpus automatically, so we measure on ours.

Baseline: depth-20 retrieval-only run `2026-10-19-d2625d91` (`fixed-512-64`, 3-small, chunk_fact_recall@5 0.495 ± 0.081, n = 32, retrieved tokens@5 = 2,335).

The harness can't run this comparison today:
- `--baseline` requires `embed_model` to match, so any model change fails the check (run.py:148).
- A model name has no dimensions, and `EMBED_DIMS` expects 3,072 for 3-large.
- There is one price constant, 3-small's, used for every model's estimate.
- Embedder has no query/document distinction, so a model that needs one (Gemini `task_type`, the Qwen3 query instruction) would run handicapped.
- The query is never length-checked, and the token limit assumes OpenAI's 8,192.

Candidates, in order (Arun, 21 Oct):
1. **Must-do:** `text-embedding-3-large` at 1,536 dims. Same provider, key, adapter and tokenizer, so only the model changes.
2. **Stretch 1:** `Qwen3-Embedding-8B` through a hosted API, only if 3-large is decided by about 14:30.
3. **Stretch 2:** `gemini-embedding-001`, only if time remains after stretch 1.

## Acceptance criteria

**Model naming and dimensions**

- AC-1: **A model name can carry its dimensions.** The name format becomes `provider:model[@dims]`, stored as-is in `chunk_embeddings.model`.
  - With `@dims`, the adapter requests that output size and checks every vector against it.
  - Without it, the model's native size is expected (`EMBED_DIMS`), so `openai:text-embedding-3-small` and its 22,378 stored vectors keep their name and stay untouched.
  - A model that can't produce the requested size fails at construction, before any call.
- AC-2: **Every candidate runs at 1,536 dims:** `openai:text-embedding-3-large@1536`, `deepinfra:Qwen/Qwen3-Embedding-8B@1536`, `gemini:gemini-embedding-001@1536`. No schema change: the `vector` column is untyped and unindexed.

**Input types**

- AC-3: **Query and document inputs are distinct.** Embedder gains an input kind, `document` or `query`.
  - Embed always uses `document`. Eval retrieval uses `query`.
  - The mapping is per model:

    | model | document | query |
    |---|---|---|
    | OpenAI 3-small, 3-large | text as-is | text as-is |
    | Qwen3-Embedding-8B | text as-is | `"Instruct: Given a question about the GitLab handbook, retrieve the passages that answer it\nQuery:{q}"` (no space after `Query:`, per the model card) |
    | gemini-embedding-001 | `task_type=RETRIEVAL_DOCUMENT` | `task_type=RETRIEVAL_QUERY` |

  - The kind changes only what goes into the embedding call. The stored name, the stored content and the search SQL don't change.
  - `ask.py` is not changed (it is frozen). Eval passes retrieval an embedder built in `query` mode. Using a non-OpenAI model from `make ask` would need a query-mode embedder there too; it is in [follow-ups](../docs/follow-ups.md#from-the-spec-0008-review-2026-10-21), for an adopted model only.
  - Tests check the exact query string and task types sent for each model.

**Over-length input**

- AC-4: **The adapter fails on over-length input. It never truncates.**
  - Each model has a `max_input_tokens` limit in its own tokens: OpenAI 8,192; Qwen3-8B 32,768; Gemini 2,048.
  - Inputs are counted with cl100k. OpenAI models are checked against their limit exactly. Other models are checked against half their limit, for headroom between tokenizers (Gemini: 1,024 cl100k tokens; every `fixed-512-64` chunk is at most 512).
  - The check covers queries as well as documents, and the prefix tokens when a prefix config is embedded.
  - Truncation is turned off wherever the API exposes it (Gemini: `autoTruncate=false`). No adapter passes a truncation option.
  - An over-length input raises before any call and names the chunk_id or the query.

**Cost**

- AC-5: **Prices are per model.** One table in `constants.py` replaces `EST_EMBED_USD_PER_1M`, each entry citing its pricing page and the date it was checked. The embed and eval dry runs use the selected model's price. An unknown model fails the dry run instead of falling back to 3-small's price.

  Estimates for one `fixed-512-64` embed (10,457,284 cl100k tokens; other tokenizers will differ):

  | model | USD per 1M | full embed | source (fetched 2026-10-21) |
  |---|---|---|---|
  | text-embedding-3-large | 0.13 | ~$1.36 | developers.openai.com/api/docs/pricing |
  | Qwen3-Embedding-8B (DeepInfra) | 0.010 | ~$0.10 | deepinfra.com/Qwen/Qwen3-Embedding-8B |
  | gemini-embedding-001 | 0.15 (unconfirmed) | ~$1.57 | not on ai.google.dev/gemini-api/docs/pricing; launch blog only. See open question 2. |

  A prefix-arm embed adds the prefix tokens; the dry run reports the exact figure. Eval query embeds are under $0.01 per run.

**Comparison**

- AC-6: **`--baseline` allows exactly one change: the chunk config or the embed model, not both.** The check otherwise holds everything as spec 0006 AC-6 does. The report header says which one changed. A run that changes both fails the check before spending.
- AC-7: **The comparison reports the paired SE.** For each row, delta = this run's `chunk_fact_recall` at its matched k minus the baseline's at k = 5. The report gives the mean delta, the paired SE (sd of the deltas / √n) and their ratio, next to the existing spec 0006 AC-7 block. recall@5 and its delta are shown too.

**Runs and decision**

- AC-8: **Run plan.** Each paid step shows its dry-run cost and waits for Arun's `CONFIRM=1`.
  1. `make embed CONFIG=fixed-512-64 EMBED_MODEL=openai:text-embedding-3-large@1536` (~$1.36).
  2. Retrieval-only eval of `fixed-512-64` with 3-large at depth 20, `BASELINE=2026-10-19-d2625d91`.
  3. Decision per AC-9.
  4. Only for a model that is adopted under AC-9: embed `fixed-512-64-prefixed` with it and run it against that model's own `fixed-512-64` run (the chunk config is then the one change).
  5. Stretches repeat steps 1–3 per model, in order, each against `2026-10-19-d2625d91`.

  Frozen: `ask.py`, the answer model (gpt-5.4-mini), the prompt, eval set v1.2, corpus 5273b21, k = 5, `EVAL_DEPTH` 20, exact cosine search with no index. Runs are retrieval-only. Run metadata already records the corpus SHA, chunk config, models, prompt hash, eval-set version and harness commit; the model name now includes the dims.
- AC-9: **Decision rule, set before any run.**
  - Adopt a candidate only if its mean paired delta in `chunk_fact_recall` at the matched k (AC-7) exceeds 2 paired SEs. Otherwise the result is "no difference", and 3-small stays.
  - The matched k is spec 0006 AC-7's, against the baseline's 2,335 tokens@5. All candidates share the chunks, so it is expected to be 5.
  - If more than one candidate passes, adopt the one with the largest mean delta. A cheaper model that ties it stays a note in the ADR, not a second decision.
  - Adopting changes `DEFAULT_EMBED_MODEL` in a follow-up PR, after a full answer run. Neither is built here.
  - The decision goes into one ADR with the numbers, adopt or reject, plus the journal entry.

**Tests**

- AC-10: Unit tests, with no API calls, cover:
  - name parsing with and without `@dims`, and the dims check failing on a mismatch
  - the input-kind mapping for each model (AC-3)
  - over-length documents and queries raising before any call, with the half-limit for non-OpenAI models (AC-4)
  - the per-model price lookup, and an unknown model failing the dry run (AC-5)
  - the baseline check accepting a model-only change and a config-only change, and rejecting both at once (AC-6)
  - the paired delta and SE on fixed numbers (AC-7)

  Existing tests stay green, with the `embed_model` lock at tests/unit/test_eval_run.py:109 updated to AC-6. Ruff is clean. No new dependencies for 3-large or Qwen.

## Out of scope

- Changing `DEFAULT_EMBED_MODEL`, a full answer run, or `make ask` query mode for an adopted model (follow-ups)
- Other chunk configs, other dims, native dims (3,072 / 4,096)
- voyage-4-large, Qwen3-Embedding-0.6B locally, gemini-embedding-2
- HNSW or any ANN index; hybrid search; reranking
- Re-normalising vectors: the search uses cosine distance, which ignores vector length
- A paid probe of providers' undocumented over-length behaviour (AC-4 makes it moot)

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| Dimensions | 1,536 for every candidate: the same size as 3-small, so only the model changes. 3-large, Qwen3 and Gemini all support shortened outputs (AC-2). | **Native dims:** 3-large would change the model and the size at once. A plain `vector` HNSW index also stops at 2,000 dims (ADR-0004). Larger vectors can still be indexed (`halfvec` up to 4,000, subvector or binary-quantized indexes with re-ranking; [pgvector README](https://github.com/pgvector/pgvector)). Those options and a 3-large@3072 run are in [follow-ups](../docs/follow-ups.md#from-the-spec-0008-review-2026-10-21), for week 6. |
| Name carries dims | `provider:model@dims` | **A dims column:** a schema change and a new PK for the same separation. |
| Query mode without touching `ask.py` | Eval builds a query-mode embedder and passes it to `ask.retrieve` | **`ask.py` calls an `embed_query` method:** edits a frozen file. |
| Over-length for other tokenizers | cl100k count against half the model's limit, plus truncation off at the API | **Each model's own tokenizer:** a new dependency per model (transformers, google-genai) for a check that has 4× headroom today. |
| Qwen provider | DeepInfra: OpenAI-compatible, so the `openai` SDK with `base_url`; supports `dimensions`; $0.010 / 1M | **OpenRouter:** dims undocumented, and its docs say over-length is "truncated or rejected". **SiliconFlow:** no 1,536. **Fireworks:** 10× the price. **Alibaba text-embedding-v4:** not confirmed to be the open 8B model. |
| Decision threshold | > 2 paired SEs | **Larger of the two run SEs (spec 0006):** unpaired, so it ignores that both runs score the same rows. |
| Prefix arm | Only for an adopted model | Running it for every model loses only a model × prefix interaction that 32 rows can't detect (prep journal). |

## Open questions

1. **Qwen via DeepInfra:** needs a new `DEEPINFRA_API_KEY` in `.env`, no new dependency. Approve before the stretch is built?
2. ~~**Gemini model.**~~ Resolved 2026-10-21 (Arun): keep gemini-embedding-001, not gemini-embedding-2. Its price isn't on the official pricing page, so it must be confirmed in the console before the stretch's paid run.
3. **Gemini client:** calling it needs either the `google-genai` dependency or REST through a new HTTP client, plus a `GEMINI_API_KEY`. Decide only if stretch 2 is reached.

## Verification

- `make test` and `make lint` pass.
- Embed dry run for 3-large shows the AC-5 price; `CONFIRM=1` on approval. Afterwards, `chunk_embeddings` holds 22,378 rows for each of 3-small and 3-large@1536, and the 3-small count and a sample of its vectors are unchanged.
- The AC-8 eval run with `BASELINE=`, the AC-7 block in summary.md, and the AC-9 decision written up.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] docs updated: journal entry, an ADR for any decision, follow-ups
