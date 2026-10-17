# 0001. Whole handbook at a pinned SHA, blobless sparse clone

- **Status:** accepted
- **Date:** 2026-10-07
- **Journal:** [2026-10-07 corpus and ingestion](../journal/2026-10-07-corpus-and-ingestion.md)

## Context
A narrow corpus (the 45 files the seed questions touch) has too few distractors and inflates retrieval numbers, and raw ingest of ~4k files is cheap. The seed questions shape the eval set, not the corpus.

A blobless clone has every commit and tree but no file contents until needed. Checkout fetches blobs only for the sparse paths. `--depth 1` drops the history needed for recency work. `--filter=tree:0` is lighter, but path-filtered `git log` then fetches trees lazily and becomes very slow.

## Decision
Corpus is all of `content/handbook/` (4,177 `.md` files), not the 45 files the seed questions touch.

Pinned `5273b21` (committed 2026-10-07T11:36:50+13:00). A blobless clone took ~14s and is 90 MB of `.git` for 105,724 commits.

## Consequences
- `git log -- <path>` works offline, but `log -p`, `blame` and historical diffs fetch blobs lazily, so they're slow and need network. The clone is a promisor remote, so those operations fail if GitLab is unreachable.
- Shallow and treeless clones were rejected (see Context).
