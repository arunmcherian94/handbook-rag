# 0001: Corpus pin

- Status: draft
- Date: 2026-10-07

## Problem

Every later metric (recall, MRR, judge scores) is only comparable across runs if the corpus can't change underneath it. The GitLab handbook changes daily, and its public/internal boundary has moved before: the Expenses page was removed from public and later restored. The corpus therefore has to be a pinned, reproducible snapshot of the handbook repo's markdown.

## Acceptance criteria

- AC-1: The corpus comes from `https://gitlab.com/gitlab-com/content-sites/handbook` via a blobless clone (`--filter=blob:none`) that keeps full commit history. It is not shallow.
- AC-2: The working tree is a sparse checkout of `content/handbook`, at a pinned commit SHA.
- AC-3: `CORPUS.md` records the source repo URL, pinned SHA, snapshot commit date, sparse paths and expected `.md` file count, in a format that code can parse.
- AC-4: `make corpus` reproduces the checkout into `data/handbook` (gitignored) from `CORPUS.md` alone. Re-running it is safe. It exits non-zero if HEAD ≠ the pinned SHA or if the on-disk `.md` count under `content/handbook` ≠ the recorded count.
- AC-5: No corpus content is committed to this repo.
- AC-6: A fresh clone of this repo reproduces the same SHA and file count with `make corpus`.

## Out of scope

- Ingestion into Postgres (spec 0002).
- Incremental sync between SHAs.
- Git-history mining or per-file dates.
- Rendered HTML.
- Other repos (e.g. www-gitlab-com YAML data).

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| Corpus breadth | All of `content/handbook/` (4,177 `.md` files at the pin, counted via the GitLab API) | **Seed-question subset (45 files):** too few distractors, so retrieval numbers would be inflated and not representative of real questions. Raw ingest of ~4k files is cheap. |
| Clone type | Blobless (`--filter=blob:none`) | **Shallow (`--depth 1`):** loses history needed for later recency work. **Full clone:** 100k+ commits, slow, mostly unused. **Treeless (`--filter=tree:0`):** lighter, but path-filtered `git log` fetches trees lazily and becomes very slow. **Tarball/archive:** no history, no verifiable SHA. |
| Sparse mode | Cone mode on `content/handbook` | **Non-cone patterns:** only needed for file-level precision, which the full tree doesn't need. Cone mode also pulls in repo-root files, which are excluded from the count. |
| Pin | `5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7` (main, committed 2026-10-07T11:36:50+13:00) | Floating `main`: results would drift silently. |
| Manifest | `CORPUS.md` is the single source of truth, parsed by code | **Separate config file:** two places to keep in sync. |

## Open questions

None.

## Verification

- `make corpus` succeeds, and a second run also succeeds without re-cloning.
- `git -C data/handbook rev-parse HEAD` prints the pinned SHA.
- `find data/handbook/content/handbook -name '*.md' | wc -l` prints 4177.
- `git -C data/handbook rev-list --count HEAD` is large, which shows the clone isn't shallow.
- A unit test parses `CORPUS.md` (AC-3).
- `git status` in this repo shows no corpus files.
- Clean-room: clone this repo under `$HOME`, run `make corpus`, and get the same SHA and count.
