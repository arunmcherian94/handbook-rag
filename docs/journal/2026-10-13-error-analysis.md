# 2026-10-13: error analysis, seed traces

- **Approach: open coding first** (the first step of the error-analysis loop in Hamel Husain's evals guidance). Read what the system did and describe it, before any categories, causes or fixes. Record: [docs/error-analysis/2026-10-13-seed-traces.md](../error-analysis/2026-10-13-seed-traces.md).
- **Four checks per trace, in order:**
  1. **Retrieval:** is the expected page in the top k, and at which rank? Is it the chunk that holds the answer or just a chunk from the same page? Which plausible distractors came back?
  2. **Answer:** correct, partly correct, wrong or abstained against the reference. Each missing fact is then assigned a side: a *retrieval failure* if it wasn't in the retrieved chunks, a *generation failure* if it was retrieved and unused or misread. This split decides where week 2 and week 3 effort goes.
  3. **Citations:** does each cited chunk support its claim, and is the heading right? Also copied URLs and missing or unneeded citations.
  4. **Behaviour:** abstention correctness and the exact fixed strings, information not in the excerpts, hedging, padding and level of detail.
- **One fixed-format line per trace** (`Qn | retrieval | answer | citation | other`) plus a "surprised by" note. Describe what was observed, not why it happened. Causes wait until a pattern repeats.
- **Reference check against the pinned corpus.** References were written from the live site; the system reads the 2026-10-07 snapshot. Every reference fact was looked up in the pinned chunks, and `ref?` marks a reference that differs from the corpus or a corpus that disagrees with itself (6 of 10, all corrected on review).
- **Git history decides currency:** → [ADR-0017](../decisions/0017-history-decides-currency.md)
- **Limitation:** 10 traces from one run, so the pattern counts are hypotheses for choosing eval-set dimensions, not measurements.

---

Prev: [2026-10-13: baseline build, spec 0003](2026-10-13-baseline-build.md) · Next: [2026-10-14: eval set design](2026-10-14-eval-set-design.md)
