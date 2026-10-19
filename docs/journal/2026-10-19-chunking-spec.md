# 2026-10-19: chunking spec, spec 0005

- **Structure-aware chunking:** → [ADR-0019](../decisions/0019-structural-first-recursive-inside-chunking.md), [spec 0005](../../specs/0005-structure-aware-chunking.md)
- **Configs coexist in one table:** → [ADR-0020](../decisions/0020-chunk-configs-coexist.md). That ADR covers the production pattern (versioned index plus alias swap, embedding cache), what `embed_input` is for, and when to switch to partitions.
- **Spec catch: the relevance rule would under-score heading-bounded chunks.** Spec 0004's rule treats a chunk's first and last lines as possible fragments and relies on the overlapping neighbour chunk to hold them whole. Heading-bounded chunks have no overlap across headings, so a short cited line just under a heading could never match. Fix in spec 0005 AC-10: an edge line counts as whole when the chunk is line-aligned. Baseline chunks have no line range and keep the old rule.
- **Finding: fact recall never used line ranges.** Relevance is text matching against chunk content. Stored line ranges are what let AC-10 tell a whole edge line from a cut one.
- **Section profile at the pin:**
  - 52,787 sections; p50 111 tokens, p90 383.
  - 31% are under 64 tokens.
  - 6% are over 512, and they hold 28% of all tokens.
  - So the structural config makes more, smaller chunks, and retrieved tokens@5 is reported next to recall.
- **Housekeeping:**
  - PR #18 reviewed after merge. ADR-0013's wording was fixed in PR #19, which also added the similarity-operator comment in `ask.py`.
  - ADR-0011's date was checked and kept, since its decision is the 15 Oct one.
  - Deleted the local branches eval-harness, eval-harness-followups and spec-0004-eval-harness. All three were squash-merged, content-checked, and already gone from the remote.

---

Prev: [2026-10-17: baseline eval numbers](2026-10-17-baseline-numbers.md)
