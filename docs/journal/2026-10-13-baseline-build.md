# 2026-10-13: baseline build, spec 0003

- **Answer model and API:** → [ADR-0005](../decisions/0005-answer-model-and-api.md)
- **Embedding failure handling:** → [ADR-0007](../decisions/0007-embedding-failure-handling.md)
- **Embedding model and schema:** → [ADR-0004](../decisions/0004-embedding-model-and-schema.md)
- **Changed content invalidates embeddings.** `chunk_id` doesn't include content, so a doc edit or chunker fix can give an existing ID new text. The chunk run deletes those embeddings in the same transaction. Gate catch while answering review comment 2: without it, a stale vector would sit silently beside new text.
- **Grounding prompt and fixed abstentions:** → [ADR-0006](../decisions/0006-grounding-prompt-fixed-abstentions.md)
- **/code-review catches (fixed):**
  - `ask` tokenized the question without `disallowed_special=()`, so a question containing `<|endoftext|>` crashed after the paid answer call, with no trace line.
  - Embed let 4xx statuses other than 400/422/401/403/404/429 escape raw. 408 and 409 are now retried; other 4xx (such as 413) are isolated like bad input.
  - The query embedding in `ask` had no retries, because the embedder's SDK retries are off. It now uses the same capped policy as `make embed`.
  - **Data integrity:** a `make chunk` running during `make embed` could store a vector computed from a chunk's old text. The insert now requires `md5(content)` to match the embedded text. A test confirms that a chunk edited mid-request gets no vector, and that it fails without the check.
  - The heading probe was measured on decoded text, so a window opening on a split multi-byte character could miss the heading right after it. It's now measured on raw bytes, past UTF-8 continuation bytes, with a test using 龘, which cl100k splits across 3 tokens.
  - An adapter error (vector count or dims mismatch) stopped the run without the chunk-range log. The range is now logged for any exception.
- **/code-review, lower priority (fixed with Arun's OK):**
  - Citation parsing now expands ranges (`[1-3]`, `[1–3]`) and accepts `;`. Groups with a number above 99 (years, amounts) are ignored, not flagged.
  - The chunk delete uses `NOT EXISTS` against `unnest(ids)`, not `<> ALL(array)` (O(rows×ids)). Added an index on `chunks(doc_id)` for ingest's cascaded deletes.
  - Removed the dead `(no heading)` fallback in `ask`, since retrieval always returns a heading or the doc title.
- **Gate catch: heading attribution for doc openings.** Docs whose body starts with blank lines and then a heading got `heading = NULL` for chunk 0, because the heading sits a byte after the window start. Found in the vector sanity check: 4,050 first chunks had no heading. The fix measures from the chunk's first non-blank character, and a unit test covers it. `FORCE=1` re-chunk: content changed 0, so all embeddings were kept. NULL first-chunk headings dropped to 1,906; those are genuine intro text before the first heading, and 268 docs have no headings at all.
- **Title fallback for citations** (Arun, 13 Oct): when a chunk has no heading, retrieval returns `COALESCE(c.heading, d.title)`, so citations and the prompt show the doc title. The fallback lives in the query, not in `chunks.heading`, so NULL keeps meaning "no section heading" and no re-chunk was needed. Spec AC-1 and AC-6 were amended.
- **Seed-question run** (10 questions, ≈ $0.04): no empty retrievals, no out-of-range citations, no truncation, and every trace line complete. Answer quality wasn't judged; that's the eval's job. Mechanical findings:
  - **Gate catch, fixed: Hugo heading attributes.** Headings kept `{#visa-tips}`, `{.h5}`, `{.text-danger #red}` and whole-heading `**bold**` (≈ 450 chunks). Now stripped, with a unit test. `FORCE=1` re-chunk: content changed 0, embeddings kept.
  - **Limitation: a chunk spanning sections is cited by its start heading.** In Expenses chunk 20, `### Internet` begins partway through a chunk that opens in the Gifts section, so Q3 cited the $100 internet cap to "Team Member Significant Life Events and Team Member Gifts". This is inherent to fixed windows plus heading-at-start (AC-1). Options for week 2:
    - store every heading inside the chunk, and cite "start → … → last"
    - cite the section holding the most tokens
    - structure-aware chunking that never crosses a heading
  - **Limitation: partial abstention isn't a fixed string.** Q6 answered part of the question, then wrote "I don't know the exact reimbursement date or timeline…". Exact-match abstention detection misses this. Prompt changes wait until there's a measurement (the baseline prompt is frozen).
  - **Limitation: answers can contain URLs copied from excerpt text.** Q4 copied a form link and a relative handbook link. Citations are still mapped by code. "The model never writes URLs" holds for citations only.
- **Design patterns:** → [ADR-0008](../decisions/0008-design-patterns.md)
- **Limitation: chunking runs in one transaction.** It's fine at ~22k rows / ~45 MB, and AC-2 wants it (retrieval never sees a half-rechunked corpus). It wouldn't scale to millions of docs: long-held locks, WAL growth, bloat, all work lost on one failure, every doc re-chunked when few changed, and an ID-list delete that grows with the corpus. Open ideas, not decisions:
  - incremental per-doc chunking keyed on a content hash (with the incremental-sync and chunk-hash follow-ups)
  - a staging table swapped in with one short transaction for full rebuilds
  - several parameter sets side by side
- Links:
  - [Chat Completions reference](https://developers.openai.com/api/reference/resources/chat)
  - [Responses reference](https://developers.openai.com/api/reference/resources/responses)
  - [Reasoning guide](https://developers.openai.com/api/docs/guides/reasoning)
  - [gpt-5.4-mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
  - [Embeddings reference](https://developers.openai.com/api/reference/resources/embeddings/methods/create)
  - [Rate limits guide](https://developers.openai.com/api/docs/guides/rate-limits)

---

Prev: [2026-10-12: baseline decisions, spec 0003](2026-10-12-baseline-decisions.md) · Next: [2026-10-13: error analysis, seed traces](2026-10-13-error-analysis.md)
