# 0014. Exact-match abstention scoring with diagnostic labels

- **Status:** accepted
- **Date:** 2026-10-16
- **Journal:** [2026-10-16 eval set review](../journal/2026-10-16-eval-set-review.md)

## Context
The prompt tells the model to reply exactly with one of two fixed strings (see [0006](0006-grounding-prompt-fixed-abstentions.md)). The eval has to decide how strictly to grade that, and how to report abstention errors.

## Decision
- **Abstention scoring:** exact match stays pass/fail, because the prompt says "reply exactly". "Starts with" was rejected: it would pass off-topic answers that add training-knowledge text. Failures that start with the right string get a diagnostic label, `abstain+extra`, which doesn't change any score.
- **Abstention reported both ways:** false abstention on answerable rows and invented answers on out-of-corpus rows, never one combined rate. The wrong abstention string (NOT_FOUND on off-topic, or OUT_OF_SCOPE on in-scope) fails the exact check and gets a diagnostic label.

## Consequences
Partial abstentions (an answer plus "I don't know…") are not caught by the exact check beyond the `abstain+extra` label.
