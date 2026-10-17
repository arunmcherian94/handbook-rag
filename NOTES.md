# NOTES

Working notes on building this with a coding agent. One bullet per entry: what happened → what I did or learned.

## 2026-10-05 (scaffold)

- Colima was not running, so `make up` failed with a Docker API socket error → the agent showed the raw error and its diagnosis, asked before running `colima start`, then re-ran.
- `brew install uv` timed out compiling cmake from source → the agent killed it and used the standalone uv installer instead.
- Clean-room check in `/tmp` failed with `type "vector" does not exist` → Colima mounts only `$HOME`, so the init SQL bind mount was empty. Re-ran from a clone under `~/tmp`. Documented in the README.
- `git commit` failed with "Author identity unknown" → the agent asked instead of guessing, then set a repo-local identity.
- The plan gate and scope rules held. The agent presented the plan, waited for approval, and left out Alembic, a settings framework, CI and pre-commit hooks, which were all explicitly out of scope.

## 2026-10-07

- Colima was down again → another `colima start`. This is a recurring failure, so the environment check is the first step of every build block.
- Adopted spec-driven flow: `specs/NNNN-*.md` → PR review and merge → plan mode builds from the spec → tests cite AC IDs → `/code-review` → diff review → clean-room. Custom review agents (spec conformance, architect) are deferred.
- Corpus is all of `content/handbook/` (4,177 `.md` files), not the 45 files the seed questions touch → a narrow corpus has too few distractors and inflates retrieval numbers, and raw ingest of ~4k files is cheap. The seed questions shape the eval set, not the corpus.
- The URL→repo path check confirmed every seed path exists, e.g. time-off-and-absence lives under `people-group/`, and expenses is a single file, `finance/expenses.md`.
- Pinned `5273b21` (committed 2026-10-07T11:36:50+13:00). A blobless clone took ~14s and is 90 MB of `.git` for 105,724 commits.
- No doc-level `content_hash` in ingestion → `git diff OLD..NEW` already identifies changed files. Hashes pay off at chunk level (re-embedding only changed chunks), together with pipeline version columns (`chunker_version`, `embed_model`), because a chunker or model change alters no file. How much a chunk hash saves depends on chunking: fixed windows shift every chunk after an edit, while heading-based chunks isolate the change.
- `/code-review` gate caught: `make corpus` checked only HEAD and the file count, so local edits (or one add plus one delete) in `data/handbook` passed as "ok" → it now fails on a dirty `git status`, and doesn't silently reset, so edits aren't destroyed. It also passes `--cone` explicitly instead of relying on the git version's default.
- Ingestion (spec 0002) result: 4,177 found, 4,088 ingested, 89 skipped (85 empty_body, 4 draft). It takes ~1.7s, and a re-run is identical.
- Plan-gate catch: the first plan skipped `redirect_to:` stubs as noise. Checking the 6 files showed 4 carry rename knowledge found nowhere else (`production/readiness.md`: "PRR retired, replaced by PREP"), the same class as the HelpLab → Compass eval traps. The other 2 are empty anyway. The rule was dropped, and redirect stubs with a body are ingested. If a stub outranks its target, evals will show it, and the fix then is to store `redirect_to` and follow it at retrieval.
- Drafts are skipped because they're unpublished: a citation would 404, and they're templates and WIP. Unverified: that the site's Hugo config doesn't build drafts. The config is outside the sparse checkout.
- Real-file findings that shaped parsing:
  - All 4,177 files use YAML front matter.
  - One uses `Title:` (capitalised), so the key match is case-insensitive.
  - 10 files have no title, so they fall back to the filename or parent directory.
  - 138 leaf bundles (`index.md`) map to the directory URL, like `_index.md`.
  - 0 `url:` overrides. The single `aliases:` is ignored.
  - `finance/expenses.md` has **two** headings numbered "4.1" (TRAVEL and NON-TRAVEL). Co-Working and Internet sit under the second. That matters for any eval or chunk citation that uses section numbers.
- Each ingest mirrors the snapshot: upsert, then delete rows not in the ingested set, in one transaction. Without this, a skip-rule change or a re-pin that drops a page (e.g. a page pulled from public) would leave stale rows that retrieval could still serve.
- `body` stores the markdown after the front matter, unmodified (shortcodes kept). Front matter is metadata, and the title is stored separately.
- `/code-review` gate caught two problems in ingestion:
  - **Ingest only checked HEAD.** A dirty checkout would have been stored labelled as pinned content. A narrowed or empty checkout would have made the mirror-delete wipe rows, and an empty scan would have emptied the table. Fix: `corpus.verify()` (HEAD, clean tree, file count) is shared by `make corpus` and `make ingest`.
  - **`url_path` kept uppercase.** Hugo lowercases URLs. On the live site, `/billing-ops-GPO/` returns 302 and `/billing-ops-gpo/` returns 200. Fix: `url_path` is lowercased. One file was affected at the pin.
- Schema is applied without a migration tool. `db/init/002_documents.sql` is run by docker init on fresh volumes and re-applied (`IF NOT EXISTS`) by `make ingest` on existing ones. A real column change later will need either a migration tool or `down -v`. Revisit when the schema first changes.

## 2026-10-12 (baseline decisions, spec 0003)

- Token profile of the 4,088 docs (cl100k_base, the tokenizer for `text-embedding-3-*`, confirmed via `tiktoken.encoding_for_model`):
  - 9.29M tokens in total.
  - Per doc: p50 1,333, p90 5,097, p99 14,194, max 65,283.
  - 180 docs exceed the 8,191-token embedding input limit, so chunking is required, not optional.
- Embedding cost barely depends on chunk size: about 10.3–11.3M tokens for every size/overlap tried. Choose the size for retrieval quality, not price.
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
  - It's a week 2 sweep candidate (0 / 32 / 64 / 100).
- **512/64 chosen over 1024/128.** "Most docs fit in one 1024 chunk" was wrong: only 42% do (1,709 of 4,088). Big chunks give the generator more context but average more topics into each vector (dilution). For example, Expenses' Internet paragraph would share a vector with co-working and phone rules. 512 sits mid-range, so week 2 can sweep 256 and 1024 on either side.
- Chunking ladder, from simplest: fixed tokens → recursive (paragraph, then sentence) → markdown headings → semantic → contextual (an LLM writes a context line per chunk) → parent/child. The baseline is fixed-size on purpose. The rest are week 2 experiments.
- Embedding options considered:
  - OpenAI 3-small ($0.02/1M, 1536d) vs 3-large ($0.13, 3072d, which needs `dimensions` to fit the 2,000-dim HNSW limit).
  - Voyage-4, Gemini, Cohere v4.
  - Open models: Qwen3-Embedding, BGE-M3, nomic, EmbeddingGemma.

  Chose 3-small: cheapest, its tokenizer is exactly cl100k, and it's the standard reference point. About $0.21 for the corpus, about 11–15 min at Tier 1 (1M TPM), but about 4.5 h on the free tier (40k TPM).
- Local models on this machine (M2, 8 GB, shared with Colima): a 0.3–0.6B embedder takes an estimated 1–3 h for the corpus. Answer models that fit (3–4B) are weak at grounding and abstention. Open embedders become a measured week 2 comparison, not a guess.
- Answer-model cost math (about 3.1k input + 250 output tokens per question, about 3,500 calls over the project):

  | Model | Per question | Per 100-question eval run | Whole project |
  |---|---|---|---|
  | Haiku 5.5 | $0.0004 | $0.04 | ~$1.50 |
  | gpt-5.4-mini | $0.004 | $0.40 | ~$15 |
  | Sonnet 5.5 | $0.009 | $0.87 | ~$30 |
  | Opus 5.5 | $0.023 | $2.34 | ~$82 |

  Cost doesn't decide it. Chose gpt-5.4-mini for three reasons: a single provider with the embeddings, a Claude judge later is cross-family (no self-preference), and its strength is checked on the seed questions. I initially left it off the shortlist because its price was unverified. The user caught that, and the price was then verified on OpenAI's pricing page.
- **Parametric-leakage risk:** the GitLab handbook is almost certainly in every model's pretraining, so a model can answer correctly from memory when retrieval missed. That hides retrieval failures. Mitigations: strict grounding instructions, reading traces, and retrieval metrics scored separately from answers.
- **k=5:** recall@5 is the standard operating point. 5×512 ≈ 2.6k tokens of context. k is coupled to chunk size (k × size = context budget), and the eval can sweep k without re-embedding.
- Embeddings go in their own table (`chunk_id`, `model`) with an untyped `vector` column, so models of different dimensions coexist for week 2 comparisons. pgvector indexes one model later with an expression index plus a partial index (README FAQ).
- Links:
  - [OpenAI pricing](https://developers.openai.com/api/docs/pricing)
  - [text-embedding-3-small](https://developers.openai.com/api/docs/models/text-embedding-3-small)
  - [pgvector README](https://github.com/pgvector/pgvector)
  - [Open embedding models roundup (premai)](https://blog.premai.io/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting)
  - [Pinecone chunking strategies](https://www.pinecone.io/learn/chunking-strategies)

## 2026-10-13 (baseline build, spec 0003)

- **Answer API: Chat Completions, not Responses.**

  | | Responses | Chat Completions |
  |---|---|---|
  | Pros | OpenAI's recommended API for reasoning models. New features (tools, reasoning carried across turns) land here first. `output_text` helper. | The de facto OpenAI-compatible format (vLLM, Ollama, OpenRouter, Groq…), so a `base_url` reaches open and local models. Not stored server-side by default. Simple to fake. |
  | Cons | Stores responses for 30 days by default (needs `store=false`). Few non-OpenAI servers implement it. Output is a list of items. | Weaker for reasoning models. Gets new features later. Some newest models (GPT-6 Astra, 6.1 Sol) can't call tools through it. |

  Decided on Chat Completions: the baseline uses no reasoning (`reasoning_effort="none"`) and one turn, so Responses' advantages don't apply. A Responses adapter comes with the agent-layer spec, as one new class under AC-10.
- **Embedding failures: layered, cheapest isolation first** (PR #7 review and build plan):
  1. Check locally before sending: empty input, over 8,192 tokens, or a batch over 300k tokens. These cost no request.
  2. 400/422: split the batch in half, recursively, so only the bad chunks fail. One bad chunk in 128 costs about 14 extra requests (≈ $0.003), against 128 for per-chunk retries.
  3. 401/403/404: stop immediately. Splitting can't fix a key or model problem; it would only multiply failing calls.
  4. 429: honour `Retry-After`, else exponential backoff with equal jitter.
  5. 5xx/timeouts: whole-batch retry. There's no partial success to keep.
  6. Cap of 6 attempts. SDK retries are off for the embedder so ours are the only, logged layer. The answerer keeps the SDK default (2), since it's a single interactive call.
  - Rejected: the Batch API (per-input errors natively, but asynchronous and needs polling code), a client-side token-bucket throttle (optimisation, out of scope), and a failures table (logs plus "no embedding row" already make failures visible and retryable).
- **No `dims` column on `chunk_embeddings`:** `vector_dims(embedding)` derives it, so a stored copy could only drift. The adapter checks each vector's length against the model's known dims before insert. Retrieval filters to one model, and `<=>` raises on mismatched dims anyway.
- **Changed content invalidates embeddings.** `chunk_id` doesn't include content, so a doc edit or chunker fix can give an existing ID new text. The chunk run deletes those embeddings in the same transaction. Gate catch while answering review comment 2: without it, a stale vector would sit silently beside new text.
- **Prompt:** restricted to the GitLab handbook, with no training knowledge, web, documents or tools. Two fixed replies: "I don't know based on the provided handbook excerpts." (in scope, not found) and "Sorry, I don't know how to answer that." (out of scope). Fixed strings let code and the eval separate a retrieval miss from an out-of-scope question without an LLM judge. Tools are enforced in code: none are passed. The prompt reduces parametric leakage but can't prevent it.
- **Assumption confirmed: `Retry-After` is enough pacing at Build tier.** The full embed hit a 429 on most requests, but no batch needed more than one retry, so the 6-attempt cap has wide margin and a client-side throttle stays unneeded.
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
- **Design patterns (AC-11):**
  - **Ports and adapters (Strategy).** `Embedder` / `Answerer` are Protocols in `models/base.py`. Adapters sit one file per provider under `models/embedders/` and `models/answerers/` (`OpenAIEmbedder`, `OpenAIAnswerer`), grouped by role because embedding and answer providers differ (PR #8 review). `chunk`, `embed` and `ask` import only the Protocols, so a model or provider change doesn't touch pipeline code (AC-10). Protocols, not ABCs: fakes satisfy them structurally without inheriting anything.
  - **Factory on `provider:model` strings.** `make_embedder` / `make_answerer` read `EMBED_MODEL` / `ANSWER_MODEL`. The string is also the stored `chunk_embeddings.model` key, so config, data and traces name a model the same way. A provider registry (`EMBEDDERS` / `ANSWERERS` in `models/factory.py`) replaces an if-chain: a new provider means one adapter file plus one registry entry, and the lookup never changes.
  - **Dependency injection.** Clients go into adapters; `sleep` and `rand` go into `embed.run`; `clock` goes into `ask`. Tests then check request shapes, backoff timing and latency fields with fakes, at zero cost and without network mocking. An autouse fixture deletes `OPENAI_API_KEY` to prove it.
  - **Functional core, imperative shell.** `chunk_doc`, `build_prompt`, `parse_citations` and the retry/split logic in `embed_with_retry` / `embed_batch` are pure and unit-tested. `run` / `ask` own SQL and commits.
  - **Schema as a seam.** The untyped `vector` column plus `(chunk_id, model)` PK let models of any dimension coexist. Deterministic `chunk_id`s make re-runs idempotent and resumable.
  - **Settings in `constants.py`, prompt in `prompts.py`** (PR #8 review). Paths, chunk parameters, embedding limits and retry policy, model defaults, reasoning effort, output cap and k live in one file. The system prompt and its two fixed replies live in `prompts.py`, so prompt versions diff on their own for the eval harness. Regexes and SQL stay beside the one function that uses them.
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

## 2026-10-13 (error analysis, seed traces)

- **Approach: open coding first** (the first step of the error-analysis loop in Hamel Husain's evals guidance). Read what the system did and describe it, before any categories, causes or fixes. Record: [docs/error-analysis/2026-10-13-seed-traces.md](docs/error-analysis/2026-10-13-seed-traces.md).
- **Four checks per trace, in order:**
  1. **Retrieval:** is the expected page in the top k, and at which rank? Is it the chunk that holds the answer or just a chunk from the same page? Which plausible distractors came back?
  2. **Answer:** correct, partly correct, wrong or abstained against the reference. Each missing fact is then assigned a side: a *retrieval failure* if it wasn't in the retrieved chunks, a *generation failure* if it was retrieved and unused or misread. This split decides where week 2 and week 3 effort goes.
  3. **Citations:** does each cited chunk support its claim, and is the heading right? Also copied URLs and missing or unneeded citations.
  4. **Behaviour:** abstention correctness and the exact fixed strings, information not in the excerpts, hedging, padding and level of detail.
- **One fixed-format line per trace** (`Qn | retrieval | answer | citation | other`) plus a "surprised by" note. Describe what was observed, not why it happened. Causes wait until a pattern repeats.
- **Reference check against the pinned corpus.** References were written from the live site; the system reads the 2026-10-07 snapshot. Every reference fact was looked up in the pinned chunks, and `ref?` marks a reference that differs from the corpus or a corpus that disagrees with itself (6 of 10, all corrected on review).
- **Recency is settled from the statement's own history** (`git log -G`/`-S` on the line), not the footer or blame. Blame misleads after a page delete-and-restore (expenses.md was removed on 18 Mar 2026 and restored whole on 14 May, so every line blames to 14 May), and commit messages mislead (the 13 Sep 2026 "Rename HelpLab to Compass" commit added new access-request content). References cite the pinned corpus only.
- **Limitation:** 10 traces from one run, so the pattern counts are hypotheses for choosing eval-set dimensions, not measurements.

## 2026-10-14 (eval set design)

- **Logging rule (replaces the old "decisions only, no summary" reading-log rule):** docs/reading-log.md gets one entry per reading with an extended takeaway summary and the decisions it informed. NOTES.md stays short, dated notes and decisions. Sources are paraphrased.
- **PR #9 final numbers:** 2 retrieval only, 1 generation only, 6 mixed, 1 correct. Top patterns: retrieved but not used (7/10), answer in a section that starts mid-chunk (6/10), right page wrong chunk (6/10). The last two share 5 questions and may have one cause (fixed windows splitting sections); they stay separate until baseline traces confirm it.
- **(a) Failure categories:** the six question types are coverage strata, not failure categories. Categories come only from coded traces (PR #9 now, baseline traces from Friday). So in the eval set, I will tag each question with its type for coverage, report failures by category, and add a category only when a trace shows it.
- **(e) Question mix** *(mix and restricted handling superseded 2026-10-15)*: a restricted-user answer is a leak, a security failure, not an accuracy miss. So in the eval set, I will score restricted questions as a separate leak rate (target zero), never averaged into accuracy, and scored from week 2 once the ACL pre-filter exists.
  - Mix 60 / 20 / 20 (answerable / out-of-corpus / restricted). About 80–85 candidates survive the first triage as a buffer; duplicates and unneeded ones are cut at review.
  - Restricted users get the same in-scope reply, "I don't know based on the provided handbook excerpts." A permission message would confirm hidden content exists, and one string keeps the check an exact match.
  - Access rule is provisional until week 2: role `contractor` can't see entity-specific benefits and compensation pages (exact paths confirmed from the pinned SHA). Each restricted question must be answerable from the corpus. If the week 2 ACL spec changes the rule, affected questions get a changelog entry.
  - Out-of-corpus splits about 2:1 between "in scope but not found" and off-topic. Plausible handbook questions with no answer are where the model fills gaps from memory.
- **(f) Order:** Friday runs the baseline and reads the traces first. Retrieval metrics and code checks need no judge. Saturday codes the new traces, updates categories, then writes judges only for failures code can't detect. So in the eval set, I will run it before any judge exists, and every judge traces back to a coded failure.
- **Candidate generation: two steps** (dimensions brief and 20 seed tuples in [docs/eval/2026-10-14-dimensions.md](docs/eval/2026-10-14-dimensions.md), reviewed before use → an LLM in a fresh context writes more tuples → a separate prompt turns tuples into questions). Questions only, no corpus reads, marked UNVERIFIED. All answers and expected docs are written by hand from the pinned SHA.
- **Candidate pool built:** 103 candidates, then a first triage by a fresh subagent with no corpus access, leaving 82 (60 / 21 / 20). Process: [docs/eval/README.md](docs/eval/README.md).
- **Persona `unstated` added:** real users rarely say who they are. Restricted questions include ones with no stated role, since access must come from the user's role, not the question text.
- **Gate catch (triage):** the provisional restricted rule ("entity-specific benefits") would also hide the Contractor Benefits section, which contractors must see. To fix in week 2 (permission cases deferred): restrict employee-only benefits and compensation pages.
- *(Superseded 2026-10-15: deferred to week 2.)* **Every case carries a principal** (the acting user, from a 5-user synthetic fixture), passed by the harness as request context. Identity never comes from the question text. Answerable cases need one too, because the pre-filter runs on every query. D5 is split into D5a (principal) and D5b (role stated in the text: none / matches / conflicts). 4 `conflicts` cases test that access follows the principal.
- *(Superseded 2026-10-15.)* **Restricted case = one question × two principals:** denied (`contractor`) and an entitled control. The control separates "ACL blocked" from "retrieval missed", which give the same reply. It's written once, with no extra answer rows.
- *(Superseded 2026-10-15.)* **Restricted scoring is phased** (`requires: acl`):
  - Week 1: controls are scored normally; denied runs are reported as a pre-ACL leak rate, never as failures. A leak is measured at retrieval level first: a restricted chunk in the top k.
  - Week 2: gates are leak 0, over-block 0, and conflicts leak 0.
  - Week 5: conflicts grow into injection cases.
- **Deferred to Thu 16:00:** (b) criteria drift, (c) judge claims, (d) binary rubric. *(Decided 2026-10-16.)*

## 2026-10-15 (ACLs in evals)

- **The quality set ignores ACLs.** It runs as an all-access user, so with exact search it stays identical to the baseline after week 2's pre-filter. Permission cases (restricted, role conflicts) are deferred until the week 2 ACL design is known. The drafts are parked in the candidates file, and nothing is built for them now.
- **Research pointers for week 2** (about 30 sources; reading log 15 Oct):
  - permissions are a deterministic layer, tested as a separate suite with paired denied/entitled cases
  - a leak rate checked on retrieved chunks, reported next to authorized recall (deny-all scores 0 leaks)
  - an identical-top-5 regression test for the all-access user
  - comparability breaks when HNSW arrives, not when ACLs do
- **(e) mix changed:** the quality set is 60 / 40 answerable / out-of-corpus, with out-of-corpus about 2:1 in-scope vs off-topic. 10 out-of-corpus candidates added; the pool is 76 (49 / 27).
- **Eval set v1 committed:** 54 rows, 33 answerable / 21 out-of-corpus (61 / 39); lookup 9, synthesis 8, contradiction 8, recency 8, ooc-in-scope 12, ooc-off-topic 9. [docs/eval/eval-set-v1.md](docs/eval/eval-set-v1.md), [CHANGELOG](docs/eval/CHANGELOG.md).
  - 16 rows reviewed (every trap verdict checked against its excerpts, plus row 65). 38 rows are `llm-draft, unreviewed`: review them first on 2026-10-16.
- **Out-of-corpus rule:** if the pin directly answers the question, recode it as answerable. If it asks for a value or personal state the pin doesn't have, keep it out-of-corpus. If the pin gives only a partial answer, cut it, because an exact-string check can't grade it fairly.
- **Git history decides currency, never facts:** facts cite pinned files only. History only judges which pinned statement is current. Bulk commits make page-level dates weak evidence, so in-page wording ("previously IT BV") is preferred.
- **Gate catch (reference drafting):** the trap hypotheses came from memory, not the pin. T7's $80 cap and the "HelpLab" name exist only in history, and T8 has no number conflict. Those rows were recoded, cut, or re-noted to what the pin contains. "Customer Success" is still in about 300 pinned files.
- **Limitation:** per-country probation and notice-period tables are Hugo shortcodes whose data isn't in `content/handbook`. The RAG can't see them either. Follow-up: check whether shortcode data should be ingested.
- **Gaps accepted for v1:** out-of-corpus is 12 : 9 in-scope vs off-topic, and there is no easy floor row.

## 2026-10-16 (eval set v1.1 review)

- **Reference-rule change (dated 2026-10-15, recorded now):** references may be drafted by Claude in a fresh session from the pin, never from model memory and never by gpt-5.4-mini. Reason: time. Mitigations: every fact tied to an excerpt, trap rows reviewed first, a `ref_source` field on every row.
- **Sample 8/38 hand-reviewed, 1 answer-level error (3 counting missing expected docs); sweep flagged 33, all triaged.** The decision rule triggered a review of all remaining rows. The owner reviewed 3 more, and 26 were auto-reviewed by Claude subagents with fixes applied on the owner's standing approval (`ref_source: llm-draft, auto-reviewed`). Fact lists of auto-reviewed rows should be hand-checked before the first judge uses them.
- **Gate catch:** row 62 (personal phone device management) was labelled out-of-corpus, but the pin partly answers it (Okta Verify enrolment, posture checks). Cut, along with 114 (performance review score) for the same reason. Missing expected docs on 44 and 96 would have scored correct retrievals as misses.
- **Abstention scoring:** exact match stays pass/fail, because the prompt says "reply exactly". "Starts with" was rejected: it would pass off-topic answers that add training-knowledge text. Failures that start with the right string get a diagnostic label, `abstain+extra`, which doesn't change any score.
- **`recency_basis`:** a contradiction or recency fact settled only by git history can't be met by a model that never sees history. Those facts are kept, labelled `history-only` and reported separately, so a later recency fix can be measured against the same facts. All 16 contradiction and recency rows are labelled: 8 `history-only` (11, 44, 49, 50, 51, 52, 53, 55) and 8 `in-page`. Rows 50, 53 and 58 don't score their conflict at all; report that alongside the per-type results.
- *(Superseded 2026-10-16: recall counts required facts, any cited source satisfies; markers on every row in v1.2. See spec 0004.)* **Spec 0004 inputs from the review:** the pages behind `[required]` facts are the must-retrieve set (recall as a fraction); other expected docs are acceptable alternates (any hit).

## 2026-10-16 (eval metric decisions, reading)

Reading: [docs/reading-log.md](docs/reading-log.md), 16 Oct.

- **(b) Eval versioning:** every change makes a new version with a changelog entry per question. Runs record the eval version, a sha256 of the eval file and the harness git SHA, and are compared only within one version. When the eval changes, the frozen baseline is re-run on the new version, so the eval's effect is measured apart from the system's. A scorer or judge change also means re-running the baseline. So in the eval set, I will bump the version on any row change and re-run the baseline before comparing.
- **(c) No "validated judge" claim:** validating a judge needs human labels of the target failure, a train/dev/test split with an untouched test set, and reported TPR and TNR. With 52 rows we have none of that. So in the eval set, I will report a judge only as "checked against N labels, TPR x, TNR y", and hold out a test portion of the coded traces from the start.
- **(d) Code checks, no labels needed:** citation present, cited heading exists at the pin, exact abstention strings, no URLs copied into the answer. Answers are scored by binary fact checks (`[required]`/`[optional]`), not a scale. So in the eval set, I will grade everything code can check with code.
- **Q1 binary relevance:** v1.1 has no relevance grades. nDCG@5 uses binary gains, stated as such. Graded nDCG from the required/alternate page tiers is a follow-up.
- **Q2 k = 1, 3, 5:** all 5 chunks go to the model, so @5 measures whether the answer could be reached and nothing above 5 means anything. @1 and @3 show ranking headroom for reranking (week 3) and for a smaller k. Reported with MRR, since recall@5 alone hides ranking (Pinecone).
- **Q3 chunk level is the headline.** A chunk counts as relevant if it contains a cited evidence line, so labels survive chunking changes in week 2. The headline metric is **fact recall@k** (required facts covered ÷ required facts), plus all-required@k. hit, MRR and nDCG count only chunks relevant to a required fact. Page level is reported as a diagnostic: page hit with chunk miss = a chunking problem (6 of 10 seed traces). At page level a page counts once, at its best rank.
- **Not reported:** precision@k (few expected pages: 26 of 33 rows have 1–2, and unlabelled relevant pages would count as misses) and MAP@k (identical to MRR for one page; nDCG covers several). Revisit precision if noisy context shows up as a failure mode.
- **Abstention reported both ways:** false abstention on answerable rows and invented answers on out-of-corpus rows, never one combined rate. The wrong abstention string (NOT_FOUND on off-topic, or OUT_OF_SCOPE on in-scope) fails the exact check and gets a diagnostic label.
- **Retrieval and generation scored separately:** spec 0004 covers retrieval metrics plus the abstention and code checks. Faithfulness and answer-relevance judges come later, only for failures found in coded traces, per (f).
- **Questions generated from pages (Hamel's FAQ) not used for v1:** page wording flatters dense retrieval, and the method can't produce out-of-corpus, contradiction or recency rows (35 of 52).
- **Noise:** 33 answerable rows means one row is about 3 points. Spec 0004 reports a standard error next to each rate.
- **Custom vs textbook metrics:** a fresh research agent found no standard for retrieval evals when chunking changes. The closest common advice is span labels fixed across chunkings (Chroma) and recall over reference facts (RAGAS and DeepEval, via an LLM). That's what we do, from labels. Textbook chunk recall is rejected: overlap and alternative pages inflate the denominator, and it shifts with chunking. Retrieved tokens are reported, because bigger chunks raise recall by covering more text.
- **Limitation:** a cited line longer than the 64-token overlap that straddles a chunk boundary is in no chunk in full, so it can't match. The AC-2 check fails the run if a fact is left unmatchable. If it fires, the decision then is to loosen the rule to span overlap. (Resolved on 17 Oct: span overlap adopted; see below.)
- **Follow-ups (week 2):** token precision/IoU when chunk size changes (Chroma); comparing chunkings at an equal retrieved-token budget.

## 2026-10-17 (eval harness build, spec 0004)

- **Layout:** `src/handbook_rag/evaluation/`, split like `ask.py` into a pure core and an I/O shell.
  - **Pure:** `evalset` (parser), `metrics`, `checks`, `report`.
  - **I/O:** `evidence` (reads the pin and the chunks table, and is the only owner of the relevance rule) and `run` (the CLI).
  - The model ports are reused from `models/`; nothing new was added.
- **Evidence check fails only on required facts** (owner, 16 Oct). The probe found one unmatchable fact, 23 F3, which is optional. Retrieval metrics count only required facts, so an unmatchable optional fact changes no score. It's listed as a warning.
- **Answer-only facts** (owner, 16 Oct). A fact with no citation tests how the answer behaves, so no chunk can satisfy it. There are two: 22 F1 and 58 F1. They're left out of the retrieval denominators and listed in the summary. Row 22 has no cited required fact left, so it has no retrieval score. It's listed under `no_retrieval_facts` and still counts for abstention and the code checks.
- **Span overlap adopted** (owner, 17 Oct). The first smoke run gave row 51 no credit for F2: its rank-1 chunk held 262 of the 345 characters of L417 (the Navan-claim half), but not the whole line. Across the set, 20 of 129 cited lines for required facts (16%) straddle a chunk boundary, affecting 18 required facts.
  - **Rule:** a chunk is relevant if it holds a cited line in full, or a piece of at least 40 normalised characters (`MIN_PIECE`) of that line at the chunk's start or end.
  - **Effect:** 19 chunks gain credit, and 23 F3 now matches, so there are no warnings. Rows 49 and 51 move from 0.50 to 1.00 fact recall@5 in the 3-row smoke run.
  - **Fixed** for every later experiment.
- **Limitation (lenient matching):**
  - A piece can be a small share of a long line: 34 F3 matches on 56 of 1,214 characters.
  - Short cited lines match any chunk of the page that contains them, for example 88 F6 `{.h2}` (optional) and 89 F3 `##### France`.
  - Both raise recall slightly. Token IoU (week 2 follow-up) would replace this.
- **`retrieved_tokens@k`:** the total tokens in the top k chunks, averaged over rows. This is the quantity an equal-token-budget comparison needs. Per-chunk mean tokens would just be the chunk size.
- **Code-review catches (fixed):**
  - `make eval CONFIRM=0` (any non-empty value) passed `--confirm` and spent money. Only `1` counts now.
  - Run metadata took chunk parameters and the corpus SHA from constants and the manifest. They're now read from the stored chunks, and a run fails if the chunks don't match the pin.
  - The headings check compared the DB with itself, so it couldn't fail. It now reads the pinned file, keyed by the cited chunk's document; `url_path` isn't unique.
  - A required fact with a malformed citation (a path with no `L<n>`) silently became answer-only. It now fails parsing. Duplicate row or fact ids also fail.
- **Follow-up fixes (owner-approved lower-priority review items, 17 Oct):**
  - **Short cited lines:** a line under 40 characters, such as `{.h2}` or `good intent.`, now matches only as a whole chunk line, not inside a longer line. At the pin this removes no chunk credit: all 55 short cited lines already matched only as whole lines. It's a guard for the week 2 chunkings.
  - **Standard-error formula:** it's set by metric kind, not inferred from the values. Rates use √(p(1−p)/n). Averages (fact recall, MRR, nDCG, tokens) use the sample sd ÷ √n. An unclassified metric name fails the summary.
  - **Retrieved tokens:** these now use the stored `chunks.token_count` instead of re-encoding the chunk text.
  - **Smaller fixes:** an out-of-range citation now produces one message instead of two, and a file's trailing newline no longer counts as an extra line.
  - **Test fix:** the dry-run test fails with "Run `make corpus` first" when the corpus is missing.
- **Code-review catches on the follow-ups (fixed):**
  - **Edge fragments:** the whole-line rule still accepted a chunk's first or last piece, which is usually a fragment the window cut. Those two pieces are now excluded.
    - **Limitation:** a short cited line at the very start of a page body, or at its end when there is no trailing newline, has no overlapping neighbour chunk, so it can't match. The evidence check fails loudly if a required fact hits this. None does at the pin, and the rule removes no credit there.
  - **Metric names:** an unclassified metric crashed only after the paid loop, and names were matched loosely. Classification now uses exact patterns, and a unit test classifies every `row_metrics` key, so `make test` catches a new metric before any spend.
- **Follow-ups (not built, lower priority):**
  - a clear error if a retrieved chunk disappears during a run
  - the "no stored chunk" message per page instead of per fact
  - normalise each chunk once per page instead of once per fact
  - token counts come from a second query per row, because `ask.py` is frozen through week 3; select `token_count` in `ask.SEARCH` when it unfreezes

## 2026-10-17 (subagent orchestration)
- **Decision:** use subagents whenever the work splits cleanly: read-only research while planning, and the build and review fixes after approval.
  - **Where it lives:** the procedure is in `.claude/skills/orchestrate/SKILL.md`, and CLAUDE.md has a one-line pointer to it.
  - **Why:** parallel slices finish faster and keep the main context clean.
  - **Why a skill:** only the skill's description is always loaded, so CLAUDE.md stays small.
- **Research takeaways:**
  - **File ownership:** split work by which files each agent owns; agents that edit the same file overwrite each other. Contracts are written first, by one owner. ([agent teams](https://code.claude.com/docs/en/agent-teams), [Cognition](https://cognition.com/blog/multi-agents-working))
  - **Waves:** run slices in waves taken from the dependency graph. A cycle means the plan is wrong.
  - **Checkpoints:** keep progress on disk, not in agent memory, and continue an interrupted agent by its ID. ([Anthropic: long-running harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), [subagents](https://code.claude.com/docs/en/sub-agents))
  - **Final check:** each slice passing its own tests doesn't mean the combined tree passes, so run the full suite once at the end.
  - **Cost and risks:** about 3–4× the tokens of a single agent. Agents slow down sequential or coupled work. Failure modes are conflicting implicit decisions and stopping early. ([Anthropic: multi-agent research](https://www.anthropic.com/engineering/multi-agent-research-system), [Cognition](https://cognition.com/blog/dont-build-multi-agents))
- **How:**
  - The plan carries a slice table: what each slice owns, reads and depends on, its model, when it's done, and its status.
  - The orchestrator writes the contracts, integrates and verifies.
  - **Models (the orchestrator decides per slice):** Sonnet 5.5 for well-defined coding slices, Haiku 5.5 for mechanical fixes.
  - The status column is the checkpoint. There are no per-slice commits.
- **Limitation:** Explore and Plan agents can't be continued after an interruption, so they're relaunched.
- **Not doing:** custom agent definitions, worktrees, a status file in the repo, scripts.

## 2026-10-17 (baseline eval numbers)
- **Week 1 closed:** run `2026-10-17-3748df5b` on clean main at 76b3fce, eval set v1.2, $0.21. The summary is in `docs/eval/results/2026-10-17-3748df5b/`. `rows.jsonl` stays local, in `runs/`, which is gitignored.
- **Numbers and takeaways:** see the `summary.md` Takeaways section. It is LLM-drafted and human-reviewed, and lists what to improve next and how to check that a fix worked.
- **Shared definitions:** metric definitions live in `docs/eval/results/metrics.md`, linked from each summary instead of copied into it.
- **Follow-ups:**
  - **False abstention:** 39% of answerable rows abstain. Code these rows against what was retrieved: did retrieval miss, or did the model refuse with the evidence in context? That decides the answer-model check below, which has to happen before the week 3 freeze.
  - **Synthesis:** chunk_all_required@5 is 0.00 (n=8). No single top-5 set covers all the facts a synthesis row needs. Candidates: larger k, parent-child chunks, hybrid search.
  - **Recency:** chunk_fact_recall@5 is 0.35. This is the target for the chunk-dates follow-up.
  - **Page hit, chunk miss:** rows 52, 53, 8, 10, 99, 38, 89 found the right page but not the right chunk. These are a chunking signal for week 2.

## Corpus: git behaviors, limitations, assumptions

Git behaviors:
- **Blobless clone:** it has every commit and tree but no file contents until needed. Checkout fetches blobs only for the sparse paths. `git log -- <path>` works offline, but `log -p`, `blame` and historical diffs fetch blobs lazily, so they're slow and need network. The clone is a promisor remote, so those operations fail if GitLab is unreachable.
- **Why not shallow or treeless:** `--depth 1` drops the history needed for recency work. `--filter=tree:0` is lighter, but path-filtered `git log` then fetches trees lazily and becomes very slow.
- **Sparse checkout limits only the working tree.** The index and history still cover the whole repo, so `git ls-files` lists every path. That's why file counts are taken from disk. Cone mode also checks out repo-root files (README, Makefile, etc.), which are excluded from the count. Widening fetches blobs only for the new paths.
- **Detached HEAD at the pin is intentional.** `git pull` doesn't move it. Re-pinning is an edit to CORPUS.md.
- **The snapshot date is the committer date of a merge commit,** in the committer's timezone (+13:00). Store it timezone-aware. Author and committer dates can differ.
- **Git stores no renames.** It detects them heuristically (about 50% similarity by default). That affects sync (R entries) and file history (`--follow` handles one file at a time).
- **Merges:** `git diff OLD NEW` compares trees, so merges don't matter for sync. Per-file history should use `--first-parent` to get main-line dates.
- **Bulk commits** (migrations, mass reformatting) pollute per-file "last changed" dates, as with the 13 Sep 2026 footer date. History-based recency needs an ignore list of such commits.

Limitations:
- It's a single point-in-time snapshot. Live edits after the pin are invisible until a re-pin.
- Only the public handbook is covered. The internal handbook is out of reach, so ACLs are synthetic.
- Footer dates and last-commit dates are not recency signals.

Assumptions (unverified):
- Repo markdown equals published pages. Hugo `draft: true`, `url:` or `aliases:` front matter could break that, so check in the 0002 plan gate.
- The URL path is derivable from the file path (`_index.md` → directory URL).
- Public repo means `acl=public` for every doc.
- There are no case-only path collisions, which matters on macOS's case-insensitive filesystem.

## Follow-ups (not built)

- **Chunk dates for recency (week 2 or later):** store a per-chunk date from `git blame` that skips the bulk commits (968e3521af, bee431b547, 4469685d7b), and show it to the model with each chunk so it can prefer the newer source. Blame needs network access on the blobless clone. Measure it against the `history-only` facts.
- **Synthetic retrieval set (week 2):** questions generated from sections (not chunks), labelled synthetic, scored for retrieval only and always reported apart from v1. Gives chunking and embedding comparisons more statistical power than 33 rows.
- **Graded nDCG:** gains 2/1/0 from required/alternate page tiers, after the tiers are reviewed as relevance labels.
- **Answer judges:** faithfulness to context and answer relevance, built only for coded failures; validated per (c).
- **False-premise rows:** add 2–3 out-of-corpus false-premise questions in a later eval version.
- **Incremental sync:**
  1. `git fetch`.
  2. `git diff --name-status OLD..NEW -- content/handbook`.
  3. Apply the changes: upsert A/M, delete D, delete and insert R. Deletes matter for permissions, because a page pulled from public must leave retrieval.
  4. Record a sync-run log (old SHA → new SHA, counts).
- **Chunk-level hashes** plus pipeline version columns for incremental re-embedding.
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
