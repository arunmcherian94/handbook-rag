# 2026-10-21: embedding model comparison, spec 0008

Build and runs for [spec 0008](../../specs/0008-embedding-model-comparison.md). Baseline: run `2026-10-19-d2625d91` (`fixed-512-64`, text-embedding-3-small, chunk_fact_recall@5 0.495 ± 0.081, n = 32). Decision rule (AC-9, set before any run): adopt only if the mean paired delta in chunk_fact_recall at the matched k exceeds 2 paired SEs.

## Build
- Four parallel slices on top of contracts written first (orchestrate skill): adapter and factory, embed, eval run, report. One commit, `6095a08`.
- Gemini was not built (spec open question 3, stretch 2). Qwen3-Embedding-8B went through DeepInfra on the existing `openai` SDK with a `base_url`, so no new dependency. `DEEPINFRA_API_KEY` approved by Arun on 21 Oct; DeepInfra's minimum top-up was $5.
- A dry run now prices the selected model and needs no API key: the embedder is built only after `CONFIRM=1`.

## 3-large@1536
- Embed: 22,378 chunks, 10,457,284 cl100k tokens, estimated $1.36. 152 HTTP 429s, all retried; 0 failed. Every vector is 1,536 dims, and the 3-small rows are unchanged.
- Eval: run `2026-10-21-d83f3edc`, retrieval-only. Matched k = 5 (2,344 vs 2,335 tokens@5).
  - chunk_fact_recall@5 0.583 ± 0.075 (+0.088). chunk_hit@5 +0.125, chunk_mrr +0.123, chunk_fact_recall@20 +0.142.
  - **Paired delta +0.088, paired SE 0.045, mean/SE 1.97.** Under 2, so "no difference" under AC-9.
  - Rows: 7 won (10, 8, 58, 89, 99, 11, 34), 2 lost (49 −0.5, 44 −0.2), 23 tied.
  - Every metric moved the same way and just missed the bar. That is the "loses narrowly" trigger in [follow-ups](../follow-ups.md#from-the-spec-0008-review-2026-10-21): run 3-large@3072 (one change: dims) before week 6.
- **Provenance:** the run's metadata says `harness_dirty: true` with `harness_sha` ca41978 (main before the build), because it ran before the build was committed. The tree that ran is commit `6095a08`: every changed file was last modified by 13:21 IST, the run started at 13:37 IST, and the commit left nothing uncommitted. Not re-run (Arun): retrieval is exact search, so a re-run would only restamp the metadata.

## Qwen3-Embedding-8B@1536 (DeepInfra)
- Probe, `LIMIT=10`: 10 vectors, 1,536 dims, unit norm. DeepInfra honours `dimensions`.
- Embed: 22,368 more chunks (10 from the probe skipped), estimated $0.10, 0 failed, 0 HTTP 429s. It took 43 minutes (14:00–14:43), about 4× slower than 3-large. Every vector is 1,536 dims.
- Eval: run `2026-10-21-c5d62f36`, retrieval-only, clean tree (`harness_sha` 7a8c798). Arun approved this eval before lunch. Matched k = 5 (2,308 tokens@5).
  - chunk_fact_recall@5 0.586 ± 0.082 (+0.091). chunk_all_required@5 0.500 (+0.094), chunk_ndcg@5 0.456 (+0.161).
  - **Paired delta +0.091, paired SE 0.076, mean/SE 1.20.** No difference under AC-9.
  - Rows: 7 won (8, 10, 99 at +1.0; 32, 58, 11, 34), 2 lost (44 and 49, each −1.0), 23 tied.

## Full answer runs
- Why: the retrieval-only runs never called the answer model, so they say nothing about answers. Arun overrode the 15:55 stop to finish today and decide on answer quality too.
- 3-small was re-run the same day as the noise floor and the baseline for this comparison, because `3748df5b` lacks `eval_depth`. Retrieval is identical to `2026-10-19-d2625d91` (recall@5 0.495).
- 52 rows, gpt-5.4-mini, k = 5, harness `26808da`, clean tree, about $0.21 each, approved by Arun. Retrieval reproduces the morning runs exactly (exact search, deterministic).

| model | run | recall@5 | mrr | false abstention (n = 33) | correct ooc abstention (n = 19) |
|---|---|---|---|---|---|
| 3-small | `2026-10-21-18f10293` | 0.495 | 0.380 | 11, 0.333 ± 0.082 | 17 |
| 3-large@1536 | `2026-10-21-e602bd95` | 0.583 | 0.504 | 10, 0.303 ± 0.080 | 17 |
| Qwen3-8B@1536 | `2026-10-21-9719cae6` | 0.586 | 0.553 | 10, 0.303 ± 0.080 | 15 |

- Flips vs 3-small, paired: 3-large −0.030 ± 0.053 (rows 99, 5 now answer; 53 now abstains). Qwen −0.030 ± 0.081 (rows 8, 55, 100, 92 now answer; 53, 44, 35 now abstain).
- Code checks pass on every non-abstaining row for all three. They say nothing about content.
- ooc: Qwen row 47 (France statutory PTO) asserts "20 statutory vacation days". That phrase is in the corpus only on `bv-benefits-belgium.md`: a wrong-entity hallucination (verified). Qwen row 112 answers "Yes" from a distractor page. 3-large row 47 says the excerpt states no minimum, a de facto abstention in non-standard wording. 3-small answered no ooc row.
- Judged by reading answers against the reference facts (Claude's judgment, not yet reviewed by Arun; directional, one run per model, no generator-variance estimate; on the 16 rows where abstention or recall differs, plus 44 and 49): 3-large vs 3-small 5 better / 2 worse / 9 tie; Qwen vs 3-small 6 / 4 / 6; 3-large vs Qwen 5 / 4 / 7.
- Row 49: all three abstain, and 3-small had recall@5 1.0, so that is generator over-abstention, not retrieval. Row 44: 3-small and 3-large are about equal, and Qwen abstains (recall 0).
- Most false abstention is generator behaviour (rows 49, 100, 58 abstain with full or high recall), so better retrieval barely moves it.

## Decision
- Proposed: adopt `openai:text-embedding-3-large@1536` as `DEFAULT_EMBED_MODEL` ([ADR-0022](../decisions/0022-adopt-text-embedding-3-large-1536.md)); Arun to accept or reject in PR #31. The prefix arm (about $1.4) is the next step, not done.
- Departs from AC-9: 1.97 SE is under 2. The rule was a pre-commitment against moving the bar after seeing numbers, and this moves it. Keeping 3-small is the choice that keeps the rule.
- For: every retrieval metric up (recall@5 bootstrap 95% CI [+0.004, +0.178]; recall@10 2.42 SE and MRR 2.51 SE, post-hoc), no measured answer harm, same provider and key, vectors already stored, reversible by a constant change.
- Against Qwen: same mean gain, double the variance, an ooc hallucination, a second provider, 4× slower embedding, and `make ask` would need query mode.
- At n = 32 the eval can't reliably detect about +0.09: "probably better, cheap, reversible", not "proven better".

## Lessons (Arun)
- **The eval set is too small for model choices.** At n = 32 a gain of about +0.09 sits on the 2-SE bar, and both candidates landed there. From today's per-row spread (paired sd 0.25 for 3-large, 0.43 for Qwen), detecting +0.05 needs about 105–300 rows to reach the bar half the time and about 210–600 for 80%. Model comparisons need a few hundred rows: the synthetic retrieval set ([follow-ups](../follow-ups.md)), reported apart from the human-authored v1.
- **Models will keep changing, so switching must be cheap.** Ports and adapters, the factory on the name string, the name as storage key, the untyped vector column and coexisting configs already carry most of it ([ADR-0008](../decisions/0008-design-patterns.md), [ADR-0020](../decisions/0020-chunk-configs-coexist.md)). This comparison still needed query/document kinds, dims in the name and a price table. The target: adding or switching a model is one adapter file, one table entry and one constant, plus a re-embed and an eval run, with no schema change. Gaps are in [follow-ups](../follow-ups.md#model-switching).
- **An LLM gateway may make sense** for answer models (one API, fallbacks, routing, central keys and spend). It does not remove the main cost of an embedding switch, the re-embed. Decide in week 7.
- **We measured retrieval closely and answers barely.** The harness scores abstention and citation form, not correctness or grounding. Answer evaluation is scheduled for week 3, before hybrid search ([follow-ups](../follow-ups.md)).

## Review (`/code-review`, 21 Oct)
Fixed (correctness or AC-breaking), commit `3e5dc67`, with tests:
- **Adapter over-length aborted the whole embed (AC-4).** The adapter counts the exact text sent. The embed pre-check sums stored counts (content plus a prefix counted on its own), and the two can differ by a token at a boundary. A chunk passing one check and failing the other raised a bare `ValueError` that stopped the run and named a batch index. Now it raises `InputTooLong` with the index, and embed records it as a local failure naming the chunk_id, then sends the rest.
- **Dry runs priced the raw spec string, not the stored name (AC-1, AC-5).** `@01536` counted pending chunks under a name run() never stores, and an out-of-range `@4000` passed the dry run, failing only after `CONFIRM=1`. Both dry runs now build a client-less embedder to get the canonical name and check dims.
- **The eval estimate left out the query instruction (AC-5).** For Qwen it counted 868 tokens. Counted as sent, it is 2,242 ($0.000022, not $0.000009), so run `c5d62f36` was quoted low; the amount is negligible either way.
- **An over-length query would fail mid-eval, after earlier rows were paid for (AC-4).** Every query as sent is now checked before `CONFIRM`.

Lower priority, decided after PR #31 (Arun delegated the call, 21 Oct):
- **Fixed:** the AC-6 both-changed check now runs in the dry run, before `CONFIRM`. Checked against a two-change baseline: the dry run fails with the AC-6 message.
- **Fixed:** a missing `DEEPINFRA_API_KEY` fails with its name, not a bare `KeyError` (unit test).
- **Skipped:** the "—" for mean/SE at SE = 0 (can't happen with mixed deltas); the adapter re-tokenizing (seconds of CPU, no money); the adapter validating `kind` (the factory already does); the repeated model-table lookup (style).

## After PR #31: adoption (branch `adopt-3-large`)
Decisions, all Arun's, 21 Oct:
1. **3-large@1536 adopted** (ADR-0022 accepted by merging PR #31). `DEFAULT_EMBED_MODEL` is now `openai:text-embedding-3-large@1536`. ADR-0004's model choice is superseded; its schema stands.
2. **Heading-path prefix not adopted.** The default config stays unprefixed `fixed-512-64`. Run `2026-10-21-586b1635` vs `d83f3edc`: +0.031 ± 0.059 (0.51 SE); page_hit@1 +0.156 (2.40 SE) but recall@10 −0.062 (−1.68 SE), from same-page crowding (rows 10, 48, 34). Decided on the evidence, not a pre-set threshold (Arun chose that before the run). Re-test after the week-3 reranker ([follow-ups](../follow-ups.md)).
3. **P-097 and P-098 marked invalid** in permissions-v1 under AC-11, not re-targeted. Re-check under 3-large: 50 of 52 valid; the row-61 controls lose `time-off-types.md` and `global-expansion.md` from admin's top 20. 3-small reproduced 52 of 52. Cost about $0.00008. Whether the dropped controls (rows 15, 22, 39, 92, 109) would now be valid was not reported: my target selection didn't reproduce the original drop list.
4. **Contextual retrieval** moved off the week-2 roadmap to an optional end-of-plan item, for cost ([follow-ups](../follow-ups.md)).

Notes:
- **Comparison baselines from now on:** `2026-10-21-d83f3edc` (retrieval-only) and `2026-10-21-e602bd95` (full), both 3-large@1536 on `fixed-512-64`.
- **Stale title on main:** PR #31 was squash-merged as "Spec 0008 build and runs: keep text-embedding-3-small (ADR-0022)". The title predates the revision; the merged files adopt 3-large. Main's history isn't rewritten, so this note is the record.
- Prefix embed: 22,378 chunks, 10,814,466 tokens, estimated $1.41, 0 failed.

---

Prev: [2026-10-20: embedding comparison prep, for spec 0008](2026-10-20-embedding-comparison-prep.md)
