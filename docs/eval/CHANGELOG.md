# Eval set changelog

Every run records the eval-set version it used. Scores from different versions are not compared directly.

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
