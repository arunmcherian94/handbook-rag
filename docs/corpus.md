# Corpus: git behaviors, limitations, assumptions

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
