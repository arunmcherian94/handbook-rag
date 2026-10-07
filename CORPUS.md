# Corpus

This file pins the handbook snapshot. `make corpus` reads it and reproduces the checkout in `data/handbook` (gitignored). See `specs/0001-corpus-pin.md`.

- Source repo: https://gitlab.com/gitlab-com/content-sites/handbook.git
- Snapshot commit SHA: 5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7
- Snapshot date: 2026-10-07T11:36:50+13:00
- File count: 4177
- Clone method: blobless (`--filter=blob:none`), full history, cone-mode sparse checkout, detached HEAD at the SHA

File count is the number of `.md` files under the included paths at the snapshot.

## Included paths

```sparse
content/handbook
```

## Widening or re-pinning

- **Widen:** add a path to the block above, update the file count, and run `make corpus`. It keeps the same SHA and doesn't re-clone.
- **Re-pin:** change the SHA, date and file count, then run `make corpus`. Metrics from different SHAs are not comparable.
