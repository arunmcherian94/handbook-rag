# 0003. Fixed 512-token chunks with 64 overlap for the baseline

- **Status:** accepted
- **Date:** 2026-10-12
- **Journal:** [2026-10-12 baseline decisions](../journal/2026-10-12-baseline-decisions.md)

## Context
Token profile of the 4,088 docs (cl100k_base, the tokenizer for `text-embedding-3-*`, confirmed via `tiktoken.encoding_for_model`):
- 9.29M tokens in total.
- Per doc: p50 1,333, p90 5,097, p99 14,194, max 65,283.
- 180 docs exceed the 8,191-token embedding input limit, so chunking is required, not optional.

Embedding cost barely depends on chunk size: about 10.3–11.3M tokens for every size/overlap tried. Choose the size for retrieval quality, not price.

"Most docs fit in one 1024 chunk" was wrong: only 42% do (1,709 of 4,088). Big chunks give the generator more context but average more topics into each vector (dilution). For example, Expenses' Internet paragraph would share a vector with co-working and phone rules.

Chunking ladder, from simplest: fixed tokens → recursive (paragraph, then sentence) → markdown headings → semantic → contextual (an LLM writes a context line per chunk) → parent/child.

## Decision
- **512/64 chosen over 1024/128.** 512 sits mid-range, so week 2 can sweep 256 and 1024 on either side.
- The baseline is fixed-size on purpose. The rest of the ladder are week 2 experiments.
- **Overlap = 64 tokens** (cl100k tokens, not characters or words). Each chunk repeats the last 64 tokens of the previous one, so windows start every 448 tokens (512 − 64).
  - **What 64 tokens is:** about 45–50 English words, or 2–3 typical policy sentences. A one-sentence fact like "Internet costs are reimbursed up to a monthly cap of USD 100…" is about 21 tokens.
  - **Why overlap at all:** with fixed windows, a sentence can be cut at a boundary. Any sentence up to 64 tokens long appears whole in at least one chunk, so a fact is never retrievable only as two half-sentences.
  - **How 64 was chosen:** the common 10–20% heuristic, at the low end (12.5%). Not tuned. Measured at 512:

    | Overlap | Chunks | Embedded tokens |
    |---|---|---|
    | 0 | 20,310 | 9.29M |
    | 32 | 21,276 | +5.9% |
    | **64** | **22,378** | **+12.6%** |
    | 100 | 23,807 | +21.2% |

  - **Trade-off:**
    - Against 32: it covers 2–3 sentences, not about one.
    - Against 100: the top-5 more often holds two near-duplicate neighbouring chunks, and each duplicate uses up one of only 5 slots.
    - The money is trivial (+12.6% ≈ $0.02).

## Consequences
- Overlap is a week 2 sweep candidate (0 / 32 / 64 / 100).
- **k=5:** recall@5 is the standard operating point. 5×512 ≈ 2.6k tokens of context. k is coupled to chunk size (k × size = context budget), and the eval can sweep k without re-embedding.

## Informed by
- [Pinecone: chunking strategies for LLM applications](../reading/week-01.md#pinecone-chunking-strategies-for-llm-applications)
- [Pinecone chunking strategies](https://www.pinecone.io/learn/chunking-strategies)
