# Follow-ups (not built)

- **Chunk dates for recency (week 2 or later):** store a per-chunk date from `git blame` that skips the bulk commits (968e3521af, bee431b547, 4469685d7b), and show it to the model with each chunk so it can prefer the newer source. Blame needs network access on the blobless clone. Measure it against the `history-only` facts.
- **Synthetic retrieval set (week 2):** questions generated from sections (not chunks), labelled synthetic, scored for retrieval only and always reported apart from v1. Gives chunking and embedding comparisons more statistical power than 33 rows. Size from spec 0008's paired spread (sd 0.25 for 3-large, 0.43 for Qwen): to clear 2 paired SEs on a true +0.05, about 105–300 rows for even odds and 210–600 for 80%; on +0.09, about 30–90 and 65–190. Aim for a few hundred (Arun, 21 Oct).
- **Graded nDCG:** gains 2/1/0 from required/alternate page tiers, after the tiers are reviewed as relevance labels.
- **Answer evaluation, week 3 before hybrid search (spec 0009; Arun, 21 Oct):** the harness scores abstention and citation form, not correctness or grounding ([ADR-0016](decisions/0016-code-checks-before-judges.md) deferred judges; its binary fact checks were never built). Week 3's retrieval changes should be judged on answers too, and it must exist before the answer model unfreezes in week 4. Fallback: first day of week 4. In cost order:
  1. Generator abstention, code only: rows whose top 5 hold the required facts but the answer abstains (49, 100, 58 on 21 Oct). Splits false abstention into retrieval misses and generator refusals.
  2. Answer fact recall, binary judge per `[required]` fact ("does the answer state this?"). Against chunk_fact_recall it measures what generation loses. Claude judge, cross-family from gpt-5.4-mini.
  3. Groundedness, binary: every claim supported by the chunk it cites (would catch Qwen's row 47, Belgium's figure given for France).
  4. Validation per ADR-0016 (c): Arun labels answers, a held-out test portion, each judge reported as "checked against N labels, TPR x, TNR y".
  5. Answer-model comparison on identical retrieved chunks (the answer-model check below).
- **False-premise rows:** add 2–3 out-of-corpus false-premise questions in a later eval version.
- **Incremental sync:**
  1. `git fetch`.
  2. `git diff --name-status OLD..NEW -- content/handbook`.
  3. Apply the changes: upsert A/M, delete D, delete and insert R. Deletes matter for permissions, because a page pulled from public must leave retrieval.
  4. Record a sync-run log (old SHA → new SHA, counts).
- **Chunk-level hashes** plus pipeline version columns for incremental re-embedding. A content-hash embedding cache, keyed by (model, input text), would also stop identical text in two chunk configs from being embedded twice ([ADR-0020](decisions/0020-chunk-configs-coexist.md)).
- **Semantic chunking:** revisit only if structure-aware chunking leaves the right-page-wrong-chunk rows (52, 53, 8, 10, 99, 38, 89) unfixed. The corpus has heading structure, so boundaries come free ([ADR-0019](decisions/0019-structural-first-recursive-inside-chunking.md)).
- **Partition chunks and embeddings when an ANN index arrives:** LIST-partition by `config_id` and model, with a typed HNSW index per partition, to avoid filtered-HNSW recall loss ([ADR-0020](decisions/0020-chunk-configs-coexist.md)).
- **Contextual retrieval, optional, end of plan if needed (Arun, 21 Oct):** before embedding, an LLM writes 50–100 tokens placing each chunk in its document (Anthropic, Sep 2024: top-20 retrieval failures −35% with contextual embeddings, −49% with contextual BM25, −67% with reranking). It targets our wrong-entity misses (row 58's five "Time Off Policies" chunks; Qwen's row 47). Cost: one LLM call per chunk with its document in the prompt, about 162M input tokens for `fixed-512-64` (22,378 chunks; characters ÷ 4) and 1.7M output, tens of dollars uncached, plus a re-embed. Prompt caching or a section-plus-intro window cuts it. The heading-path prefix is the free version; test that first. Moved off the week-2 roadmap.
- **Review agents** for spec conformance and architecture.
- **Answer-model check:** if the seed outputs show grounding, abstention or citation problems, run 10 questions on identical retrieved chunks through gpt-5.4-mini and Sonnet 5.5 (about $0.35) before the week 3 freeze.
- **Chunk expansion / parent-child:** retrieve small, then pass neighbouring chunks to the answer.
- **Production observability** (PR #7 review):
  - Replace or augment the JSONL traces (spec 0003, AC-8) with a tracing tool that has nested spans (retrieve → prompt → LLM), cost and latency dashboards, and a link from traces to eval runs.
  - Candidates to brainstorm:
    - [LangSmith](https://docs.smith.langchain.com/)
    - [Langfuse](https://langfuse.com/docs) (open source, self-hostable)
    - [Arize Phoenix](https://docs.arize.com/phoenix) (open source)
    - [Braintrust](https://www.braintrust.dev/docs)
    - plain OpenTelemetry with the [GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
  - Criteria: self-hosting vs SaaS, vendor neutrality (OTel), eval integration, and cost.
  - Best decided alongside the eval harness.

## From the baseline run (2026-10-17)

- **False abstention:** 39% of answerable rows abstain. Code these rows against what was retrieved: did retrieval miss, or did the model refuse with the evidence in context? That decides the answer-model check above, which has to happen before the week 3 freeze.
- **Synthesis:** chunk_all_required@5 is 0.00 (n=8). No single top-5 set covers all the facts a synthesis row needs. Candidates: larger k, parent-child chunks, hybrid search.
- **Recency:** chunk_fact_recall@5 is 0.35. This is the target for the chunk-dates follow-up.
- **Page hit, chunk miss:** rows 52, 53, 8, 10, 99, 38, 89 found the right page but not the right chunk. These are a chunking signal for week 2.

## From the spec 0005 build review (2026-10-19)

Lower-priority `/code-review` items, noted for later (Arun, 19 Oct). Details in [the build journal](journal/2026-10-19-chunker-build.md).

- **Heading-only parent chunks:** a heading followed directly by a child heading becomes a chunk of a few tokens, since AC-8 forbids merging with a child. Excluding them at query time (19 Oct preview) moved recall@5 only from 0.358 to 0.374 and page_hit@5 not at all, so they are not the main cause. Small heading-plus-teaser sections are. Size and overlap sweeps are dropped under the stop rule ([journal](journal/2026-10-19-chunker-build.md)).
- **Merged heading paths read like nesting:** a merged chunk stores the first path plus each sibling's heading (AC-9), so `Per diem > France > Germany` looks nested. Store or render merged siblings distinctly.
- **Mostly-overlap windows:** `pack` can emit a window that is nearly all overlap when the only cut sits just past the previous end. Rare; costs a near-duplicate chunk.
- **Front-matter line count:** `chunk.run` re-reads each source file to count front-matter lines. Ingest could store the count instead.
- **Embed cost query:** the cost SQL repeats the pending-chunks predicate; derive it from `PENDING`.

## From the spec 0006 build (2026-10-19)

- **Stale prefixed vectors:** for a prefixed config, the embedded text includes `documents.title` and `heading_path`, but `flush` and embed's insert guard only notice changes to `content`. A new pin that changes a title or a heading path without changing a chunk's bytes would keep the old vector. That can't happen at pin 5273b21. If a prefixed config is kept, guard on the md5 of the embedded text instead (a spec change to AC-5).

## From the spec 0006 runs (2026-10-19)

- **Heading-path prefix, on the winner only:** every candidate in the embedding-model comparison runs on `fixed-512-64`. Only a model that beats text-embedding-3-small then gets a `fixed-512-64-prefixed` run (about $1). Adopt the prefix only if it wins there. On 3-small it was +0.036 at k=5, 3 rows won and 1 lost, within the SE (Arun, 19 Oct). Changed from both arms for every candidate (Arun, 20 Oct): 33 rows can't detect a model-by-prefix interaction.
- **Fixed size and overlap sweep, week 4 with context assembly:** 256/32 and 1024/128, then overlap 0 and 128 at 512 ([ADR-0003](decisions/0003-baseline-chunking-512-64.md)). Decide on recall at the token-matched k, after the week-3 reranker, when k unfreezes. About $0.2 of embedding per config (Arun, 19 Oct).

## From the spec 0007 review (2026-10-20)

- **Prompt injection beyond retrieval, week 5:** the Principal guardrail is structural. Groups come only from the session, and the filter runs in SQL before ranking, so no prompt text can widen what is retrieved. Claimed-identity cases (AC-15) test exactly that. It does not stop a prompt from changing the answer model's behaviour over chunks it *is* allowed to see:
  - ignoring the grounding rules
  - leaking the system prompt
  - indirect injection planted in corpus content
  - in week 5, steering agent tools into calls the user didn't intend

  Week 5 grows the claimed-identity cases into an injection suite. Agent tools take the session principal, never one from model output (spec 0007 AC-14). Model-based identity-claim detection is out of scope for spec 0007 (Arun, 20 Oct).

## From the spec 0008 review (2026-10-21)

- **`make ask` query mode, before adopting a non-OpenAI embedder:** spec 0008 gives eval a query-mode embedder without touching the frozen `ask.py`. `make ask` still builds a document-mode one. With Qwen3 or Gemini as the default, every live question would be embedded as a document: no query instruction, wrong `task_type`. Fix it in the PR that changes `DEFAULT_EMBED_MODEL` (spec 0008 AC-3, AC-9). Not needed for OpenAI models, which have no input types.
- **Indexing vectors over 2,000 dims, week 6 (ANN):** spec 0008 runs every candidate at 1,536, so only the model changes against 3-small, and HNSW on `vector` stays possible. Options if native dims are wanted later, from the [pgvector README](https://github.com/pgvector/pgvector) (checked 21 Oct):
  - HNSW on `halfvec` (up to 4,000 dims) covers 3-large's 3,072.
  - An expression index on `subvector(embedding, 1, n)`, then re-rank the shortlist on the full vector.
  - Binary quantization (`binary_quantize`, HNSW on `bit`, up to 64,000 dims), then re-rank on the full vector.
  - Dedicated vector databases, which have higher limits and usually quantize.

  Trigger: a 1,536-dim candidate that wins or loses narrowly. Then run 3-large@3072 (one change: dims) before week 6.

## Model switching (2026-10-21)

Arun, after spec 0008: embedding and answer models will keep changing, so the folder layout, design, code and schema should make a switch cheap. Target: adding or switching a model is one adapter file, one table entry and one constant, plus a re-embed and an eval run, with no schema change. Gaps spec 0008 exposed:
- `make ask` has no query-mode embedder (entry above).
- An ANN index needs typed, fixed-dims vectors: partition by model (entry under the general list).
- Every model re-embeds the whole corpus (3-large: $1.36; Qwen: 43 minutes). The content-hash cache helps only across configs, not across models.
- Prompts and reasoning settings may be model-specific on the answer side; `prompts.py` holds one prompt.
- **LLM gateway, decide in week 7** with the FastAPI service (graceful degradation, cost per query): LiteLLM, Portkey or OpenRouter give one API, fallbacks, routing, central keys and spend for answer models. It doesn't remove an embedding switch's main cost, the re-embed, and it is a new dependency. Week 6 instead if it should sit with observability.

## Reading (deferred)

- **Chroma, [Evaluating chunking strategies for retrieval](https://research.trychroma.com/evaluating-chunking):** dropped on 20 Oct because the chunking track is closed. Trigger: the week 4 size sweep.
