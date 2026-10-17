# 0011. Quality set ignores ACLs; permission cases are a separate suite

- **Status:** accepted
- **Date:** 2026-10-15
- **Journal:** [2026-10-15 ACLs in evals](../journal/2026-10-15-acls-in-evals.md)

## Context
Earlier plan (2026-10-14, superseded 2026-10-15), (e) question mix: a restricted-user answer is a leak, a security failure, not an accuracy miss. So in the eval set, I will score restricted questions as a separate leak rate (target zero), never averaged into accuracy, and scored from week 2 once the ACL pre-filter exists.
- Mix 60 / 20 / 20 (answerable / out-of-corpus / restricted). About 80–85 candidates survive the first triage as a buffer; duplicates and unneeded ones are cut at review.
- Restricted users get the same in-scope reply, "I don't know based on the provided handbook excerpts." A permission message would confirm hidden content exists, and one string keeps the check an exact match.
- Access rule is provisional until week 2: role `contractor` can't see entity-specific benefits and compensation pages (exact paths confirmed from the pinned SHA). Each restricted question must be answerable from the corpus. If the week 2 ACL spec changes the rule, affected questions get a changelog entry.
- Out-of-corpus splits about 2:1 between "in scope but not found" and off-topic. Plausible handbook questions with no answer are where the model fills gaps from memory.

Gate catch (triage): the provisional restricted rule ("entity-specific benefits") would also hide the Contractor Benefits section, which contractors must see. To fix in week 2 (permission cases deferred): restrict employee-only benefits and compensation pages.

Also superseded 2026-10-15 (deferred to week 2):
- **Every case carries a principal** (the acting user, from a 5-user synthetic fixture), passed by the harness as request context. Identity never comes from the question text. Answerable cases need one too, because the pre-filter runs on every query. D5 is split into D5a (principal) and D5b (role stated in the text: none / matches / conflicts). 4 `conflicts` cases test that access follows the principal.
- **Restricted case = one question × two principals:** denied (`contractor`) and an entitled control. The control separates "ACL blocked" from "retrieval missed", which give the same reply. It's written once, with no extra answer rows.
- **Restricted scoring is phased** (`requires: acl`):
  - Week 1: controls are scored normally; denied runs are reported as a pre-ACL leak rate, never as failures. A leak is measured at retrieval level first: a restricted chunk in the top k.
  - Week 2: gates are leak 0, over-block 0, and conflicts leak 0.
  - Week 5: conflicts grow into injection cases.

## Decision
- **The quality set ignores ACLs.** It runs as an all-access user, so with exact search it stays identical to the baseline after week 2's pre-filter. Permission cases (restricted, role conflicts) are deferred until the week 2 ACL design is known. The drafts are parked in the candidates file, and nothing is built for them now.
- **(e) mix changed:** the quality set is 60 / 40 answerable / out-of-corpus, with out-of-corpus about 2:1 in-scope vs off-topic. 10 out-of-corpus candidates added; the pool is 76 (49 / 27).

## Consequences
Research pointers for week 2 (about 30 sources; reading log 15 Oct):
- permissions are a deterministic layer, tested as a separate suite with paired denied/entitled cases
- a leak rate checked on retrieved chunks, reported next to authorized recall (deny-all scores 0 leaks)
- an identical-top-5 regression test for the all-access user
- comparability breaks when HNSW arrives, not when ACLs do

## Informed by
- [Research: access control in RAG evals (three research subagents)](../reading/week-01.md#research-access-control-in-rag-evals-three-research-subagents)
