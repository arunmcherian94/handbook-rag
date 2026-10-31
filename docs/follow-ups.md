# Follow-ups (not built)

- **Chunk dates for recency (week 2 or later):** store a per-chunk date from `git blame` that skips the bulk commits (968e3521af, bee431b547, 4469685d7b), and show it to the model with each chunk so it can prefer the newer source. Blame needs network access on the blobless clone. Measure it against the `history-only` facts.
- **Synthetic retrieval set (week 2):** questions generated from sections (not chunks), labelled synthetic, scored for retrieval only and always reported apart from v1. Gives chunking and embedding comparisons more statistical power than 33 rows. Size from spec 0008's paired spread (sd 0.25 for 3-large, 0.43 for Qwen): to clear 2 paired SEs on a true +0.05, about 105–300 rows for even odds and 210–600 for 80%; on +0.09, about 30–90 and 65–190. Aim for a few hundred (Arun, 21 Oct).
- **Hybrid search re-test, once the eval set has keyword-heavy questions:** hybrid was not adopted on v1.2 ([journal, 30 Oct](journal/2026-10-30-hybrid-runs.md)). v1.2 has 32 conversational questions and few exact names, codes or rare terms, which are the cases keyword search is for. When the synthetic retrieval set (above) or a later version adds such questions, re-run hybrid with an AND query that falls back to dense when empty (+0.016 offline on v1.2), and BM25 if an extension is available. Report the keyword-heavy subset separately. Not tied to spec 0012 (Arun, 31 Oct).
- **Graded nDCG:** gains 2/1/0 from required/alternate page tiers, after the tiers are reviewed as relevance labels.
- **Answer evaluation, week 3 before hybrid search (spec 0010; Arun, 21 Oct. Earmarked as 0009 on 21 Oct; that number went to the paid-call guardrails on 24 Oct):** the harness scores abstention and citation form, not correctness or grounding ([ADR-0016](decisions/0016-code-checks-before-judges.md) deferred judges; its binary fact checks were never built). Week 3's retrieval changes should be judged on answers too, and it must exist before the answer model unfreezes in week 4. Fallback: first day of week 4. In cost order:
  1. **Built (spec 0010, 27 Oct)**, along with answer-content assertions, the code-only part of item 2. Generator abstention, code only: rows whose top 5 hold the required facts but the answer abstains (49, 100, 58 on 21 Oct). Splits false abstention into retrieval misses and generator refusals. The baseline run (17 Oct) had 39% of answerable rows abstaining; coding them against what was retrieved decides the answer-model check below.
  2. Answer fact recall, binary judge per `[required]` fact ("does the answer state this?"). Against chunk_fact_recall it measures what generation loses. Claude judge, cross-family from gpt-5.4-mini.
  3. Groundedness, binary: every claim supported by the chunk it cites (would catch row 47 in the Qwen-embedding run, where the generator answered with Belgium's figure for France).
  4. Validation per ADR-0016 (c): Arun labels answers, a held-out test portion, each judge reported as "checked against N labels, TPR x, TNR y".
  5. Answer-model comparison on identical retrieved chunks (the answer-model check below).
- **Eval set v1.3 candidates (Arun's review, 27 Oct; [fact-list-review.md](eval/fact-list-review.md)):** row 22 F1 wording (France and Belgium have no supplementary plan; cite F2–F8), and row 23 F1 cadence (the pin also says calibration happens each quarter at L229, and Sales Development reviews monthly at L102). Neither blocks the assertions: 22 F1 is `expressible: false`, and 23 F1 leaves out the cadence.
- ~~**fact-list-review.md row order (spec 0010 AC-11):** AC-11 asks for eval-set order; the file lists answerable rows first, then out-of-corpus rows. Reorder at the next edit of the file (found 29 Oct).~~ Not needed: the file already matches eval-set order. The reviewed answerable rows all come before the reviewed ooc rows in `eval-set-v1.md` (checked 30 Oct).
- **False-premise rows:** add 2–3 out-of-corpus false-premise questions in a later eval version.
- **Incremental sync:**
  1. `git fetch`.
  2. `git diff --name-status OLD..NEW -- content/handbook`.
  3. Apply the changes: upsert A/M, delete D, delete and insert R. Deletes matter for permissions, because a page pulled from public must leave retrieval.
  4. Record a sync-run log (old SHA → new SHA, counts).
- **Chunk-level hashes** plus pipeline version columns for incremental re-embedding. A content-hash embedding cache, keyed by (model, input text), would also stop identical text in two chunk configs from being embedded twice ([ADR-0020](decisions/0020-chunk-configs-coexist.md)).
- **Semantic chunking:** revisit only if structure-aware chunking leaves the right-page-wrong-chunk rows (52, 53, 8, 10, 99, 38, 89) unfixed. The corpus has heading structure, so boundaries come free ([ADR-0019](decisions/0019-structural-first-recursive-inside-chunking.md)).
- **Partition chunks and embeddings when an ANN index arrives:** LIST-partition by `config_id` and model, with a typed HNSW index per partition, to avoid filtered-HNSW recall loss ([ADR-0020](decisions/0020-chunk-configs-coexist.md)). Updated 24 Oct (spec 0007 Part B): the ACL filter doesn't need group partitions, because `relaxed_order` iterative scans recover recall at 1.15% selectivity (22k chunks, ef_search 40, on a measurement copy; production stays on exact search). The config and model filters are equality filters, and partitioning still fits them better than a shared index.
- **Contextual retrieval, optional, end of plan if needed (Arun, 21 Oct):** before embedding, an LLM writes 50–100 tokens placing each chunk in its document (Anthropic, Sep 2024: top-20 retrieval failures −35% with contextual embeddings, −49% with contextual BM25, −67% with reranking). It targets our wrong-entity misses (row 58's five "Time Off Policies" chunks; row 47 in the Qwen-embedding run, where the generator answered with Belgium's figure). Cost: one LLM call per chunk with its document in the prompt, about 162M input tokens for `fixed-512-64` (22,378 chunks; characters ÷ 4) and 1.7M output, tens of dollars uncached, plus a re-embed. Prompt caching or a section-plus-intro window cuts it. The heading-path prefix is the free version; test that first. Moved off the week-2 roadmap.
- **Review agents** for spec conformance and architecture.
- **Answer-model check:** if the seed outputs show grounding, abstention or citation problems, run 10 questions on identical retrieved chunks through gpt-5.4-mini and Sonnet 5.5 (about $0.35) before the answer model unfreezes in week 4. Also item 5 of answer evaluation above.
- **Chunk expansion / parent-child:** retrieve small, then pass neighbouring chunks to the answer. A candidate for the synthesis rows (baseline-run entry below).
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

- **False abstention:** 39% of answerable rows abstain. Code these rows against what was retrieved: did retrieval miss, or did the model refuse with the evidence in context? Merged into answer evaluation item 1 above (26 Oct).
- **Synthesis:** chunk_all_required@5 is 0.00 (n=8). No single top-5 set covers all the facts a synthesis row needs. Candidates: larger k, parent-child chunks (entry above), hybrid search.
- **Recency:** chunk_fact_recall@5 is 0.35. This is the target for the chunk-dates follow-up.
- ~~**Page hit, chunk miss:** rows 52, 53, 8, 10, 99, 38, 89 found the right page but not the right chunk. These are a chunking signal for week 2.~~ Done in specs 0005 and 0006 (#21–#26): structure-aware chunking was tested against it and rejected ([ADR-0019](decisions/0019-structural-first-recursive-inside-chunking.md)).

## From the spec 0005 build review (2026-10-19)

Lower-priority `/code-review` items, noted for later (Arun, 19 Oct). Details in [the build journal](journal/2026-10-19-chunker-build.md).

- **Heading-only parent chunks:** a heading followed directly by a child heading becomes a chunk of a few tokens, since AC-8 forbids merging with a child. Excluding them at query time (19 Oct preview) moved recall@5 only from 0.358 to 0.374 and page_hit@5 not at all, so they are not the main cause. Small heading-plus-teaser sections are. Structural size and overlap sweeps are dropped under the stop rule ([journal](journal/2026-10-19-chunker-build.md)); the fixed-512 sweep moved to week 4 (below).
- ~~**Merged heading paths read like nesting:** a merged chunk stores the first path plus each sibling's heading (AC-9), so `Per diem > France > Germany` looks nested. Store or render merged siblings distinctly.~~ Superseded by spec 0006 AC-4 (#25): the packed configs drop sibling appending, and only the rejected `structural-v1` keeps it.
- **Mostly-overlap windows:** `pack` can emit a window that is nearly all overlap when the only cut sits just past the previous end. Rare; costs a near-duplicate chunk.
- **Front-matter line count:** `chunk.run` re-reads each source file to count front-matter lines. Ingest could store the count instead.
- **Embed cost query:** the cost SQL repeats the pending-chunks predicate; derive it from `PENDING`.

## From the spec 0006 build (2026-10-19)

- **Stale prefixed vectors:** for a prefixed config, the embedded text includes `documents.title` and `heading_path`, but `flush` and embed's insert guard only notice changes to `content`. A new pin that changes a title or a heading path without changing a chunk's bytes would keep the old vector. That can't happen at pin 5273b21. If a prefixed config is kept, guard on the md5 of the embedded text instead (a spec change to AC-5).

## From the spec 0006 runs (2026-10-19)

- **Heading-path prefix, re-test after the week-3 reranker:** on 3-small it was +0.036 at k=5 (Arun, 19 Oct). On the adopted 3-large@1536 (run `2026-10-21-586b1635` vs `d83f3edc`) it was +0.031 ± 0.059 (0.51 SE): page_hit@1 +0.156 (2.40 SE) but chunk_fact_recall@10 −0.062 (−1.68 SE), from same-page crowding (rows 10, 48, 34). Not adopted (Arun, 21 Oct). Retrieve-50-rerank-to-5 needs depth and gives its own top ordering, so re-test prefixed vs unprefixed with the reranker in place. The 3-large prefixed vectors are stored: one eval. If revisited, a title-only prefix separates the title (always correct) from the heading path (only the window's start; 85% of windows cross a heading).
- **Fixed size and overlap sweep, week 4 with context assembly:** 256/32 and 1024/128, then overlap 0 and 128 at 512 ([ADR-0003](decisions/0003-baseline-chunking-512-64.md)). Decide on recall at the token-matched k, after the week-3 reranker, when k unfreezes. About $0.2 of embedding per config (Arun, 19 Oct).

## From the spec 0007 review (2026-10-20)

- **Prompt injection beyond retrieval, week 5:** the Principal guardrail is structural. Groups come only from the session, and the filter runs in SQL before ranking, so no prompt text can widen what is retrieved. Claimed-identity cases (AC-15) test exactly that. It does not stop a prompt from changing the answer model's behaviour over chunks it *is* allowed to see:
  - ignoring the grounding rules
  - leaking the system prompt
  - indirect injection planted in corpus content
  - in week 5, steering agent tools into calls the user didn't intend

  Week 5 grows the claimed-identity cases into an injection suite. Agent tools take the session principal, never one from model output (spec 0007 AC-14). Model-based identity-claim detection is out of scope for spec 0007 (Arun, 20 Oct).

## From the spec 0008 review (2026-10-21)

- **`make ask` query mode, before adopting a non-OpenAI embedder:** spec 0008 gives eval a query-mode embedder without touching the frozen `ask.py`. `make ask` still builds a document-mode one. With Qwen3 or Gemini as the default, every live question would be embedded as a document: no query instruction, wrong `task_type`. Fix it in the PR that changes `DEFAULT_EMBED_MODEL` (spec 0008 AC-3, AC-9). Not needed for OpenAI models, which have no input types. In the same PR, make `ask.estimate` and the trace's `query_embed` count go through `query_embedder.prepare()`, so the dry run counts the template's tokens and runs the InputTooLong check (#39 review item 2, 24 Oct).
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

## From the spec 0007 Part A build (2026-10-22)

- ~~**Guardrails against unapproved paid calls**~~ Done in [spec 0009](../specs/0009-paid-call-guardrails.md) (24 Oct): plain targets only dry-run and `make paid-<target>` spends, a PreToolUse hook asks a human before any paid target, and `runs/spend.jsonl` logs each paid run.
- **Runtime agent spend controls, weeks 6 and 8:** the spec 0009 hook guards only the coding agent's shell; the product agent's model calls run in-process and never pass through it. Approval sits at the run boundary (one `make paid-eval` per batch eval). Inside a run, caps bound the cost: per request (max steps, tool calls, tokens), per run (abort above an estimated-cost cap), per day (a spend ceiling and an alert). `spend.log_spend` is the hook-in point, unless a gateway replaces it.
- **Store `redirect_to:` at ingest:** ACL resolution re-reads every pinned file to find redirect stubs (the stored body has no front matter), and the stale check does it again on every `make ask`/`eval`/`permissions`. A documents column set at ingest would drop the disk scan and remove the risk of ingest and ACL time reading different checkouts. Needs a schema change.
- **Detect duplicate `url_path`s at ingest:** `x.md` and `x/_index.md` would share one. `make acl` now fails if a redirect targets such a path, but citations and url_path lookups can't tell the two apart. None exist at the pin.
- **`make ask` stale-check latency:** the check reads every corpus file per question. Fine for a CLI; revisit with the week-6 service (cache the policy sha and redirect map at `make acl` time).
- **Retrieval-only eval empty-result message:** an empty retrieval says "run `make embed`", which is right only while the quality set runs as admin (AC-9). If that user changes, distinguish "no embeddings" from "nothing visible".

## Permissions switch (2026-10-23)

- **`PERMISSIONS=on|off` flag, default on (Arun, 23 Oct; Arun writes the spec when time frees up):** with it off, the whole pipeline behaves as if there were no synthetic permissions. It needs its own spec: it amends spec 0007 AC-8 ("no unfiltered overload") and the unfiltered path [ADR-0021](decisions/0021-permission-model.md) rejected, so it also needs an ADR. Spec 0010 is earmarked for answer evaluation (above), so take the next free number (0011 or later; corrected 26 Oct, was "0009"). Draft design:
  - One reader, `acl.permissions_enabled()`. Any other value is an error.
  - `identity.UNRESTRICTED`, a Principal with no groups. Every retrieval path still takes a required principal. `ask.search()` switches to a second literal, `SEARCH_UNRESTRICTED`: the same SQL without the `allowed_groups &&` line, with the same order and `chunk_id` tiebreak. The AC-8 predicate-scan test exempts only that literal.
  - `make ask`: skips the policy load and the stale check, `--as` becomes optional, and it prints `permissions: off`.
  - `make eval`: runs as `UNRESTRICTED`, with no stale check.
  - `make permissions`: refuses, because leak scoring needs permissions on.
  - `make acl`: unchanged. The ACL data stays in the DB, so switching back on needs no re-run.
  - Traceability: `runs/ask.jsonl` and the eval metadata record the flag, so an off run can't pass as an on run.
  - Tests use seeded vectors: off returns chunks no persona can see (including fail-closed `{}`), and on is unchanged.
  - Out of scope: per-user toggles and agent wiring (week 5 inherits the principal).
  - When built, add a true permissions-off row to the spec 0007 Part B measurement (`make ann`). Admin is the proxy until then.

## Reading (deferred)

- **Chroma, [Evaluating chunking strategies for retrieval](https://research.trychroma.com/evaluating-chunking):** dropped on 20 Oct because the chunking track is closed. Trigger: the week 4 size sweep.

## From spec 0007 Part B (2026-10-24)

- **HNSW parameter sweep:** Part B ran pgvector's defaults only (m 16, ef_construction 64, ef_search 40) on a 22k-chunk copy; production stays on exact search. Admin's unfiltered HNSW ceiling was 0.981 ANN recall@20. Sweep `ef_search` (and `max_scan_tuples` for the narrow persona) against latency before any production ANN index. The saved query vectors make it free.
- **Reading to do, filtered ANN** (from Part B; takeaways go in the week's reading log, in Arun's words):
  - [pgvector README, iterative index scans](https://github.com/pgvector/pgvector#iterative-index-scans): the settings, the re-sort CTE, `max_scan_tuples` and `scan_mem_multiplier`. Also confirm how strict_order drops out-of-order candidates (the journal's account is unverified).
  - [pgvector 0.8.0 release notes](https://www.postgresql.org/about/news/pgvector-080-released-2952/): why iterative scans were added, and the planner changes for filtered queries.
  - Malkov and Yashunin, *Efficient and robust approximate nearest neighbor search using HNSW graphs* ([arXiv 1603.09320](https://arxiv.org/abs/1603.09320)): what `m`, `ef_construction` and `ef_search` trade, before the sweep.
  - Patel et al., *ACORN: Performant and Predicate-Agnostic Search Over Vector Embeddings and Structured Data* ([arXiv 2403.04871](https://arxiv.org/abs/2403.04871)): filter-aware graph traversal, the alternative to post-filtering plus iterative scans.
  - [Qdrant, filterable HNSW](https://qdrant.tech/articles/filtrable-hnsw/) and [Weaviate, filtering](https://weaviate.io/developers/weaviate/concepts/filtering): how dedicated vector DBs handle restrictive filters (extra graph links per payload value, switching to flat search below a threshold).
  - Gollapudi et al., *Filtered-DiskANN* (WWW 2023): label-aware graph indexes, relevant if groups ever become partitions.
- **Exact-search latency:** about 100–225 ms p50 for the ~98% personas on the laptop DB (a full scan and sort of 22k vectors). This is the cost an ANN index would remove. It matters in week 7 (the service) more than now.

## From the #39 deferred review items (2026-10-24)

- **One `spend.logged(target, usd, …)` context manager** in place of the five try/finally spend blocks (ask, embed, eval, permissions, ann). Do it when the next paid target lands (the week 3 reranker). (Spec 0007 Part B, the earlier blocker, merged in #40.)

## From the week 2 docs audit (2026-10-26)

- **`make ann-build` empty-source hint:** `src/handbook_rag/evaluation/ann.py:759` says "run `make embed`", which only dry-runs now. Match the other hints: "run `make embed` for the cost, then `make paid-embed`".

## From spec 0011 (2026-10-29)
- **BM25 instead of `ts_rank_cd`:** Postgres FTS has no IDF, so common words ("team", "policy") outweigh rare ones ("POSH"). Candidates: Tiger Data `pg_textsearch` (PostgreSQL licence), ParadeDB `pg_search` (AGPL), VectorChord-bm25, or BM25 weights in pgvector `sparsevec`. Each is a new dependency or pipeline and needs an ADR. Trigger: the spec 0011 FTS-only run shows common words crowding out rare ones ([reading, Q3](reading/week-03.md#hybrid-search-postgres-full-text-search-reciprocal-rank-fusion)).
- **Weighted RRF or a convex score combination:** both need a tuned weight. Tune it on the synthetic retrieval set, not on v1.2 (n = 32).
- **Weighting the heading above the body** (`setweight(..., 'A')`) in the `tsvector`.

## From spec 0012 (2026-10-31)
- **Self-hosted reranker:** `Alibaba-NLP/gte-reranker-modernbert-base` (8192 context, 0% truncation on `fixed-512-64`, Apache-2.0, 600 MB, ~3–6 s CPU per 50 pairs on the M2, estimated). It removes the paid call and pins the weights, but needs torch (sentence-transformers) or onnxruntime as a new dependency. Trigger: the API reranker is adopted and latency or provider drift matters (week 6 observability, week 7 service) ([reading](reading/week-03.md#cross-encoder-reranking-candidate-models-truncation-hosted-apis)).
- **Smaller or larger Qwen3 reranker (0.6B, 8B):** a latency and cost trade-off against 4B, only once 4B has a measured result.
- **Rerank depth sweep:** out of scope in spec 0012; depth stays 50, where the ceiling was measured.
