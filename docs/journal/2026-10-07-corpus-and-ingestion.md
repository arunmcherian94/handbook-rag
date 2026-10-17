# 2026-10-07: corpus and ingestion

- Colima was down again → another `colima start`. This is a recurring failure, so the environment check is the first step of every build block.
- **Spec-driven workflow:** → [ADR-0009](../decisions/0009-spec-driven-workflow.md)
- **Corpus scope and pin:** → [ADR-0001](../decisions/0001-corpus-scope-and-pin.md)
- The URL→repo path check confirmed every seed path exists, e.g. time-off-and-absence lives under `people-group/`, and expenses is a single file, `finance/expenses.md`.
- No doc-level `content_hash` in ingestion → `git diff OLD..NEW` already identifies changed files. Hashes pay off at chunk level (re-embedding only changed chunks), together with pipeline version columns (`chunker_version`, `embed_model`), because a chunker or model change alters no file. How much a chunk hash saves depends on chunking: fixed windows shift every chunk after an edit, while heading-based chunks isolate the change.
- `/code-review` gate caught: `make corpus` checked only HEAD and the file count, so local edits (or one add plus one delete) in `data/handbook` passed as "ok" → it now fails on a dirty `git status`, and doesn't silently reset, so edits aren't destroyed. It also passes `--cone` explicitly instead of relying on the git version's default.
- **Ingest mirrors the snapshot:** → [ADR-0002](../decisions/0002-ingest-mirrors-snapshot.md)
- Real-file findings that shaped parsing:
  - All 4,177 files use YAML front matter.
  - One uses `Title:` (capitalised), so the key match is case-insensitive.
  - 10 files have no title, so they fall back to the filename or parent directory.
  - 138 leaf bundles (`index.md`) map to the directory URL, like `_index.md`.
  - 0 `url:` overrides. The single `aliases:` is ignored.
  - `finance/expenses.md` has **two** headings numbered "4.1" (TRAVEL and NON-TRAVEL). Co-Working and Internet sit under the second. That matters for any eval or chunk citation that uses section numbers.
- `/code-review` gate caught two problems in ingestion:
  - **Ingest only checked HEAD.** A dirty checkout would have been stored labelled as pinned content. A narrowed or empty checkout would have made the mirror-delete wipe rows, and an empty scan would have emptied the table. Fix: `corpus.verify()` (HEAD, clean tree, file count) is shared by `make corpus` and `make ingest`.
  - **`url_path` kept uppercase.** Hugo lowercases URLs. On the live site, `/billing-ops-GPO/` returns 302 and `/billing-ops-gpo/` returns 200. Fix: `url_path` is lowercased. One file was affected at the pin.
- Schema is applied without a migration tool. `db/init/002_documents.sql` is run by docker init on fresh volumes and re-applied (`IF NOT EXISTS`) by `make ingest` on existing ones. A real column change later will need either a migration tool or `down -v`. Revisit when the schema first changes.

---

Prev: [2026-10-05: scaffold](2026-10-05-scaffold.md) · Next: [2026-10-12: baseline decisions, spec 0003](2026-10-12-baseline-decisions.md)
