# 0019. Structural first, recursive inside: headings bound chunks

- **Status:** rejected (2026-10-19, spec 0006 runs): fixed-512 chunking stays ([0003](0003-baseline-chunking-512-64.md))
- **Date:** 2026-10-19
- **Journal:** [2026-10-19 chunking spec](../journal/2026-10-19-chunking-spec.md)

## Context
The baseline uses fixed 512-token chunks with 64 overlap ([0003](0003-baseline-chunking-512-64.md)). In run `2026-10-17-3748df5b`, page_hit@5 is 0.812 but chunk_hit@5 is 0.594: retrieval finds the right page but not the right chunk. A known limitation is chunks that span sections and are cited by their start heading only.

Options:
- **Structural:** split on Markdown headings. Boundaries follow the author's topics, and each chunk carries its heading path. Weakness: sizes vary, with over-long sections and tiny subsections.
- **Recursive:** size-driven. Cut with the coarsest separator first (paragraph, then sentence, then token), recurse on oversized pieces, then pack small pieces up to the target size with overlap. Weakness: packing merges across sections, which is the baseline's cross-section problem in a neater form.
- **Semantic:** embed sentences and cut where similarity drops. Rejected: the corpus has heading structure, so boundaries come free, and the extra embedding cost buys no new signal.

## Decision
Structural first, recursive inside:
- Headings are hard boundaries.
- A section over the max size splits recursively, with overlap only within that section.
- A tiny section merges only with siblings under the same parent, and the chunk records every heading it covers.

## Consequences
- Chunk count and size distribution change; retrieved tokens are reported next to recall.
- Citations stay valid, by heading text.
- The effect on the 7 right-page-wrong-chunk rows is a hypothesis until the spec 0005 run measures it.
- Follow-up runs: size and overlap sweeps; title-chain prefix.
- Measured in run `2026-10-19-62a52a83` against `2026-10-17-3748df5b`: chunk_fact_recall@5 fell from 0.495 to 0.358. Most of the gap is the smaller token budget at k=5 (−0.037 at a matched 2,335 tokens); the rest is short sections that match the question's wording while the fact sits in the adjacent section. Heading-only chunks are a minor factor (0.358 → 0.374 when excluded; [journal](../journal/2026-10-19-chunker-build.md)) → [summary](../eval/results/2026-10-19-62a52a83/summary.md).

- **Negative result, spec 0006 (2026-10-19):** retrieval-only runs at depth 20 against the new baseline `2026-10-19-d2625d91` (same top 5 as `3748df5b` on all 33 rows). The decision metric is chunk_fact_recall at each run's token-matched k (target 2,335 tokens); a change counts only if it exceeds the larger SE.

  | config | run | recall@5 | matched k | recall @ matched k |
  |---|---|---|---|---|
  | `fixed-512-64` | d2625d91 | 0.495 | 5 | 0.495 ± 0.081 |
  | `structural-v1` | f06df047 | 0.358 | 13 | 0.421 ± 0.076 |
  | `structural-v2` (packed) | e585d65b | 0.375 | 7 | 0.417 ± 0.078 |
  | `structural-v3` (packed + prefix) | 068599a6 | 0.422 | 7 | 0.469 ± 0.081 |
  | `fixed-512-64-prefixed` | fbadbf12 | 0.531 | 5 | 0.531 ± 0.081 |

  - Boundaries (v2 vs fixed): −0.078, no difference. Both together (v3 vs prefixed): −0.063, no difference. No structural config beats its fixed counterpart, so fixed-512 stays (stop rule).
  - At k=5, which users get while k is frozen, structural is worse: paired over the same rows, v2 − fixed is −0.120 ± 0.054 (7 rows lose, 1 wins) and v3 − prefixed is −0.109 ± 0.054.
  - Prefix (prefixed vs fixed): +0.036, no difference (3 rows win, 1 loses). Not adopted; carried as a second arm in the embedding-model comparison (Arun, 19 Oct; [follow-ups](../follow-ups.md#from-the-spec-0006-runs-2026-10-19)).
  - Size and overlap sweeps are dropped. Summaries: [d2625d91](../eval/results/2026-10-19-d2625d91/summary.md), [f06df047](../eval/results/2026-10-19-f06df047/summary.md), [e585d65b](../eval/results/2026-10-19-e585d65b/summary.md), [068599a6](../eval/results/2026-10-19-068599a6/summary.md), [fbadbf12](../eval/results/2026-10-19-fbadbf12/summary.md).

- **Negative result, spec 0006 (2026-10-19):** retrieval-only runs at depth 20 against the new baseline `2026-10-19-d2625d91` (same top 5 as `3748df5b` on all 33 rows). The decision metric is chunk_fact_recall at each run's token-matched k (target 2,335 tokens); a change counts only if it exceeds the larger SE.

  | config | run | recall@5 | matched k | recall @ matched k |
  |---|---|---|---|---|
  | `fixed-512-64` | d2625d91 | 0.495 | 5 | 0.495 ± 0.081 |
  | `structural-v1` | f06df047 | 0.358 | 13 | 0.421 ± 0.076 |
  | `structural-v2` (packed) | e585d65b | 0.375 | 7 | 0.417 ± 0.078 |
  | `structural-v3` (packed + prefix) | 068599a6 | 0.422 | 7 | 0.469 ± 0.081 |
  | `fixed-512-64-prefixed` | fbadbf12 | 0.531 | 5 | 0.531 ± 0.081 |

  - Boundaries (v2 vs fixed): −0.078, no difference. Both together (v3 vs prefixed): −0.063, no difference. No structural config beats its fixed counterpart, so fixed-512 stays (stop rule).
  - At k=5, which users get while k is frozen, structural is worse: paired over the same rows, v2 − fixed is −0.120 ± 0.054 (7 rows lose, 1 wins) and v3 − prefixed is −0.109 ± 0.054.
  - Prefix (prefixed vs fixed): +0.036, no difference (3 rows win, 1 loses). Not adopted; carried as a second arm in the embedding-model comparison (Arun, 19 Oct; [follow-ups](../follow-ups.md#from-the-spec-0006-runs-2026-10-19)).
  - Structural size, overlap and min-size sweeps are dropped. Summaries: [d2625d91](../eval/results/2026-10-19-d2625d91/summary.md), [f06df047](../eval/results/2026-10-19-f06df047/summary.md), [e585d65b](../eval/results/2026-10-19-e585d65b/summary.md), [068599a6](../eval/results/2026-10-19-068599a6/summary.md), [fbadbf12](../eval/results/2026-10-19-fbadbf12/summary.md).

## Informed by
- [Yang, Structure-Aware Semantic Chunking with Title-Chain Prefixes](../reading/week-02.md#yang-structure-aware-semantic-chunking-with-title-chain-prefixes-arxiv-260800824)
