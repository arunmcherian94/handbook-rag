# 0012. Versioned eval set; compare runs only within a version

- **Status:** accepted
- **Date:** 2026-10-16
- **Journal:** [2026-10-16 eval metric decisions](../journal/2026-10-16-eval-metric-decisions.md)

## Context
Eval rows change as they are reviewed, and scorers and judges change too. A score is only comparable if the thing measuring it is held fixed, so the eval's effect has to be measured apart from the system's.

## Decision
**(b) Eval versioning:** every change makes a new version with a changelog entry per question. Runs record the eval version, a sha256 of the eval file and the harness git SHA, and are compared only within one version. When the eval changes, the frozen baseline is re-run on the new version, so the eval's effect is measured apart from the system's. A scorer or judge change also means re-running the baseline. So in the eval set, I will bump the version on any row change and re-run the baseline before comparing.

## Consequences
Every eval change costs a baseline re-run before any comparison.

## Informed by
- [Research: versioning evals and keeping the baseline comparable](../reading/week-01.md#research-versioning-evals-and-keeping-the-baseline-comparable)
