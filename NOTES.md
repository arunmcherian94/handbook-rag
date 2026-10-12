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

- **Incremental sync:**
  1. `git fetch`.
  2. `git diff --name-status OLD..NEW -- content/handbook`.
  3. Apply the changes: upsert A/M, delete D, delete and insert R. Deletes matter for permissions, because a page pulled from public must leave retrieval.
  4. Record a sync-run log (old SHA → new SHA, counts).
- **Chunk-level hashes** plus pipeline version columns for incremental re-embedding.
- **Review agents** for spec conformance and architecture.
- **Answer-model check:** if the seed outputs show grounding, abstention or citation problems, run 10 questions on identical retrieved chunks through gpt-5.4-mini and Sonnet 5.5 (about $0.35) before the week 3 freeze.
- **Chunk expansion / parent-child:** retrieve small, then pass neighbouring chunks to the answer.
