# 2026-10-19: structure-aware chunker build, spec 0005

- **Built from [spec 0005](../../specs/0005-structure-aware-chunking.md)** in four file-disjoint slices (chunker; embed; evidence and report; retrieval and eval run), after the contracts were written first: the config constants, the migration, and the Makefile flags. → [ADR-0019](../decisions/0019-structural-first-recursive-inside-chunking.md), [ADR-0020](../decisions/0020-chunk-configs-coexist.md)
- **Baseline unchanged (AC-3):** `fixed-512-64` has 22,378 chunks, md5 over chunk_id‖content `a74cd032…`, and 22,378 embeddings, the same before the migration and after chunking `structural-v1`. A test asserts it.
- **`structural-v1` at the pin:**
  - 49,215 chunks (2.2× the baseline) and 9.59M tokens (baseline 10.46M; less overlap)
  - tokens p50 154, p90 438, max 512
  - 6,223 chunks are under 64 tokens: a section with no sibling to merge with stays alone (AC-8)
  - 2,053 are preambles (text before the first heading, empty heading path)
  - embedding all of them is estimated at $0.19
  - **Why fewer tokens than the baseline with 2.2× the chunks:** the corpus is 9.29M tokens with each doc encoded once. The baseline repeats 64 overlap tokens at every window boundary: (22,378 − 4,088 docs) × 64 = 1.17M extra, giving 10.46M. Structural overlap exists only inside split sections: 4,753 continuation sub-chunks × 64 ≈ 0.30M, giving 9.59M. More chunks, but each is smaller, and nearly all boundaries fall on headings, which carry no overlap.
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
- **Code-review items not fixed:** noted as [follow-ups](../follow-ups.md#from-the-spec-0005-build-review-2026-10-19) (Arun, 19 Oct).
  - Heading-only parent chunks: a heading followed directly by a child heading becomes a chunk of a few tokens. AC-8 forbids merging with a child; the min-size sweep measures it.
  - The merged heading path reads like nesting. Spec AC-9 defines it as the first path plus each merged sibling's heading.
  - The packer can emit a mostly-overlap window when the only cut sits just past the previous end. It's rare, and costs a near-duplicate chunk, not correctness.
  - `front_matter_lines` re-reads each file per run (the run takes about 30s).
  - The embed cost SQL repeats the pending predicate.
- **First run (Task 7):** structural-v1 was embedded (49,215 chunks, about $0.19). The baseline retrieval-only re-run `2026-10-19-287181bb` matches `2026-10-17-3748df5b` on all 33 answerable rows (AC-5). The full run `2026-10-19-62a52a83` cost about $0.21. The summary and takeaways are in `docs/eval/results/2026-10-19-62a52a83/`, and recall@5 fell from 0.495 to 0.358.
- **Preview: heading-only vs budget (19 Oct, about $0.0001 of query embeddings; scratch script, not committed).** Each of the 32 scored rows was retrieved to depth 20 in three arms. "Budget" is fact recall over the top-ranked chunks whose cumulative tokens stay within 2,335, the baseline's mean retrieved_tokens@5.

  | arm | recall@5 | page_hit@5 | recall @ 2,335 tokens | chunks in budget |
  |---|---|---|---|---|
  | fixed-512-64 | 0.495 | 0.812 | 0.479 | 4.5 |
  | structural-v1 | 0.358 | 0.688 | 0.442 | 13.1 |
  | structural-v1 without heading-only chunks | 0.374 | 0.688 | 0.442 | 11.3 |

  - Heading-only chunks are not the main cause. Dropping them leaves row 58 and the page_hit drop unchanged. Row 58's top 5 still has the entity pages' `## Time Off Policies` sections, which are a heading plus one teaser line ("Comprehensive support when you need time away.") at 12–14 tokens. 14 chunks under 32 tokens remain in the top 5s, all short sections that have a body.
  - At a matched budget the gap shrinks from −0.137 to −0.037. Structural wins on rows 52, 53 and 38 at budget. Rows 49, 58, 88 and 100 still lose: short sections whose heading matches the question's wording outrank the section that holds the fact, while a 512-token window carries the heading and the fact together.
  - Row 112 (ooc, "do i still have admin rights on the AWS sandbox acct"): structural retrieved the sandbox page's "Accessing your AWS Account" section, which says the IAM user has `AdministratorAccess`. The model answered from it and hedged on "still". The baseline's top 5 didn't include that section, so the model abstained. Better-targeted retrieval caused the change, not lost evidence. The other ooc_pass changes are the wording check flipping (19 rows, so about three rows of noise).
- **Stop rule (Arun, 19 Oct):** one more iteration, spec 0006: packed sections (`structural-v2`), the same plus a heading-path prefix (`structural-v3`), the prefix alone on the baseline (`fixed-512-64-prefixed`), and a matched-budget retrieval metric (a harness reporting change; ask.py and the answer model stay frozen). Planned to finish today; the deadline is the end of Tuesday.s build blocks. If structural chunking still loses to `fixed-512-64` at a matched token budget, keep fixed-512, write the negative result into ADR-0019, and move to the embedding comparison on Wednesday. Size and overlap sweeps are dropped either way.

---

Prev: [2026-10-19: chunking spec, spec 0005](2026-10-19-chunking-spec.md)
