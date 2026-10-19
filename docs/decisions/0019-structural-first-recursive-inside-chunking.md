# 0019. Structural first, recursive inside: headings bound chunks

- **Status:** proposed
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

## Informed by
- [Yang, Structure-Aware Semantic Chunking with Title-Chain Prefixes](../reading/week-02.md#yang-structure-aware-semantic-chunking-with-title-chain-prefixes-arxiv-260800824)
