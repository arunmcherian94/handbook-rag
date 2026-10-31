# 0012: Cross-encoder reranker over dense candidates

- Status: draft
- Date: 2026-10-31

## Problem

Three diagnoses say retrieval loses on order, not coverage:

- In spec 0010, 5 of the 7 retrieval-side false abstentions (rows 8, 49, 89, 53, 55) had their facts at dense ranks 6–8.
- In spec 0007, the authorized-recall misses (0.878) were ranking among pages the persona could open.
- In the spec 0011 audit, FTS added no fact chunks beyond dense's top 50. The best possible top 5 from dense's top 50 has `chunk_fact_recall@5` 0.875, against 0.583 today (run `2026-10-21-d83f3edc`). That gap is the headroom.

A cross-encoder scores the question and each candidate together, so it can reorder the 50 chunks dense search already found. This spec adds one, retrieval-only and off by default, and measures how much of the headroom it captures.

## Depends on / frozen inputs

| Input it fixes | Open decision that could change it | Handling |
|---|---|---|
| Embedding model `openai:text-embedding-3-large@1536`, exact cosine, ties on `chunk_id` | None in week 3 ([ADR-0022](../docs/decisions/0022-adopt-text-embedding-3-large-1536.md)) | **Frozen.** The candidates are `ask.search`'s dense list, unchanged |
| Chunk config `fixed-512-64` | The size and overlap sweep is week 4 | **Frozen.** The reranker sees `chunks.content` for that config only |
| Eval set v1.2 at corpus pin `5273b21` (`eval_sha256 995acb3b…`) | A v1.3 bump ([follow-ups](../docs/follow-ups.md)) | **Frozen for this spec's runs.** If v1.3 lands first, the runs wait or the spec is amended |
| Answer model and prompt (`ask.py`, `prompts.py`), `TOP_K = 5` | None through week 3; k tuning is week 4 | **Frozen.** The reranker enters through retrieval only and is off by default (AC-8). The recall@k curve (AC-10) is input for week 4, not a k decision |
| Reranker `deepinfra:Qwen/Qwen3-Reranker-4B` | A self-hosted model ([follow-ups](../docs/follow-ups.md)) | **Decided (Arun, 31 Oct).** One model. A second is added only if truncation turns out to be the problem, and at 32k context it can't be (AC-4) |
| Reranker instruction | None | **Decided before any run:** the model card's default, "Given a web search query, retrieve relevant passages that answer the query". It is sent explicitly, so a provider change of default can't change it. Writing our own would be a choice made against v1.2 |
| Candidate depth 50 | None; no depth sweep | **Decided:** the depth where the 0.875 ceiling was measured |
| Model weights behind the API name | Nothing pins the weights: DeepInfra shows no model revision | **Accepted risk.** The primary comparison is paired within one run (AC-11), so drift between runs can't bias it. Each run records the model ID, the date and the provider's `input_tokens` |
| Decision rule | None | **Decided before any run** (Decisions) |
| Continuity baseline `2026-10-21-d83f3edc` | A new dense run, or a model or config change | **Decided.** Pass the full run ID; the short form fails the dry run |

## Acceptance criteria

Each criterion is testable. Tests and plan steps cite them by ID.

**Reranker**

- AC-1: **A `Reranker` port with one DeepInfra adapter.**
  - `rerank(question, documents) -> list[float]` returns one score per document, in input order.
  - The adapter posts to `https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-4B` with `queries` (the question repeated once per document), `documents` and `instruction`.
  - It uses the existing `DEEPINFRA_API_KEY` and adds no dependency: the HTTP call uses the standard library.
  - Transient errors retry with the existing backoff constants (`MAX_ATTEMPTS`, `BACKOFF_BASE`, `BACKOFF_CAP`, `RETRY_4XX`).
  - A count mismatch, a missing score or a final failure raises. It never falls back to the dense order.
  - It returns the provider's `input_tokens`.
  - Unit tests use a fake transport: the request body, score order, retries, the mismatch error and no fallback.
- AC-2: **The model's settings live in `constants.py`**, beside `EMBED_MODELS`:
  - model ID
  - endpoint
  - instruction
  - `max_input_tokens = 32768`
  - `usd_per_1m = 0.025`
  - `price_source = "deepinfra.com/Qwen/Qwen3-Reranker-4B, 2026-10-31"`
  - `template_tokens`, an estimate of ~80 per pair, used by the cost estimate and the truncation guard
  - `RERANK_DEPTH = 50`
- AC-3: **The reranked order.**
  - `search(..., retriever="rerank")` fetches the dense list to `RERANK_DEPTH` for the principal and config, scores each candidate's `content`, and sorts by score descending, then dense rank ascending, then `chunk_id`.
  - It cuts to the requested k.
  - Each result carries `dense_rank` and `rerank_score`.
  - The dense list is fetched once per question per principal. Its first k entries are the in-run dense top k (AC-11).
  - Unit tests on fixed lists cover the sort, both tie-break steps and the cut.

**Truncation**

- AC-4: **No silent truncation.**
  - Before any request, each pair's length is estimated: cl100k tokens of question + content, + `template_tokens`, × 1.5 as a margin for the tokenizer difference.
  - A pair whose estimate exceeds `max_input_tokens` stops the run with an error naming the chunk. The client never truncates.
  - The run reports the truncation share: the share of pairs over the limit, expected 0. In the reading, the longest pair in Qwen3's tokenizer was 897 tokens.
  - The run also reports the mean `input_tokens` per pair from the provider.

**Permissions**

- AC-5: **Only pre-filtered candidates are reranked.**
  - The candidates come from the dense statement, which carries `allowed_groups && %(groups)s` (spec 0007 AC-8). The reranker adds no SQL.
  - The spec 0011 static test still covers every ranking statement in `src/`.
  - An integration test with a restricted chunk shows a persona without access never gets it under `rerank`, at any k, and `admin` does. The test uses a fake reranker that scores the restricted chunk highest.
  - A principal with no groups is an error (unchanged).
- AC-6: **The permissions suite runs on the reranked path.**
  - `make paid-permissions RETRIEVER=rerank` scores permissions-v1 as today: leak, over-block and authorized recall at k = 5 and 20.
  - Its metadata records the reranker settings (AC-9).

**Guards and defaults**

- AC-7: **The dense path is unchanged.**
  - `ask.search`, `ask.retrieve` and `ask.ask` keep their SQL and behaviour.
  - Spec 0007 AC-9's regression still holds against `d83f3edc`.
- AC-8: **Reranking is off by default.**
  - `rerank` joins `RETRIEVERS` in `run.py` and `permissions.py`, exposed as `RETRIEVER=rerank` on `make eval`, `make paid-eval`, `make permissions` and `make paid-permissions`.
  - `--retriever rerank` needs `--retrieval-only` in the eval harness, as hybrid does.
  - `DEFAULT_RETRIEVER` stays `"dense"`. It changes only through ADR-0023, and only if the reranker is adopted.
  - `ask.py` and `make ask` are unchanged.

**Harness and reporting**

- AC-9: **Run metadata, cost and spend.**
  - The run's metadata records `retriever: "rerank"` and, under `rerank`:
    - `model`
    - `depth`
    - `instruction`
    - `max_input_tokens`
    - `truncation: "none; refuse over limit"`
    - `input_tokens` (the provider's total)
  - Each retrieved entry in `rows.jsonl` carries `dense_rank` and `rerank_score`. Each row records its rerank latency in ms.
  - The dry run shows the rerank cost next to the embed cost: pairs × (estimated tokens per pair) × `usd_per_1m`.
  - The spend log records the combined estimate under the existing target.
  - `BASELINE=` accepts a dense run that differs only in `retriever` (spec 0011 AC-10).
- AC-10: **The recall@k curve.**
  - For k = 3..10, the run reports `chunk_fact_recall@k` for both orderings: the in-run dense list and the reranked list.
  - The standard metrics at @1/3/5/10/20 are unchanged.
- AC-11: **The paired comparison within one run (primary).**
  - The reranked top 5 is compared with the same run's dense top 5: the first 5 of the dense list fetched in AC-3, from the same query vector.
  - The report shows:
    - the mean paired delta in `chunk_fact_recall@5`, its paired SE (sd of per-row deltas / √n), and the delta in SEs
    - rows won, lost and tied
    - headroom captured = (reranked@5 − 0.583) / (0.875 − 0.583)
    - for rows 8, 49, 89, 53 and 55: each required fact's dense rank and reranked rank, and whether it enters the top 5
    - rerank latency per query, p50 and p95, next to the in-run dense search p50
    - the truncation share (AC-4)
  - Unit tests on fixed rows check the delta, the SE, the headroom arithmetic and the won, lost and tied counts.
- AC-12: **The continuity comparison.**
  - The same run, with `BASELINE=2026-10-21-d83f3edc`, reports the existing paired comparison against that run.
  - The report states that `d83f3edc` used separately embedded query vectors (the row 32 and 93 drift), so the decision rests on AC-11.

## Out of scope

- LLM listwise reranking.
- Fine-tuning a reranker (week 7).
- Depth sweeps, or any depth other than 50.
- A second reranker model, or a self-hosted one ([follow-ups](../docs/follow-ups.md)).
- Reranking the hybrid list. The spec 0011 audit found FTS adds no fact chunks to dense's top 50.
- Answer-quality claims and answer runs: retrieval-only.
- Any k decision: week 4.
- Reranking in `ask.py` and the answer path. It enters only through ADR-0023.

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| Hosting | DeepInfra API (existing account and key; paid path through the existing `paid-eval` / `paid-permissions` guard) | **Self-hosted `gte-reranker-modernbert-base`** (8192 context, 0% truncation, $0 per query): needs torch through sentence-transformers or onnxruntime as a new dependency, plus 3–6 s of CPU per query; it is a follow-up. **Voyage rerank-3, Cohere Rerank 5:** a new vendor, key and adapter for no measured gain. **Jina v3.5:** price not published; the weights are CC BY-NC |
| Model | Qwen3-Reranker-4B | **8B:** 0.74 points behind 4B on English MTEB-R, ahead by 0.2 on MLDR and MMTEB-R, at 2× the price; the card's gaps can't predict our 33 rows, and 4B is the closer match to our case (English passages). **0.6B:** about 4 points lower on MTEB-R. **Nemotron-3.5-Rerank-8B:** its card reports only visual-document benchmarks; OpenMDW licence. **Any 512-cap model:** truncates 82–88% of our pairs ([reading](../docs/reading/week-03.md#cross-encoder-reranking-candidate-models-truncation-hosted-apis)) |
| Truncation | None; refuse a pair over the limit (AC-4) | **Truncate the document tail:** loses text without telling us; unnecessary at 32k. **Split long chunks into passages and take the max:** solves a problem we don't have |
| Text sent | `chunks.content` only | **Heading + content:** the heading-prefix arm wasn't adopted for dense ([ADR-0022](../docs/decisions/0022-adopt-text-embedding-3-large-1536.md)). Keeping what dense embedded isolates the reranker as the one change |
| Instruction | The model card's default, sent explicitly | **A handbook-specific instruction:** a wording choice we'd be tempted to check against v1.2 |
| Depth | 50 | **A sweep:** out of scope; 50 is where the ceiling was measured |
| Tie-break | Score, then dense rank, then `chunk_id` | **`chunk_id` alone:** arbitrary at the top-5 boundary |
| On API failure | The run fails | **Fall back to the dense order:** a silent mix of two retrievers in one run corrupts the paired comparison |
| HTTP client | Standard library (`urllib.request`) | **`httpx` or `requests`:** a new or undeclared dependency for one POST. **The openai SDK:** DeepInfra's reranker isn't on its OpenAI-compatible route |
| Primary comparison | Paired within one run, on identical query vectors | **Against `d83f3edc` only:** separately embedded query vectors drift (rows 32 and 93), which would mix embedding noise into the reranker's delta |
| **Decision rule** (fixed before any run) | **Adopt at ≥ +2 paired SE** on `chunk_fact_recall@5` (AC-11), through ADR-0023, which also sets `DEFAULT_RETRIEVER`. **At 1–2 SE: not adopted.** Record it in the journal as promising, and re-test on the synthetic retrieval set (larger n). **Below 1 SE: not adopted** | **A documented exception at 1–2 SE, as for 3-large (ADR-0022, 1.97 SE):** that exception cost nothing at query time. A reranker adds a paid external call and seconds of latency to every query, so a gain inside the noise doesn't pay for it. *Proposed; Arun to confirm at the spec review* |
| Default | Off (`dense`) | **On:** changes the frozen answer path before measurement |

## Open questions

- **The ceiling within the run.** The headroom formula uses `d83f3edc`'s 0.583 and 0.875, as fixed above. Should the report also show the in-run dense@5 and the in-run ceiling (the best top 5 from this run's dense top 50)? They cost nothing extra and remove the drift from the headroom figure. Proposed: yes, as an extra line, with the fixed formula still the headline.
- **The `spend.logged` follow-up** was due "when the next paid target lands". This spec adds cost to existing targets, not a new target, so it stays deferred unless Arun wants it here.

## Evaluation plan (each run with Arun's session approval, after a commit)

All runs are retrieval-only, as `admin` unless noted, on `fixed-512-64`, eval v1.2.

1. **Reranked vs in-run dense, plus continuity:** `make paid-eval RETRIEVAL_ONLY=1 RETRIEVER=rerank BASELINE=2026-10-21-d83f3edc`.
   - The decision rests on AC-11 under the rule above. At n = 32, the 2-SE bar is about +0.08, if the SE is like spec 0011's.
   - AC-12 is reported beside it.
2. **Permissions on the reranked path:** `make paid-permissions RETRIEVER=rerank`.
   - Leak and over-block must be 0 at k = 5 and 20.
   - Report authorized recall (n shown) against run `2026-10-24-086eca8a`.
3. **Cost, from the reading** (the dry runs give the exact figures before each run):
   - eval: 33 questions × 50 pairs, ~1.0M tokens, ≈ $0.025 rerank + ~$0.0001 embed
   - permissions: ≤ 104 reranked lists, ≤ 3.1M tokens, ≈ $0.078 rerank + ~$0.00007 embed

## Verification

- Unit (in memory, no API):
  - the adapter's request body, retries and errors (AC-1)
  - sort and tie-breaks (AC-3)
  - the truncation guard (AC-4)
  - mode defaults (AC-8)
  - metadata, the cost estimate and the baseline rule (AC-9)
  - the recall curve (AC-10)
  - paired-comparison arithmetic (AC-11)
- Integration (DB, fake reranker):
  - restricted-chunk denial and the admin control under `rerank` (AC-5)
  - the dense path unchanged (AC-7)
- Free checks:
  - `make eval RETRIEVAL_ONLY=1 RETRIEVER=rerank BASELINE=2026-10-21-d83f3edc` and `make permissions RETRIEVER=rerank` dry runs show the mode, the model and the estimate.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] docs updated: ADR-0023 if adopted, otherwise a journal entry; follow-ups

## References

- [Reading log, week 3: cross-encoder reranking](../docs/reading/week-03.md#cross-encoder-reranking-candidate-models-truncation-hosted-apis)
- [Spec 0011: hybrid search](0011-hybrid-search.md) (the audit and the ceiling)
- [Journal, 30 Oct: hybrid runs](../docs/journal/2026-10-30-hybrid-runs.md)
- [Spec 0010: answer evaluation](0010-answer-evaluation.md) (the retrieval-side false abstentions)
- [ADR-0022](../docs/decisions/0022-adopt-text-embedding-3-large-1536.md) (the decision rule and its exception)
- [DeepInfra Qwen3-Reranker-4B](https://deepinfra.com/Qwen/Qwen3-Reranker-4B)
