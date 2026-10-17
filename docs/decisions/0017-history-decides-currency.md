# 0017. Git history decides currency, never facts

- **Status:** accepted
- **Date:** 2026-10-13
- **Journal:** [2026-10-13 error analysis](../journal/2026-10-13-error-analysis.md)

## Context
Reference answers were written from the live site; the system reads the 2026-10-07 snapshot. Some statements conflict or have changed, so the eval needs to know which pinned statement is current. Footer dates and blame mislead: blame misleads after a page delete-and-restore (expenses.md was removed on 18 Mar 2026 and restored whole on 14 May, so every line blames to 14 May), and commit messages mislead (the 13 Sep 2026 "Rename HelpLab to Compass" commit added new access-request content).

## Decision
- **Recency is settled from the statement's own history** (`git log -G`/`-S` on the line), not the footer or blame. References cite the pinned corpus only.
- **Git history decides currency, never facts:** facts cite pinned files only. History only judges which pinned statement is current. Bulk commits make page-level dates weak evidence, so in-page wording ("previously IT BV") is preferred.
- **`recency_basis`:** a contradiction or recency fact settled only by git history can't be met by a model that never sees history. Those facts are kept, labelled `history-only` and reported separately, so a later recency fix can be measured against the same facts. All 16 contradiction and recency rows are labelled: 8 `history-only` (11, 44, 49, 50, 51, 52, 53, 55) and 8 `in-page`.

## Consequences
Rows 50, 53 and 58 don't score their conflict at all; report that alongside the per-type results.
