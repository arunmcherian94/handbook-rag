# Eval dimensions brief (2026-10-14)

Status: DRAFT, pending review. Input for candidate generation: tuples
first, then questions in a separate prompt. Questions only: no answers,
no expected docs, no citations.

## Dimensions

**D1 Question type** (coverage strata, not failure categories)
- `lookup`: one fact or rule from one place
- `synthesis`: the answer combines several sections or pages
- `contradiction`: the corpus holds two statements that disagree, or an
  old and a new name for the same thing
- `recency`: the answer depends on which statement is current
- `ooc-in-scope`: a plausible handbook question the corpus doesn't
  answer; expected reply "I don't know based on the provided handbook
  excerpts."
- `ooc-off-topic`: not about the handbook; expected reply "Sorry, I
  don't know how to answer that."
- `restricted`: answerable from the corpus, but the principal can't
  see the source; expected reply is the in-scope "I don't know" string

**D2 Answer location** (from PR #9: right page wrong chunk 6/10, answer
in a section that starts mid-chunk 6/10)
- `short-section`: one short section
- `deep-in-long-page`: one section well inside a long page
- `several-sections`: several sections of one page
- `several-pages`: two or more pages
- `none`: not in the corpus (ooc types only)

**D3 Answer shape** (from PR #9: retrieved but not used 7/10, one
number given for a conditional answer in Q9)
- `single-fact`: one figure, name or yes/no
- `list`: several items, all needed
- `conditional`: depends on role, country, entity or situation
- `process`: steps, approvals or deadlines in order

**D4 Phrasing** (from PR #9: plausible distractors 5/10; known
abbreviation sensitivity)
- `handbook-terms`: uses the handbook's own words
- `everyday`: paraphrase in a user's own words
- `abbrev-or-old-name`: an abbreviation or a former name
- `ambiguous-scope`: words that match several entities, countries or
  teams, so distractor pages look relevant

**D5a Principal** (the acting user; always set)

Identity comes from the authenticated session, never from the question
text. Every case names a principal from the table below. The harness
passes it as request context, the way auth would in production.
Answerable cases need one too, because the pre-filter runs on every
query: with the wrong principal, an answerable case silently turns
into a restricted one. When the expected answer depends on the
principal (country, entity, manager or not), it is written for that
principal.

**D5b Role stated in the question text**
- `none`: the question doesn't say who is asking (the usual case)
- `matches`: the text states a role or situation consistent with the
  principal ("new starter here", "my report", "I'm in India")
- `conflicts`: the text claims an ACL-relevant attribute the principal
  doesn't have (e.g. "as a full-time employee…" from a contractor
  principal). Access must still follow the principal. Only employment
  type counts as a conflict: country mismatches don't, since every
  employee can read every country page.
- Include role-stated and role-unstated questions, plus 3–4
  `conflicts` cases.

**D6 Topic area**
- expenses, time off, benefits, compensation, access and IT tools,
  relocation and travel, values and ways of working, org and teams,
  onboarding, security and compliance, people policies (conduct,
  performance reviews, probation, exits), company and strategy

## Named traps (each appears in at least one tuple)

| ID | Trap |
|---|---|
| T1 | new-hire equipment purchase: virtual card vs own funds |
| T2 | access requests: Compass vs Lumos (HelpLab renamed to Compass) |
| T3 | reimbursement payout: two US timelines |
| T4 | values page (CREDIT) vs operating principles |
| T5 | contractor entity: IT BV vs GitLab Services Inc (GSI) |
| T6 | Customer Success renamed Customer Experience (rename only in git history) |
| T7 | internet reimbursement cap: $80 vs $100 |
| T8 | "PTO" vs "paid time off" |

Traps may repeat across tuples, but at most 4 candidates per trap in
the full pool. Exception: T8 allows up to 8, because PTO and holiday
questions are among the most common real user questions.

## Principals (synthetic fixture)

Attributes are limited to what the provisional ACL rule uses. Week 2's
ACL spec adds more if it needs them.

| ID | Employment type | Entity | Country | Manager |
|---|---|---|---|---|
| `emp-us` | employee | GitLab Inc | US | no |
| `emp-nl` | employee | GitLab BV | Netherlands | no |
| `emp-in` | employee | GitLab India | India | no |
| `mgr-us` | employee | GitLab Inc | US | yes |
| `contractor` | contractor | GitLab Services Inc (GSI) | Brazil | no |

## Restricted scope (provisional until week 2)

Principal `contractor` can't see entity-specific benefits and compensation
pages. Exact paths are confirmed from the pinned SHA on Thursday.
Fix due Thursday: as worded, this would also hide the Contractor
Benefits section, which contractors must see. Restrict employee-only
benefits and compensation pages instead.

Each restricted case is one question run twice:
- as the denied principal (`contractor`): the expected reply is the
  in-scope "I don't know" string
- as a control principal (an entitled employee): the expected outcome
  is a correct answer

The question and the reference answer are written once. The control
separates "the ACL blocked it" from "retrieval missed it", since both
produce the same reply.

**Phases** (cases that need ACLs carry `requires: acl`):
- **Week 1 baseline (no ACL):** controls are scored as normal
  answerable cases. If a control misses, the restricted case tests
  nothing and gets fixed or cut. The denied runs are reported in a
  separate "pending: needs ACL" block as a pre-ACL leak rate (the
  before number), never as failures. A leak is measured at retrieval
  level first: any chunk from a restricted doc in the denied
  principal's top k (a code check).
- **Week 2 (ACL pre-filter):** restricted cases are scored. Gates: leak
  rate 0 at retrieval and answer level; over-block rate 0 (a control
  that passed in week 1 and fails now); `conflicts` cases leak 0.
- **Week 5 (injection):** `conflicts` cases grow into injection cases,
  scored with the same leak checks.

## Target counts

Candidate pool: about 100 generated and added; 80–85 after first
triage. Final set: 50–60.

| D1 | Pool (~85) | Final (~55) |
|---|---|---|
| lookup | 13 | 9 |
| synthesis | 13 | 8 |
| contradiction | 13 | 8 |
| recency | 12 | 8 |
| ooc-in-scope | 11 | 7 |
| ooc-off-topic | 6 | 4 |
| restricted | 17 | 11 |

Spread D2–D6 values across each type; no single value in more than
about 40% of a type.

## Invalid combinations (skip)

- `ooc-*` with any D2 value other than `none`, or with a trap
- `ooc-off-topic` with any D6 value (topic is outside the handbook)
- any non-ooc type with D2 `none`
- `restricted` with a principal other than `contractor`, without a
  control principal, or with a topic other than benefits or
  compensation
- `conflicts` on a non-restricted case
- `lookup` with `several-pages`
- `synthesis` with `short-section`
- `contradiction` or `recency` without a trap

## 20 seed tuples

These came before the D5a/D5b split, so their D5 is the old persona value.

| # | D1 | D2 | D3 | D4 | D5 | D6 | Trap |
|---|---|---|---|---|---|---|---|
| 1 | lookup | deep-in-long-page | single-fact | everyday | team-member | expenses | – |
| 2 | lookup | short-section | process | handbook-terms | manager | relocation and travel | – |
| 3 | lookup | short-section | list | abbrev-or-old-name | team-member | org and teams | T6 |
| 4 | lookup | deep-in-long-page | single-fact | abbrev-or-old-name | team-member | time off | T8 |
| 5 | synthesis | several-sections | conditional | everyday | country-specific | time off | – |
| 6 | synthesis | several-pages | process | everyday | new-hire | onboarding | – |
| 7 | synthesis | several-pages | list | ambiguous-scope | contractor | benefits | T5 |
| 8 | contradiction | several-pages | single-fact | everyday | team-member | expenses | T3 |
| 9 | contradiction | several-sections | single-fact | handbook-terms | team-member | expenses | T7 |
| 10 | contradiction | several-pages | list | handbook-terms | team-member | values and ways of working | T4 |
| 11 | recency | several-pages | process | everyday | new-hire | expenses | T1 |
| 12 | recency | several-pages | process | abbrev-or-old-name | team-member | access and IT tools | T2 |
| 13 | recency | several-pages | conditional | ambiguous-scope | contractor | benefits | T5 |
| 14 | ooc-in-scope | none | single-fact | handbook-terms | team-member | benefits | – |
| 15 | ooc-in-scope | none | conditional | everyday | country-specific | compensation | – |
| 16 | ooc-in-scope | none | process | everyday | manager | security and compliance | – |
| 17 | ooc-off-topic | none | single-fact | everyday | team-member | – | – |
| 18 | restricted | short-section | single-fact | handbook-terms | contractor | benefits | – |
| 19 | restricted | several-sections | conditional | everyday | contractor | compensation | – |
| 20 | restricted | deep-in-long-page | list | ambiguous-scope | contractor | benefits | – |
