# Eval set changelog

Every run records the eval-set version it used. Scores from different versions are not compared directly.

## v1.2 (2026-10-16)

- **Counts:** unchanged from v1.1 (52 live rows, 33 / 19).
- **Markers on every answerable row:** `[required]` / `[optional]` added to the 17 rows that had none (8, 10, 11, 13, 26, 32, 46, 48, 49, 51, 52, 53, 55, 59, 65, 99, 100), from each row's `Scored:` line and notes, owner-approved. Exception: row 10 F7 (the six values spell CREDIT) is optional although its `Scored:` line lists F1–F7. Variant facts are optional. Each row has a `decision:` line naming its required facts.
- **Markers completed on 44, 89, 96:** facts left unmarked in v1.1 now carry the markers their 2026-10-16 owner decisions already stated.
- **Why:** spec 0004 computes recall over required facts, so every answerable row needs machine-readable markers.
- **Unchanged:** question text, fact text, citations, expected docs, row types, out-of-corpus strings. Checked by diff against v1.1: only marker tokens, `decision:` lines and the header changed.

## v1.1 (2026-10-16)

- **Counts:** 52 live rows, 33 answerable / 19 out-of-corpus (63 / 37). By type: lookup 9, synthesis 8, contradiction 8, recency 8, ooc-in-scope 10, ooc-off-topic 9.
- **Sweep:** a fresh subagent searched the pin blind (questions and expected paths only, no facts) for other pages answering the 38 unreviewed rows: 33 flagged, 5 none. [sweep-2026-10-16.md](sweep-2026-10-16.md).
- **Owner review:** seeded 8-row sample (`random.Random(20261016)`: 26, 44, 89, 96, 47, 62, 111, 113) plus 50, 58, 87. Sample result: 1 of 8 answer-level errors (62), 3 of 8 counting missing expected docs (44, 96). Under the decision rule any error meant reviewing all remaining rows before a baseline run.
- **Auto-review:** the remaining 26 rows were reviewed by Claude subagents against the cited excerpts and the sweep, with fixes applied on the owner's standing approval. They carry `ref_source: llm-draft, auto-reviewed`.
- **Cut (2):** 62 and 114. The pin partly answers both, so a grounded answer would fail the exact abstention string.
- **Fact changes:** facts reworded to what the cited lines state in 96, 5, 9, 22, 23, 34, 35, 38, 92. `[required]` / `[optional]` markers added to every row reviewed on 2026-10-16. New optional variant facts in 5, 22, 34, 87, 89, 96.
- **Expected docs added:** 44 (`customer-experience/csm/segment/_index.md`), 87 (`usecase-gtm/devops-platform/_index.md`), 96 (`on-call/tier-2.md`, `support/support-time-off.md`), 38 (`incident-management/roles/communications-lead.md`, `corporate-communications/incident-communications-plan.md`).
- **New field:** `recency_basis` on all 16 contradiction and recency rows, each with what scores the conflict. `history-only` (8): 11, 44, 49, 50, 51, 52, 53, 55. `in-page` (8): 8, 10, 13, 46, 48, 58, 59, 100. The conflict isn't scored at all on 50, 53 and 58.
- **Unchanged:** question text, row types (except the two cuts) and out-of-corpus expected strings, checked by diff against the pre-review file. Citations re-checked against the pin: 239 checked, 0 real problems.

## v1 (2026-10-15)

- **File:** [eval-set-v1.md](eval-set-v1.md). Corpus pin `5273b21`.
- **Counts:** 54 live rows, 33 answerable / 21 out-of-corpus (61 / 39). By type: lookup 9, synthesis 8, contradiction 8, recency 8, ooc-in-scope 12, ooc-off-topic 9.
- **Source:** the 76 UNVERIFIED quality candidates of 2026-10-14. Questions were written with no corpus access; question text is unchanged.
- **References:** drafted by Claude in a fresh session from the pinned corpus only, as fact lists (k-of-n), each fact tied to path + heading + line range. All 367 citations machine-checked against the pin. Out-of-corpus rows use the exact abstention strings.
- **Review:** 16 rows `llm-draft, reviewed` (trap verdicts checked against excerpts, plus row 65); 38 rows `llm-draft, unreviewed`.
- **Recoded against the pin:**
  - to answerable: 109 (discounts), 15, 61, 64, 65 (later cut except 65)
  - to lookup, trap removed: 9, 56 (only the $100 internet cap is in the pin)
  - to ooc-in-scope: 47 (France's statutory minimum isn't in the pin)
- **Cut (22):**
  - ungradable: 45 (old name "HelpLab" absent from the pin), 101, 108 (partial answers in the pin)
  - final cut to 54: 54, 56, 1, 15, 28, 29, 64, 86, 91, 95, 103, 6, 33, 37, 39, 61, 97, 98, 109. Reasons are on each row.
- **Known gaps:**
  - out-of-corpus split is 12 : 9 in-scope vs off-topic, not about 2:1
  - no easy "floor" lookup row
  - per-country probation and notice-period tables are Hugo shortcode data, not in the corpus
  - trap hypotheses T2, T7, T8 don't hold in the pin; those rows test what the pin actually contains
