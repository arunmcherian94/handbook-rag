# 2026-10-15: ACLs in evals

- **ACLs deferred from the quality set:** → [ADR-0011](../decisions/0011-acls-deferred-from-quality-set.md)
- **Eval set v1 committed:** 54 rows, 33 answerable / 21 out-of-corpus (61 / 39); lookup 9, synthesis 8, contradiction 8, recency 8, ooc-in-scope 12, ooc-off-topic 9. [docs/eval/eval-set-v1.md](../eval/eval-set-v1.md), [CHANGELOG](../eval/CHANGELOG.md).
  - 16 rows reviewed (every trap verdict checked against its excerpts, plus row 65). 38 rows are `llm-draft, unreviewed`: review them first on 2026-10-16.
- **Eval questions human-authored:** → [ADR-0010](../decisions/0010-eval-questions-human-authored.md)
- **Git history decides currency:** → [ADR-0017](../decisions/0017-history-decides-currency.md)
- **Gate catch (reference drafting):** the trap hypotheses came from memory, not the pin. T7's $80 cap and the "HelpLab" name exist only in history, and T8 has no number conflict. Those rows were recoded, cut, or re-noted to what the pin contains. "Customer Success" is still in about 300 pinned files.
- **Limitation:** per-country probation and notice-period tables are Hugo shortcodes whose data isn't in `content/handbook`. The RAG can't see them either. Follow-up: check whether shortcode data should be ingested.
- **Gaps accepted for v1:** out-of-corpus is 12 : 9 in-scope vs off-topic, and there is no easy floor row.

---

Prev: [2026-10-14: eval set design](2026-10-14-eval-set-design.md) · Next: [2026-10-16: eval set v1.1 review](2026-10-16-eval-set-review.md)
