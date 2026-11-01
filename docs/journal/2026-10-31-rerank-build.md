# 2026-10-31: cross-encoder reranker build, spec 0012

Builds [spec 0012](../../specs/0012-cross-encoder-reranker.md): `--retriever rerank` scores the dense top 50 with DeepInfra `Qwen/Qwen3-Reranker-4B` and cuts the reranked order to k. The default stays `dense`, and `ask.py` is unchanged. No paid calls; the measurement runs come after the build PR.

## Build
- **Port and adapter:**
  - `Reranker` sits beside `Embedder` in `models/base.py`.
  - The DeepInfra adapter posts with `urllib.request`, so there is no new dependency. Its retry policy mirrors `embed_with_retry`.
  - A bad response raises. The run never falls back to the dense order.
- **One rerank call per row:**
  - The eval harness embeds each question once and calls `hybrid.rerank_lists` once.
  - The top 5 and the depth-20 list are cuts of the same reranked order. Hybrid and dense call the retriever twice per row, so this is half the embeds, and the two lists can't disagree.
  - Each row keeps all 50 candidates with both ranks, so the in-run dense order (AC-11) is read from the same row.
- **Ceiling:** `metrics.best_top_k` searches every combination of the fact-bearing candidates for the best possible top 5. In spec 0011 the 0.875 figure came from a manual audit; this is the first time the code computes it.
- **Dry runs (free):**
  - Eval: $0.0250. That is ~998,500 rerank tokens plus $0.000056 to embed 434 tokens; the longest pair is ~938 of 32,768.
  - Permissions: $0.0594. That is ~2,374,800 rerank tokens for one search per unique (persona, question) pair, plus $0.000066 to embed. The spec's upper bound was $0.078.
  - The baseline `2026-10-21-d83f3edc` is accepted as a retriever-only change.

## AC-7 check without spend
- **Method:** `ask.search` as admin, using the saved 3-large query vectors, compared with the top 5 of `d83f3edc`.
- **Result:** 31 of 33 rows are identical. Rows 32 and 93 differ, the same as on 29 Oct ([hybrid build](2026-10-29-hybrid-build.md)), because the saved vectors were embedded separately. `git diff main -- src/handbook_rag/ask.py` is empty.

## Review catches (`/code-review`)
There were ten findings: six fixed by default, one fixed lower-priority item (Arun's choice), and three skipped with reasons.
- **Fixed by default:**
  - **Provenance:** the permissions runner went through `hybrid.search`, which throws away the provider's `input_tokens`, so permissions runs never recorded reranker usage (AC-6, AC-9). It now calls `rerank_lists` and records the total.
  - **Correctness:** `json.loads` accepts `NaN` and `Infinity`. A non-finite score would have passed validation and left the sort order undefined. It now raises.
  - **Spend safety:**
    - The dry run printed "no truncation" without checking anything. It now bounds the longest pair (the longest question with the config's longest chunk) and exits before any spend if it's over the limit.
    - `run()` in rerank mode without a reranker crashed only after the first paid embed. It now raises first.
  - **Cost display:** the permissions headline "estimated cost" showed only the embed cost, while the spend log recorded the total.
  - **Robustness:** a connection dropped mid-body (`IncompleteRead`) escaped the retry loop. It now counts as a transient connection error.
- **Fixed, lower priority (Arun):** the rerank cost formula, the longest-chunk query and the dry-run line were duplicated in `run.py` and `permissions.py`. They are now one helper in `hybrid.py`.
- **Skipped:**
  - **Using the stored `token_count` in the truncation guard:** `Retrieved` doesn't carry it, so this needs an extra query, and re-encoding 50 chunks takes milliseconds.
  - **One retry helper shared with `embed.py`** and **one call path through `hybrid.retrieve`:** both are refactors spec 0012 doesn't need, so they're in [follow-ups](../follow-ups.md).

## Clean room
- **Setup:** a fresh clone under `$HOME` with its own DB on port 5434, the pinned corpus linked, and no API keys in its `.env`. Then ingest, chunk all five configs and `make acl`.
- **Result:** 747 unit and 102 integration tests passed, and lint is clean, the same as the working copy. The rerank tests use a fake transport and a fake reranker, so they need no key and make no call.

## Limitations
- **The truncation guard is an estimate:** cl100k × 1.5 plus ~80 template tokens. In the reading, the longest pair in Qwen3's own tokenizer was 897 tokens, so the margin is wide.
- **Nothing pins the weights behind the API name.** Each run records the model ID, the date and the provider's token count; this is the risk the spec accepts.
