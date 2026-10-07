# 0002: Ingestion

- Status: implemented
- Date: 2026-10-07
- Depends on: 0001

## Problem

Retrieval and evals need the pinned handbook markdown in Postgres, with stable identifiers and the provenance (commit SHA and date) that ties every row to the snapshot.

## Acceptance criteria

- AC-1: `make ingest` loads the markdown from the pinned checkout (`data/handbook`) into Postgres.
- AC-2: `make ingest` refuses to run if the checkout HEAD ≠ the SHA in `CORPUS.md`.
- AC-3: It's idempotent: re-running gives the same row count and no duplicates (upsert on `doc_id`).
- AC-4: Columns:
  - `doc_id`: stable, derived from the repo-relative path.
  - `path`
  - `url_path`
  - `title`: from front matter, falling back to the first H1, then the filename.
  - `body`: raw markdown.
  - `source_type`: stub, default `'unclassified'`.
  - `acl_tags`: stub, default public.
  - `commit_sha`
  - `commit_date`: the snapshot commit date, **not** a per-file date.
  - `ingested_at`
- AC-5: It logs counts of files found, ingested and skipped, with a reason for each skip.
- AC-6: A test asserts that the files-found count equals the file count in `CORPUS.md`, and that ingested + skipped = found.
- AC-7: A test asserts that the Expenses doc (`content/handbook/finance/expenses.md`) is present in full. That includes section 3 (General Guidelines) and the Co-Working and Internet sections (section 4.1).
- AC-8: The existing tests stay green, and ruff is clean.

## Out of scope

- Chunking and embeddings.
- Git-history or per-file date ingestion.
- Real ACL logic.
- Source-type classification.
- The Act 2 blog (decision due Thursday).
- YAML data from www-gitlab-com.
- Hugo shortcode stripping or rendering.
- Rendered HTML ingestion.
- Any retrieval or LLM calls.
- Incremental sync and content hashes.

## Corpus facts that constrain this

- Ingest from repo markdown only, never rendered HTML. The rendered site's large navigation menu truncates page content.
- The "last modified" footer (13 Sep 2026) is a bulk-commit date, not a recency signal. That's why `commit_date` is the snapshot date only.
- A number is stale only if the live page changed it (e.g. the internet cap was $80 in history and is $100 live). Don't assume history is wrong.
- Renames are eval cases (HelpLab → Compass, Customer Success → Customer Experience). Don't normalise them away at ingestion.

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| Date column | `commit_date` = snapshot commit date | **Per-file `last_modified`:** needs history mining, and bulk commits make it misleading. A separate `content_last_changed` column can come later. |
| ACL and source type | Columns with stub defaults | **Real logic now:** it would design ACLs before any retrieval result exists. **No columns:** forces a schema change in Week 2. |
| Content hash | Not added | Git diff between SHAs covers doc-level change detection. Hashes pay off at chunk level (re-embedding only changed chunks), together with pipeline version columns, when chunking exists. |
| Shortcodes | Left raw in `body` | **Stripping now:** a rabbit hole. Measure the impact against the eval set during chunking. |
| `url_path` | `content/handbook/a/b.md` → `/handbook/a/b/`. `_index.md` and `index.md` → the directory URL. | **Honouring front-matter `url:`:** 0 files use it at the pin. **`aliases:`:** 1 file, an old URL, ignored. |
| Skip rules | Skip `draft` (4) and `empty_body` (85), plus `decode_error` as a guard (0). Draft takes precedence. | **Skip redirect stubs:** rejected at the plan gate. 4 of 6 carry unique rename knowledge (e.g. PRR → PREP), and the other 2 are empty. **Ingest drafts:** they're unpublished, so a citation would 404, and the content is templates and WIP. |
| `body` | The raw markdown after the front matter, otherwise unmodified | **Including front matter:** it's metadata, and the title is stored separately. |
| `doc_id` | `uuid5(NAMESPACE_URL, repo-relative path)` | **The path string itself:** works, but duplicates the `path` column and isn't fixed-width. |
| Stale rows | Each run mirrors the snapshot: upsert, then delete rows not in the ingested set, in one transaction | **Upsert only:** a skip-rule change or re-pin would leave stale rows, including pages removed from public. |
| Schema | `db/init/002_documents.sql` (`CREATE TABLE IF NOT EXISTS`), run by docker init on fresh volumes and by `make ingest` on existing ones | **A migration tool:** out of scope. **Init-only:** existing volumes would need `down -v`. |

## Open questions

None. Both were resolved at the plan gate against the real files (see Decisions).

## Verification

- `make up && make corpus && make ingest`, then `make ingest` again: the same row count.
- `make test` (including AC-6 and AC-7) and `make lint` pass.
- A clean-room run from a fresh clone gives the same counts.
