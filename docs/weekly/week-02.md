# Week 2 (19–24 Oct 2026): chunking rejected, 3-large adopted, permission-aware retrieval, paid-call guardrails

**Outcome:** production retrieval is `fixed-512-64` chunks, text-embedding-3-large at 1,536 dims, exact cosine search, and a SQL pre-filter on synthetic ACLs. Structure-aware chunking was tested and rejected. 3-large was adopted as a documented exception to the pre-set bar. Filtered-HNSW recall starvation was measured on a separate copy, and production stays on exact search. Paid calls now need a separate `make paid-<target>` and a hook approval. PRs #19–#43.

## 1. Decisions

### Chunking: structure-aware rejected, `fixed-512-64` stays → [ADR-0019](../decisions/0019-structural-first-recursive-inside-chunking.md) (rejected), specs [0005](../../specs/0005-structure-aware-chunking.md), [0006](../../specs/0006-packed-sections-and-heading-prefix.md)
- **Fixed-k loss.** `structural-v1` (run `2026-10-19-62a52a83`) fell from 0.495 to 0.358 chunk_fact_recall@5. The baseline is `fixed-512-64` on text-embedding-3-small, 32 scored rows.
- **Matched-k comparison.** Spec 0006 compared each config at the k whose mean retrieved tokens match the baseline's 2,335. The baseline is `2026-10-19-d2625d91`, with recall@5 0.495 ± 0.081.

  | comparison | run | matched k | recall at matched k | delta |
  |---|---|---|---|---|
  | `structural-v1` vs fixed | f06df047 | 13 | 0.421 ± 0.076 | −0.074 |
  | `structural-v2` (packed) vs fixed | e585d65b | 7 | 0.417 ± 0.078 | −0.078 |
  | `fixed-512-64-prefixed` vs fixed | fbadbf12 | 5 | 0.531 ± 0.081 | +0.036 |
  | `structural-v3` (packed + prefix) vs prefixed | 068599a6 | 7 | 0.469 ± 0.081 | −0.063 |

- **Decision on the SE.** Every matched-k delta is inside the unpaired SE of about 0.08, so each counts as "no difference". No structural config beat its fixed counterpart, and the stop rule kept fixed-512. At k=5, the k users actually get, structural is worse by about two paired SEs: v2 − fixed −0.120 ± 0.054, v3 − prefixed −0.109 ± 0.054.
- **Heading prefix.** Not adopted (+0.036; 3 rows won, 1 lost). It was carried into the embedding comparison, where it was rejected again on 3-large: run `2026-10-21-586b1635`, +0.031 ± 0.059, 0.51 SE.
- **Sweeps.** The structural size and overlap sweeps were dropped. The fixed-512 size and overlap sweep moved to week 4, with context assembly.

### Embedding model: text-embedding-3-large@1536, a documented exception → [ADR-0022](../decisions/0022-adopt-text-embedding-3-large-1536.md), [spec 0008](../../specs/0008-embedding-model-comparison.md)
- **Pre-set rule (AC-9).** Adopt only if the mean paired delta in chunk_fact_recall at the matched k exceeds 2 paired SEs.
- **3-large@1536,** run `2026-10-21-d83f3edc` (retrieval-only, matched k = 5):
  - recall@5: 0.583 ± 0.075, against 0.495 ± 0.081 for 3-small
  - paired delta: +0.088, SE 0.045, **1.97 SE**, just under the bar
  - rows: 7 won, 2 lost, 23 tied
- **Qwen3-Embedding-8B@1536,** run `2026-10-21-c5d62f36`: +0.091, paired SE 0.076, 1.20 SE. Rejected: same mean gain, double the variance, a second provider, and 4× slower embedding.
- **Adopted as a documented exception** (Arun, PRs #31 and #32). It is a retrieval gain, not an answer-quality gain:
  - In the full runs (`2026-10-21-e602bd95` against `18f10293`), false abstention was 10/33 against 11/33, paired −0.030 ± 0.053.
  - The 5 better / 2 worse answer comparison is Claude's judgment and hasn't been reviewed.
  - Keeping 3-small was the choice that kept the rule. At n = 32 this is "probably better, cheap, reversible", not "proven better".
- **New comparison baselines:** `2026-10-21-d83f3edc` (retrieval-only) and `2026-10-21-e602bd95` (full).

### Permission-aware retrieval → [ADR-0021](../decisions/0021-permission-model.md), [spec 0007](../../specs/0007-permission-aware-retrieval.md) Part A (#35)
- **Synthetic ACLs.** The handbook is public, so `acl/policy-v1.yaml` assigns group allow-lists by path from audience signals in the content. 46 docs (379 of 22,378 chunks, 1.7%) are restricted from staff. Six fixture personas see between 1.15% (narrow) and 100% (admin) of `fixed-512-64`.
- **Pre-filter in SQL.** `make acl` copies each document's allow-list onto its chunks (`allowed_groups text[]`, GIN index). Every retrieval goes through one `SEARCH` that filters on `allowed_groups && :groups` before the cosine order. There is no unfiltered path.
- **Fail-closed.** A chunk with no ACL is hidden, never public. A principal with no groups is an error, never an unfiltered search. A stale ACL fails the run before retrieval. An ambiguous or bad redirect target stops `make acl`.
- **Typed `Principal`.** The identity module is the only place one is built, and its groups are resolved in code from the user's attributes, never from the question. `retrieve`, `ask` and the eval runner require one, with no default. Admin sees everything through explicit allow-lists, not a bypass.
- **Admin regression (AC-9).** Run `2026-10-22-7ff9d687` has the same top 5 as `d83f3edc` on 33 of 33 rows. Ordering is now `distance, chunk_id`, because duplicate pages tie exactly.

### Permissions suite run `2026-10-24-086eca8a`
- permissions-v1: 52 cases, LLM-drafted from the pin and the policy, with outcomes computed by code. 50 were scored; P-097 and P-098 are invalid under 3-large.
- Config: `fixed-512-64`, 3-large@1536, harness `c7c14798`, clean tree.
- Leaked chunks 0 and over-block 0, at k = 5 and k = 20. Leak 0 holds by construction under the SQL pre-filter; it is not an empirical result.
- Authorized recall@5 0.878 (n = 26; 24 cases n/a), and 1.000 at k = 20.
- **Why 0.878 and not 1.000:** 22 of the 26 cases score 1.0, and four lose part of their target at k = 5. In all four, the persona's top 5 is identical to admin's, so the filter removed nothing. The targets were outranked by open pages, so the shortfall is ranking, not permissions: over-block is 0, and all four reach 1.000 at k = 20.

  | case | persona, category | recall@5 | what took the top 5 |
  |---|---|---|---|
  | P-038 | us-ic, twin | 0 | the target is first at rank 9; four chunks of `promotions-transfers.md` hold ranks 1–4 |
  | P-042 | us-ic, twin | 0 | the target is first at rank 9, behind YubiKey, laptop-security and USB-encryption pages |
  | P-087 | admin, control | 0.333 | scored on facts: both target docs are in the top 5, but the chunk holding 2 of the 3 facts is at rank 6 |
  | P-093 | manager, cut-row target | 0.5 | one target is at rank 3 and the other at rank 7 |

### Part B: recall starvation on a separate HNSW path, run `2026-10-24-ddf4a2dc` (#40)
22k chunks, ef_search 40, on a measurement copy (`ann.hnsw_chunks`, pgvector defaults m 16, ef_construction 64). Production stays on exact search.

| persona (visible) | ANN recall@20, iterative scans off | returned of 20 | relaxed_order |
|---|---|---|---|
| admin (100%) | 0.981 | 20 | 0.981 |
| us-ic (98.62%) | 0.871 | 17.8 | 0.977 |
| agency (32.46%) | 0.311 | 6.2 | 0.950 |
| narrow (1.15%) | 0.178 | 3.6 | 0.995 |

- With iterative scans off, the filter starves recall, even for the ~98% personas on about a quarter of the questions.
- relaxed_order returns k every time and comes within about 0.03 of admin's 0.981 ceiling. That remaining loss comes from HNSW at ef_search 40, not from the filter.
- Fact recall rests on 17 to 32 rows per persona.
- **Recorded in ADR-0021 for when production gets an ANN index:** relaxed_order, with three conditions:
  - an outer re-sort on (distance, chunk_id)
  - `SET LOCAL` in each query's transaction
  - a log line when fewer than k rows come back
- No partitioning by group is needed at these selectivities.

### Paid-call guardrails: #39 and #42 → [spec 0009](../../specs/0009-paid-call-guardrails.md)
- **#39:**
  - Plain `make ask | embed | eval | permissions | ann` only dry-run and print an estimate. `make paid-<target>` spends.
  - The Python mains also require `HANDBOOK_PAID_RUN=1`, which only the `paid-*` recipes set.
  - A PreToolUse hook asks for a human click on any `paid-*` name or assignment of that variable. It reads the target list from the Makefile and fails closed.
  - Every paid run appends a line to `runs/spend.jsonl`.
- **#42:** a failed eval, permissions or ann run now creates its run folder before spending, so its spend line names the partial folder (`new_run_dir`).
- **Verified live:** the hook prompted on `make paid-permissions` (086eca8a). A live decline, with the spend log unchanged, has not been run yet.

## 2. Learnings
- **Heading-only chunks were the wrong diagnosis; token budget was the confound.**
  - At fixed k = 5, structural chunks are smaller, so the model sees fewer tokens.
  - Dropping heading-only chunks moved v1's recall@5 only from 0.358 to 0.374.
  - At a matched 2,335-token budget, the gap shrank from −0.137 to −0.037.
  - What remained were short "heading plus teaser" sections whose heading matches the question's wording and outranks the section that holds the fact.
  - Since then, chunking comparisons report recall at matched retrieved tokens, not only at fixed k.
- **Specs need their frozen inputs listed against open decisions.** Spec 0007 froze its AC-9 baseline on 3-small while the embedding decision was still open, so ADR-0022 moved it mid-flight to `d83f3edc`. Its control rows also rested on cut eval rows, caught at two gates (#33, #34). The spec template now has a "Depends on / frozen inputs" table, filled before the ACs (#41).
- **A rule in a prompt didn't stop an unapproved paid call; a hook does.** On 22 Oct, Claude appended `make ask` to a test command with its output hidden. It cost about $0.001, with no approval, and Arun rated it serious.
  - "Paid needs CONFIRM" lived in instructions and habit. `make ask` was the one paid target without a dry run, so neither fired.
  - The fix moved the check outside the model: dry-run by default, separate `paid-*` names, an env var only those recipes set, a hook that asks, and a spend log.
  - Two caveats were found while building it. Hooks probably load at session start: the prompts seen before a restart weren't the hook. The hook matches command text, so it stops accidents, not a determined bypass.
- **Save query vectors; re-embedding moves near-ties.**
  - Part B's exact admin path matched `d83f3edc` on 31 of 33 rows. The two misses were near-ties: distances 0.49978 vs 0.49986, and 0.60781 vs 0.60987. This is consistent with OpenAI query vectors varying slightly between calls.
  - Qwen's rank metrics also drifted between two runs, with MRR 0.522 against 0.553 and recall@5 unchanged.
  - Saving the vectors made the Part B rerun cost $0 and made it reproducible. An HNSW rebuild adds about ±0.01 of noise on top.
- **Local selectivity, not corpus share, predicts starvation.** us-ic sees 98.6% of chunks, yet with iterative scans off it got fewer than 20 results on 15 of 61 questions. The suite asks about restricted pages, and their neighbourhoods are mostly restricted. A filtered-ANN test needs queries aimed at the restricted content.

## 3. Week 2 takeaway
Week 2's results came from retrieval measurement rather than new retrieval machinery. The chunking track ended in a clean negative result once the token budget was controlled for. The embedding switch was taken knowingly below the pre-set bar and recorded as an exception, because the eval set is too small to detect a +0.09 gain reliably. The permission filter was built so that a leak is impossible by construction, with fail-closed defaults. Part B showed what would break if production moved to ANN, and what fixes it. The process lessons were about enforcement: rules held in prompts gave way to hooks, frozen-inputs tables and saved vectors.

## 4. Into week 3
- **Answer evaluation first, spec 0010, before hybrid search:**
  - code-only generator-abstention coding
  - binary answer-fact recall and groundedness judges, validated against Arun's labels
  - the answer-model check
  - Today the harness doesn't score answer correctness, and there is no judge.
- **Hybrid search:** Postgres full-text plus dense, fused with RRF, then a cross-encoder rerank. The ACL predicate must follow every new path (ADR-0021).
- **Frozen through week 3:** the answer model and prompt.
- **Re-test triggers:**
  - the heading prefix, after the reranker
  - 3-large@3072, before week 6
  - an HNSW `ef_search` sweep, before any production ANN index
- **Open:**
  - a synthetic retrieval set, because n = 32 can't detect gains of about 0.05
  - the `PERMISSIONS=on|off` spec (Arun)
  - a live decline test of the hook
