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

## Decision
- Neither candidate passes, so 3-small stays ([ADR-0022](../decisions/0022-keep-text-embedding-3-small.md)). No prefix arm.
- Both models lose rows 44 and 49, where 3-small scored 1.0. On row 49 both rank `general-onboarding/tanewki-tips.md` first. Not investigated further today.

## Review (`/code-review`, 21 Oct)
Fixed (correctness or AC-breaking), commit `3e5dc67`, with tests:
- **Adapter over-length aborted the whole embed (AC-4).** The adapter counts the exact text sent. The embed pre-check sums stored counts (content plus a prefix counted on its own), and the two can differ by a token at a boundary. A chunk passing one check and failing the other raised a bare `ValueError` that stopped the run and named a batch index. Now it raises `InputTooLong` with the index, and embed records it as a local failure naming the chunk_id, then sends the rest.
- **Dry runs priced the raw spec string, not the stored name (AC-1, AC-5).** `@01536` counted pending chunks under a name run() never stores, and an out-of-range `@4000` passed the dry run, failing only after `CONFIRM=1`. Both dry runs now build a client-less embedder to get the canonical name and check dims.
- **The eval estimate left out the query instruction (AC-5).** For Qwen it counted 868 tokens. Counted as sent, it is 2,242 ($0.000022, not $0.000009), so run `c5d62f36` was quoted low; the amount is negligible either way.
- **An over-length query would fail mid-eval, after earlier rows were paid for (AC-4).** Every query as sent is now checked before `CONFIRM`.

Not fixed, waiting for Arun (lower priority):
- The AC-6 both-changed check runs after `CONFIRM`, though still before any spend. It could move to the dry run.
- The mean/SE cell shows "—" when SE = 0. That can't happen at n = 32 with mixed deltas.
- A missing `DEEPINFRA_API_KEY` raises a bare `KeyError` after `CONFIRM`.
- The adapter re-tokenizes inputs that embed already counted, wasting CPU (about 10M tokens per full embed).
- The adapter doesn't validate `kind` itself; only the factory does.
- The model-table lookup is repeated in the factory and the adapter.

---

Prev: [2026-10-20: embedding comparison prep, for spec 0008](2026-10-20-embedding-comparison-prep.md)
