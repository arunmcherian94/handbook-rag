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
- `restricted`: deferred to week 2 (see "Permission cases" below)

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

**D5b Role stated in the question text**
- `none`: the question doesn't say who is asking (the usual case)
- `stated`: the text states a role or situation ("new starter here",
  "my report", "I'm in India")
- Include both. Quality questions carry no principal: they run as an
  all-access user, so the set stays identical to the baseline before
  and after week 2's ACLs. There is no user context, so when the
  answer depends on who is asking, the expected answer covers the
  variants or says what it depends on.

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

## Permission cases (deferred to week 2)

Restricted and role-conflict cases are not part of the quality set. The
drafts are parked in the candidates file until the week 2 ACL design is
known. Research pointers are in NOTES (2026-10-15).

## Target counts

Quality set: 60 / 40 answerable / out-of-corpus, with out-of-corpus
split about 2:1 between in-scope and off-topic. Pool: about 76.
Final set: 50–60.

| D1 | Pool (~76) | Final (~55) |
|---|---|---|
| lookup | 14 | 9 |
| synthesis | 14 | 8 |
| contradiction | 11 | 8 |
| recency | 10 | 8 |
| ooc-in-scope | 18 | 15 |
| ooc-off-topic | 9 | 7 |

Spread D2–D6 values across each type; no single value in more than
about 40% of a type.

## Invalid combinations (skip)

- `ooc-*` with any D2 value other than `none`, or with a trap
- `ooc-off-topic` with any D6 value (topic is outside the handbook)
- any non-ooc type with D2 `none`
- `lookup` with `several-pages`
- `synthesis` with `short-section`
- `contradiction` or `recency` without a trap

## 20 seed tuples

These came before D5b, so their D5 is the old persona value.

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
