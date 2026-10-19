# 0006: Packed sections, heading-path prefix, deeper top-K (week 2, final chunking iteration)

- Status: implemented
- Date: 2026-10-19
- Depends on: 0005, eval set v1.2, baseline run `2026-10-17-3748df5b`, run `2026-10-19-62a52a83`

## Problem

`structural-v1` (spec 0005) lost to the baseline: chunk_fact_recall@5 fell from 0.495 to 0.358. A query-time preview ([journal, 19 Oct](../docs/journal/2026-10-19-chunker-build.md)) found three things:

- **Most of the gap is the token budget.** At k=5, structural-v1 hands over 815 tokens against the baseline's 2,335. Scored over the same 2,335 tokens from a top-20 list, the gap shrinks from −0.137 to −0.037.
- **Short sections cause the rest.** The median chunk is 154 tokens, and most of them are short sections: a heading plus a line or two. A short section whose heading matches the question's wording outranks the adjacent section that holds the fact. A 512-token window carries both, so the baseline gets them (rows 11, 49, 88, 100).
- **Heading-only chunks are a minor factor.** Excluding them moves recall@5 only to 0.374.

Two more problems follow from this:

- **Recall at a fixed k mixes boundary quality with chunk size.** Smaller chunks need a larger k to give the model the same amount of text. Without a token-matched comparison, a better boundary rule can still lose.
- **Short chunks look alike.** The embedded text is the section body only, so ten entity pages each give an identical-looking "Time Off Policies" chunk.

This spec runs the final chunking iteration under the stop rule. Each run changes one thing:
- `structural-v2` packs sections up to the baseline's size, changing boundaries only.
- `structural-v3` is v2 plus a heading-path prefix in the embedded text.
- `fixed-512-64-prefixed` is the baseline plus the same prefix, so the prefix's effect is measured apart from the chunking.

The decision is made on fact recall at a token-matched k. If a config is kept, it would be deployed by raising K, not by switching to a token budget.

Profile at the pin (simulated, cl100k_base):
- Packing whole sections in document order up to 512 tokens gives about 18,700 packed chunks: p50 392 tokens, p10 170.
- 2,947 sections over 512 are split as in spec 0005. That is about 25k chunks in all, against the baseline's 22,378.
- Packing only up to 400 tokens gives p50 312.

## Acceptance criteria

**Configs**

- AC-1: **Three new configs** are registered as in spec 0005 AC-1. Each has its own chunk rows: chunk_ids are `uuid5(doc_id:config_id:i)`, and line ranges are stored when the chunker produces them.

  | config_id | strategy | params |
  |---|---|---|
  | `structural-v2` | `structural-packed` | `{max_tokens: 512, overlap: 64}` |
  | `structural-v3` | `structural-packed` | `{max_tokens: 512, overlap: 64, embed_prefix: "title-path"}` |
  | `fixed-512-64-prefixed` | `fixed` | `{size: 512, overlap: 64, embed_prefix: "title-path"}` |

  - `structural-v3` has the same chunk content and line ranges as `structural-v2`.
  - `fixed-512-64-prefixed` has the same chunk content as `fixed-512-64`.
  - Tests assert both.
- AC-2: **Existing configs are untouched.** Chunking the new configs leaves every `fixed-512-64` and `structural-v1` row, chunk_id and embedding unchanged. The baseline fingerprint stays at 22,378 chunks, `a74cd032…`.

**Packed sections (`structural-v2`, `structural-v3`)**

- AC-3: **Sections pack up to max_tokens.**
  - Sections are cut at headings exactly as in spec 0005 AC-6, preamble included.
  - Within a document, consecutive sections are packed greedily in document order while the packed span stays at or under `max_tokens`. Any heading level can be packed with any other: parent, child or sibling.
  - A section over `max_tokens` closes the current pack and is split on its own, as in spec 0005 AC-7 (paragraph, then sentence, then token, with overlap inside that section only).
  - No chunk crosses a document. There is no overlap between packs.
- AC-4: **Metadata:**
  - `content` is the exact source span.
  - `heading` and `heading_path` are those of the first section in the chunk, and the path is a real path (it no longer appends merged siblings, as AC-9 of spec 0005 did).
  - `line_start` and `line_end` are as in spec 0005 AC-9.
  - `token_count` is unchanged.
  - For `fixed-512-64-prefixed`, `heading_path` is the path of the heading in force at the chunk's first byte (empty before the first heading), and line ranges stay NULL, as for the baseline.

**Heading-path prefix (`structural-v3`, `fixed-512-64-prefixed`)**

- AC-5: **The prefix goes into the embedded text only.**
  - For a config with `embed_prefix: "title-path"`, the text sent to the embedding model is `"{documents.title}\n{' > '.join(heading_path)}\n\n{content}"`. The path line is omitted when the path is empty.
  - Stored `content` is unchanged, so the relevance rule, the line ranges and the answer prompt see exactly the text they see today. `ask.py` is not changed.
  - Embed's md5 guard stays on `content`.
  - The embed cost estimate counts the prefix tokens.

**Deeper top-K**

- AC-6: **The eval scores every answerable row to depth 20.**
  - For every answerable row, the run also retrieves the top `EVAL_DEPTH = 20` chunks: one extra `ask.retrieve` call from `evaluation/run.py`, which costs one more query embedding per row. In full mode, `ask.ask` is called exactly as today with k = 5. The answer path doesn't change.
  - `EVAL_KS` grows from (1, 3, 5) to (1, 3, 5, 10, 20). Every at-k retrieval metric, including `retrieved_tokens@k`, is reported at each cut-off, computed on the depth-20 list. The 5-chunk metrics must equal those computed from the k=5 list.
  - The record stores the depth-20 list (rank, chunk_id, tokens, facts).
  - If the deep list's top 5 ids differ from the k=5 list, the row is listed in summary.md (a near-tie). This does not fail the run.
  - Run metadata records `EVAL_DEPTH`.
  - The `--baseline` compatibility check (spec 0005 AC-11) also requires `EVAL_DEPTH` to match.
- AC-7: **Token-matched k in the comparison report.**
  - The matched k of a run is the k in 1..20 whose mean `retrieved_tokens@k` over the answerable rows is closest to the baseline run's mean `retrieved_tokens@5`. Ties go to the smaller k.
  - The summary records `matched_k` and the run's overall `chunk_fact_recall`, `chunk_hit` and `page_hit` at that k, with ± SE.
  - The spec 0005 AC-14 table adds a block for the matched k: the baseline at k=5 against this run at its matched k, with the tokens for each, next to recall@5.
  - The per-row table adds `chunk_fact_recall` at the matched k for each run.
  - The per-row rows are COMPARE_ROWS, the synthesis rows, and the structural-v1 regressions (11, 34, 44, 49, 51, 58, 88, 100).

**Runs and decision**

- AC-8: **Run plan.** Each step is gated on Arun's `CONFIRM=1`. Estimates come from the dry runs.
  1. `make chunk` for the three configs (free).
  2. `make embed` for each: about 25k chunks for each structural config and 22,378 for the prefixed baseline, about $0.6 for all three.
  3. A retrieval-only run of `fixed-512-64` at depth 20, the new baseline for comparisons. Its top 5 must match `3748df5b` on all 33 rows (spec 0005 AC-5).
  4. Retrieval-only runs of `structural-v1`, `structural-v2`, `structural-v3` and `fixed-512-64-prefixed`, each with `BASELINE=` the step-3 run. About $0.001 in all.
  5. A full answer run for the winner, today, if it isn't `fixed-512-64`. About $0.21. It reports answer metrics at k = 5, the frozen answer path.

  Every other run setting is as in spec 0005 AC-11: corpus 5273b21, eval v1.2, embed model, answer model, prompt, k = 5, exact search.
- AC-9: **Decision rule (the stop rule), applied to step 4:**
  - Boundaries: compare `structural-v2` against `fixed-512-64`.
  - Prefix: compare `fixed-512-64-prefixed` against `fixed-512-64`.
  - Both together: compare `structural-v3` against `fixed-512-64-prefixed`.
  - The primary metric is `chunk_fact_recall` at each run's matched k (AC-7). The comparator is the baseline-side run at its own matched k: k=5 for `fixed-512-64`, and its matched k for `fixed-512-64-prefixed`. A change counts only if its delta exceeds the larger of the two runs' SEs. Otherwise it is "no difference".
  - If no structural config beats its fixed counterpart, keep fixed-512 chunking and write the negative result into ADR-0019. The prefix is decided separately, on its own comparison.
  - recall@5 is reported next to every comparison, because it is what users get while k stays frozen. If the winner's matched k isn't 5, using it means raising K for that config. That's a week-4 change, after the freeze, recorded in follow-ups and not built here.
  - The result goes into an ADR (a new one, or an ADR-0019 update), the journal and the run takeaways. Arun writes the takeaways.

**Cost guard and tests**

- AC-10: `make embed` and `make eval` keep their dry runs (spec 0005 AC-13). The embed estimate counts prefix tokens.
- AC-11: Unit tests run on in-memory text, with no API calls:
  - packing:
    - parent, child and sibling sections pack together up to `max_tokens`
    - an over-max section closes the pack and splits with overlap only inside itself
    - no chunk crosses a document
    - each chunk's content equals the file lines `line_start..line_end` on a real handbook file with front matter and nested headings
    - `heading_path` is the first section's path
  - the prefixed configs' content and line ranges equal their source configs' (`structural-v3` = `structural-v2`; `fixed-512-64-prefixed` = the baseline)
  - the prefix string, including the empty-path case. Embed sends the prefixed text and stores the md5 of `content`.
  - the fixed chunks' heading_path at the first byte
  - deeper top-K:
    - metrics at k = 10 and 20 from the depth-20 list; the k ≤ 5 metrics equal those from the k=5 list
    - matched k: the closest mean tokens, ties to the smaller k
    - the near-tie listing
    - the compatibility check failing on an `EVAL_DEPTH` mismatch
  - Integration tests cover AC-2 against the DB and retrieval scoping for the new configs. Existing tests stay green and ruff is clean.

## Out of scope

- size, overlap and min-size sweeps (dropped under the stop rule)
- changing k or the retrieval rule in `ask.py`: k stays 5, and the answer model and prompt stay frozen through week 3. A larger K for a kept config is week 4.
- token-budget retrieval (Arun, 19 Oct: deploy with top-K and a larger K instead)
- prefixing what the answer model sees
- a `chunk_embeddings.embed_input` column: the prefix is part of the config, so the configs already keep the embeddings apart
- deleting `structural-v1` rows
- embedding comparison, ACLs, contextual retrieval, hybrid search, reranking, ANN

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| Packing scope | Whole sections, packed greedily within a document, any heading level, up to 512 | **Within an H2 only:** H2 units have a median of 157 tokens, so chunks stay short. It also wouldn't fix rows 11 and 49, where the fact sits in the next H2. **Target 400:** p50 312; 512 matches the baseline's size, so the comparison isolates the boundaries. |
| Prefix | Title and heading path, embedded text only | **In the answer text too:** changes what the frozen prompt sees. **Path only:** the title is what tells the ten entity pages apart. |
| Prefix storage | A config param with its own chunk rows | **`embed_input` column (spec 0005 plan):** a schema change and a new PK for the same separation. The cost is duplicated chunk rows, about 47k. |
| Prefix control | `fixed-512-64-prefixed` | **Skip it:** a v3 win couldn't be told apart from a prefix win that would help fixed chunks just as much. |
| Decision metric | Fact recall at the token-matched k, with recall@5 next to it (Arun, 19 Oct) | **recall@5 only:** penalizes smaller chunks for their size, not their boundaries. **Recall within a fixed token budget:** deployment would need token-budget retrieval; Arun prefers top-K with a larger K. **A fixed k=10 for all:** the token amounts differ, so it is still unfair to small chunks. |
| Depth | 20 | structural-v1 needs about k=13 to match the baseline's tokens; packed configs should need about 5–6. |

## Open questions

1. ~~**Packing scope.**~~ Resolved 2026-10-19 (Arun): across headings within a document (AC-3). Every chunk boundary still falls on a heading unless a single section is over max.
2. ~~**Full answer run for the winner.**~~ Resolved 2026-10-19 (Arun): yes, today, if the winner isn't `fixed-512-64` (AC-8 step 5).
3. ~~**Budget metric.**~~ Resolved 2026-10-19 (Arun): deeper top-K with a token-matched k instead of a token budget (AC-6, AC-7).

## Verification

- `make chunk CONFIG=…` for each new config. Check the counts and the token distribution, and confirm the baseline fingerprint is unchanged.
- Hand-check 3 `structural-v2` chunks against `finance/expenses.md` and the row 88 section pair (Timeline, then Cadence/Eligibility, in one chunk).
- Embed dry runs, then the `CONFIRM=1` runs on approval.
- The AC-8 run plan, then the AC-9 decision written up.
- `make test` and `make lint` pass.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] docs updated: journal entry, an ADR for any decision, follow-ups
