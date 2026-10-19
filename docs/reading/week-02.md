# Reading log: week 2

Notes from reading done for handbook-rag. Each entry: link, summary,
and what it changes in this project. Newest first within each date.

---

## Mon 19 Oct 2026

### Yang, Structure-Aware Semantic Chunking with Title-Chain Prefixes (arXiv 2608.00824)

https://arxiv.org/abs/2608.00824 (Aug 2026, single author). Abstract only.

Summary:
- **Pipeline:** a header split, then a semantic merge, then a title-chain prefix. The prefix reuses the document's own header hierarchy, so it adds no LLM calls (unlike contextual retrieval).
- **Setup:** a production Markdown knowledge base, with 1,600 stratified queries. This is close to our corpus.
- **Reported result:** MRR@5 rises from 0.374 to 0.463 on the full set (+23.8%), and from 0.828 to 0.925 on the answerable subset (n=563). Our baseline MRR is 0.380, so the starting points are similar. This is one paper's claim, and I've only read the abstract.
- **Main methodological finding:** in a prefix on/off ablation over the same pool, human annotator agreement fell from κ 0.45 to 0.04 under identical prompts. The paper argues this invalidates a common way of evaluating chunking changes, and recommends judging each retrieved candidate at retrieval time instead.

Takeaway: the title-chain experiment we already have planned makes sense. It costs nothing in LLM calls and fits our heading-structured corpus.

What it changes here:
- **No change to spec 0005.** The title-chain prefix stays a later, separate run, so there is one change per run.
- **It backs one design choice.** Our planned title-chain run changes only the text that gets embedded. Stored chunk content and line ranges stay fixed, and relevance comes from fixed text-span labels rather than from annotators rating what they see. So the labelling trap the paper reports doesn't apply to us ([ADR-0020](../decisions/0020-chunk-configs-coexist.md)).
- **Not adopted:** the semantic merge step. Spec 0005 merges tiny sections by heading structure instead ([ADR-0019](../decisions/0019-structural-first-recursive-inside-chunking.md)).
