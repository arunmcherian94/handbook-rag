# 2026-10-19: structure-aware chunker build, spec 0005

- **Built from [spec 0005](../../specs/0005-structure-aware-chunking.md)** in four file-disjoint slices (chunker; embed; evidence and report; retrieval and eval run), after the contracts were written first: the config constants, the migration, and the Makefile flags. → [ADR-0019](../decisions/0019-structural-first-recursive-inside-chunking.md), [ADR-0020](../decisions/0020-chunk-configs-coexist.md)
- **Baseline unchanged (AC-3):** `fixed-512-64` has 22,378 chunks, md5 over chunk_id‖content `a74cd032…`, and 22,378 embeddings, the same before the migration and after chunking `structural-v1`. A test asserts it.
- **`structural-v1` at the pin:**
  - 49,215 chunks (2.2× the baseline) and 9.59M tokens (baseline 10.46M; less overlap)
  - tokens p50 154, p90 438, max 512
  - 6,223 chunks are under 64 tokens: a section with no sibling to merge with stays alone (AC-8)
  - 2,053 are preambles (text before the first heading, empty heading path)
  - embedding all of them is estimated at $0.19
- **Judgment calls in the build** (within the ACs):
  - Structural chunk_ids are `uuid5(doc_id:config_id:i)`. After review, the same applies to any fixed config other than the baseline (see below).
  - Structural rows fill `chunk_size`/`chunk_overlap` with max_tokens and overlap, since both columns are NOT NULL.
  - Merge (AC-8): a tiny section absorbs the following adjacent siblings until the group reaches `min_tokens`. If none can be absorbed, it joins the preceding sibling group when that fits.
  - Split (AC-7): when a piece doesn't fit after the overlap, the window is cut at the token limit.
  - Line ranges count the front matter: `chunk.run` reads the pinned file and checks that it ends with the stored body.
  - `make embed` is now a dry run for every config unless `CONFIRM=1` is given (AC-13).
- **Spec detail corrected while building:** both `### 4.1` headings in `finance/expenses.md` sit under `4. PROCEDURES`, so they share a parent. They stay separate sections because they aren't adjacent siblings. The plan had said their parents differed.
- **Hand check:** 3 `finance/expenses.md` chunks match the file's lines exactly. The two `4.1` headings have distinct paths and ranges.
- **Code-review catches (fixed):**
  - The migration's `ALTER TABLE` ran on every `make chunk` and took an exclusive lock for the whole chunk transaction, blocking embed and eval. It now runs only when the columns are missing.
  - A second fixed config with the baseline's size and overlap would have reused the baseline's chunk_ids and moved its rows over (AC-3). Only the baseline keeps the spec 0003 id formula now.
  - Run metadata had dropped the tokenizer and strategy. `chunk_params` now records strategy, params and tokenizer (AC-12).
  - `--baseline` accepted any run folder. The run now fails before spending if the baseline differs in eval-set hash, corpus, embed model, k or limit, or, when both runs answered, in answer model or prompt (AC-11).
  - The evidence check recomputed `line_end` instead of reading the stored value (AC-10).
- **Code-review items not fixed, pending Arun:**
  - Heading-only parent chunks: a heading followed directly by a child heading becomes a chunk of a few tokens. AC-8 forbids merging with a child; the min-size sweep measures it.
  - The merged heading path reads like nesting. Spec AC-9 defines it as the first path plus each merged sibling's heading.
  - The packer can emit a mostly-overlap window when the only cut sits just past the previous end. It's rare, and costs a near-duplicate chunk, not correctness.
  - `front_matter_lines` re-reads each file per run (the run takes about 30s).
  - The embed cost SQL repeats the pending predicate.

---

Prev: [2026-10-19: chunking spec, spec 0005](2026-10-19-chunking-spec.md)
