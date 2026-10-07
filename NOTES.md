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
