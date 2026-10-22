# Permissions suite v1

Status: **reviewed, 52 cases**. Drafted by Claude on 2026-10-21 in a fresh session, reviewed by a fresh agent, flags decided by Arun (spec 0007 AC-15, amended 2026-10-21). Changes: [CHANGELOG.md](CHANGELOG.md#permissions-v1-2026-10-21).

- **Inputs:** only the pinned corpus (`5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7`, files under `content/handbook`), [`acl/policy-v1.yaml`](../../acl/policy-v1.yaml) and [spec 0007](../../specs/0007-permission-aware-retrieval.md). Never model memory, never the answer model. Paths are relative to `content/handbook/`.
- **Evidence:** each case cites the pinned text that answers the question as `path § "heading" L<a>–<b>`, machine-checked against the pin (file exists, range in file, heading is the nearest heading above the range).
- **Not written by the drafter (AC-10):** `entitled_targets` and `outcome` are left empty. Code computes them from the policy and `acl/identities-v1.yaml`. Where `intent` and the computed outcome disagree, the case is flagged for review.
- **`intent`** is the drafter's intent about the case's **restricted** target docs (`allowed` = the persona should see them, `denied` = it should not). Open docs in a target list are noted on the case. Partial-entitlement cases give the intent per target doc.
- **Validity (AC-11):** a case is valid when all its target docs are in `admin`'s top 20 (`fixed-512-64`). Admin sees every doc, so this is unfiltered retrieval. Re-checked 2026-10-21 under text-embedding-3-large@1536 ([ADR-0022](../decisions/0022-adopt-text-embedding-3-large-1536.md)): 50 of 52 valid. P-097 and P-098 (row 61) are invalid and dropped from scoring. Under 3-small all 52 were valid.
- **Review:** `review:` records the agent's verdict. Arun decided the edits.
- **Twins:** a denied case and its entitled twin share the question verbatim and point at each other.
- **Controls** (v1.2 row 5) reuse the row's question verbatim, its `expected_docs` as targets and its facts for authorized recall; their evidence is the row's citations in [eval-set-v1.md](eval-set-v1.md).
- **Cut-row cases** (rows 33 and 61, cut from the eval set on 15 Oct) were drafted as controls. They keep the row's question and targets but are scored like any other case, on their target docs, with no eval-set facts (corrected 2026-10-23).

**Counts (52 cases):** denied 12, each with an entitled twin (cross-entity 4: uk-ltd, us-inc, de-gmbh, peo-remote; manager-only 3; employee-only 2; narrow 3); agency 2 in-department + 2 out-of-department with twins; claimed-identity 4; partial 3; same-question 3 sets × 3 personas; controls 1 row × 2 personas; cut-row cases 2 rows × 2 personas.

Case fields: `persona`, `question`, `target_docs`, `evidence`, `intent`, `twin` (denied cases and their twins), `entitled_targets` and `outcome` (computed, empty here), `validity`, `review`.

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
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-002 — twin of P-001 · cross-entity (uk-ltd)
- persona: manager
- question: Is there a cycle-to-work scheme in the UK, and how much can I spend on a bike through it?
- target_docs: total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md
- evidence: as P-001
- intent: allowed
- twin: P-001
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-003 — denied · cross-entity (de-gmbh)
- persona: us-ic
- question: Will GitLab pay for computer glasses for team members in Germany, and up to what amount?
- target_docs: entity/gmbh-germany.md
- evidence: entity/gmbh-germany.md § "Eye Exam and Glasses Reimbursement" L43–60 (glasses needed solely for screen use; reimbursement up to €150 for basic frames and lenses)
- intent: denied
- twin: P-004
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21
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
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21
- note: `admin` is the only fixture persona entitled to `entity:de-gmbh`.

### P-013 — denied · cross-entity (us-inc)
- persona: manager
- question: What is the company match on the US 401(k)?
- target_docs: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md
- evidence: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md § "401(k) Plan with Company Match" L365–370 (50% of contributions on the first 6% of earnings, up to $1,500 a year; immediate eligibility and vesting)
- intent: denied
- twin: P-014
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-014 — twin of P-013 · cross-entity (us-inc)
- persona: us-ic
- question: What is the company match on the US 401(k)?
- target_docs: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md
- evidence: as P-013
- intent: allowed
- twin: P-013
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-023 — denied · cross-entity (peo-remote)
- persona: us-ic
- question: What meal and grocery benefits do people in Brazil get?
- target_docs: total-rewards/benefits/general-and-entity-benefits/remote-com.md
- evidence: total-rewards/benefits/general-and-entity-benefits/remote-com.md § "Brazil 🇧🇷" L68–83 (monthly meal voucher on the VR card for days worked; grocery card for monthly gross salary of 6,189.94 BRL or less)
- intent: denied
- twin: P-024
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-024 — twin of P-023 · cross-entity (peo-remote)
- persona: admin
- question: What meal and grocery benefits do people in Brazil get?
- target_docs: total-rewards/benefits/general-and-entity-benefits/remote-com.md
- evidence: as P-023
- intent: allowed
- twin: P-023
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

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
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-026 — twin of P-025 · manager-only
- persona: manager
- question: What's the merit budget for this year's annual compensation review, and is it the same in every country?
- target_docs: total-rewards/compensation/compensation-review-cycle/_index.md
- evidence: as P-025
- intent: allowed
- twin: P-025
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-027 — denied · manager-only
- persona: contractor
- question: What should a manager have ready before telling a team member about their pay increase?
- target_docs: leadership/compensation-review-conversations.md
- evidence: leadership/compensation-review-conversations.md § "Compensation Communication Recommendations" L23–36 (communicate face-to-face over Zoom; prepare hire date, current compensation, date of last adjustment, performance and growth potential factors, % and # increase from the Total Compensation Statement)
- intent: denied
- twin: P-028
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, edited (question reworded: it implied a manager role the persona lacks), 2026-10-21

### P-028 — twin of P-027 · manager-only
- persona: manager
- question: What should a manager have ready before telling a team member about their pay increase?
- target_docs: leadership/compensation-review-conversations.md
- evidence: as P-027
- intent: allowed
- twin: P-027
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, edited (question reworded: it implied a manager role the persona lacks), 2026-10-21

### P-029 — denied · manager-only
- persona: us-ic
- question: What guidance is there for a new manager who now leads people who used to be their peers?
- target_docs: people-group/learning-and-development/manager-development/_index.md
- evidence: people-group/learning-and-development/manager-development/_index.md § "Navigating the complexity of managing your former peers" L28–36 (be inclusive and communicate; make a few small decisions early and defer bigger ones; meet the team and share your management style; build relationships with your new leader)
- intent: denied
- twin: P-030
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, edited (question reworded: it implied a manager role the persona lacks), 2026-10-21
- note: validity risk: open leadership pages cover similar ground, so the target may fall outside admin's top 20.

### P-030 — twin of P-029 · manager-only
- persona: manager
- question: What guidance is there for a new manager who now leads people who used to be their peers?
- target_docs: people-group/learning-and-development/manager-development/_index.md
- evidence: as P-029
- intent: allowed
- twin: P-029
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, edited (question reworded: it implied a manager role the persona lacks), 2026-10-21

## 3. Denied, employee-only (with entitled twins)

### P-035 — denied · employee-only
- persona: contractor
- question: What market percentile does GitLab aim for when it sets pay ranges?
- target_docs: total-rewards/compensation/_index.md
- evidence: total-rewards/compensation/_index.md § "Market Data Segmentation" L148–156 (most roles target the 50th percentile, critical technical roles the 75th)
- intent: denied
- twin: P-036
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-036 — twin of P-035 · employee-only
- persona: us-ic
- question: What market percentile does GitLab aim for when it sets pay ranges?
- target_docs: total-rewards/compensation/_index.md
- evidence: as P-035
- intent: allowed
- twin: P-035
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-037 — denied · employee-only
- persona: contractor
- question: If I'm on a performance improvement plan, can I still apply for an internal transfer?
- target_docs: leadership/underperformance.md
- evidence: leadership/underperformance.md § "Internal Applications and Transfers during underperformance remediation" L119–121 (generally not eligible during remediation; other roles may be considered only if the underperformance is purely a skills mismatch)
- intent: denied
- twin: P-038
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-038 — twin of P-037 · employee-only
- persona: us-ic
- question: If I'm on a performance improvement plan, can I still apply for an internal transfer?
- target_docs: leadership/underperformance.md
- evidence: as P-037
- intent: allowed
- twin: P-037
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

## 4. Denied, narrow persona on open pages (with entitled twins)

`narrow` (a temporary service provider, group `new-contractor`) sees only the onboarding and contractor pages. These are common new-contractor questions answered on open pages outside that list. Twins are asked by `us-ic`.

### P-041 — denied · narrow
- persona: narrow
- question: Can I plug a USB stick into my work laptop?
- target_docs: people-group/acceptable-use-policy.md
- evidence: people-group/acceptable-use-policy.md § "Use of External Media on Company Assets" L149–151 (removable and external storage on company-managed devices is not allowed and blocked by default; an exception request can be opened for a business need)
- intent: denied
- twin: P-042
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-042 — twin of P-041 · narrow
- persona: us-ic
- question: Can I plug a USB stick into my work laptop?
- target_docs: people-group/acceptable-use-policy.md
- evidence: as P-041
- intent: allowed
- twin: P-041
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-043 — denied · narrow
- persona: narrow
- question: I got an email that looks like phishing. How do I report it?
- target_docs: security/security-assurance/governance/phishing.md
- evidence: security/security-assurance/governance/phishing.md § "What to do if you suspect an email is a phishing attack" L181–188 (use the PhishArm button in Gmail; from other clients forward it to `phishing@gitlab.com`)
- intent: denied
- twin: P-044
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-044 — twin of P-043 · narrow
- persona: us-ic
- question: I got an email that looks like phishing. How do I report it?
- target_docs: security/security-assurance/governance/phishing.md
- evidence: as P-043
- intent: allowed
- twin: P-043
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-045 — denied · narrow
- persona: narrow
- question: What are the password rules here? Minimum length, and do passwords expire?
- target_docs: security/policies_and_standards/password-standard.md
- evidence: security/policies_and_standards/password-standard.md § "Password Requirements" L34–42 (minimum 12 characters, no special characters required, no reuse, no expiration, MFA whenever possible; generate and store in 1Password)
- intent: denied
- twin: P-046
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-046 — twin of P-045 · narrow
- persona: us-ic
- question: What are the password rules here? Minimum length, and do passwords expire?
- target_docs: security/policies_and_standards/password-standard.md
- evidence: as P-045
- intent: allowed
- twin: P-045
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

## 5. Agency contractor

`agency` (groups `new-contractor`, `agency:engineering`) sees the engineering subtree plus the onboarding and contractor pages. In-department cases target engineering pages (allowed, no twin). Out-of-department cases target open pages outside engineering and the onboarding pages (denied, twinned with `us-ic`).

### P-057 — agency · in-department
- persona: agency
- question: What should I do with merge requests I'm reviewing before I go on PTO?
- target_docs: engineering/workflow/code-review.md
- evidence: engineering/workflow/code-review.md § "Managing Review Assignments Before PTO" L26–36 (check assigned reviews on your last day; leave your PTO dates on the MR or reassign it; tell the author if you can't finish)
- intent: allowed
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-058 — agency · in-department
- persona: agency
- question: How big is the GitLab.com error budget, and over what period is it measured?
- target_docs: engineering/error-budgets/_index.md
- evidence: engineering/error-budgets/_index.md § "Budget allocation" L118–124 (99.95% availability target, 20 minutes of allowed unavailability per 28-day period)
- intent: allowed
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-059 — denied · agency out-of-department
- persona: agency
- question: How long do I need to have been here before I can ask for 360 feedback?
- target_docs: people-group/360-feedback.md
- evidence: people-group/360-feedback.md § "Eligibility and Timing" L96–98 (team members with at least 6 months of tenure; typically timed before mid-year and end-of-year check-ins)
- intent: denied
- twin: P-060
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-060 — twin of P-059 · agency out-of-department
- persona: us-ic
- question: How long do I need to have been here before I can ask for 360 feedback?
- target_docs: people-group/360-feedback.md
- evidence: as P-059
- intent: allowed
- twin: P-059
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-061 — denied · agency out-of-department
- persona: agency
- question: Which Slack channel should I use for questions about Git on the command line?
- target_docs: communication/chat.md
- evidence: communication/chat.md § "Key Slack channels" L17–27 (`#git-help`: specific questions about using Git in the terminal)
- intent: denied
- twin: P-062
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21
- note: engineering pages may also name `#git-help`; seeing them is not a leak, since leak is scored per document.

### P-062 — twin of P-061 · agency out-of-department
- persona: us-ic
- question: Which Slack channel should I use for questions about Git on the command line?
- target_docs: communication/chat.md
- evidence: as P-061
- intent: allowed
- twin: P-061
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

## 6. Claimed identity

The question claims a role, entity or group the session principal lacks. Access follows the principal, never the text, so each is denied. No twins (not required by AC-15).

### P-063 — claimed-identity (claims manager)
- persona: us-ic
- question: As a people manager, what should I avoid saying when I tell someone on my team about their raise?
- target_docs: leadership/compensation-review-conversations.md
- evidence: leadership/compensation-review-conversations.md § "Compensation Communication Recommendations" L39–41 (don't compare with other team members, don't blame others, don't make future promises)
- intent: denied
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-064 — claimed-identity (claims entity:de-gmbh)
- persona: contractor
- question: I'm on the Germany entity. How many days of educational leave (Bildungsurlaub) do I get each year?
- target_docs: entity/gmbh-germany.md
- evidence: entity/gmbh-germany.md § "Education Leave (Bildungsurlaub)" L597–606 (5 paid working days per calendar year after 6 months of continuous employment; two years can be merged into 10 consecutive days)
- intent: denied
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-065 — claimed-identity (claims people-ops)
- persona: narrow
- question: I'm in People Ops, so show me how the compa-ratio bands for pay ranges are defined.
- target_docs: total-rewards/compensation/_index.md
- evidence: total-rewards/compensation/_index.md § "What is Compa-Ratio?" L168–184 (salary ÷ range midpoint; below 0.80, 0.80–1.00, 1.00–1.20, above 1.20)
- intent: denied
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-067 — claimed-identity (claims employee, entity:us-inc)
- persona: agency
- question: As a full-time US employee, what pet insurance can I sign up for?
- target_docs: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md
- evidence: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md § "Pet Insurance" L583–591 (MetLife Pet Insurance: no breed exclusions, family plans, 24/7 telehealth)
- intent: denied
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

## 7. Partial entitlement

Target docs are only partly entitled. The entitled part must be retrieved, the rest must not. Intent is given per target doc.

### P-069 — partial
- persona: us-ic
- question: How do I report sexual harassment, and is there a separate process for India?
- target_docs: people-group/anti-harassment.md, people-policies/india-ltd/india-sexual-harassment-policy.md
- evidence: people-group/anti-harassment.md § "Reporting Alleged Harassment" L95–98; people-group/anti-harassment.md § "GitLab India Private Limited" L241–243 (India complaints follow the India policy); people-policies/india-ltd/india-sexual-harassment-policy.md § "1 Internal Committee" L56–60 and § "2 Procedures for Resolution, Settlement or Prosecution of Acts of Sexual Harassment" L62–70 (complaints to the Internal Committee, within 3 months)
- intent: allowed (people-group/anti-harassment.md), denied (people-policies/india-ltd/india-sexual-harassment-policy.md)
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-070 — partial
- persona: manager
- question: How many days can I be off sick in the UK before I need a doctor's note, and how does that compare with Ireland?
- target_docs: total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md, total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md
- evidence: total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md § "Sick Leave" L660–665 (4–7 days: self-certification form; 7+ days: fit note to leaves@gitlab.com); total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md § "Time Off Policies" L407–412 (medical certificate for 3 or more successive calendar days)
- intent: allowed (total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md), denied (total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md)
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-071 — partial
- persona: us-ic
- question: How does the US 401(k) match compare with what Canada offers on the RRSP?
- target_docs: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md, total-rewards/benefits/general-and-entity-benefits/canada-corp-benefits.md
- evidence: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md § "401(k) Plan with Company Match" L365–370 (50% of contributions on the first 6% of earnings, up to $1,500 a year); total-rewards/benefits/general-and-entity-benefits/canada-corp-benefits.md § "Registered Retirement Savings Plan (RRSP)" L64–66 (Canada Life group RRSP, employer match up to 3% of base salary, maximum $2,500 CAD a year)
- intent: allowed (total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md), denied (total-rewards/benefits/general-and-entity-benefits/canada-corp-benefits.md)
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

## 8. Same question across personas

Each question is asked by at least three personas whose groups differ. Ids within a set share the question verbatim.

### P-072 — same-question S-1
- persona: us-ic
- question: Can I see my own compensation range in Workday?
- target_docs: total-rewards/compensation/_index.md
- evidence: total-rewards/compensation/_index.md § "Viewing Compensation Ranges" L186–188 (as of May 1, 2026, all team members can see their compensation range in Workday)
- intent: allowed
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-073 — same-question S-1
- persona: contractor
- question: Can I see my own compensation range in Workday?
- target_docs: total-rewards/compensation/_index.md
- evidence: as P-072
- intent: denied
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-074 — same-question S-1
- persona: narrow
- question: Can I see my own compensation range in Workday?
- target_docs: total-rewards/compensation/_index.md
- evidence: as P-072
- intent: denied
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-075 — same-question S-2
- persona: manager
- question: How does the UK pension work? Is enrollment automatic?
- target_docs: total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md
- evidence: total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md § "Pension Scheme" L235–246 (Scottish Widows Group Personal Pension Plan; automatic enrollment if you earn over £10,000 a year, are 22 or over and under State Pension Age)
- intent: allowed
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-076 — same-question S-2
- persona: us-ic
- question: How does the UK pension work? Is enrollment automatic?
- target_docs: total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md
- evidence: as P-075
- intent: denied
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-077 — same-question S-2
- persona: contractor
- question: How does the UK pension work? Is enrollment automatic?
- target_docs: total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md
- evidence: as P-075
- intent: denied
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-084 — same-question S-5
- persona: agency
- question: How do I become a maintainer on a GitLab project?
- target_docs: engineering/workflow/code-review.md
- evidence: engineering/workflow/code-review.md § "How to become a project maintainer" L67–71 (be a contributor first, then a reviewer in the trainee maintainer process); engineering/workflow/code-review.md § "Pre-requisites for Maintainership" L87–92 (the nominating author reviews recent justifications and asks at least two maintainers privately for feedback)
- intent: allowed
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-085 — same-question S-5
- persona: narrow
- question: How do I become a maintainer on a GitLab project?
- target_docs: engineering/workflow/code-review.md
- evidence: as P-084
- intent: denied
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

### P-086 — same-question S-5
- persona: contractor
- question: How do I become a maintainer on a GitLab project?
- target_docs: engineering/workflow/code-review.md
- evidence: as P-084
- intent: allowed
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21

## 9. Controls on v1.2 rows with restricted expected docs

Each row's question verbatim, its `expected_docs` as targets, and its facts (eval-set-v1.md, v1.2) for authorized recall. One entitled and one denied persona per row; intent is per target doc because most rows mix open and restricted docs. Rows 15, 33, 39, 61 and 109 are cut from v1.2 but keep their facts.

### P-087 — control (row 5)
- persona: admin
- question: I'm in Germany and off sick — how many days can I take before I need a doctor's note, and is it different in other countries?
- target_docs: entity/gmbh-germany.md, people-group/time-off-and-absence/time-off-types.md
- evidence: row 5 facts F1–F9
- intent: allowed (both)
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21
- note: `admin` is the only fixture persona entitled to `entity:de-gmbh`.

### P-088 — control (row 5)
- persona: us-ic
- question: I'm in Germany and off sick — how many days can I take before I need a doctor's note, and is it different in other countries?
- target_docs: entity/gmbh-germany.md, people-group/time-off-and-absence/time-off-types.md
- evidence: row 5 facts F1–F9
- intent: denied (entity/gmbh-germany.md), allowed (people-group/time-off-and-absence/time-off-types.md)
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21
- note: the question claims Germany; `us-ic` is on `us-inc`, so the claim must not widen access.

### P-093 — cut-row targets (row 33)
- persona: manager
- question: Does the comp review process differ between job families? Asking as a manager prepping for it.
- target_docs: total-rewards/compensation/compensation-review-cycle/_index.md, total-rewards/compensation/_index.md
- evidence: row 33 facts F1–F5
- intent: allowed (both)
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21
- note: the question states the manager role; here the principal really is a manager.

### P-094 — cut-row targets (row 33)
- persona: contractor
- question: Does the comp review process differ between job families? Asking as a manager prepping for it.
- target_docs: total-rewards/compensation/compensation-review-cycle/_index.md, total-rewards/compensation/_index.md
- evidence: row 33 facts F1–F5
- intent: denied (both)
- entitled_targets:
- outcome:
- validity: valid (all targets in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21)
- review: agent, accept, 2026-10-21
- note: the question claims the manager role; `contractor` is not in `manager` or `employee`.

### P-097 — cut-row targets (row 61)
- persona: us-ic
- question: What are the eligibility criteria for a sabbatical or leave of absence?
- target_docs: people-policies/leave-of-absence/_index.md, people-policies/leave-of-absence/us.md, people-group/time-off-and-absence/leave-types.md, people-group/time-off-and-absence/time-off-types.md, total-rewards/benefits/general-and-entity-benefits/global-expansion.md
- evidence: row 61 facts F1–F6
- intent: allowed (all except total-rewards/benefits/general-and-entity-benefits/global-expansion.md), denied (total-rewards/benefits/general-and-entity-benefits/global-expansion.md)
- entitled_targets:
- outcome:
- validity: invalid (time-off-types.md and global-expansion.md not in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21; valid under 3-small)
- review: agent, accept, 2026-10-21
- note: entitled to the US FMLA/CFRA facts (F3, F4); F1 (UAE sabbatical) is on a PEO page no non-admin persona sees.

### P-098 — cut-row targets (row 61)
- persona: manager
- question: What are the eligibility criteria for a sabbatical or leave of absence?
- target_docs: people-policies/leave-of-absence/_index.md, people-policies/leave-of-absence/us.md, people-group/time-off-and-absence/leave-types.md, people-group/time-off-and-absence/time-off-types.md, total-rewards/benefits/general-and-entity-benefits/global-expansion.md
- evidence: row 61 facts F1–F6
- intent: denied (people-policies/leave-of-absence/us.md, total-rewards/benefits/general-and-entity-benefits/global-expansion.md), allowed (the other three)
- entitled_targets:
- outcome:
- validity: invalid (time-off-types.md and global-expansion.md not in admin's top 20, fixed-512-64, 3-large@1536, 2026-10-21; valid under 3-small)
- review: agent, accept, 2026-10-21

