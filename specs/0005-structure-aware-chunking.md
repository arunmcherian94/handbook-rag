# 0005: Structure-aware chunking (week 2, first chunking run)

- Status: implemented
- Date: 2026-10-19
- Depends on: 0003, 0004, eval set v1.2, baseline run `2026-10-17-3748df5b`

## Problem

The baseline (spec 0003) cuts fixed 512-token windows with 64 overlap, blind to the Markdown structure. Run `2026-10-17-3748df5b` shows retrieval finds the right page far more often than the right chunk: page_hit@5 0.812 vs chunk_hit@5 0.594. Seven rows (52, 53, 8, 10, 99, 38, 89) hit the page with no relevant chunk, and synthesis rows score chunk_all_required@5 0.00. One known cause is chunks that span sections and are cited by their start heading only. This spec adds a structure-aware chunker and measures it against the baseline, with the baseline kept intact and reproducible ([ADR-0019](../docs/decisions/0019-structural-first-recursive-inside-chunking.md), [ADR-0020](../docs/decisions/0020-chunk-configs-coexist.md)).

Section profile at the pin (cl100k_base, text from one heading to the next): 52,787 sections; p50 111 tokens, p90 383, p99 1,059. 31% are under 64 tokens; 6% are over 512 and hold 28% of all tokens. So this chunker makes more, smaller chunks than the baseline, and retrieved tokens@5 will drop. That is part of the change being measured, and the report shows it next to recall.

## Acceptance criteria

**Configs coexist**

- AC-1: **Config registry.** A `chunk_configs` table (config_id PK, strategy, params jsonb, tokenizer, created_at) records every config. Configs are defined in code; the first chunk run of a config inserts its row, and later runs fail if the stored params differ from the code's. Two configs: `fixed-512-64` (the baseline, params `{size: 512, overlap: 64}`) and `structural-v1` (params `{max_tokens: 512, overlap: 64, min_tokens: 64}`). Tokenizer cl100k_base for both.
- AC-2: **Every chunk row carries a config.** `chunks` gains `config_id` (NOT NULL, FK to `chunk_configs`), `heading_path text[]`, `line_start int`, `line_end int`. The migration backfills existing rows as `fixed-512-64` with the new columns NULL, and is idempotent (`db/init` DDL re-run by `make chunk`).
- AC-3: **The baseline stays byte-identical.** Chunking `structural-v1` leaves every `fixed-512-64` chunk row, chunk_id and embedding unchanged. `make chunk` takes `CONFIG=` (default `fixed-512-64`); its early-exit check and its delete of stale rows are scoped to that config. Baseline chunk_ids keep their current formula.
- AC-4: **Everything that reads chunks is scoped to one config:** `make embed CONFIG=` embeds only that config's chunks; the eval run takes `CONFIG=` (default `fixed-512-64`), checks that config's stored params and corpus SHA, and fails if the config has no chunks or no embeddings for the model; the evidence check reads only that config's chunks; retrieval (`ask.retrieve`, `SEARCH`) adds `AND c.config_id = %(config_id)s`, with the baseline as the default. This one `WHERE` clause and parameter is the only change to `ask.py`; the answer model and prompt are untouched (see Open questions).
- AC-5: **Baseline reproducible.** `make eval CONFIG=fixed-512-64 RETRIEVAL_ONLY=1` after this change reproduces the committed retrieval metrics of `2026-10-17-3748df5b`. Any row whose metrics differ is listed with its retrieved chunk ids (embedding API nondeterminism can flip near-ties); a difference with no such cause is a bug.

**Structure-aware chunker (`structural-v1`)**

- AC-6: **Headings are hard boundaries.** Every ATX heading outside a fenced code block (the existing `find_headings` rule) starts a new section, at every level. No chunk and no overlap crosses a heading, except through the tiny-section merge in AC-8. Text before the first heading is its own section with an empty heading path.
- AC-7: **Over-max sections split recursively.** A section over `max_tokens` is cut at the coarsest separator that fits: paragraph (blank line), then sentence, then token. Pieces are packed in order up to `max_tokens`. Consecutive sub-chunks of one section overlap by `overlap` tokens; there is no overlap between sections. A fenced code block is one paragraph and is cut only if it alone exceeds `max_tokens`.
- AC-8: **Tiny sections merge only with siblings.** A section under `min_tokens` merges with the adjacent following (else preceding) sections that share its parent heading and level, while the result stays at or under `max_tokens`. It never merges with its parent's text, a child, or a section under another parent. A section with no eligible sibling stays a small chunk. A merged chunk records every heading it covers.
- AC-9: **Chunk metadata.** Each chunk stores:
  - `content`: the exact source text of its span, as in spec 0003
  - `heading`: the first heading it covers (what citations show today)
  - `heading_path`: the full path from the top-level heading down to that heading, for example `{"4. PROCEDURES", "4.1 TRAVEL RELATED EXPENSES", "Airfare"}`; for a merged chunk, the path of the first section plus every merged sibling's heading
  - `line_start`, `line_end`: 1-based, inclusive line numbers in the source file at the pin, counting the front matter that ingest strips, so they line up with eval-set citations
  - `token_count` in cl100k_base
- AC-10: **Edge lines of a line-aligned chunk count as whole.** The relevance rule (spec 0004, AC-2) treats a chunk's first and last lines as possible fragments because token windows cut mid-line. For a chunk with `line_start` set, an edge line counts as whole when it equals the full source line at that line number. Without this, a short cited line right under a heading (for example `##### France`) could never match, since no overlapping neighbour holds it. Baseline chunks have NULL line ranges and keep today's rule, so their scores are unchanged (AC-5 proves it).

**Experiment rules**

- AC-11: **One change per run.** The `structural-v1` run differs from the baseline only in the chunk config: same corpus SHA (5273b21), eval set v1.2, embed model, answer model, prompt, k = 5, and exact search (no ANN index).
- AC-12: **Run metadata** (spec 0004, AC-6) adds `config_id` and the config's params from `chunk_configs`. Every run records corpus SHA, config, eval-set version and hash, and harness commit.
- AC-13: **Cost guard.** `make embed CONFIG=structural-v1` prints the chunk count and estimated cost before spending and spends only with `CONFIRM=1`. `make eval` keeps its dry run (spec 0004, AC-8).

**Run report**

- AC-14: **Comparison against the baseline.** `make eval ... BASELINE=2026-10-17-3748df5b` adds to `summary.md`:
  - every metric in the baseline summary, with ± SE and n, for both runs and the delta
  - retrieved tokens@k for both runs next to recall
  - a per-row table for the right-page-wrong-chunk rows (52, 53, 8, 10, 99, 38, 89) and the synthesis rows: for each run, chunk_fact_recall@5, chunk_hit@5, page_hit@5, and the rank and heading path of the best relevant chunk
  The baseline side is read from the baseline's `rows.jsonl`; if it is missing (a fresh clone), the report says to re-run the baseline retrieval-only (AC-5) first.

**Tests**

- AC-15: Unit tests, all on in-memory text, no API calls:
  - line ranges are correct on a real handbook file with nested headings and front matter (each chunk's `content` equals the file's lines `line_start..line_end`, allowing for a cut first or last line in a token-split sub-chunk)
  - `finance/expenses.md`'s two `### 4.1` headings (lines 103 and 346) give separate sections with distinct line ranges and correct heading paths
  - an over-max section splits recursively, sub-chunks overlap, and no overlap crosses into the next heading's section
  - a tiny section merges only with siblings under the same parent and records every heading it covers; one with no sibling stays alone
  - AC-10 on line-aligned and non-aligned chunks, and the baseline rule unchanged for NULL line ranges
  - config scoping: chunking one config leaves another's rows untouched; param drift for an existing config_id fails
  Integration tests cover the migration and AC-3/AC-4 against the DB. Existing tests stay green; ruff is clean.

## Later runs (listed, not built here)

Each is one change against the `structural-v1` run:

1. **Size sweep:** `max_tokens` 256 and 1024.
2. **Min-size sweep:** `min_tokens` 0, 32, 128.
3. **Overlap sweep:** 0, 32, 100 within sections.
4. **Title-chain prefix:** prepend the heading path to the text that is embedded; stored `content` and line ranges stay unchanged, so fact-recall scoring is unaffected. Planned storage: `chunk_embeddings.embed_input` (`'content'` default, `'title-chain'`), PK `(chunk_id, model, embed_input)` ([ADR-0020](../docs/decisions/0020-chunk-configs-coexist.md)).

## Considered, not planned

- **Recursive-only chunking:** packs small sections together across headings, which is the baseline's known cross-section limitation in a neater form.
- **Pure semantic chunking:** the corpus has heading structure, so boundaries come free; embedding every sentence adds cost for no new signal. Revisit only if structure-aware leaves the right-page-wrong-chunk rows unfixed.
- **A table per config, or partitioning:** physical separation is cleaner once an ANN index exists (a typed `vector(n)` and an HNSW index per partition). With exact search, one table and a tested `config_id` filter is simpler. `config_id` is the partition key we would use later ([ADR-0020](../docs/decisions/0020-chunk-configs-coexist.md)).

## Out of scope

- the sweeps and the title-chain run above; `embed_input`
- embedding model comparison, ACLs, contextual retrieval, hybrid search, reranking
- any ANN index; partitioning
- changes to the answer model, prompt, k, or eval rows
- deleting old configs

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| Strategy | Structural first, recursive inside ([ADR-0019](../docs/decisions/0019-structural-first-recursive-inside-chunking.md)) | Recursive-only, semantic: see above. |
| Params | max 512, overlap 64 (as the baseline); min 64 | **Other max/overlap:** would make two changes at once. Min 64: 31% of sections are under it; swept later. |
| Config storage | `chunk_configs` table + `chunks.config_id` ([ADR-0020](../docs/decisions/0020-chunk-configs-coexist.md)) | **Dict in code only:** editing params under an existing id silently mislabels rows. **Table per config:** dynamic SQL in five places for no benefit under exact search. |
| Line ranges | Stored per chunk, file line numbers | **Derived at eval time:** the chunker already knows them; storing them makes AC-10 a lookup. |
| Baseline comparison | Read the baseline's `rows.jsonl`, re-run retrieval-only if missing | **Commit rows.jsonl:** runs stay out of git (spec 0004). |

## Open questions

1. ~~**ask.py freeze (AC-4).**~~ Resolved 2026-10-19 (Arun): approved. The one `WHERE` clause and defaulted `config_id` parameter in `retrieve` change retrieval scoping only; the answer model and prompt stay frozen.
2. ~~**Run mode for the first `structural-v1` run.**~~ Resolved 2026-10-19 (Arun): full run, answers included (about $0.21), so every baseline metric has a comparison.
3. ~~**arXiv 2608.00824 (title-chain prefixes).**~~ Resolved 2026-10-19 (Arun read the abstract): no change. The title-chain run stays as planned ([reading, week 2](../docs/reading/week-02.md)).

## Verification

- `make chunk CONFIG=structural-v1`, then `make embed CONFIG=structural-v1` (dry run, then `CONFIRM=1` on approval).
- AC-5: `make eval CONFIG=fixed-512-64 RETRIEVAL_ONLY=1 CONFIRM=1` reproduces the baseline retrieval numbers.
- `make eval CONFIG=structural-v1 BASELINE=2026-10-17-3748df5b` dry run; the paid run only on Arun's `CONFIRM=1`.
- Spot-check 3 structural chunks from `finance/expenses.md` by hand against the file's lines.
- `make test` and `make lint` pass.

Before the implementation PR:

- [x] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [x] docs updated: journal entry, an ADR for any decision, follow-ups
