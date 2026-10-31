# 2026-10-30: hybrid search runs, spec 0011

The three measurement runs from the [spec 0011 build](2026-10-29-hybrid-build.md), plus a separate audit of why hybrid scores lower than dense. The decision (hybrid not adopted) is at the end.

## Runs
All runs are at harness `cd22409` (#49 merged), config `fixed-512-64`, 3-large@1536, retrieval-only, admin.

| run | retriever | run ID | spend |
|---|---|---|---|
| eval vs `2026-10-21-d83f3edc` | hybrid | `2026-10-30-e1e47d72` | $0.000113 |
| eval | fts | `2026-10-30-e95364c1` | $0 |
| permissions-v1 | hybrid | `2026-10-30-a4975b23` | $0.000066 |

- **FTS run had no `BASELINE`:** spec 0011 lists the fts run with `BASELINE=2026-10-21-d83f3edc`, but it ran without one, so its summary has no comparison section. The fts column in the results table comes from the two summaries side by side, and no decision rests on it.
- **`BASELINE` takes the full run ID.** The short ID `d83f3edc` fails the dry run with "baseline run not found". `BASELINE=2026-10-21-d83f3edc` works.

## Results (n = 32; row 22 has answer-only facts and scores nothing)

| metric | dense | hybrid | fts |
|---|---|---|---|
| chunk_fact_recall@5 | 0.583 | 0.521 | 0.148 |
| chunk_hit@5 | 0.719 | 0.625 | 0.219 |
| page_hit@5 | 0.844 | 0.812 | 0.312 |
| chunk_mrr | 0.504 | 0.393 | 0.084 |
| chunk_fact_recall@10 | 0.744 | 0.626 | 0.216 |
| chunk_fact_recall@20 | 0.819 | 0.844 | 0.357 |
| chunk_all_required@5 | 0.406 | 0.438 | 0.094 |

- **Paired delta (hybrid − dense), chunk_fact_recall@5:** −0.062, paired SE 0.057, −1.08 SE. The adoption bar was +2 SE, set in advance. At @20 the delta is +0.025 (+0.68 SE).
- **Won (3):** 52 (0 → 0.5), 53 (0 → 1), 44 (0.8 → 1).
- **Lost (7):** 10 (0.857 → 0), 8, 49, 89, 35 (each 0.5 → 0), 58 (1 → 0.5), 11 (0.667 → 0.333).
- **Unchanged:** 22 rows.
- **Near-tie rows 32 and 93:** unchanged (0 and 1), and flagged `near_tie` in neither run.

### Ranks of the missing facts
`fts_rank` is computed over the whole FTS match set with a read-only query (the run rows record only to depth 20). `fts_query_empty` is false on every row.

| row | fact | hybrid rank | dense_rank | fts_rank | rrf_score |
|---|---|---|---|---|---|
| 8 | F1 | 17 | 6 | 79 | 0.0152 |
| 8 | F4 | 13 | 2 | 169 | 0.0161 |
| 49 | F1 | 18 | 8 | 363 | 0.0147 |
| 49 | F4 | 9 | 3 | 1101 | 0.0159 |
| 89 | F2 | 9 | 5 | no match | 0.0154 |
| 89 | F4 | 15 | 8 | no match | 0.0147 |
| 53 | F1 | 4 | 17 | 7 | 0.0279 |
| 55 | F1 | 18 | 8 | 14113 | 0.0147 |
| 65 | F1 | >20 | >20 | 1188, 3159 | — |
| 92 | F1 | >20 | >20 | 89 | — |
| 92 | F4 | >20 | >20 | 1172, 1784 | — |

Rows 65 and 92, the two rows dense misses entirely, are not rescued by FTS. Every fact chunk ranks well past the fusion depth of 50.

### Permissions (hybrid vs dense `086eca8a`)
- **Leak** is 0 at k = 5 and k = 20. **Over-block** is 0 at both.
- **Authorized recall:** 0.913 @5 and 1.000 @20 (n = 25), against dense's 0.878 and 1.000 (n = 26).
- **Not paired:** validity is computed per retriever. On hybrid, P-070's UK target (`ltd-benefits-uk.md`) drops out of admin's top 20, so P-070 becomes invalid and 49 cases score instead of 50.
- **Same 25 cases:** dense 0.873 against hybrid 0.913 @5. The only change is P-038 (0 → 1). On P-070, dense scored 1.0 at both k.

## Why hybrid scores lower
A fresh-context agent audited the runs read-only and without spend. It recomputed every figure above from the run files and found no mismatch. Dense lists were rebuilt from the saved query vectors (`runs/ann/query-vectors.jsonl`), and re-fusing them reproduced hybrid's per-row chunk_fact_recall@5 on all 32 rows. Causes, strongest evidence first:

1. **FTS contributes no new fact chunks.**
   - The FTS top 50 holds 1,294 chunks that are not in the dense top 50. Only 2 of them carry a required fact (both in row 32, FTS ranks 25 and 30), and the FTS top 20 holds none.
   - The best possible top 5 has chunk_fact_recall@5 0.875 from the dense top 50, and still 0.875 with the FTS top 50 added.
   - So fusion can only reorder dense's candidates.
2. **Equal-weight RRF favours chunks found by both lists.**
   - The OR-of-lexemes query matches a median of 11,334 of 22,378 chunks (51%), so FTS rank is close to noise.
   - FTS ranks 1–5 carry a fact 4.4% of the time, against 21.9% for dense ranks 1–5.
   - A chunk in both top-50 lists scores at least 2/110 = 0.0182. That beats a chunk only dense found, even at dense rank 1 (1/61 = 0.0164).
   - Both-list chunks take 131 of the 160 hybrid top-5 slots, and carry a fact 18% of the time.
   - In 6 of the 7 lost rows (8, 10, 11, 35, 49, 58), a fact chunk at dense rank 2–3 with no FTS rank fell to hybrid rank 6–13, pushed down by both-list chunks from dense ranks 3–46. In row 10, dense #2 carries F1–F6, and chunks at dense ranks 10, 40 and 41 outrank it.
   - The wins are the same effect in reverse: fact chunks at dense/FTS ranks 11/5 (row 52), 17/7 (row 53) and 24/13 (row 44).
3. **The lists alternate when few chunks are in both.**
   - 11 rows have fewer than 5 chunks in both lists. FTS rank n ties dense rank n, and only the tie-break puts dense first, so the top 5 alternates between the lists.
   - Row 89 shows this: its dense-rank-5 fact chunk falls to rank 9.
   - The 10 top-5 slots that went to FTS-only chunks carry 0 facts. This matches spec 0011's prediction about when FTS-only chunks reach the top 5.
4. **The question wording makes poor search terms.**
   - Conversational words survive as lexemes: `pleas` (4,127 chunks), `need` (9,233), `get`, `actual`, `m` from "I'm" (563), and `us` from "US" (2,713).
   - Row 87's typo "competitiors" matches 3 chunks.
   - `posh` (row 92) matches 0 chunks, so no lexical method reaches it.
5. **Missing IDF is real but not the main cause.**
   - A simulated BM25 list (k1 1.2, b 0.75, built from `tsvector` counts) scores 0.344 on its own, against 0.148 for `ts_rank_cd`.
   - Fused by RRF it does worse (−0.100, −1.67 SE). It overlaps dense more, so cause 2 grows.

## Variants tried offline
Re-fused from the same lists at no cost. Indicative only: n = 32, and the tuned rows are fitted on the same 32 rows they are scored on.

| variant | chunk_fact_recall@5 delta vs dense | kind |
|---|---|---|
| AND query (`plainto`/`websearch`), dense when the FTS list is empty | +0.016 (+1.0 SE); 17–18 rows empty, so mostly dense | principled |
| weighted RRF, FTS weight 0.5 / 0.33 / 0.25 | −0.004 / +0.011 / +0.002 | tuned |
| RRF k = 10 / 20 | −0.034 / −0.035 | tuned |
| RRF k = 30, 100 or 200 | same as k = 60 | tuned |
| FTS depth 20 / 10 / 5 | −0.030 / −0.021 / −0.037 | tuned |
| both lists at depth 20 | −0.040 | tuned |
| `ts_rank_cd` normalization 1 / 4 / 2 / 8 | −0.062 / −0.067 / −0.103 / −0.103 | semi |
| RRF over dense candidates only | −0.020 (@20: +0.041) | semi |
| BM25 in place of FTS, equal / 0.5 weight | −0.100 / −0.074 | principled / tuned |
| dense top 4, then FTS #1 or BM25 #1 in slot 5 | −0.031 / −0.016 | tuned |

No variant comes near +2 SE, and the best only get back to dense level. Because of cause 1, fusion's upside on v1.2 is limited to reordering dense's own candidates. Only 7 fact chunks could move up into the top 5 (rows 32, 38, 44, 52, 53 and 99). A reranker reorders those same candidates (spec 0012).

## Abbreviation probe (spec 0011, evaluation step 4; run 31 Oct)
A finding, not a metric. It is free: FTS lists come from `hybrid.search_fts` as admin, and dense and hybrid figures come from the existing rows 46 and 100.
- **FTS treats the two phrasings as unrelated:**
  - "PTO" becomes the lexeme `pto` and matches 240 chunks.
  - "paid time off" becomes `paid` and `time` ("off" is a stop word) and matches 7,994 chunks under the OR query.
  - 50 chunks contain both `pto` and `paid` & `time`.
  - The two FTS top 10s share 1 chunk.
  - There is no synonym dictionary, which is out of scope in spec 0011.
- **v1.2 doesn't feel this:** rows 46 and 100 ask with "PTO", and their fact chunks are the same two `time-off-types` chunks, which contain both "PTO" and "paid time off".

| row | dense fact ranks | fts fact ranks | hybrid fact ranks | chunk_fact_recall@5 (dense / hybrid) | chunk_mrr (dense / hybrid) |
|---|---|---|---|---|---|
| 46 | 3, 4 | 14, 15 | 1, 2 | 1.0 / 1.0 | 0.333 / 1.0 |
| 100 | 1, 2 | 24, 39 | 2, 4 | 1.0 / 1.0 | 1.0 / 0.5 |

Dense handles the abbreviation on both rows. A question phrased one way, about a page that uses only the other phrasing, would get no help from FTS. That case is for the keyword-heavy re-test in follow-ups.

## AC-7: no paid dense re-run (Arun, 31 Oct)
The [29 Oct entry](2026-10-29-hybrid-build.md) left exact reproduction of `d83f3edc` as a paid dense re-run. It is not run, for three reasons:
- **The original vectors are gone:** the query vectors behind `d83f3edc` are not stored. A paid run would embed the questions again, and re-embeddings drift by about 1e-4, which is what swaps the near-tie rows 32 and 93. A re-run would be no more exact than the free check.
- **The free check passes:** with the saved 24 Oct vectors, 31 of 33 rows have the same top 5 (32 and 93 swap), and the audit reproduced dense's per-row chunk_fact_recall@5 on all 32 scored rows.
- **The code is unchanged:** the dense SQL and `ask.py` are untouched by #49.

## Decision: hybrid not adopted (Arun, 31 Oct)
Dense stays the default retriever. Hybrid misses the pre-set bar: −0.062 paired delta, −1.08 SE, against +2 SE. `DEFAULT_RETRIEVER`, `ask.py` and the answer path are unchanged, so no ADR is needed. `--retriever fts|hybrid` stays as a measurement flag.

Alternatives considered:
- **Adopt hybrid as the default.**
  - For: recall@20 is +0.025, and rows 52, 53 and 44 gain from keyword matches.
  - Against: it misses the bar, and every early-rank metric falls (MRR −0.111, hit@5 −0.094, recall@3 −0.146). The loss is structural (cause 2), and no offline variant recovers it.
- **Keep hybrid as an opt-in and re-test it under the spec 0012 reranker, or with BM25.**
  - Against: with dense's top 50, the best possible top 5 is 0.875 with or without FTS's top 50 (cause 1), so reranking hybrid's candidates can reach nothing that dense's candidates don't already hold. BM25 fused scored −0.100.

Re-testing hybrid waits for an eval set with keyword-heavy questions ([follow-ups](../follow-ups.md)).

## Caveats
- **Literature:** the comparison with published hybrid results was made from memory and not checked against sources, so it is not recorded here.
- **Saved query vectors:** they are the 24 Oct re-embeddings, not the vectors from the original run. They reproduce per-row chunk_fact_recall@5 everywhere; the top-5 order differs only on near-tie rows 32 and 93.
