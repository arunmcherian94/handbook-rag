# 0016. Grade with code first; judges only for coded failures

- **Status:** accepted
- **Date:** 2026-10-14
- **Journal:** [2026-10-14 eval set design](../journal/2026-10-14-eval-set-design.md)

## Context
(a) Failure categories: the six question types are coverage strata, not failure categories. Categories come only from coded traces (PR #9 now, baseline traces from Friday). Decisions (b) criteria drift, (c) judge claims and (d) binary rubric were deferred to Thu 16:00 and decided 2026-10-16.

## Decision
- **(a)** In the eval set, I will tag each question with its type for coverage, report failures by category, and add a category only when a trace shows it.
- **(f) Order:** Friday runs the baseline and reads the traces first. Retrieval metrics and code checks need no judge. Saturday codes the new traces, updates categories, then writes judges only for failures code can't detect. So in the eval set, I will run it before any judge exists, and every judge traces back to a coded failure.
- **(c) No "validated judge" claim:** validating a judge needs human labels of the target failure, a train/dev/test split with an untouched test set, and reported TPR and TNR. With 52 rows we have none of that. So in the eval set, I will report a judge only as "checked against N labels, TPR x, TNR y", and hold out a test portion of the coded traces from the start.
- **(d) Code checks, no labels needed:** citation present, cited heading exists at the pin, exact abstention strings, no URLs copied into the answer. Answers are scored by binary fact checks (`[required]`/`[optional]`), not a scale. So in the eval set, I will grade everything code can check with code.
- **Retrieval and generation scored separately:** spec 0004 covers retrieval metrics plus the abstention and code checks. Faithfulness and answer-relevance judges come later, only for failures found in coded traces, per (f).

## Consequences
Judges are not built yet; see [follow-ups](../follow-ups.md) (answer judges, validated per (c)).

## Informed by
- [Hamel Husain & Shreya Shankar: How do I know if I can trust my automated eval?](../reading/week-01.md#hamel-husain--shreya-shankar-how-do-i-know-if-i-can-trust-my-automated-eval)
- [Hamel Husain & Shreya Shankar: Why binary pass/fail instead of 1–5 ratings?](../reading/week-01.md#hamel-husain--shreya-shankar-why-binary-passfail-instead-of-15-ratings)
