# 0011: Hybrid search (Postgres FTS + dense, fused with RRF)

- Status: draft
- Date: 2026-10-29

## Problem

Retrieval is dense only. Dense search misses exact-term matches: acronyms, policy names and rare words (POSH, PTO, probation). Rows 65 and 92 have no required-fact chunk in the dense top 20 on run `2026-10-21-d83f3edc`. Five more (8, 49, 89, 53, 55) are retrieval-side false abstentions in the spec 0010 classification. Week 3's plan is to add a lexical list and fuse it with the dense list, then measure the result before anything changes in the answer path.

This adds the first new retrieval path since spec 0007. Leak stays at zero only if the new SQL carries the same ACL pre-filter, so the spec treats that as an AC with its own tests.

Postgres full-text search is not BM25. `ts_rank_cd` scores a chunk from its own text: term counts and proximity. It uses no corpus-wide statistics, so it has no IDF (PostgreSQL docs §12.3.3), and a common word like "team" weighs as much as a rare one like "POSH". This spec measures native FTS as the lexical list. A BM25 extension is a follow-up, depending on what the FTS-only diagnosis shows ([reading, week 3](../docs/reading/week-03.md#hybrid-search-postgres-full-text-search-reciprocal-rank-fusion)).

## Depends on / frozen inputs

| Input it fixes | Open decision that could change it | Handling |
|---|---|---|
| Embedding model: `openai:text-embedding-3-large@1536` | None in week 3 ([ADR-0022](../docs/decisions/0022-adopt-text-embedding-3-large-1536.md)) | **Frozen.** The dense list is today's `ask.search`, unchanged |
| Chunk config: `fixed-512-64` | None in week 3; the size and overlap sweep is week 4 | **Frozen.** Every new reader filters on `config_id` |
| Eval set v1.2 at corpus pin `5273b21` (`eval_sha256 995acb3b…`) | A v1.3 bump ([follow-ups](../docs/follow-ups.md)) | **Frozen for this spec's runs.** If v1.3 lands first, the runs wait or the spec is amended |
| Exact dense search (no ANN index) | None; HNSW stays a measurement copy (spec 0007 Part B) | **Frozen** |
| Answer model and prompt (`ask.py`, `prompts.py`) | None through week 3 | **Frozen.** Hybrid enters through retrieval only and is **off by default** until an ADR adopts it (AC-8) |
| Baseline run for the paired comparison | A new dense run, or a model or config change | **Decided:** `2026-10-21-d83f3edc` (retrieval-only, admin, `fixed-512-64`, 3-large@1536). The spec 0007 AC-9 regression shows the dense path still reproduces it exactly |
| RRF k = 60, per-list depth 50, equal list weights | None | **Decided before any run (Arun, 29 Oct), not tuned on v1.2.** With n = 32, tuning any of them on v1.2 would overfit. k = 60 is the paper's constant, fixed in a pilot and not tuned (Cormack et al. 2009). Depth 50 is chosen to be well beyond the scored depth of 20 |
| FTS query semantics: OR of the question's lexemes | None | **Decided (Arun, 29 Oct).** `websearch_to_tsquery` and `plainto_tsquery` AND every content word, and 18 of 33 answerable v1.2 questions match no chunk under AND (a match-count check; reading, Q1) |
| `ts_rank_cd` normalization 0 | None | **Decided (Arun, 29 Oct).** `fixed-512-64` chunks are near-equal in length (median 512 tokens; the 14.5% under 400 are page tails), so length normalization would mostly promote tails (reading, Q2) |
| Generated `tsvector` column | None | **Decided (Arun, 29 Oct).** It can't go stale, and it is correct for every config by construction (reading, Q4) |
| Tie-break | None | **Decided (Arun, 29 Oct):** RRF score, then dense rank (missing last), then `chunk_id` |

## Acceptance criteria

Each criterion is testable. Tests and plan steps cite them by ID.

**FTS**

- AC-1: **A generated `tsvector` column with a GIN index.**
  - `chunks.fts tsvector GENERATED ALWAYS AS (to_tsvector('english', content)) STORED`.
  - `CREATE INDEX … ON chunks USING gin (fts)`.
  - The DDL lives in `db/init/003_chunks.sql`. It is guarded and idempotent, like the `config_id` and `allowed_groups` blocks: it adds the column only when it is missing. It runs through docker init on fresh volumes and through the existing DDL re-run in `make chunk` on existing ones.
  - It uses the two-argument `to_tsvector('english', …)` everywhere, so the index doesn't depend on `default_text_search_config`.
  - No ingest or chunk code writes the column.
- AC-2: **The query is an OR of the question's lexemes.**
  - The `tsquery` is built in SQL from `to_tsvector('english', :q)`: its lexemes are joined with `|`, each quoted as a literal.
  - No search-box syntax: quotes, `or` and `-` in a question carry no operator meaning.
  - A question with no lexemes (only stop words or punctuation) yields an empty FTS list, never an error and never a match-everything query.
  - Unit tests cover:
    - "PTO - paid time off" gives no NOT operator.
    - "what is it?" gives an empty list.
    - A quote or apostrophe in the question can't break the SQL.
- AC-3: **FTS search ranks with `ts_rank_cd(fts, query)` and normalization 0.**
  - `ORDER BY` rank descending, then `chunk_id`.
  - It filters `c.config_id = %(config_id)s` and `c.fts @@ query`.
  - It returns the same `Retrieved` shape as the dense path, plus its rank.
  - The function signature requires a `Principal`.

**Permissions**

- AC-4: **The FTS path applies the ACL pre-filter before ranking.**
  - The statement includes `AND c.allowed_groups && %(groups)s::text[]` in its `WHERE` clause.
  - Spec 0007 AC-8's static test is extended: every SQL statement in `src/` that ranks chunks, by embedding distance or by `ts_rank_cd`, must include the predicate.
  - An integration test inserts or uses a restricted chunk whose text matches the query terms. Searching as a persona without access never returns it under `fts` or `hybrid`, at any depth. Searching as `admin` does return it, as a positive control.
  - A principal with no groups is an error (unchanged from spec 0007).

**Fusion**

- AC-5: **RRF over the dense and FTS lists.**
  - Each list is retrieved to depth `FUSION_DEPTH = 50` for the same principal and config.
  - The score is Σ 1/(`RRF_K` + rank) over the lists the chunk appears in, with `RRF_K = 60`, equal weights and 1-based ranks.
  - Sort order: score descending, then dense rank ascending (a chunk absent from the dense list sorts after any chunk the dense list found), then `chunk_id`.
  - The fused list is cut to the requested k: 5 for the scored top 5, 20 for the deep list.
  - Each fused result carries `dense_rank` and `fts_rank`, each `None` when absent from that list, plus `rrf_score`.
  - `RRF_K` and `FUSION_DEPTH` live in `constants.py`.
  - Unit tests on fixed lists check:
    - the arithmetic
    - both tie-break steps
    - a chunk in only one list
    - an empty FTS list (hybrid equals the dense order)
    - cutting to k

**Guards and defaults**

- AC-6: **A stale-FTS check, in `fts` and `hybrid` modes.**
  - Before any retrieval, the harness, the permissions runner and the search function's caller check the column. They refuse to run, with a message naming the fix, when:
    - the `chunks.fts` column or its GIN index is missing, or
    - the active config has chunks but none with a non-NULL `fts`.
  - This follows the stale-ACL pattern (spec 0007 AC-5). `dense` mode doesn't run the check.
- AC-7: **The dense path is unchanged.**
  - `ask.search`, `ask.retrieve` and `ask.ask` keep their SQL and behaviour.
  - Spec 0007 AC-9's regression still holds: a dense retrieval-only run as `admin` reproduces `d83f3edc`'s top 5 on all 33 answerable rows, in order.
- AC-8: **Hybrid is off by default.**
  - The eval harness and the permissions runner take `--retriever dense|fts|hybrid`, exposed as `RETRIEVER=` on `make eval`, `make paid-eval`, `make permissions` and `make paid-permissions`.
  - The default is `dense`.
  - `ask.py` and `make ask` are unchanged and stay dense. Adoption into the answer path needs an ADR and its own change.

**Harness and reporting**

- AC-9: **Run metadata and rows record the retriever.**
  - The run's metadata includes:
    - `retriever`
    - for `hybrid`, `rrf_k` and `fusion_depth`
    - the FTS settings: config `english`, normalization 0, OR semantics
  - Runs without the key (all existing runs) read as `dense`.
  - Each retrieved entry in `rows.jsonl` carries `dense_rank` and `fts_rank` (hybrid), or its list's rank (fts).
  - Each row records `fts_query_empty` in `fts` and `hybrid` modes.
  - Metrics, their definitions and @1/3/5/10/20 are unchanged.
  - In `fts` mode, no question is embedded and the estimate shows $0.
- AC-10: **Baseline comparison across retriever modes.**
  - `BASELINE=<run id>` accepts a run that differs only in `retriever`, and reports `retriever` as the one change (spec 0008 AC-6 pattern).
  - A run that changes the retriever together with the config or the embedding model is refused as two changes at once.
- AC-11: **The permissions suite on the hybrid path.**
  - `make paid-permissions RETRIEVER=hybrid` scores permissions-v1 as today: leak, over-block and authorized recall at k = 5 and 20.
  - Its metadata includes `retriever`.

## Out of scope

- BM25, by extension (`pg_search`, `pg_textsearch`, VectorChord-bm25) or by `sparsevec` weights. This is a follow-up, depending on the FTS-only diagnosis.
- Weighted RRF, convex score combination, or tuning k or depth. Any of them needs tuning data beyond v1.2's 32 rows; a follow-up after the synthetic retrieval set.
- Weighting the heading above the body (`setweight`), other text-search configs, or synonym and abbreviation dictionaries.
- Hybrid search in `ask.py` and the answer path (AC-8). It enters only by ADR.
- Cross-encoder reranking (spec 0012).
- HNSW on the dense list (dense stays exact).

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| Lexical retriever | Postgres native FTS (`tsvector`, GIN, `ts_rank_cd`) | **A BM25 extension:** IDF and term-frequency saturation, but a new dependency, a DB image change and `shared_preload_libraries`; deferred until FTS is measured. **`sparsevec` BM25 weights:** needs a weighting pipeline we would build |
| Query parsing | OR of the question's lexemes | **`websearch_to_tsquery` / `plainto_tsquery`:** AND every content word, and 18 of 33 answerable v1.2 questions match nothing. A spaced " - " becomes NOT. **`to_tsquery`:** errors on raw text. **A share of words required (`minimum_should_match`-style):** a new constant we can't tune. **A `plainto_tsquery` fallback on empty:** it comes out empty in exactly the same cases, so it never helps |
| Ranking | `ts_rank_cd`, normalization 0 | **`ts_rank`:** no proximity. **Options 1, 2, 8, 16:** length normalization on near-equal chunks mostly promotes page tails. **Option 4:** a second proximity term, unjustified. **Option 32:** cosmetic, and RRF ignores scores |
| `tsvector` storage | Stored generated column | **Script-filled column:** can go stale or NULL and needs ingest changes. **Expression index only:** queries must repeat the expression, and `ts_rank_cd` re-parses each matched chunk |
| Fusion | RRF, k = 60, equal weights, depth 50 | **Weighted RRF, convex combination:** tuned weights would overfit n = 32. **CombSUM, CombMNZ:** need score normalization. **Learning to rank:** needs training data we don't have |
| Tie-break | Score, then dense rank, then `chunk_id` | **`chunk_id` only:** deterministic but arbitrary at the top-5 boundary. Dense is the stronger list on v1.2 |
| Default | Off (`dense`) | **On:** it would change the frozen answer path before measurement |

## Open questions

- **The abbreviation probe.** Does "paid time off" retrieve what "PTO" does? Proposed: report FTS-only lists for both phrasings (free, from the same query builder via `make db-shell`). For dense and hybrid, read the existing v1.2 rows that use "PTO" (46, 100). No new CLI.

## Evaluation plan (runs Fri 30 Oct AM, each with Arun's session approval)

All runs are retrieval-only, as `admin`, on `fixed-512-64`, eval v1.2.

1. **Hybrid vs `d83f3edc`, paired by row:** `make paid-eval RETRIEVAL_ONLY=1 RETRIEVER=hybrid BASELINE=2026-10-21-d83f3edc`.
   - **Decision rule, set before the run:** the week 2 rule ([ADR-0022](../docs/decisions/0022-adopt-text-embedding-3-large-1536.md)). Adopt only if the mean paired delta in `chunk_fact_recall@5` exceeds 2 paired SEs (sd of per-row deltas / √n). At n = 32 that bar is about +0.08.
   - Report @1/3/5/10/20, rows won, lost and tied, and retrieved tokens@5.
   - Adoption is by ADR; no adoption follows from this spec alone.
2. **FTS-only, for diagnosis:** `make paid-eval RETRIEVAL_ONLY=1 RETRIEVER=fts BASELINE=2026-10-21-d83f3edc`. No adoption decision rests on it. Report whether common words crowd out rare ones; this is the IDF gap.
3. **Targeted table for rows 8, 49, 89, 53, 55, 65, 92.** For each required fact, give its rank under dense, fts and hybrid (from the three runs' `rows.jsonl`; "–" beyond 20). For hybrid chunks, add `dense_rank` and `fts_rank`.
   - Note whether 65 and 92 appear via FTS.
   - **Prediction, written before the run:** with two lists at depth 50 and k = 60, any chunk found by both lists outranks every chunk found by only one (2/110 > 1/61). So an FTS-only find reaches the fused top 5 only when fewer than five chunks are in both lists.
4. **Abbreviation probe:** per the open question. Reported as a finding, not a metric.
5. **Permissions on the hybrid path:** `make paid-permissions RETRIEVER=hybrid`. Leak and over-block must stay 0 at k = 5 and 20; report authorized recall (n shown) against run `2026-10-24-086eca8a`.
6. **Cost (dry-runs on 29 Oct):**
   - hybrid eval: about $0.0001 (868 query tokens)
   - fts eval: $0 (no embeds)
   - hybrid permissions: about $0.00007 (509 tokens, 29 unique questions)
   - Query embeds only; FTS costs nothing.

## Verification

- Unit (in memory, no API):
  - query construction and its edge cases (AC-2)
  - RRF arithmetic and tie-breaks (AC-5)
  - mode defaults (AC-8)
  - metadata, and the baseline rules across modes (AC-9, AC-10)
  - the extended static ACL-predicate test (AC-4)
- Integration (DB):
  - the column, the index and idempotent DDL (AC-1)
  - FTS ordering and config scoping (AC-3)
  - restricted-chunk denial and the admin control under `fts` and `hybrid` (AC-4)
  - stale-FTS refusals (AC-6)
  - the dense path unchanged (AC-7)
- Free checks:
  - `make eval RETRIEVAL_ONLY=1 RETRIEVER=hybrid` and `RETRIEVER=fts` dry-runs show the estimate and the mode.
  - `make permissions RETRIEVER=hybrid` likewise.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] docs updated: journal entry, an ADR for any decision, follow-ups

## References

- [Reading log, week 3: hybrid search](../docs/reading/week-03.md#hybrid-search-postgres-full-text-search-reciprocal-rank-fusion)
- [Spec 0007: permission-aware retrieval](0007-permission-aware-retrieval.md) (AC-5, AC-8, AC-9)
- [Spec 0010: answer evaluation](0010-answer-evaluation.md) (the retrieval-side false abstentions)
- [ADR-0022](../docs/decisions/0022-adopt-text-embedding-3-large-1536.md) (the decision rule)
