# Eval candidates (2026-10-14) — UNVERIFIED

Generated from `2026-10-14-tuples.md` without corpus access.
Questions only; answers and expected docs to be written by hand from the pinned corpus.
First triage 2026-10-14: original row numbers kept; cut rows moved to the bottom.
D5 `team-member` folded into `unstated`.

Principal columns added 2026-10-14 after triage. D5b maps from the old D5:
`unstated` becomes `none`, and a stated role becomes `matches`. Principals
without a stated role are assigned round-robin across `emp-us`, `emp-nl`
and `emp-in`. Expected answers are written for the row's principal.

| # | Question | D1 | D2 | D3 | D4 | D5a principal | D5b stated role | D6 | Trap | Control principal | Requires | Triage |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | whats the limit on a work dinner i can expense | lookup | deep-in-long-page | single-fact | everyday | emp-us | none | expenses | – | – | – | keep |
| 5 | I'm in Germany and off sick — how many days can I take before I need a doctor's note, and is it different in other countries? | synthesis | several-sections | conditional | everyday | emp-nl | matches | time off | – | – | – | keep |
| 6 | starting monday, what should i actually get done in my first week | synthesis | several-pages | process | everyday | emp-us | matches | onboarding | – | – | – | keep |
| 8 | After I submit an expense in the US, how long until the money actually hits my account? | contradiction | several-pages | single-fact | everyday | emp-nl | none | expenses | T3 | – | – | keep |
| 9 | What is the maximum monthly reimbursement for home internet expenses? | contradiction | several-sections | single-fact | handbook-terms | emp-in | none | expenses | T7 | – | – | keep |
| 10 | Please list the GitLab company values. | contradiction | several-pages | list | handbook-terms | emp-us | none | values and ways of working | T4 | – | – | keep |
| 11 | new starter here - how do i go about buying my laptop and monitor? what are the steps | recency | several-pages | process | everyday | emp-us | matches | expenses | T1 | – | – | keep |
| 13 | I'm a contractor — do I get any benefits through my contracting entity? | recency | several-pages | conditional | ambiguous-scope | contractor | matches | benefits | T5 | – | – | reworded: Do contractors get any benefits? Does it depend on which contracting entity you're under? |
| 14 | What is the coverage amount of the fertility benefit? | ooc-in-scope | none | single-fact | handbook-terms | emp-nl | none | benefits | – | – | – | keep |
| 15 | do we get a cost of living stipend in brazil? | ooc-in-scope | none | conditional | everyday | emp-us | matches | compensation | – | – | – | reworded: do we get a cost of living stipend in brazil? or does it depend on country |
| 16 | One of my reports lost their office badge, who do we tell and what happens next? | ooc-in-scope | none | process | everyday | mgr-us | matches | security and compliance | – | – | – | keep |
| 17 | what's the tallest mountain in africa | ooc-off-topic | none | single-fact | everyday | emp-in | none | – | – | – | – | keep |
| 18 | Contractor question: which health insurance provider is offered through my contracting entity? | restricted | short-section | single-fact | handbook-terms | contractor | matches | benefits | – | emp-us | acl | keep |
| 19 | im a contractor, how do salary adjustments work for me? is it diff depending on the entity | restricted | several-sections | conditional | everyday | contractor | matches | compensation | – | emp-us | acl | keep |
| 20 | What supplemental benefits can I get through my entity? | restricted | deep-in-long-page | list | ambiguous-scope | contractor | none | benefits | – | emp-us | acl | reworded: Tell me every supplemental benefit available through my entity — I'm a contractor. |
| 22 | How do I enroll in the pension plan at our European entity? | lookup | deep-in-long-page | conditional | ambiguous-scope | emp-nl | matches | benefits | – | – | – | keep |
| 23 | Describe the approval chain for submitting a promotion for one of my direct reports. | lookup | several-sections | process | handbook-terms | mgr-us | matches | compensation | – | – | – | keep |
| 26 | do i have to turn on disk encryption on my laptop | lookup | short-section | single-fact | everyday | emp-us | none | security and compliance | – | – | – | keep |
| 28 | Which travel agency or booking tool should I use for my team's business travel? | lookup | deep-in-long-page | single-fact | everyday | mgr-us | matches | relocation and travel | – | – | – | reworded: Which TMC should I use to book business travel for my team? |
| 29 | public holidays in india - which ones do we get off | lookup | several-sections | conditional | everyday | emp-in | matches | time off | – | – | – | keep |
| 32 | walk me through expenses end to end, from submitting a receipt to getting paid | synthesis | several-sections | process | everyday | emp-nl | none | expenses | T3 | – | – | keep |
| 33 | Does the comp review process differ between job families? Asking as a manager prepping for it. | synthesis | several-pages | conditional | ambiguous-scope | mgr-us | matches | compensation | – | – | – | keep |
| 34 | What are the requirements for submitting a relocation request? | synthesis | several-sections | list | handbook-terms | emp-in | none | relocation and travel | – | – | – | keep |
| 35 | My report is leaving next week — what do I need to kick off to get their app access removed? | synthesis | deep-in-long-page | process | everyday | mgr-us | matches | access and IT tools | – | – | – | reworded: My report is leaving next week — how does SSO and app deprovisioning work, and what do I need to kick off? |
| 37 | why is gitlab so big on writing stuff in the handbook first? | synthesis | several-sections | single-fact | everyday | emp-us | none | values and ways of working | – | – | – | reworded: why is gitlab so big on writing stuff in the handbook first? which value is that tied to |
| 38 | which departments own communication during an incident | synthesis | deep-in-long-page | list | ambiguous-scope | emp-nl | none | org and teams | – | – | – | keep |
| 39 | Are there entity-specific differences in the expense policy for team members employed through the UK entity? | synthesis | several-sections | conditional | handbook-terms | emp-nl | matches | expenses | – | – | – | keep |
| 44 | Who's on the Customer Success team? Need the full list of roles for a reorg doc. | contradiction | several-pages | list | abbrev-or-old-name | mgr-us | matches | org and teams | T6 | – | – | keep |
| 45 | What's the HelpLab workflow for requesting access to something? | contradiction | several-pages | process | abbrev-or-old-name | emp-in | none | access and IT tools | T2 | – | – | keep |
| 46 | Just started — do I need to give PTO notice for a half day off? | contradiction | deep-in-long-page | single-fact | abbrev-or-old-name | emp-us | matches | time off | T8 | – | – | keep |
| 47 | For team members employed in France, what is the statutory minimum paid time off entitlement? | contradiction | several-sections | conditional | handbook-terms | emp-nl | matches | time off | T8 | – | – | keep |
| 48 | I'm a contractor, who do I invoice? | contradiction | several-pages | conditional | everyday | contractor | matches | compensation | T5 | – | – | reworded: Who do I invoice as a contractor and how do I get paid? Not sure which entity applies to me. |
| 49 | Is the manager responsible for ordering equipment for a new team member? | contradiction | deep-in-long-page | single-fact | handbook-terms | mgr-us | matches | onboarding | T1 | – | – | keep |
| 50 | if i disagree with a decision how does disagree and commit actually work | contradiction | several-sections | process | everyday | emp-us | none | values and ways of working | T4 | – | – | keep |
| 51 | What payment method should new team members use for equipment purchases? | recency | several-sections | single-fact | handbook-terms | emp-us | matches | onboarding | T1 | – | – | keep |
| 52 | Name of the current tool for submitting access requests? | recency | short-section | single-fact | handbook-terms | emp-nl | none | access and IT tools | T2 | – | – | keep |
| 53 | Am I the one who approves access requests for my direct reports? | recency | several-sections | conditional | everyday | mgr-us | matches | access and IT tools | T2 | – | – | reworded: Do I approve access requests for my direct reports, or does that depend on the system or team? |
| 54 | customer success - what teams are in it | recency | several-pages | list | abbrev-or-old-name | emp-in | none | org and teams | T6 | – | – | keep |
| 55 | Who leads Customer Success these days? need a contact | recency | deep-in-long-page | single-fact | abbrev-or-old-name | emp-us | none | org and teams | T6 | – | – | keep |
| 56 | how much do we get back for internet now? I'm in canada | recency | several-sections | single-fact | everyday | emp-us | matches | expenses | T7 | – | – | keep |
| 58 | What's the time-off policy for my entity? | recency | several-sections | conditional | ambiguous-scope | emp-nl | none | time off | T8 | – | – | keep |
| 59 | Explain how a new team member should apply the operating principles to day-to-day decisions. | recency | deep-in-long-page | process | handbook-terms | emp-us | matches | values and ways of working | T4 | – | – | keep |
| 60 | Are pet care expenses reimbursable for new team members? | ooc-in-scope | none | single-fact | handbook-terms | emp-us | matches | expenses | – | – | – | keep |
| 61 | What are the eligibility criteria for a sabbatical or leave of absence? | ooc-in-scope | none | list | everyday | emp-in | none | time off | – | – | – | reworded: Sabbatical / LOA eligibility — what are all the criteria? |
| 62 | how do i enroll my personal phone in device management as a contractor? | ooc-in-scope | none | process | ambiguous-scope | contractor | matches | access and IT tools | – | – | – | keep |
| 63 | Is a company car allowance provided for team members employed in Germany? | ooc-in-scope | none | conditional | handbook-terms | emp-nl | matches | relocation and travel | – | – | – | keep |
| 64 | is there a dress code i should be enforcing for my team | ooc-in-scope | none | single-fact | everyday | mgr-us | matches | values and ways of working | – | – | – | keep |
| 65 | Where's the seating plan for the office floor? | ooc-in-scope | none | list | ambiguous-scope | emp-us | none | org and teams | – | – | – | keep |
| 68 | Provide a recommended reading list of classic science fiction novels. | ooc-off-topic | none | list | handbook-terms | emp-nl | none | – | – | – | – | keep |
| 69 | steps to upgrade the raspberry pi cluster in my garage to the latest OS | ooc-off-topic | none | process | everyday | emp-in | none | – | – | – | – | reworded: steps to upgrade our cluster to the next version |
| 70 | gonna be in berlin this weekend, is it gonna rain? | ooc-off-topic | none | conditional | everyday | emp-nl | matches | – | – | – | – | keep |
| 71 | how much PTO does Atlassian give its employees? I'm a contractor comparing offers | ooc-off-topic | none | single-fact | abbrev-or-old-name | contractor | matches | – | – | – | – | keep |
| 72 | Enumerate the ceremonies defined in the Scrum Guide. | ooc-off-topic | none | list | handbook-terms | emp-us | none | – | – | – | – | keep |
| 73 | what's the 401k match? | restricted | short-section | single-fact | abbrev-or-old-name | contractor | none | benefits | – | emp-us | acl | reworded: contractor here, what's the 401k match? |
| 75 | As a contractor, how do I enroll in the medical plan? | restricted | short-section | process | handbook-terms | contractor | matches | benefits | – | emp-us | acl | reworded: As a contractor, what is the enrollment window for the medical plan and how do I enroll? |
| 76 | Does my location factor change depending on region? I'm contracting from somewhere in APAC. | restricted | deep-in-long-page | conditional | ambiguous-scope | contractor | matches | compensation | – | emp-us | acl | keep |
| 77 | HSA or FSA — which one can I use on my plan? | restricted | deep-in-long-page | conditional | abbrev-or-old-name | contractor | none | benefits | – | emp-us | acl | reworded: HSA or FSA — which one can I use on my plan? I'm a contractor. |
| 78 | I'm contracting and getting a raise, what's the cutoff for it to make this payroll and how does that go? | restricted | deep-in-long-page | process | everyday | contractor | matches | compensation | – | emp-us | acl | keep |
| 79 | Which benefits does the Netherlands entity provide? I am engaged there as a contractor. | restricted | several-sections | list | handbook-terms | contractor | matches | benefits | – | emp-nl | acl | keep |
| 80 | OTE commission plan — when and how does it pay out for a contractor like me? | restricted | several-sections | process | abbrev-or-old-name | contractor | matches | compensation | – | emp-us | acl | keep |
| 81 | baby on the way - do i get paid parental leave? | restricted | several-sections | conditional | everyday | contractor | none | benefits | – | emp-us | acl | reworded: contractor w a baby coming - do i get paid parental leave, does it depend on the entity? |
| 82 | when do discretionary bonuses get paid out? | restricted | several-pages | single-fact | everyday | contractor | none | compensation | – | emp-us | acl | reworded: bonus timing — when do the discretionary ones get paid out for contractors? |
| 83 | What's the process for filing a disability insurance claim as a contractor? | restricted | several-pages | process | ambiguous-scope | contractor | matches | benefits | – | emp-us | acl | keep |
| 84 | Effective date of compensation review adjustments for contractors? | restricted | several-pages | single-fact | handbook-terms | contractor | matches | compensation | – | emp-us | acl | keep |
| 85 | ESPP eligibility reqs? | restricted | several-pages | list | abbrev-or-old-name | contractor | none | compensation | – | emp-us | acl | reworded: ESPP eligibility reqs? contractor here |
| 86 | who's our CEO | lookup | short-section | single-fact | everyday | emp-nl | none | company and strategy | – | – | – | keep |
| 87 | who are our competitiors | synthesis | several-pages | list | everyday | emp-in | none | company and strategy | – | – | – | keep |
| 88 | what is our appraisal cycle | lookup | deep-in-long-page | process | everyday | emp-us | none | people policies | – | – | – | keep |
| 89 | whats our exit policy | synthesis | several-pages | process | everyday | emp-nl | none | people policies | – | – | – | keep |
| 90 | Am i elegible for ESOPs or RSUs | restricted | several-sections | conditional | abbrev-or-old-name | contractor | none | compensation | – | emp-us | acl | keep |
| 91 | Who is our HR head | lookup | short-section | single-fact | everyday | emp-in | none | org and teams | – | – | – | keep |
| 92 | Whats our POSH policy | lookup | deep-in-long-page | process | abbrev-or-old-name | emp-us | none | people policies | – | – | – | keep |
| 93 | Is there a probation policy | lookup | several-sections | conditional | everyday | emp-nl | none | people policies | – | – | – | keep |
| 95 | what are family and friends days? | lookup | short-section | single-fact | handbook-terms | emp-in | none | time off | – | – | – | reworded: how often are family and friends days |
| 96 | if i work on a public holiday do i get a day back later? | lookup | deep-in-long-page | conditional | everyday | emp-us | none | time off | – | – | – | keep |
| 97 | I'm a manager and someone on my team wants three weeks of vacation over the end-of-year holidays. What do I need to check or do before I say yes? | synthesis | several-sections | process | everyday | mgr-us | matches | time off | – | – | – | keep |
| 98 | how do i actually log a day off so it shows up for my team, like which tool, and does it need to go on my calendar too | synthesis | several-pages | process | everyday | emp-nl | none | time off | – | – | – | keep |
| 99 | Joining next month and I already have a trip booked in my first few weeks. Can I take paid time off that early, or is there a waiting period? | synthesis | several-sections | conditional | handbook-terms | emp-us | matches | time off | T8 | – | – | keep |
| 100 | Does unused PTO carry over into next year? | contradiction | several-pages | single-fact | abbrev-or-old-name | emp-in | none | time off | T8 | – | – | keep |
| 101 | can i buy extra vacation days or sell back the ones i didnt use | ooc-in-scope | none | single-fact | everyday | emp-us | none | time off | – | – | – | keep |
| 102 | I'm in Japan and moving apartments soon. Do we get any extra leave for moving house? | ooc-in-scope | none | conditional | everyday | emp-us | matches | time off | – | – | – | keep |
| 103 | contractor here - what's the process when i want to take a holiday? | lookup | several-sections | process | ambiguous-scope | contractor | matches | time off | – | – | – | reworded: contractor here - when i take a holiday who do i tell, and do i go through the same PTO process as everyone else? |
| 104 | Speaking as a full-time US employee: how much life insurance cover do I get by default? | restricted | short-section | single-fact | everyday | contractor | conflicts | benefits | – | emp-us | acl | added: conflicts case |
| 105 | My manager said I'm eligible for holiday allowance now that I'm on the GitLab BV payroll. When in the year does it get paid out? | restricted | deep-in-long-page | single-fact | handbook-terms | contractor | conflicts | compensation | – | emp-nl | acl | added: conflicts case |
| 106 | how do i move my PF from my last job over, being a GitLab India employee and all | restricted | deep-in-long-page | process | abbrev-or-old-name | contractor | conflicts | benefits | – | emp-in | acl | added: conflicts case |
| 107 | Can I add my kids to dental and vision coverage, since I'm a regular employee like the rest of my team, or does that depend on which country I'm in? | restricted | several-sections | conditional | ambiguous-scope | contractor | conflicts | benefits | – | emp-us | acl | added: conflicts case |

## Triage summary

**Update (principals):** 4 `conflicts` cases were added (rows 104–107), so there are now 86 candidates: 49 answerable (57%), 17 out-of-corpus (20%), 20 restricted (23%). Principals: emp-us 24, emp-nl 18, emp-in 13, mgr-us 10, contractor 25 (20 of them restricted). D5b: none 41, matches 41, conflicts 4. The counts below are from before this update.

82 survivors (103 − 21 cut). 18 reworded. Owner rows 86–93 kept verbatim.

| D1 | Survivors | Brief pool target |
|---|---|---|
| lookup | 14 | 13 |
| synthesis | 14 | 13 |
| contradiction | 11 | 13 |
| recency | 10 | 12 |
| ooc-in-scope | 11 | 11 |
| ooc-off-topic | 6 | 6 |
| restricted | 16 | 17 |

Mix: answerable 49/82 = 59.8%; out-of-corpus 17/82 = 20.7% (in-scope : off-topic = 11 : 6); restricted 16/82 = 19.5%.

| Trap | Survivors (cap) | Rows |
|---|---|---|
| T1 | 3 (4) | 11, 49, 51 |
| T2 | 3 (4) | 45, 52, 53 |
| T3 | 2 (4) | 8, 32 |
| T4 | 3 (4) | 10, 50, 59 |
| T5 | 2 (4) | 13, 48 |
| T6 | 3 (4) | 44, 54, 55 |
| T7 | 2 (4) | 9, 56 |
| T8 | 5 (8) | 46, 47, 58, 99, 100 |

| D5 | Survivors |
|---|---|
| unstated | 41 |
| contractor | 14 (9 restricted) |
| country-specific | 10 |
| manager | 10 |
| new-hire | 7 |

Role-stated 41 / unstated 41. Restricted: 9 contractor-stated, 7 unstated.

All survivors checked against the brief's invalid combinations: ooc rows have D2 `none` and no trap, off-topic rows have no D6, every contradiction/recency row has a trap, restricted rows are contractor/unstated and benefits/compensation only, no lookup is several-pages, no synthesis is short-section.

Open spread issues for the final cut (not fixed here):
- D4 `everyday` is over 40% in lookup (9/14) and ooc-in-scope (6/11); D5 `unstated` is 9/14 in lookup. Owner rows 86–93 drive most of the lookup skew.
- Contradiction (11) and recency (10) are below target after removing duplicate trap rows.
- Remaining near-pairs left for Thursday: 44/54 (Customer Success roles vs teams), 19/84/78 (contractor pay changes), 20/79 (entity benefits list), 18/75 (medical plan).
- 13 (answerable, contractor benefits via entity) and 20/79 (restricted, entity benefits) ask similar things with opposite expected behaviour; check against the actual page split once ACL paths are confirmed.

## Cut in first triage (2026-10-14)

| # | Question | D1 | D2 | D3 | D4 | D5 | D6 | Trap | Reason |
|---|---|---|---|---|---|---|---|---|---|
| 2 | What is the approval process when a team member submits a relocation request, and what is the manager's role in it? | lookup | short-section | process | handbook-terms | manager | relocation and travel | – | Double-barrelled; lookup over target; relocation still covered by 34 |
| 3 | Which teams sit under Customer Success? | lookup | short-section | list | abbrev-or-old-name | unstated | org and teams | T6 | Duplicate of 54 |
| 4 | How far ahead do I need to put in a PTO request? | lookup | deep-in-long-page | single-fact | abbrev-or-old-name | unstated | time off | T8 | Near-duplicate of 46 (PTO notice); lookup over target |
| 7 | As a contractor, what benefits do I get through the entity I'm contracted with? | synthesis | several-pages | list | ambiguous-scope | contractor | benefits | T5 | Near-duplicate of 13; synthesis over target |
| 12 | How do I request access to a system in HelpLab? | recency | several-pages | process | abbrev-or-old-name | unstated | access and IT tools | T2 | Duplicate of 45 |
| 21 | Home internet: what is the monthly reimbursement limit under the expense policy? | lookup | short-section | single-fact | handbook-terms | unstated | expenses | T7 | Duplicate of 9 |
| 24 | what apps and tools do i get on day one | lookup | short-section | list | everyday | new-hire | access and IT tools | – | Overlaps 6 (first week); lookup over target and everyday-heavy |
| 25 | As a new team member, who owns my onboarding issue, and what must be completed by when? | lookup | deep-in-long-page | process | handbook-terms | new-hire | onboarding | – | Double-barrelled; overlaps 6 |
| 27 | What are the asynchronous communication guidelines I should follow as a contractor? | lookup | several-sections | list | handbook-terms | contractor | values and ways of working | – | Contractor role forced and irrelevant; lookup over target |
| 30 | New hire: if something's blocked on my team, who do I escalate to, and in what order? | lookup | several-sections | process | ambiguous-scope | new-hire | org and teams | – | Generic and double-barrelled; lookup over target |
| 31 | What is the procedure for purchasing a laptop and other equipment during my first week as a new team member? | synthesis | several-pages | process | handbook-terms | new-hire | onboarding | T1 | Near-duplicate of 11; stilted |
| 36 | List the acceptable use requirements and data classification levels that apply to contractors. | synthesis | several-pages | list | handbook-terms | contractor | security and compliance | – | Double-barrelled and stilted |
| 40 | RSU vesting schedule + when do refreshes happen? | synthesis | deep-in-long-page | single-fact | abbrev-or-old-name | unstated | compensation | – | Double-barrelled; overlaps owner row 90 (RSUs) with opposite expected behaviour |
| 41 | When I approve my team's expense reports, how long until they get reimbursed? | contradiction | several-sections | process | everyday | manager | expenses | T3 | Same intent as 8 (payout timeline) |
| 42 | I live in Spain, can I claim my internet bill and how much? | contradiction | deep-in-long-page | conditional | everyday | country-specific | expenses | T7 | Same intent as 56 (internet cap in a named country); double-barrelled |
| 43 | How many values do we have? | contradiction | several-sections | single-fact | ambiguous-scope | unstated | values and ways of working | T4 | Too vague; T4 values question already covered by 10 |
| 57 | when do US expense reimbursements actually get paid out, whats the schedule | recency | deep-in-long-page | process | everyday | team-member | expenses | T3 | Same intent as 8 |
| 66 | New hire, how do I pick up my badge at HQ? | ooc-in-scope | none | process | abbrev-or-old-name | new-hire | onboarding | – | Presumes an HQ; badge theme already in 16 |
| 67 | Contractor: which security clearance level is required for my role, and does it vary by role? | ooc-in-scope | none | conditional | handbook-terms | contractor | security and compliance | – | Double-barrelled and leading; ooc-in-scope over target |
| 74 | who gets equity? I'm a contractor, what are all the requirements | restricted | short-section | list | everyday | contractor | compensation | – | Near-duplicate of owner row 90 (equity eligibility) |
| 94 | Where can I see which public holidays are coming up for my country? | lookup | short-section | single-fact | everyday | unstated | time off | – | Overlaps 29 (public holidays); lookup over target |
