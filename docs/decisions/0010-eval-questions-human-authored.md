# 0010. Eval questions human-authored; references from the pin

- **Status:** accepted
- **Date:** 2026-10-14
- **Journal:** [2026-10-14 eval set design](../journal/2026-10-14-eval-set-design.md)

## Context
Eval questions and reference answers need a source that does not flatter the retriever and does not come from model memory. The handbook is almost certainly in every model's pretraining, so references drafted from memory can disagree with the pinned corpus.

Reference-rule change (dated 2026-10-15, recorded 2026-10-16): references may be drafted by Claude in a fresh session from the pin, never from model memory and never by gpt-5.4-mini. Reason: time.

## Decision
- **Candidate generation: two steps** (dimensions brief and 20 seed tuples in [docs/eval/2026-10-14-dimensions.md](../eval/2026-10-14-dimensions.md), reviewed before use → an LLM in a fresh context writes more tuples → a separate prompt turns tuples into questions). Questions only, no corpus reads, marked UNVERIFIED. All answers and expected docs are written by hand from the pinned SHA.
- **Candidate pool built:** 103 candidates, then a first triage by a fresh subagent with no corpus access, leaving 82 (60 / 21 / 20). Process: [docs/eval/README.md](../eval/README.md).
- **Persona `unstated` added:** real users rarely say who they are. Restricted questions include ones with no stated role, since access must come from the user's role, not the question text.
- **Out-of-corpus rule:** if the pin directly answers the question, recode it as answerable. If it asks for a value or personal state the pin doesn't have, keep it out-of-corpus. If the pin gives only a partial answer, cut it, because an exact-string check can't grade it fairly.
- **Reference rule (2026-10-15):** references may be drafted by Claude in a fresh session from the pin, never from model memory and never by gpt-5.4-mini. Mitigations: every fact tied to an excerpt, trap rows reviewed first, a `ref_source` field on every row.
- **Questions generated from pages (Hamel's FAQ) not used for v1:** page wording flatters dense retrieval, and the method can't produce out-of-corpus, contradiction or recency rows (35 of 52).

## Consequences
- Fact lists of auto-reviewed rows should be hand-checked before the first judge uses them.
- The restricted-user handling in this pool was later superseded; see [0011](0011-acls-deferred-from-quality-set.md).

## Informed by
- [Hamel Husain: Your AI Product Needs Evals](../reading/week-01.md#hamel-husain-your-ai-product-needs-evals)
