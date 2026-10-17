# 2026-10-14: eval set design

- **Logging rule (replaces the old "decisions only, no summary" reading-log rule):** the reading log (now `docs/reading/week-NN.md`) gets one entry per reading with an extended takeaway summary and the decisions it informed. NOTES.md stays short, dated notes and decisions. Sources are paraphrased.
- **PR #9 final numbers:** 2 retrieval only, 1 generation only, 6 mixed, 1 correct. Top patterns: retrieved but not used (7/10), answer in a section that starts mid-chunk (6/10), right page wrong chunk (6/10). The last two share 5 questions and may have one cause (fixed windows splitting sections); they stay separate until baseline traces confirm it.
- **Code checks before judges:** → [ADR-0016](../decisions/0016-code-checks-before-judges.md)
- **ACLs deferred from the quality set:** → [ADR-0011](../decisions/0011-acls-deferred-from-quality-set.md)
- **Eval questions human-authored:** → [ADR-0010](../decisions/0010-eval-questions-human-authored.md)
- **Deferred to Thu 16:00:** (b) criteria drift, (c) judge claims, (d) binary rubric. *(Decided 2026-10-16.)*

---

Prev: [2026-10-13: error analysis, seed traces](2026-10-13-error-analysis.md) · Next: [2026-10-15: ACLs in evals](2026-10-15-acls-in-evals.md)
