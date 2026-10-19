# 2026-10-19: packed sections and heading-path prefix build, spec 0006

- **Built from [spec 0006](../../specs/0006-packed-sections-and-heading-prefix.md)** in four file-disjoint slices: chunker; embed; metrics and report; eval run. The contracts came first: three configs, `EVAL_KS = (1, 3, 5, 10, 20)`, `EVAL_DEPTH = 20`, `REGRESSION_ROWS`.
- **Existing configs unchanged (AC-2):** after chunking the three new configs, `fixed-512-64` (22,378) and `structural-v1` (49,215) have identical chunks and embeddings. The md5 covers chunk_id, content, line ranges and heading path. A unit test also pins v1's output on `finance/expenses.md`, because the v1 emit loop was moved into a helper shared with the packer.
- **New configs at the pin:**

  | config | chunks | tokens p10 / p50 / p90 | under 64 tokens | embed estimate |
  |---|---|---|---|---|
  | `structural-v2` | 26,372 | 161 / 400 / 501 | 548 | $0.19 (9.59M tokens) |
  | `structural-v3` | 26,372 | same | same | $0.20 (10.01M, incl. prefix) |
  | `fixed-512-64-prefixed` | 22,378 | 286 / 512 / 512 | 221 | $0.22 (10.81M, incl. prefix) |

  - In the DB, v3 equals v2 on content, line ranges and heading path, and the prefixed baseline equals the baseline on content, heading and token count (AC-1).
  - v2 has the same total tokens as v1 (9,586,867). Both carry overlap only inside split sections, and the sections over 512 tokens are the same ones.
- **Judgment calls in the build** (within the ACs):
  - Fixed-prefixed `heading_path` is taken at the same byte as `heading` (the first non-blank byte), so `heading == heading_path[-1]`. The spec says "first byte"; the two differ only when a window opens on blank lines followed by a heading.
  - In a record, the metrics at k ≤ 5, plus the MRR and nDCG, come from the k=5 list the model saw; @10 and @20 come from the depth-20 list. Rows where the two lists' top 5 differ are listed as `near_ties`.
  - The matched k is computed over scored rows, and only when `--baseline` is given. A matched k ≤ 5 reads the k=5 list too (a review catch, below).
  - The prefix token count is added to `token_count` for the embed size limits; `chunks.token_count` stays the content's count.
  - The `eval_depth` key is new, so `BASELINE=3748df5b` fails the compatibility check. The new depth-20 baseline run (AC-8 step 3) is checked against 3748df5b's top 5 by a one-off comparison.
- **Hand check:**
  - `finance/expenses.md`: 3 v2 chunks match their file lines exactly. Chunk 0 is the preamble packed with `## 1. POLICY`, with an empty path.
  - Row 88: the spec's check expected Timeline and Cadence in one chunk, which is wrong. The Timeline section is over 512 tokens, so it is split on its own (L441–470 plus a continuation). The fact (L475) is in a 466-token chunk from `### Cadence` through Eligibility and the sections after it, where v1 had a short section.
- **Code-review catch (fixed):** the token-matched block read the depth-20 list even when the matched k was ≤ 5. On a near-tie row, it could disagree with the same run's recall@5, and recall at the matched k is the decision metric (AC-9). It now reads the k=5 list for k ≤ 5, and a test covers it.
- **Integration fix:** the new chunk test assumed the dev DB had no rows of the new configs. It now compares their counts before and after its rolled-back transaction.
- **Code-review items not fixed:** listed for Arun in the PR.

---

Prev: [2026-10-19: structure-aware chunker build, spec 0005](2026-10-19-chunker-build.md)
