# 2026-10-29: hybrid search build, spec 0011

Builds [spec 0011](../../specs/0011-hybrid-search.md): an FTS list (`ts_rank_cd` over a generated `tsvector` column), RRF fusion with the dense list, and `--retriever dense|fts|hybrid` on the eval harness and the permissions runner. The default is `dense`, and `ask.py` is unchanged. No paid calls; the measurement runs are on 30 Oct.

## Build
- **Migration:** `make chunk` re-ran `db/init/003_chunks.sql` before its early exit. That added `chunks.fts` and `chunks_fts_idx` across all 146,715 rows (5 configs) in about 30 s, a one-time table rewrite. Every row has a non-NULL `fts`.
- **Code:**
  - `hybrid.py` sits beside `ask.py`, so the dense path stays byte-identical (AC-7).
  - `hybrid.Ranked` subclasses `ask.Retrieved`, adding `dense_rank`, `fts_rank`, `rrf_score` and `fts_score`. Dense runs return plain `Retrieved`, so their rows keep their old shape.
- **Full mode:** fts and hybrid require `--retrieval-only`. A run with an answerer and a non-dense retriever is refused, both in `main` and in `run()` (AC-8).
- **AC-2 test placement:** the spec lists AC-2's cases as unit tests, but the `tsquery` is built by Postgres, so those cases run as integration tests. A unit test pins the SQL text: no `websearch_`, `plainto_` or `to_tsquery(` parsers, and the `quote_literal` builder is present. Arun approved this at the plan gate.
- **Static ACL test (AC-4):**
  - It now also flags `ts_rank`, using `(?<![a-z_])` so that the `fts_rank` field name doesn't match.
  - It only checks literals that contain `SELECT`, because a docstring mentions `ts_rank_cd`.
- **Dry runs (free):**
  - The hybrid eval and fts eval estimates match the spec: $0.0001 (868 tokens) and $0.
  - The hybrid permissions run estimates $0.000066 (509 tokens).
  - The baseline `2026-10-21-d83f3edc` is accepted as a retriever-only change.

## AC-7 check without spend
- **Method:** `ask.search` as admin, using the saved 3-large query vectors (`runs/ann/query-vectors.jsonl`), compared with the top 5 of `d83f3edc`.
- **Result:** 31 of 33 rows are identical. Rows 32 and 93 differ by the same near-tie swaps recorded on 24 Oct ([Part B](2026-10-24-part-b.md)). The saved vectors were re-embedded, which moves distances by about 1e-4. The dense SQL and `ask.py` are unchanged.
- **Status:** the exact AC-9 reproduction needs the original query embeddings, so it remains a paid dense re-run.

## Review catches (`/code-review`)
Ten findings: one must-fix (fixed), five lower-priority fixed, three skipped with reasons, one rejected.
- **Must-fix (provenance):** a hybrid row whose dense list came back empty (no embeddings for the model on that config) became an FTS-only list labelled `hybrid`. The run only stopped when the fused list was empty. Now it also stops when no chunk in the list has a `dense_rank`. A regression test fails without the fix.
- **Fixed, lower priority:**
  - **Embed model as a change axis:** fts runs counted `embed_model` as one, although fts never embeds. An fts run against a dense baseline would have been refused as two changes whenever the embed spec differed.
  - **fts mode prepared and tokenized every question,** so an embedding-limit error could abort a run that embeds nothing.
  - **Static ACL scan:** the AST scan sees f-strings as fragments, so it could miss a ranking query built with interpolation. A second test now imports every module and scans its evaluated module-level strings, and it must find `hybrid.FTS_SEARCH`.
  - **Missing retriever key:** a baseline without one now reads as the literal `dense`, not `DEFAULT_RETRIEVER`. Adopting hybrid as the default later can't relabel old runs.
  - **A comment** misstated where the stale-FTS check runs.
- **Skipped:**
  - **Two embeds per hybrid row:** planned; it mirrors the dense harness and costs about $0.0001.
  - **Sharing the query-embed step with `ask.retrieve`:** it would mean editing `ask.py`, which AC-7 freezes.
  - **One extra `query_empty` query per row:** 33 cheap queries, and keeping it separate is clearer.
- **Rejected:** "the no-`fts` branch of `check_fts` can never fire". It fires when `fts` is a plain column; the AC-6 test shows this, and the spec requires the check.

## Clean room
- **Setup:** a fresh clone under `$HOME` with its own DB on port 5434 and the pinned corpus linked. Then ingest, chunk all five configs and `make acl`.
- **Fresh volume:** docker init created `chunks.fts` and its index, and the stale-FTS check passed on the fts dry run.
- **Result:** 681 unit and 98 integration tests passed, and lint is clean, the same as the working copy.

## Limitations
- **The IDF gap shows up:** in a local FTS-only probe, common words ("day", "get") outranked the rare term in "How many PTO days do I get?". The spec expected this (no IDF in `ts_rank_cd`). BM25 is a follow-up.
- **Hybrid embeds each answerable question twice.** The k = 5 call and the depth-20 call each fuse the same depth-50 lists. This mirrors the dense harness and costs about $0.0001 more per run.
