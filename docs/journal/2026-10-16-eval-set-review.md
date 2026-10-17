# 2026-10-16: eval set v1.1 review

- **Eval questions human-authored:** → [ADR-0010](../decisions/0010-eval-questions-human-authored.md)
- **Sample 8/38 hand-reviewed, 1 answer-level error (3 counting missing expected docs); sweep flagged 33, all triaged.** The decision rule triggered a review of all remaining rows. The owner reviewed 3 more, and 26 were auto-reviewed by Claude subagents with fixes applied on the owner's standing approval (`ref_source: llm-draft, auto-reviewed`). Fact lists of auto-reviewed rows should be hand-checked before the first judge uses them.
- **Gate catch:** row 62 (personal phone device management) was labelled out-of-corpus, but the pin partly answers it (Okta Verify enrolment, posture checks). Cut, along with 114 (performance review score) for the same reason. Missing expected docs on 44 and 96 would have scored correct retrievals as misses.
- **Abstention scoring:** → [ADR-0014](../decisions/0014-abstention-scoring.md)
- **Git history decides currency:** → [ADR-0017](../decisions/0017-history-decides-currency.md)
- **Retrieval metrics:** → [ADR-0013](../decisions/0013-retrieval-metrics.md)

---

Prev: [2026-10-15: ACLs in evals](2026-10-15-acls-in-evals.md) · Next: [2026-10-16: eval metric decisions, reading](2026-10-16-eval-metric-decisions.md)
