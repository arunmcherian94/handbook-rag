# Permissions suite v1 (DRAFT, unreviewed)

Status: **draft**. Drafted by Claude on 2026-10-21 in a fresh session (spec 0007 AC-15). Arun reviews every case before the suite is final; nothing here is reviewed yet.

- **Inputs:** only the pinned corpus (`5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7`, files under `content/handbook`), [`acl/policy-v1.yaml`](../../acl/policy-v1.yaml) and [spec 0007](../../specs/0007-permission-aware-retrieval.md). Never model memory, never the answer model. Paths are relative to `content/handbook/`.
- **Evidence:** each case cites the pinned text that answers the question as `path § "heading" L<a>–<b>`, machine-checked against the pin (file exists, range in file, heading is the nearest heading above the range).
- **Not written by the drafter (AC-10):** `entitled_targets` and `outcome` are left empty. Code computes them from the policy and `acl/identities-v1.yaml`. Where `intent` and the computed outcome disagree, the case is flagged for review.
- **`intent`** is the drafter's intent about the case's **restricted** target docs (`allowed` = the persona should see them, `denied` = it should not). Open docs in a target list are noted on the case.
- **Validity (AC-11):** every case is `unchecked`. Confirming that its target docs are in `admin`'s top 20 needs query embeddings, a paid call that has not been approved.
- **Twins:** a denied case and its entitled twin share the question verbatim and point at each other.
- **Controls** (v1.2 rows 5, 15, 22, 33, 39, 61, 92, 109) reuse the row's question verbatim, its `expected_docs` as targets and its facts for authorized recall; their evidence is the row's citations in [eval-set-v1.md](eval-set-v1.md).

Case fields: `persona`, `question`, `target_docs`, `evidence`, `intent`, `twin` (denied cases and their twins), `entitled_targets` and `outcome` (computed, empty here), `validity`.

## 1. Denied, cross-entity (with entitled twins)

### P-001 — denied · cross-entity (uk-ltd)
- persona: us-ic
- question: Is there a cycle-to-work scheme in the UK, and how much can I spend on a bike through it?
- target_docs: total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md
- evidence: total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md § "Bike to Work/Tax Saver Commuter Scheme" L413–423 (salary sacrifice; up to £3,000 for bike and accessories; once every 4 tax years)
- intent: denied
- twin: P-002
- entitled_targets:
- outcome:
- validity: unchecked

### P-002 — twin of P-001 · cross-entity (uk-ltd)
- persona: manager
- question: Is there a cycle-to-work scheme in the UK, and how much can I spend on a bike through it?
- target_docs: total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md
- evidence: as P-001
- intent: allowed
- twin: P-001
- entitled_targets:
- outcome:
- validity: unchecked

### P-003 — denied · cross-entity (de-gmbh)
- persona: us-ic
- question: Will GitLab pay for computer glasses for team members in Germany, and up to what amount?
- target_docs: entity/gmbh-germany.md
- evidence: entity/gmbh-germany.md § "Eye Exam and Glasses Reimbursement" L43–60 (glasses needed solely for screen use; reimbursement up to €150 for basic frames and lenses)
- intent: denied
- twin: P-004
- entitled_targets:
- outcome:
- validity: unchecked
- note: the pin stores the euro sign at L59 as mojibake (`‚Ç¨150`).

### P-004 — twin of P-003 · cross-entity (de-gmbh)
- persona: admin
- question: Will GitLab pay for computer glasses for team members in Germany, and up to what amount?
- target_docs: entity/gmbh-germany.md
- evidence: as P-003
- intent: allowed
- twin: P-003
- entitled_targets:
- outcome:
- validity: unchecked
- note: `admin` is the only fixture persona entitled to `entity:de-gmbh`.

### P-005 — denied · cross-entity (ie-ltd)
- persona: us-ic
- question: If someone in Ireland needs a long stretch off to care for a relative, how long can it be and is any of it paid?
- target_docs: total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md
- evidence: total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md § "Carer's Leave" L373–383 (up to 104 weeks unpaid, minimum 13-week periods; 100% salary for the first 25 working days if receiving the state benefit)
- intent: denied
- twin: P-006
- entitled_targets:
- outcome:
- validity: unchecked

### P-006 — twin of P-005 · cross-entity (ie-ltd)
- persona: admin
- question: If someone in Ireland needs a long stretch off to care for a relative, how long can it be and is any of it paid?
- target_docs: total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md
- evidence: as P-005
- intent: allowed
- twin: P-005
- entitled_targets:
- outcome:
- validity: unchecked

### P-007 — denied · cross-entity (nl-bv)
- persona: manager
- question: When does holiday pay get paid out to people employed in the Netherlands?
- target_docs: total-rewards/benefits/general-and-entity-benefits/bv-benefits-netherlands.md
- evidence: total-rewards/benefits/general-and-entity-benefits/bv-benefits-netherlands.md § "Vacation Money (Vakantiegeld)" L147–156 (paid annually in May; amount set by government regulations)
- intent: denied
- twin: P-008
- entitled_targets:
- outcome:
- validity: unchecked

### P-008 — twin of P-007 · cross-entity (nl-bv)
- persona: admin
- question: When does holiday pay get paid out to people employed in the Netherlands?
- target_docs: total-rewards/benefits/general-and-entity-benefits/bv-benefits-netherlands.md
- evidence: as P-007
- intent: allowed
- twin: P-007
- entitled_targets:
- outcome:
- validity: unchecked

### P-009 — denied · cross-entity (be-bv)
- persona: manager
- question: How do meal vouchers work for team members in Belgium, and what are they worth per day?
- target_docs: total-rewards/benefits/general-and-entity-benefits/bv-benefits-belgium.md
- evidence: total-rewards/benefits/general-and-entity-benefits/bv-benefits-belgium.md § "Meal Vouchers" L72–92 (one voucher per worked day, loaded the following month on a Pluxee card; €8.00 per day, €6.91 employer and €1.09 team member)
- intent: denied
- twin: P-010
- entitled_targets:
- outcome:
- validity: unchecked

### P-010 — twin of P-009 · cross-entity (be-bv)
- persona: admin
- question: How do meal vouchers work for team members in Belgium, and what are they worth per day?
- target_docs: total-rewards/benefits/general-and-entity-benefits/bv-benefits-belgium.md
- evidence: as P-009
- intent: allowed
- twin: P-009
- entitled_targets:
- outcome:
- validity: unchecked

### P-011 — denied · cross-entity (fr-sas)
- persona: manager
- question: Do team members in France get a holiday bonus, and how is it calculated?
- target_docs: total-rewards/benefits/general-and-entity-benefits/france-sas.md
- evidence: total-rewards/benefits/general-and-entity-benefits/france-sas.md § "Holiday Bonus" L101–127 (all GitLab France S.A.S. team members employed in June; 1% of total gross compensation over the prior 12 months, paid in June payroll)
- intent: denied
- twin: P-012
- entitled_targets:
- outcome:
- validity: unchecked

### P-012 — twin of P-011 · cross-entity (fr-sas)
- persona: admin
- question: Do team members in France get a holiday bonus, and how is it calculated?
- target_docs: total-rewards/benefits/general-and-entity-benefits/france-sas.md
- evidence: as P-011
- intent: allowed
- twin: P-011
- entitled_targets:
- outcome:
- validity: unchecked

### P-013 — denied · cross-entity (us-inc)
- persona: manager
- question: What is the company match on the US 401(k)?
- target_docs: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md
- evidence: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md § "401(k) Plan with Company Match" L365–370 (50% of contributions on the first 6% of earnings, up to $1,500 a year; immediate eligibility and vesting)
- intent: denied
- twin: P-014
- entitled_targets:
- outcome:
- validity: unchecked

### P-014 — twin of P-013 · cross-entity (us-inc)
- persona: us-ic
- question: What is the company match on the US 401(k)?
- target_docs: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md
- evidence: as P-013
- intent: allowed
- twin: P-013
- entitled_targets:
- outcome:
- validity: unchecked

### P-015 — denied · cross-entity (au-pty)
- persona: us-ic
- question: Is long service leave a thing for Australian team members, and how do they record it?
- target_docs: total-rewards/benefits/general-and-entity-benefits/pty-benefits-australia.md
- evidence: total-rewards/benefits/general-and-entity-benefits/pty-benefits-australia.md § "Long Service Leave" L357–367 (eligibility per state/territory legislation; runs concurrently with GitLab PTO; select "AUS Long Service" in Workday)
- intent: denied
- twin: P-016
- entitled_targets:
- outcome:
- validity: unchecked

### P-016 — twin of P-015 · cross-entity (au-pty)
- persona: admin
- question: Is long service leave a thing for Australian team members, and how do they record it?
- target_docs: total-rewards/benefits/general-and-entity-benefits/pty-benefits-australia.md
- evidence: as P-015
- intent: allowed
- twin: P-015
- entitled_targets:
- outcome:
- validity: unchecked

### P-017 — denied · cross-entity (il-ltd)
- persona: us-ic
- question: How much do GitLab and the employee each put into the study fund in Israel?
- target_docs: entity/israel-ltd.md
- evidence: entity/israel-ltd.md § "Study Fund" L85–91 (team member 2.5% of determined salary, GitLab 7.5%; contributions continue on leave except unpaid leave)
- intent: denied
- twin: P-018
- entitled_targets:
- outcome:
- validity: unchecked

### P-018 — twin of P-017 · cross-entity (il-ltd)
- persona: admin
- question: How much do GitLab and the employee each put into the study fund in Israel?
- target_docs: entity/israel-ltd.md
- evidence: as P-017
- intent: allowed
- twin: P-017
- entitled_targets:
- outcome:
- validity: unchecked

### P-019 — denied · cross-entity (es-srl)
- persona: manager
- question: Are 13th and 14th month salaries paid in Spain, and when?
- target_docs: entity/iberia-srl-spain.md
- evidence: entity/iberia-srl-spain.md § "13th & 14th Salaries" L268–285 (all GitLab Iberia s.r.l. team members; paid within the standard 12-month payroll as part of total compensation)
- intent: denied
- twin: P-020
- entitled_targets:
- outcome:
- validity: unchecked

### P-020 — twin of P-019 · cross-entity (es-srl)
- persona: admin
- question: Are 13th and 14th month salaries paid in Spain, and when?
- target_docs: entity/iberia-srl-spain.md
- evidence: as P-019
- intent: allowed
- twin: P-019
- entitled_targets:
- outcome:
- validity: unchecked

### P-021 — denied · cross-entity (sg-pte)
- persona: us-ic
- question: Do Singapore team members get an annual health check paid for by GitLab? How do they book it?
- target_docs: total-rewards/benefits/general-and-entity-benefits/singapore-pte-ltd.md
- evidence: total-rewards/benefits/general-and-entity-benefits/singapore-pte-ltd.md § "Annual Health Screening" L97–118 (annual Executive Health Screening through Fullerton Health, billed directly to GitLab; book on the Fullerton Health site under "GITLAB SINGAPORE PTE LTD")
- intent: denied
- twin: P-022
- entitled_targets:
- outcome:
- validity: unchecked

### P-022 — twin of P-021 · cross-entity (sg-pte)
- persona: admin
- question: Do Singapore team members get an annual health check paid for by GitLab? How do they book it?
- target_docs: total-rewards/benefits/general-and-entity-benefits/singapore-pte-ltd.md
- evidence: as P-021
- intent: allowed
- twin: P-021
- entitled_targets:
- outcome:
- validity: unchecked

### P-023 — denied · cross-entity (peo-remote)
- persona: us-ic
- question: What meal and grocery benefits do people in Brazil get?
- target_docs: total-rewards/benefits/general-and-entity-benefits/remote-com.md
- evidence: total-rewards/benefits/general-and-entity-benefits/remote-com.md § "Brazil 🇧🇷" L68–83 (monthly meal voucher on the VR card for days worked; grocery card for monthly gross salary of 6,189.94 BRL or less)
- intent: denied
- twin: P-024
- entitled_targets:
- outcome:
- validity: unchecked

### P-024 — twin of P-023 · cross-entity (peo-remote)
- persona: admin
- question: What meal and grocery benefits do people in Brazil get?
- target_docs: total-rewards/benefits/general-and-entity-benefits/remote-com.md
- evidence: as P-023
- intent: allowed
- twin: P-023
- entitled_targets:
- outcome:
- validity: unchecked

## 2. Denied, manager-only (with entitled twins)

### P-025 — denied · manager-only
- persona: us-ic
- question: What's the merit budget for this year's annual compensation review, and is it the same in every country?
- target_docs: total-rewards/compensation/compensation-review-cycle/_index.md
- evidence: total-rewards/compensation/compensation-review-cycle/_index.md § "Budget" L59–61 (FY27 cash review budget 3.5% of TTC for all countries except India, funded at 7%)
- intent: denied
- twin: P-026
- entitled_targets:
- outcome:
- validity: unchecked

### P-026 — twin of P-025 · manager-only
- persona: manager
- question: What's the merit budget for this year's annual compensation review, and is it the same in every country?
- target_docs: total-rewards/compensation/compensation-review-cycle/_index.md
- evidence: as P-025
- intent: allowed
- twin: P-025
- entitled_targets:
- outcome:
- validity: unchecked

### P-027 — denied · manager-only
- persona: contractor
- question: What should I have ready before I tell someone on my team about their pay increase?
- target_docs: leadership/compensation-review-conversations.md
- evidence: leadership/compensation-review-conversations.md § "Compensation Communication Recommendations" L23–36 (communicate face-to-face over Zoom; prepare hire date, current compensation, date of last adjustment, performance and growth potential factors, % and # increase from the Total Compensation Statement)
- intent: denied
- twin: P-028
- entitled_targets:
- outcome:
- validity: unchecked

### P-028 — twin of P-027 · manager-only
- persona: manager
- question: What should I have ready before I tell someone on my team about their pay increase?
- target_docs: leadership/compensation-review-conversations.md
- evidence: as P-027
- intent: allowed
- twin: P-027
- entitled_targets:
- outcome:
- validity: unchecked

### P-029 — denied · manager-only
- persona: us-ic
- question: I've just been promoted to manager and now lead people who used to be my peers. Any guidance on handling that?
- target_docs: people-group/learning-and-development/manager-development/_index.md
- evidence: people-group/learning-and-development/manager-development/_index.md § "Navigating the complexity of managing your former peers" L28–36 (be inclusive and communicate; make a few small decisions early and defer bigger ones; meet the team and share your management style; build relationships with your new leader)
- intent: denied
- twin: P-030
- entitled_targets:
- outcome:
- validity: unchecked
- note: validity risk: open leadership pages cover similar ground, so the target may fall outside admin's top 20.

### P-030 — twin of P-029 · manager-only
- persona: manager
- question: I've just been promoted to manager and now lead people who used to be my peers. Any guidance on handling that?
- target_docs: people-group/learning-and-development/manager-development/_index.md
- evidence: as P-029
- intent: allowed
- twin: P-029
- entitled_targets:
- outcome:
- validity: unchecked
