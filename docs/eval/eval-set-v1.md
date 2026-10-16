# Eval set v1.1 (2026-10-16)

Status: **v1.1**, 52 live rows: 33 answerable / 19 out-of-corpus (63 / 37).
By D1: lookup 9, synthesis 8, contradiction 8, recency 8, ooc-in-scope 10, ooc-off-topic 9.
Built from the 76 quality rows of [2026-10-14-candidates-UNVERIFIED.md](2026-10-14-candidates-UNVERIFIED.md);
the parked permission cases are out of scope. Question text is verbatim and row numbers are the original
ones. Cut rows stay in section 5 with the reason. Changes: [CHANGELOG.md](CHANGELOG.md).

- **Reference provenance (`ref_source`):** drafted by Claude (never the model under test) from the pinned corpus only.
  - `llm-draft, reviewed` (26): the owner checked the trap verdict or the facts against the cited excerpts and approved each change (rows 8, 10, 11, 13, 26, 32, 44, 46, 47, 48, 49, 50, 51, 52, 53, 55, 58, 59, 65, 87, 89, 96, 99, 100, 111, 113).
  - `llm-draft, auto-reviewed` (26): a separate Claude review against the cited excerpts and the [sweep](sweep-2026-10-16.md), with its fixes applied on the owner's standing approval (2026-10-16); the owner did not read these excerpts (rows 5, 9, 14, 16, 17, 22, 23, 34, 35, 38, 60, 63, 68, 69, 70, 71, 72, 88, 92, 93, 102, 110, 112, 115, 116, 117).
  - `human`: rewritten by the owner (none in v1.1).
- **Source:** pinned corpus SHA `5273b21a9a2ebc01055526f4d4ce245ae7d1a7d7`, files under `content/handbook` only. Paths below are relative to `content/handbook/`.
- **Method:** fresh session, `rg`/`sed` over the pin, never model memory. Rows were split across three parallel subagents by topic, each given the owner's rules verbatim. Rows 109, 110 and 113 were checked first and decided by the owner. Every `path § "heading" L<a>–<b>` citation was then machine-checked against the pin: the file exists, the range is inside the file, and the heading is the nearest heading above the range (or inside it). The facts were not machine-checked; key names, figures and trap excerpts were spot-checked by hand.
- **Facts:** each `F<n>` is one binary check (k-of-n). `[variant: X]` marks one branch of a conditional answer. `[required]` facts are the minimum a correct answer must contain; `[optional]` facts are credit only. Rows without markers use the minimum stated in their notes.
- **`recency_basis`** (contradiction and recency rows, added from 2026-10-16): `in-page` when pinned text signals which statement is current, `history-only` when only git history does. The model under test never sees git history, so `history-only` facts are reported separately.
- **Out-of-corpus expected strings:** in-scope → "I don't know based on the provided handbook excerpts."; off-topic → "Sorry, I don't know how to answer that."
- **Currency evidence:** `git log -1 --format='%h %ad' --date=short -- <path>` on each conflicting page. History is used only to judge which pinned statement is current, never as a source of facts. Caveat: three bulk commits touched hundreds of pages (`968e3521af` 2026-09-24 Customer Success → Customer Experience rename, 565 files; `bee431b547` 2026-09-13 HelpLab → Compass rename; `4469685d7b` 2026-08-27 marketing link cleanup). A page's last-commit date therefore often says nothing about the sentence in question. Rows note where in-page wording was used instead.

## Owner decisions applied (2026-10-15)

Each affected row carries a `decision:` line, or a "Recoded" line for recoded rows.

- **109:** recoded from ooc-in-scope to answerable (synthesis, several-pages, conditional, no trap).
- **113:** stays ooc-in-scope with the exact string; its distractors are noted on the row.
- **T6 (44, 54, 55):** pinned excerpts with both names are quoted, and currency comes from git. 55: F1 checks the name only.
- **9, 56:** D1 → lookup, trap → none (T7 isn't in the pin); distractor notes kept.
- **47:** → ooc-in-scope (France's statutory minimum isn't in the pin); searches and distractors kept.
- **46, 58, 99, 100, 50:** D1 kept; trap note rewritten to the conflict actually in the pin.
- **10, 52, 23:** accepted as drafted.
- **15, 61, 64, 65:** recoded to answerable (15 lookup, 61 synthesis, 64 lookup, 65 lookup). Row 61 also gained a UAE national-service sabbatical fact found while recoding.
- **14, 62, 63, 112:** stay ooc-in-scope; nearby excerpts added as distractor notes.
- **68:** stays ooc-off-topic.
- **45, 101, 108:** cut (section 5).

- **Final cut to 54:** 54, 56, 1, 15, 28, 29, 64, 86, 91, 95, 103, 6, 33, 37, 39, 61, 97, 98, 109 moved to section 5, each with a `cut:` line.
- **87:** kept as answerable synthesis. F1 (no single company-wide list) and F2 are required; the per-category variants are optional.
- **89, 93:** kept. Neither question asks for per-country values; the per-country notice-period and probation tables are Hugo shortcodes whose data isn't in `content/handbook`.

## 1. Trap rows (T1–T8)

### Row 11 — recency · process · trap T1
Q: new starter here - how do i go about buying my laptop and monitor? what are the steps
expected_docs: eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md, finance/expenses.md
citation: "New Hire Laptop Ordering Process" (eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md); "Equipment" (finance/expenses.md); "New Hires- 1,500 USD (or equivalent local currency) Guidelines" (finance/expenses.md)
facts:
- F1. You don't buy the laptop. GitLab issues it: fill in the laptop request form linked in the Candidate Experience Specialist's welcome email, as soon as possible. — eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md § "New Hire Laptop Ordering Process" L24–24
- F2. The laptop is expected to arrive the week before your start date. If it hasn't arrived near your start date, email it-help@gitlab.com (cc people_operations@gitlab.com). — eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md § "New Hire Laptop Ordering Process" L26–26; people-group/general-onboarding/tanewki-tips.md § "Equipment" L74–74
- F3. [variant: country without vendor delivery, e.g. Brazil or Ukraine] Self-procure the laptop with IT approval (funds can be advanced). Costs are not covered without approval. — eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md § "Shipping Locations" L11–11 and § "Self procurement" L99–101
- F4. The monitor comes from the new-hire home office stipend of 1,500 USD (or local equivalent) for your first year. — finance/expenses.md § "Equipment" L417–417
- F5. Buy the monitor with your own funds, then submit a claim in Navan with Expense Type "Work From Home – New Hire Stipend". — finance/expenses.md § "New Hires- 1,500 USD (or equivalent local currency) Guidelines" L429–429
- F6. Monitors and monitor stands are on the approved WFH equipment list. Items outside the list need pre-approval via Compass (`Expenses -> Home Office Equipment`). — finance/expenses.md § "Computer Equipment/Other" L448–448; § "Equipment" L422–422
conflict:
- A: "Purchase the items you need using your own funds and submit a claim in Navan for reimbursement. Select the Expense Type: Work From Home – New Hire Stipend." — finance/expenses.md § "New Hires- 1,500 USD (or equivalent local currency) Guidelines" L429–429 (same text at § "Equipment" L417); currency evidence: bee431b547 2026-09-13 (text introduced by c72b6af5ef 2026-08-31 "Update Equipment New hire Stipend information", which replaced the virtual-card wording)
- B: "We recommend waiting until your start date, as you'll receive a virtual card with funds for equipment purchases." / "All new team members receive $1,500 USD (or local equivalent) via a [virtual card](...) for office equipment purchases." — people-group/general-onboarding/tanewki-tips.md § "Equipment and Expenses" L126–126, L142–142; currency evidence: bee431b547 2026-09-13 (rename-only touch; the virtual-card sentence dates from 0a32929759 2026-04-22). Also "These virtual cards within Navan ... are used solely for providing new Team Members with a $1,500 USD ... stipend" — finance/expenses.md § "6. Purchase Cards" L753–753 (stale in the same file)
- current: A because c72b6af5ef (2026-08-31) explicitly replaced the virtual-card process with own-funds-plus-reimbursement in the expense policy. B is stale text left on the onboarding FAQ and in §6.
flag: trap T1. The conflict is confirmed in the pin.
ref_source: llm-draft, reviewed
notes: A correct answer says to pay with your own funds and claim in Navan, not to use a virtual card. Navan access arrives during your first week (tanewki L134). Distractors: business-technology/enterprise-applications/guides/coupa-virtual-cards (supplier virtual cards) and laptop-management "Laptop Refreshes" (existing staff).

### Row 49 — contradiction · single-fact · trap T1
Q: Is the manager responsible for ordering equipment for a new team member?
expected_docs: eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md, finance/expenses.md
citation: "New Hire Laptop Ordering Process" (eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md); "Equipment" (finance/expenses.md)
facts:
- F1. No. The new hire orders their own laptop through the request form linked in the Candidate Experience Specialist's welcome email. — eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md § "New Hire Laptop Ordering Process" L24–24
- F2. The hiring manager (or hiring team) can check the status and contents of the new hire's laptop order in the IT Equipment Order Process project. — eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md § "New Hire Laptop Ordering Process" L30–30
- F3. If the laptop isn't available by the start date, the hiring manager or hiring team must request a security exception so the new hire can temporarily use a personal macOS or Linux laptop. — eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md § "New Hire Laptop Ordering Process" L38–38
- F4. The new hire buys home-office equipment themselves with their own funds and claims it against the 1,500 USD new-hire stipend in Navan. — finance/expenses.md § "Equipment" L417–417
conflict:
- A: "Purchase the items you need using your own funds and submit a claim in Navan for reimbursement." — finance/expenses.md § "New Hires- 1,500 USD (or equivalent local currency) Guidelines" L429–429; currency evidence: bee431b547 2026-09-13 (introduced c72b6af5ef 2026-08-31)
- B: "All new team members receive $1,500 USD (or local equivalent) via a [virtual card](...) for office equipment purchases." — people-group/general-onboarding/tanewki-tips.md § "Equipment and Expenses" L142–142; currency evidence: bee431b547 2026-09-13 (rename-only; sentence dates from 0a32929759 2026-04-22). Also finance/expenses.md § "6. Purchase Cards" L753–753.
- current: A because c72b6af5ef replaced the virtual-card process in the expense policy on 2026-08-31.
flag: trap T1. The conflict is confirmed in the pin. Note that the question's actual answer (who orders: the new hire, not the manager) is not itself contested. T1 only affects how the equipment is paid for.
ref_source: llm-draft, reviewed
notes: Strong distractor: engineering/careers/training/em-role/work_of_a_manager.md L67 lists "getting new team members their laptops" as manager administrivia. That is an example matrix, not policy. people-group/general-onboarding/tanewki-tips.md L95 says "work with your manager and IT for these standard items" (ergonomic equipment), which a model may over-read as manager responsibility. The welcome email is cc'd to the hiring manager (hiring/talent-acquisition-framework/coordinator.md L397).

### Row 51 — recency · single-fact · trap T1
Q: What payment method should new team members use for equipment purchases?
expected_docs: finance/expenses.md
citation: "Equipment" (finance/expenses.md); "New Hires- 1,500 USD (or equivalent local currency) Guidelines" (finance/expenses.md)
facts:
- F1. New team members pay with their own funds (personal payment method). — finance/expenses.md § "New Hires- 1,500 USD (or equivalent local currency) Guidelines" L429–429
- F2. They then submit a reimbursement claim in Navan with Expense Type "Work From Home – New Hire Stipend". — finance/expenses.md § "Equipment" L417–417
- F3. The stipend is 1,500 USD (or local equivalent) toward a home office in the first year. — finance/expenses.md § "Equipment" L417–417
- F4. (Optional, existing staff) The yearly 500 USD refresh can't use the Navan Virtual Card either; use your own payment method. — finance/expenses.md § "Existing Team Members- 500 USD (or equivalent local currency) Refresh Guidelines" L435–435
conflict:
- A: "As you onboard and start your GitLab journey, new hires will receive a 1,500 USD (or equivalent local currency) stipend ... Purchase the items you need using your own funds and submit a claim in Navan for reimbursement." — finance/expenses.md § "Equipment" L417–417; currency evidence: bee431b547 2026-09-13 (introduced c72b6af5ef 2026-08-31 "Update Equipment New hire Stipend information")
- B: "We recommend waiting until your start date, as you'll receive a virtual card with funds for equipment purchases." — people-group/general-onboarding/tanewki-tips.md § "Equipment and Expenses" L126–126; and "These virtual cards within Navan are only utilized by the AP team, and they are used solely for providing new Team Members with a $1,500 USD (or local currency equivalent) stipend for their home office set up." — finance/expenses.md § "6. Purchase Cards" L753–753; currency evidence: people-group/general-onboarding/tanewki-tips.md bee431b547 2026-09-13 (sentence from 0a32929759 2026-04-22); finance/expenses.md §6 sentence last changed a47f8fb619 2026-05-14
- current: A because the 2026-08-31 commit removed the virtual-card instructions from §Equipment and replaced them with own-funds-plus-reimbursement. B survives as stale text.
flag: trap T1. The conflict is confirmed in the pin, and it appears both across pages and within finance/expenses.md itself (§Equipment vs §6 Purchase Cards).
ref_source: llm-draft, reviewed
notes: An answer that says "virtual card" is wrong under the recency rule. Distractors: Coupa/Zip virtual-card guides for supplier payments and finance/accounts-payable/corp-credit-cards.md.

### Row 52 — recency · single-fact · trap T2
Q: Name of the current tool for submitting access requests?
expected_docs: eta/corporate-it/compass/compass-guide/_index.md, eta/corporate-it/end-user-services/access-requests/_index.md
citation: "What you gain" (eta/corporate-it/compass/compass-guide/_index.md); "Requesting Access in Lumos" (eta/corporate-it/end-user-services/access-requests/_index.md)
facts:
- F1. Compass (built on the third-party Serval platform) is described as the one place to submit and track access requests, replacing separate tools. — eta/corporate-it/compass/compass-guide/_index.md § "What you gain" L41–41; § "What is Compass?" L14–14
- F2. The access-requests page says most access requests are now made through the Lumos App Store. — eta/corporate-it/end-user-services/access-requests/_index.md § "Requesting Access in Lumos" L17–17
- F3. Apps not yet in Lumos still use GitLab access-request issue templates. — eta/corporate-it/end-user-services/access-requests/_index.md § "Approve a request" L39–39
conflict:
- A: "One place for access requests | Submit and track access requests directly through Compass instead of separate tools." — eta/corporate-it/compass/compass-guide/_index.md § "What you gain" L41–41; currency evidence: bee431b547 2026-09-13
- B: "Most access requests are now made through the [Lumos App Store](https://app.lumosidentity.com/app_store) rather than by opening an issue." — eta/corporate-it/end-user-services/access-requests/_index.md § "Requesting Access in Lumos" L17–17; currency evidence: 8f22e33fea 2026-07-28
- current: unresolved, leaning A. The Compass statement is newer, but the controlled access-requests page (Lumos) was not updated to match. They may also be complementary (Compass as front door, Lumos as the identity-governance back end; Lumos is described as consolidating access requests in security/corporate/systems/lumos/_index.md L5).
flag: trap T2. The conflict is in the pin. The reference answer needs human adjudication: is "Compass" alone acceptable, or must the answer mention both? Suggest accepting an answer that names Compass and notes Lumos, or names both with the conflict.
decision: owner 2026-10-15 — accepted as drafted.
ref_source: llm-draft, reviewed
notes: The brief's "HelpLab renamed to Compass" has no in-pin text; HelpLab has zero hits. Distractors: issue-template workflow pages (eta/corporate-it/end-user-services/access-requests/access-requests/_index.md) and the Okta FAQ (okta-enduser-faq L209).

### Row 53 — recency · conditional · trap T2
Q: Am I the one who approves access requests for my direct reports?
expected_docs: eta/corporate-it/end-user-services/access-requests/_index.md, security/corporate/systems/lumos/ar/_index.md, eta/corporate-it/end-user-services/access-requests/access-requests/_index.md
citation: "Requesting Access in Lumos" / "Approve a request" (eta/corporate-it/end-user-services/access-requests/_index.md); "Overview" (security/corporate/systems/lumos/ar/_index.md); "Individual or Bulk Access Request" (eta/corporate-it/end-user-services/access-requests/access-requests/_index.md)
facts:
- F1. Yes, as the manager you are an approver. Lumos automatically routes your report's request to you, plus the system owner and any other required approvers. — eta/corporate-it/end-user-services/access-requests/_index.md § "Requesting Access in Lumos" L17–17; security/corporate/systems/lumos/ar/_index.md § "Overview" L9–9
- F2. You are not the only approver. The system owner and others also approve, and Infrastructure-owned systems additionally need `@gitlab-com/gl-infra/managers` approval (~InfrastructureApproved). — security/corporate/systems/lumos/ar/_index.md § "Overview" L9–9; eta/corporate-it/end-user-services/access-requests/access-requests/_index.md § "Individual or Bulk Access Request" L41–41
- F3. [variant: Lumos] Approve, comment on or deny from the Slack/email notification or in Lumos. You can edit which groups the user is added to before approving. — eta/corporate-it/end-user-services/access-requests/_index.md § "Approve a request" L37–37
- F4. [variant: issue-template AR for apps not in Lumos] The manager adds `AR-Approval::Manager Approved` and `ReadyForProvisioning` labels, then assigns the issue to the system provisioner. — eta/corporate-it/end-user-services/access-requests/access-requests/_index.md § "Individual or Bulk Access Request" L54–57
- F5. [variant: bulk request across several managers in one department] Approval can come from the highest-level manager (Director, VP or Executive). — eta/corporate-it/end-user-services/access-requests/access-requests/_index.md § "Individual or Bulk Access Request" L52–52
- F6. [variant: Compass] Compass can grant time-bound app access automatically "based on your team's policy", without a stated manager step. — eta/corporate-it/compass/compass-guide/_index.md § "What Compass can resolve automatically" L109–109
conflict:
- A: "App access request | Grants time-bound access via Okta SSO or direct provisioning, based on your team's policy." — eta/corporate-it/compass/compass-guide/_index.md § "What Compass can resolve automatically" L109–109; currency evidence: bee431b547 2026-09-13
- B: "Lumos automatically routes the request to your manager, the system owner, and any other required approvers" — eta/corporate-it/end-user-services/access-requests/_index.md § "Requesting Access in Lumos" L17–17; currency evidence: 8f22e33fea 2026-07-28 (also security/corporate/systems/lumos/ar/_index.md, edd8c6568d 2026-04-09)
- current: unresolved. Every pin page that describes approval says the manager approves. The newer Compass page doesn't contradict that explicitly; it just doesn't mention approvers.
flag: trap T2. The tool conflict is in the pin, but it doesn't change the core answer (manager approval is required in both the Lumos and issue routes). Consider whether T2 is a good fit for this row.
ref_source: llm-draft, reviewed
notes: Related manager duty: if the baseline-entitlements AR isn't auto-created for a new hire, the manager must create it (eta/corporate-it/end-user-services/access-requests/_index.md L98). Distractors: eta/css/zendesk/api/_index.md L213 (Zendesk-specific manager approval) and engineering/infrastructure-platforms/gitlab-dedicated/_index.md L166 (Dedicated-specific double approval).

### Row 8 — contradiction · single-fact · trap T3
Q: After I submit an expense in the US, how long until the money actually hits my account?
expected_docs: finance/expenses.md, finance/accounting/_index.md
citation: "Legal entities" (finance/expenses.md); "Paying Navan Reports" (finance/accounting/_index.md)
facts:
- F1. GitLab Inc and GitLab Federal expenses are reimbursed via Navan within 7 business days: in-policy expenses after submission, out-of-policy expenses after Accounts Payable approval. — finance/expenses.md § "Legal entities" L698–698
- F2. Your bank account must be set up in Navan for payment to complete. — finance/expenses.md § "Legal entities" L699–699
- F3. Navan batches approved expenses into a single weekly payment paid out on Mondays, covering approvals through the prior Sunday evening. The money should reach your bank on Tuesday or Wednesday. The page says Navan "will be implementing" this. — finance/expenses.md § "Legal entities" L701–701
- F4. The answer should note that the accounting page gives a different figure: 1–4 business days after the report is "final approved". — finance/accounting/_index.md § "Paying Navan Reports" L459–459
conflict:
- A: "Expenses for GitLab Inc, GitLab Federal, ... are reimbursed via Navan within 7 business days for the expenses within policy or after approval by the Accounts Payable team (for out of policy expenses)." — finance/expenses.md § "Legal entities" L698–698; currency evidence: bee431b547 2026-09-13 (this line was last introduced or changed in a47f8fb619 2026-05-14)
- B: "Team members in a US expense policy will be automatically reimbursed through Navan after their report is \"final approved\" within 1-4 business days." — finance/accounting/_index.md § "Paying Navan Reports" L459–459; currency evidence: c2934665d9 2026-03-18
- current: A because finance/expenses.md is the canonical policy page (the accounting page itself says "Please refer to GitLab's Expense Policy", L444) and it was edited more recently (2026-09-13 vs 2026-03-18). Caveat: A's own batched-payment bullet (L701) is written in the future tense, so the exact day is soft.
flag: trap T3. The conflict exists in the pin as described: 7 business days (plus a weekly Monday batch landing Tue/Wed) versus 1–4 business days.
ref_source: llm-draft, reviewed
notes: Grading should accept an answer that gives the 7-business-day figure and the Tue/Wed batch, and ideally notes the 1–4 day statement. An answer that gives only "1–4 business days" relies on the older page. "Final approved" means manager approval plus AP audit (accounting L450). Distractor: "Expense Reimbursement for Terminated Team Members" (L817, "within 1 week").

### Row 32 — synthesis · process · trap T3
Q: walk me through expenses end to end, from submitting a receipt to getting paid
expected_docs: finance/expenses.md, finance/accounting/_index.md
citation: "3. General Guidelines" (finance/expenses.md); "2. Responsibilities" (finance/expenses.md); "Legal entities" (finance/expenses.md); "PEO (Professional Employer Organization/ Employer of Record and not a GitLab entity or Branch)" (finance/expenses.md); "Processing Navan Reports" (finance/accounting/_index.md)
facts:
- F1. Submit expenses in Navan with receipts. Non-US team members need receipts for everything; US team members only for expenses over $50. Receipts must show vendor, date, items and a subtotal/tax breakout. — finance/expenses.md § "3. General Guidelines" L53–53
- F2. The Navan description box is required: what the expense is and why. Blank descriptions are bounced back. — finance/expenses.md § "3. General Guidelines" L58–60
- F3. Submit by the end of the fiscal quarter in which the expense was incurred. Claims over 90 days old need manager approval. — finance/expenses.md § "2. Responsibilities" L26–26; § "3. General Guidelines" L57–57
- F4. If you're missing a receipt, attach a completed Missing Receipt Affidavit as a PDF. — finance/expenses.md § "4.3 Missing Receipt Affidavit" L689–689
- F5. The report is approved by your manager and then audited by Accounts Payable ("final approved"). AP reviews reports that need admin review within 7 working days. — finance/accounting/_index.md § "Processing Navan Reports" L450–450; finance/expenses.md § "2. Responsibilities" L44–44
- F6. [variant: GitLab entity employees, incl. US] Payment comes via Navan within 7 business days, once your bank account is set up in Navan. Navan batches a weekly Monday payout that lands Tue/Wed. — finance/expenses.md § "Legal entities" L698–701
- F7. [variant: PEO / CXC / iiPay contractors] Expenses must be submitted and approved by the 3rd of the month to be included in that month's payroll or payment. iiPay pays by the 22nd. — finance/expenses.md § "PEO (Professional Employer Organization/ Employer of Record and not a GitLab entity or Branch)" L709–709, L729–729, L735–735
- F8. [variant: France and Finland entities] Submit and get approval by the 6th of the month for inclusion in that month's payroll. — finance/expenses.md § "Legal entities" L700–700
conflict:
- A: "... are reimbursed via Navan within 7 business days for the expenses within policy or after approval by the Accounts Payable team (for out of policy expenses)." — finance/expenses.md § "Legal entities" L698–698; currency evidence: bee431b547 2026-09-13
- B: "Team members in a US expense policy will be automatically reimbursed through Navan after their report is \"final approved\" within 1-4 business days." — finance/accounting/_index.md § "Paying Navan Reports" L459–459; currency evidence: c2934665d9 2026-03-18. A third timing statement on the same page: non-US entities are paid in the weekly AP run if final-approved by EOD Tuesday (L466–468).
- current: A because finance/expenses.md is the canonical, more recently edited policy, and the accounting page defers to it (L444).
flag: trap T3. The conflict is confirmed in the pin.
ref_source: llm-draft, reviewed
notes: The long process has many optional details. Core checks are F1, F3, F5 and F6. Distractors: Coupa/Zip procurement guides (supplier payments), finance/accounts-payable/corp-credit-cards.md (physical card), and "Expense Reimbursement for Terminated Team Members" (L817).

### Row 10 — contradiction · list · trap T4
Q: Please list the GitLab company values.
expected_docs: values/_index.md, company/operating-principles.md
citation: "CREDIT" (values/_index.md); "Acknowledging CREDIT" (company/operating-principles.md)
facts:
- F1. Collaboration is a GitLab value. — values/_index.md § "CREDIT" L14–15
- F2. Results (for Customers) is a GitLab value. — values/_index.md § "CREDIT" L14, L16
- F3. Efficiency is a GitLab value. — values/_index.md § "CREDIT" L14, L17
- F4. Diversity, Inclusion & Belonging is a GitLab value. — values/_index.md § "CREDIT" L14, L18
- F5. Iteration is a GitLab value. — values/_index.md § "CREDIT" L14, L19
- F6. Transparency is a GitLab value. — values/_index.md § "CREDIT" L14, L20
- F7. Together the six values spell CREDIT. — values/_index.md § "CREDIT" L21–22
- F8. The newer Operating Principles page says GitLab is moving its focus from CREDIT to three operating principles (Speed with Quality, Ownership Mindset, Customer Outcomes), built on a Culture of Excellence, and that the CREDIT values "remain part of who we are". — company/operating-principles.md § "Acknowledging CREDIT" L77–79; (front matter) L3
conflict:
- A: "GitLab's six core values are [Collaboration], [Results for Customers], [Efficiency], [Diversity, Inclusion & Belonging], [Iteration], and [Transparency], and together they spell the **CREDIT** we give each other by assuming good intent." — values/_index.md § "CREDIT" L14–22; currency evidence: 4469685d7b 2026-08-27 (only a link-path tweak in the "Bias towards asynchronous communication" section; the CREDIT list wasn't touched)
- B: "We aren't retiring CREDIT because those values were wrong. We are choosing to focus on something different for an era that demands a different operating posture. The values CREDIT represented remain part of who we are. They live in the principles above…" — company/operating-principles.md § "Acknowledging CREDIT" L79; currency evidence: 7c0a88b0a2 2026-06-10 ("Add new operating principles page"); in-text `last_updated: "2026-05-15"` (L6), `status: active` (L4). The mission page (L67, 1b7fdfe2d1 2026-05-13) also names the three principles.
- current: unresolved. B is the newer statement of intent and frames CREDIT as being replaced ("aren't retiring CREDIT because…"). But A is still the canonical "GitLab Values" page, has no deprecation notice, and many pages still link to it as current (e.g. sales/_index.md L95 "embodies our CREDIT values"). A correct answer lists the six CREDIT values (A) and says that operating principles now take the lead (B).
flag: T4 trap. The pin really has the conflict. The owner needs to decide whether "company values" should be answered as CREDIT (A) or the three operating principles (B). The draft expects both.
decision: owner 2026-10-15 — accepted as drafted.
ref_source: llm-draft, reviewed
notes: The pin names the value "Results for Customers" on values/_index.md (L16) but "Results" on company/history.md L135 and company/culture/all-remote/onboarding.md L192. Either name should pass. Distractors: the "Operating principles" section on values/_index.md (L896–901), which treats operating principles as sub-behaviours of CREDIT, not a replacement; and ceo/_index.md "My Personal Values" (Integrity, Curious, Results), which are the CEO's personal values, not the company's.

### Row 50 — contradiction · process · trap T4
Q: if i disagree with a decision how does disagree and commit actually work
expected_docs: values/_index.md
citation: "Disagree, commit, and advocate" (values/_index.md); "Escalate to unblock" (values/_index.md)
facts:
- F1. [required] Once a decision is in place, you commit to executing it. Past decisions are open to questioning as long as you act in line with them until they change. — values/_index.md § "Disagree, commit, and advocate" L315
- F2. [optional] Every decision can be changed. — values/_index.md § "Disagree, commit, and advocate" L316–317
- F3. [optional] In a manager-report relationship the report is usually the DRI. The manager may disagree but still commits to the DRI's decision. — values/_index.md § "Disagree, commit, and advocate" L318–319
- F4. [required] Voice your disagreement (dissent) based on facts rather than agreeing just to avoid conflict. — values/_index.md § "Disagree, commit, and advocate" L321–322
- F5. [required] To reopen a decision, show your argument builds on previous conversations and assume best intent. Keep delivering results while the decision stands, and take it to the DRI who can change it. — values/_index.md § "Disagree, commit, and advocate" L324–326
- F6. [optional] If the disagreement blocks progress, agree to escalate to one or both managers. — values/_index.md § "Escalate to unblock" L330
conflict:
- A: "##### Disagree, commit, and advocate {#disagree-and-commit}" — values/_index.md § "Disagree, commit, and advocate" L313; currency evidence: 4469685d7b 2026-08-27 (link-only edit elsewhere on the page)
- B: "Once a DRI has made a decision, team members are asked to [disagree, commit, and disagree](/handbook/values/#disagree-and-commit)." — leadership/making-decisions.md § "Making decisions" L28; currency evidence: 5ab934bec3 2025-12-01. Also "exercise our [disagree, commit, and disagree value]" — product/product-management/_index.md L378 (968e3521af 2026-09-24, bulk rename commit).
- current: A. It's the defining section that B links to (#disagree-and-commit), and values/_index.md was committed more recently than leadership/making-decisions.md. B uses an older name for the same sub-value.
recency_basis: history-only (no pinned page states which name replaced which; no fact checks the name, so the conflict is a distractor, not scored)
trap note (T4): the conflict in the pin is an old vs new name, not CREDIT vs operating principles. "disagree, commit, and disagree" (leadership/making-decisions.md L28; product/product-management/_index.md L378) vs the current values heading "Disagree, commit, and advocate" (values/_index.md L313). company/operating-principles.md does not mention disagree-and-commit.
decision: owner 2026-10-15 — keep D1; trap note rewritten to the conflict actually in the pin.
ref_source: llm-draft, reviewed
decision: owner 2026-10-16 — F1, F4, F5 required; F2, F3, F6 optional; recency_basis history-only; expected docs unchanged (values/_index.md defines the value; other pages only name it).
notes: Other variant names in the pin: "Disagree, Commit, Disagree" (leadership/emotional-intelligence/psychological-safety-short-course.md L76, called an "operating principle"), and "Disagree and commit" (people-group/directly-responsible-individuals.md L88; product/ux/navigation/_index.md L40). Distractor: values/_index.md "Collaboration is not consensus" (L202–208), which is related but doesn't define the process.

### Row 59 — recency · process · trap T4
Q: Explain how a new team member should apply the operating principles to day-to-day decisions.
expected_docs: company/operating-principles.md
citation: "Speed with Quality", "Ownership Mindset", "Customer Outcomes", "Culture of Excellence" (company/operating-principles.md)
facts:
- F1. There are three operating principles, Speed with Quality, Ownership Mindset, and Customer Outcomes, built on a foundation of Culture of Excellence. — company/operating-principles.md (front matter / intro) L3, L10
- F2. Speed with Quality: move fast with discipline. Build, experiment, and fail fast, especially on two-way-door decisions. Automate what an agent can do. Tolerate no unnecessary bureaucracy. — company/operating-principles.md § "Speed with Quality" L18, L24–26
- F3. Ownership Mindset: the people closest to the work make the decisions and own the result. "It is never someone else's problem". Be efficient with budget, people, and time. — company/operating-principles.md § "Ownership Mindset" L35, L40, L43
- F4. Customer Outcomes: judge work by what changes for the customer, not by activity. Be able to explain how your work connects to a customer outcome. — company/operating-principles.md § "Customer Outcomes" L51, L55
- F5. Culture of Excellence: Excellence in Thought, Excellence in Action, Interpersonal Excellence (be a good human, assume good intent). — company/operating-principles.md § "Culture of Excellence" L65–71
conflict:
- A: "Operating principles are behaviors that empower GitLab team members to definitively live out a given value. They clarify what a given core value means and looks like *at GitLab*. Understanding this distinction is critical to thriving at GitLab, particularly for [newer team members]…" — values/_index.md § "Operating principles" L898–900; currency evidence: 4469685d7b 2026-08-27 (unrelated link edit)
- B: "These three principles are built on a foundation of **Culture of Excellence**, which we expect every team member to uphold." … "We aren't retiring CREDIT because those values were wrong. We are choosing to focus on something different…" — company/operating-principles.md L10, § "Acknowledging CREDIT" L79; currency evidence: 7c0a88b0a2 2026-06-10 "Add new operating principles page"; in-text `last_updated: "2026-05-15"`, `status: active`
- current: B. It's a dedicated page added 2026-06-10 that frames CREDIT as the previous framework, and company/mission.md L67 (1b7fdfe2d1 2026-05-13) confirms the three principles. A's section text predates it and defines operating principles as sub-behaviours of CREDIT values.
flag: T4 trap. The pin contains two meanings of "operating principles": the CREDIT sub-behaviours (values page) and the three new principles (operating-principles page). The values page isn't marked deprecated. Owner review: confirm B as the expected answer.
ref_source: llm-draft, reviewed
notes: Supporting detail: leadership/building-trust.md § "How trust connects to our operating principles" L84–92. Distractors: values page operating principles such as "Bias towards asynchronous communication" and "Make two-way door decisions" (values/_index.md L735), which an answer built on A would cite.

### Row 13 — recency · conditional · trap T5
Q: I'm a contractor — do I get any benefits through my contracting entity?
expected_docs: total-rewards/benefits/general-and-entity-benefits/_index.md, people-group/time-off-and-absence/time-off-types.md, people-group/employment-solutions.md
citation: "Contractor Benefits" (total-rewards/benefits/general-and-entity-benefits/_index.md); "Overview" (people-group/time-off-and-absence/time-off-types.md); "Team Members Hired as Contractors via our GitLab Services Inc Entity" (people-group/employment-solutions.md)
facts:
- F1. Contractors get company-wide benefits but not entity-specific benefits. — total-rewards/benefits/general-and-entity-benefits/_index.md § "Contractor Benefits" L426; people-group/time-off-and-absence/time-off-types.md § "Overview" L60
- F2. Contractors are responsible for their own health insurance, social security taxes, and payroll administration. — total-rewards/benefits/general-and-entity-benefits/_index.md § "Contractor Benefits" L426
- F3. Company-wide benefits are available to all GitLab team members worldwide, regardless of location (unless stated otherwise). — total-rewards/benefits/general-and-entity-benefits/_index.md § "How Our Benefits Work" L9
- F4. Contractors aren't eligible for entity-specific public holidays, but GitLab gives them a standard allocation of 12 public holidays. — people-group/time-off-and-absence/time-off-types.md § "Overview" L60
- F5. [rewording: depends on entity?] In locations with no GitLab entity or PEO, team members contract with GitLab Services Inc (GSI), previously IT BV, as independent or C2C contractors. Entity-specific benefits apply only to team members employed through a GitLab entity or a PEO. — people-group/employment-solutions.md § "Team Members Hired as Contractors via our GitLab Services Inc Entity" L69; people-group/time-off-and-absence/time-off-types.md § "Overview" L60; total-rewards/benefits/general-and-entity-benefits/_index.md § "How Our Benefits Work" L11
conflict:
- A: "GitLab IT BV contractors are eligible for company-wide benefits but not entity-specific benefits." — total-rewards/benefits/general-and-entity-benefits/_index.md § "Contractor Benefits" L426; currency evidence: f96a52e199 2026-09-28 ("Removing Finland benefits page"; that commit didn't touch the contractor sentence)
- B: "Contractors of GitLab GSI (previously IT BV) are eligible for general benefits but not entity-specific benefits (including public holidays)." — people-group/time-off-and-absence/time-off-types.md § "Overview" L60; currency evidence: bee431b547 2026-09-13 (bulk HelpLab→Compass rename). Also: "Where we do not have an entity or a PEO, team members contract with our GitLab Services Inc entity as independent or C2C contractors." — people-group/employment-solutions.md L69; currency evidence: 7593cd32dc 2026-04-09
- current: B (GSI). The in-text "(previously IT BV)" marks IT BV as the old name. The git dates don't settle it, because both latest commits were unrelated or bulk edits. Both statements give the same eligibility answer; only the entity name differs.
flag: T5 trap. The pin has the old/new entity name (IT BV vs GSI), but the benefits answer is the same under both. The hypothesis is confirmed as a naming conflict, not a policy conflict.
ref_source: llm-draft, reviewed
notes: Distractors: entity-specific benefit pages (e.g. total-rewards/benefits/general-and-entity-benefits/remote-com.md, inc-benefits-us), which apply only to employees or PEO hires. legal/esg/_index.md L242 mentions team members "who contract with CXC or directly with GitLab IT BV" (a third contracting route the pin doesn't explain). hiring/talent-acquisition-framework/coordinator.md L1212–1216 still issues "IT BV contractor agreements".

### Row 48 — contradiction · conditional · trap T5
Q: I'm a contractor, who do I invoice?
expected_docs: finance/_index.md, people-group/employment-solutions.md
citation: "Invoice template and where to send", "Correspondence" (finance/_index.md); "Team Members Hired as Contractors via our GitLab Services Inc Entity" (people-group/employment-solutions.md)
facts:
- F1. Contractor invoices go to payroll@gitlab.com, and an "Invoice Template" is provided. — finance/_index.md § "Invoice template and where to send" L100
- F2. [variant: non-US contractors not from Hungary, Italy, Japan, New Zealand, Nigeria, South Africa, Switzerland, Ukraine] You are paid through iiPay. Submit your monthly salary/bonus/commission invoice via Google form by the 8th, submit expenses in Navan by the 8th, and payment is scheduled for the 22nd. — finance/_index.md § "Invoice template and where to send" L102–109
- F3. [variant: non-US contractors from Italy, Nigeria, South Africa, Switzerland, Ukraine] Email your monthly invoice and expenses to payroll@gitlab.com by the 15th. — finance/_index.md § "Invoice template and where to send" L111
- F4. Questions about contractor invoices go to nonuspayroll@gitlab.com. — finance/_index.md § "Correspondence" L35
- F5. [rewording: which entity] The contracting entity is GitLab Services Inc (GSI, formerly IT BV) where GitLab has no entity or PEO. — people-group/employment-solutions.md § "Team Members Hired as Contractors via our GitLab Services Inc Entity" L69; people-group/time-off-and-absence/time-off-types.md § "Overview" L60
conflict:
- A: "VAT shifted to recipient … along with the VAT-number of GitLab IT BV (NL860316828B01)." — finance/_index.md § "Invoice template and where to send" L113–118; and "Generate IT BV Contractor Agreement - Independent or the IT BV Contractor Agreement - C2C" — hiring/talent-acquisition-framework/coordinator.md § "Employment Agreements for GitLab team members located everywhere else (IT BV contractor agreements)" L1212–1216; currency evidence: finance/_index.md 0067cfa872 2026-02-12; hiring/talent-acquisition-framework/coordinator.md bee431b547 2026-09-13 (bulk rename)
- B: "Where we do not have an entity or a PEO, team members contract with our GitLab Services Inc entity as independent or C2C contractors." — people-group/employment-solutions.md L69; currency evidence: 7593cd32dc 2026-04-09. Plus "Contractors of GitLab GSI (previously IT BV)…" — people-group/time-off-and-absence/time-off-types.md § "Overview" L60; currency evidence: bee431b547 2026-09-13
- current: B (GSI). The in-text "(previously IT BV)" marks IT BV as superseded. The git dates don't decide it (bulk commits). finance/_index.md (2026-02-12) predates employment-solutions (2026-04-09).
flag: T5 trap. The pin contains the IT BV vs GSI naming conflict as hypothesised. Also flagged: the two country lists in finance/_index.md disagree (L102 excludes Hungary, Japan, New Zealand from iiPay; L111 lists only Italy, Nigeria, South Africa, Switzerland, Ukraine for email invoicing), so Hungary/Japan/NZ contractors aren't covered.
ref_source: llm-draft, reviewed
notes: Distractors: finance/_index.md L31 (ap@gitlab.com is for vendor invoices), finance/procurement/contingent-worker-policy.md (third-party contingent workers, IT BV for India/Philippines L275–276), communication/chat.md L33 (#payroll channel; links to the internal handbook).

### Row 44 — contradiction · list · trap T6
Q: Who's on the Customer Success team? Need the full list of roles for a reorg doc.
expected_docs: customer-experience/_index.md, customer-experience/roles-overview/_index.md, customer-experience/csm/segment/_index.md
citation: "Customer Experience Teams" (customer-experience/_index.md); "Role Comparison", "1. The \"Hands on Keyboard\" Boundary" (customer-experience/roles-overview/_index.md)
facts:
- F1. The Customer Success organization is now named Customer Experience, a department within the GitLab Sales function. — customer-experience/_index.md § (front matter / intro) L2, L6
- F2. Customer Success Manager (CSM) is a role on the team. — customer-experience/_index.md § "Customer Experience Teams" L31; customer-experience/roles-overview/_index.md § "Role Comparison" L14
- F3. Customer Success Engineer (CSE) is a role on the team. — customer-experience/_index.md § "Customer Experience Teams" L32; customer-experience/roles-overview/_index.md § "Role Comparison" L15
- F4. Customer Success Architect (CSA) is a role on the team. — customer-experience/_index.md § "Customer Experience Teams" L33; customer-experience/roles-overview/_index.md § "Role Comparison" L16
- F5. Renewals Manager (RM) is a role on the team ("Global Renewals Organization within CS"). — customer-experience/_index.md § "Customer Experience Teams" L34; customer-experience/roles-overview/_index.md § "Role Comparison" L18
- F6. [optional] Professional Services Engineers (PSE), Solutions Architects (SA), and Assigned Support Engineers (ASE) are related customer-facing roles, but they are distinct from the advisory "Customer Success roles (CSM, CSE, CSA)". — customer-experience/roles-overview/_index.md § "1. The \"Hands on Keyboard\" Boundary" L26; (intro) L6
conflict:
- A: "- [VP, Customer Success](/job-description-library/sales/customer-success-leadership/#vice-president-of-customer-success)" (listed as reporting to the CRO) — sales/_index.md § "Who We Are" L75, L80; also "Roles covered include Customer Success Manager (CSM), Customer Success Engineer (CSE), Customer Success Architect (CSA)…" — customer-experience/roles-overview/_index.md (intro) L6; currency evidence: 968e3521af 2026-09-24 (both files, bulk rename commit)
- B: "The Customer Experience department is part of the [GitLab Sales](/handbook/sales/) function who partners with our customers to deliver value and positive business outcomes throughout their journey with GitLab." — customer-experience/_index.md (intro) L6; currency evidence: 968e3521af 2026-09-24 "Rename Customer Success handbook to Customer Experience, delete the stale CX handbook"
- current: B (Customer Experience) is the department name. The commit message explicitly renames Customer Success to Customer Experience. Role titles still use "Customer Success" (CSM/CSE/CSA), so both names stay valid inside the org.
recency_basis: history-only (no pinned page states the rename; only commit 968e3521af does)
flag: T6 trap. Owner review requested: "Customer Success" appears in ~300 files at the pin (rg count 303) next to "Customer Experience" (20 files), so the old name is everywhere in pinned text, not only in history. Also, whether PSE (and Demo Systems / Digital Strategy staff) count as "on the team" is ambiguous: the CX index lists only CSM/CSE/CSA/RM under "Customer Experience Teams".
ref_source: llm-draft, reviewed
decision: owner 2026-10-16 — added customer-experience/csm/segment/_index.md L9–19 (same four roles under "The Customer Success team"); F6 optional (question doesn't fix team scope); F1–F5 required.
notes: Distractors: customer-experience/account-team.md (the account team includes AE/SAE and SA, who aren't CX); customer-experience/csm/csm-manager/_index.md "CS Leadership" table (people, not roles); support/ pages (Support is a separate org).

### Row 55 — recency · single-fact · trap T6
Q: Who leads Customer Success these days? need a contact
expected_docs: eba/_index.md, customer-experience/csm/csm-manager/_index.md
citation: "Executive Business Administrator Team" (eba/_index.md); "CS Leadership" (customer-experience/csm/csm-manager/_index.md)
facts:
- F1. Sherrod Patching leads Customer Success (now Customer Experience). Name only; the title is not checked. — eba/_index.md § "Executive Business Administrator Team" L36
- F2. Sherrod Patching is the Global, VP-level head in the CS Leadership table. — customer-experience/csm/csm-manager/_index.md § "CS Leadership" L14–18
- F3. Executive support (EBA) contact for Sherrod Patching is Lauren Traylor (Sr EBA). — eba/_index.md § "Executive Business Administrator Team" L36
conflict:
- A: "the [Senior Director, Technical Account Management](https://gitlab.com/spatching) who reports the [Vice President, Customer Success](https://gitlab.com/dsakamoto)." — customer-experience/apj-customer-success.md § "APJ Customer Success Team" L32–33; also "| Executive Sponsor | David Sakamoto | VP, Customer Success |" — company/working-groups/lighthouse-metric-definitions.md § "Roles and Responsibilities" L49; currency evidence: customer-experience/apj-customer-success.md 968e3521af 2026-09-24 (bulk rename only); company/working-groups/lighthouse-metric-definitions.md 2b66c7af25 2025-03-28 (target end date 2024-01-31, L28)
- B: "| [Sales](/handbook/sales/) | **Lauren Traylor**<br>Sr EBA | Sherrod Patching (Chief Customer Officer)<br>Ted Ohr (VP, Professional Services) |" — eba/_index.md § "Executive Business Administrator Team" L36; currency evidence: 1ff992d7b4 2026-08-26 (content edit "Update Engineering/IT executive support alignments")
- current: B. The EBA table had a content edit on 2026-08-26, while A sits on pages last touched only by a bulk rename or dated 2025. A names spatching as reporting to dsakamoto, which B supersedes.
flag: T6 trap. Owner review requested: no pinned page says outright "Customer Experience is led by X". The answer comes from the EBA table and the CS Leadership table. Titles disagree even in current pages (Chief Customer Officer in eba L36 vs "VP" in csm-manager L18). Older pages still name David Sakamoto as VP Customer Success (several company/working-groups pages; sales/field-manager-development.md L92).
decision: owner 2026-10-15 — F1 checks the name only (Sherrod Patching); title not required.
ref_source: llm-draft, reviewed
notes: The question uses the old name "Customer Success". The answer should map it to Customer Experience. Distractors: sales/_index.md L80 links only a job-description, no name; security plan "VP Customer Success" (role, no name); engineering/_index.md L442 "VP, Customer Success Management - Sherrod Patching" (older title).

### Row 46 — contradiction · single-fact · trap T8
Q: Just started — do I need to give PTO notice for a half day off?
expected_docs: people-group/time-off-and-absence/time-off-types.md, people-group/time-off-and-absence/time-away-philosophy.md
citation: "PTO Protocols (Planning and Coordination)" (people-group/time-off-and-absence/time-off-types.md); "Timely & Transparent Communication" (people-group/time-off-and-absence/time-away-philosophy.md)
facts:
- F1. Yes: discuss planned time off with your manager first, giving as much notice as possible and at least twice as many days as the time off. — people-group/time-off-and-absence/time-off-types.md § "PTO Protocols (Planning and Coordination)" L25
- F2. The 2x advance-notice rule covers planned PTO, Public Holidays and Volunteer time. — people-group/time-off-and-absence/time-away-philosophy.md § "Timely & Transparent Communication" L69
- F3. By the 2x rule, a half day off needs at least 1 day of notice (derived from the 2x rule; the pin has no half-day example). — derived from people-group/time-off-and-absence/time-off-types.md L25
- F4. The time off must also be logged in Workday. — people-group/time-off-and-absence/time-off-types.md § "How to Enter PTO in Workday" L37
conflict:
- A: "provide as much notice as possible, but at least twice as many days as your planned time off (e.g., 6 business days notice for 3 days off)" — people-group/time-off-and-absence/time-off-types.md § "PTO Protocols (Planning and Coordination)" L25; currency evidence: bee431b547 2026-09-13
- B: "Share PTO plans 2-3 weeks in advance or more when possible" — people-group/time-off-and-absence/time-away-philosophy.md § "Summary of Best Practices: Results-Focused Approach" L140; currency evidence: bee431b547 2026-09-13
- current: unresolved by history (same mass-rename commit). In-text: A is stated as a minimum ("at least"), and the same rule is repeated in people-group/time-off-and-absence/time-away-philosophy.md L69 and L191. B is a "when possible" best practice. A is the binding rule.
trap note (T8): no "PTO" vs "paid time off" conflict in the pin; both terms are used for the same rule. The conflict in the pin is the notice rule: the binding minimum "at least twice as many days as your planned time off" (people-group/time-off-and-absence/time-off-types.md L25) vs the best practice "Share PTO plans 2-3 weeks in advance or more when possible" (people-group/time-off-and-absence/time-away-philosophy.md L140). The only half-day rule is Support-only (support/support-time-off.md L94–96). Nothing differs for new hires.
decision: owner 2026-10-15 — keep D1; trap note rewritten to the conflict actually in the pin.
ref_source: llm-draft, reviewed
notes: Distractors: the Support half-day rule above. Answers that apply it to everyone should fail. India entity requires entering scheduled time off 30 days ahead for payroll (entity/india-pvt-ltd.md § "India Specific Leave" L262), an entity variant. Public holidays cannot be partial (people-group/time-off-and-absence/time-off-types.md L93).

### Row 58 — recency · conditional · trap T8
Q: What's the time-off policy for my entity?
expected_docs: people-group/time-off-and-absence/time-off-types.md, total-rewards/benefits/general-and-entity-benefits/_index.md
citation: "Overview" under "Flexible Paid Time Off (PTO)" (people-group/time-off-and-absence/time-off-types.md); "Global Statutory Requirements" (people-group/time-off-and-absence/time-off-types.md); "Entity-Specific Benefits" (total-rewards/benefits/general-and-entity-benefits/_index.md)
facts:
- F1. [required] The answer depends on which entity or employment type you are under. The question doesn't say. A correct answer asks, or gives the general policy plus where to find the entity rules.
- F2. [required] All team members get GitLab's Flexible PTO: no set annual limit; coordinate with your manager and have a coverage plan; more than 25 consecutive calendar days needs special approval. — people-group/time-off-and-absence/time-off-types.md § "Overview" L17–18
- F3. [required] Statutory minimums, accrual and carryover rules vary by location and are on the location-specific (entity) benefits pages. — people-group/time-off-and-absence/time-off-types.md § "Global Statutory Requirements" L47
- F4. [optional] The entity pages are listed in the Entity-Specific Benefits table (e.g. GitLab BV Netherlands/Belgium, GitLab Inc/Fed US, GmbH Germany, GK Japan, India Pvt Ltd, plus the Remote Technology and Global Expansion partner pages). — total-rewards/benefits/general-and-entity-benefits/_index.md § "Entity-Specific Benefits" L17–29
- F5. [optional] [variant: contractor] GitLab GSI contractors don't get entity-specific benefits but receive a standard 12 public holidays. — people-group/time-off-and-absence/time-off-types.md § "Overview" (Public Holiday) L60
- F6. [optional] "Time off" (annual leave/holiday/vacation, sick days, public holidays) is distinct from "leave" (longer, circumstance-specific absences such as parental or medical leave). — people-group/time-off-and-absence/_index.md § "About Our Terminology" L12–15
conflict:
- A: "[Remote Technology (Brazil, Italy, Switzerland, Hungary, Luxembourg, and Sweden)] ... [Global Expansion (Austria, Denmark, Kenya, Mexico, Philippines, Poland, South Africa, and UAE)]" — total-rewards/benefits/general-and-entity-benefits/_index.md § "Entity-Specific Benefits" L21–22; currency evidence: f96a52e199 2026-09-28
- B: "[Remote Technology (Brazil, Denmark, Italy, Switzerland, Hungary, and Sweden)] ... [Global Expansion (Austria, Kenya, Mexico, Philippines, South Africa, and UAE)]" — people-policies/leave-of-absence/_index.md § "Company-Wide Leave of Absence Policies" L28–29; currency evidence: f96a52e199 2026-09-28
- current: A. Git history doesn't separate them (same commit, "Removing Finland benefits page"). The target pages settle it: total-rewards/benefits/general-and-entity-benefits/remote-com.md has a "Luxembourg 🇱🇺" section (L494) and no Denmark section, and total-rewards/benefits/general-and-entity-benefits/global-expansion.md has "Denmark 🇩🇰" (L100) and "Poland 🇵🇱" (L457). So the list in B is stale.
- secondary (T8 framing): "GitLab does not set a specific limit on the amount of PTO" (people-group/time-off-and-absence/time-off-types.md § "Overview" L18) vs "Flexible time off ... with the option to take up to 25 consecutive calendar days for vacation" (total-rewards/benefits/general-and-entity-benefits/_index.md § "Flexible Paid Time Off" L239). These are compatible: 25 consecutive days is the threshold for special approval, not a cap. currency: bee431b547 2026-09-13 vs f96a52e199 2026-09-28.
recency_basis: in-page (cross-page; resolved from remote-com.md and global-expansion.md, not git). Conflict not scored on this row: F4 names no countries.
trap note (T8): no "PTO" vs "paid time off" number conflict in the pin. The conflict in the pin is two country-to-provider lists that disagree on Denmark, Poland and Luxembourg: current in total-rewards/benefits/general-and-entity-benefits/_index.md L21–22, stale in people-policies/leave-of-absence/_index.md L28–29 (see conflict above). The terminology issue is company-wide Flexible PTO vs entity statutory vacation/annual leave.
decision: owner 2026-10-15 — keep D1; trap note rewritten to the conflict actually in the pin.
ref_source: llm-draft, reviewed
decision: owner 2026-10-16 — F1–F3 required, F4–F6 optional; recency_basis in-page; conflict not scored; entity pages not added to expected docs (retrieving one entity's page is the trap for this ambiguous question).
notes: The question is ambiguous by design. Penalize answers that pick one entity without saying so. Germany's statutory vacation "Runs separately to with GitLab's PTO policy, which can be used, but does not accrue" (entity/gmbh-germany.md L554), while Belgium/Singapore say "Runs concurrently with GitLab PTO" (total-rewards/benefits/general-and-entity-benefits/bv-benefits-belgium.md L212, total-rewards/benefits/general-and-entity-benefits/singapore-pte-ltd.md L244). That difference is per entity, not a contradiction.

### Row 99 — synthesis · conditional · trap T8
Q: Joining next month and I already have a trip booked in my first few weeks. Can I take paid time off that early, or is there a waiting period?
expected_docs: people-group/general-onboarding/tanewki-tips.md, people-group/time-off-and-absence/time-off-types.md
citation: "Payroll & Benefits" (people-group/general-onboarding/tanewki-tips.md); "Overview" under "Flexible Paid Time Off (PTO)" (people-group/time-off-and-absence/time-off-types.md)
facts:
- F1. For pre-planned vacations, discuss them with your manager as soon as possible to arrange cover, then enter them in Workday once you have access after starting. — people-group/general-onboarding/tanewki-tips.md § "Payroll & Benefits" L150–152
- F2. Flexible PTO has no stated tenure or waiting period. Time off is approved once you've coordinated with your manager and made a coverage plan. — people-group/time-off-and-absence/time-off-types.md § "Overview" L17
- F3. Give at least twice as many days of notice as the time off. — people-group/time-off-and-absence/time-off-types.md § "PTO Protocols (Planning and Coordination)" L25
- F4. [variant: Japan] Statutory annual leave starts at 10 days only after six months of service. — total-rewards/benefits/general-and-entity-benefits/gitlab-gk.md § "Time Off & Leave Policies" L185
- F5. [variant: Singapore] Statutory holiday allowance accrual by tenure starts after 3 months of employment (runs concurrently with GitLab PTO). — total-rewards/benefits/general-and-entity-benefits/singapore-pte-ltd.md § "Annual Leave" L234, L244
- F6. [variant: Germany] Statutory vacation accrues from the start date at 1.67 days/month. — entity/gmbh-germany.md § "Vacation Entitlement" L551
conflict:
- A: "Our Flexible PTO policy means that as long as you have coordinated with your manager about your planned time off and made a coverage plan, you are free to take PTO." — people-group/time-off-and-absence/time-off-types.md § "Overview" L17; currency evidence: bee431b547 2026-09-13
- B: "Guaranteed annual leave starting at 10 days after six months, increasing to maximum 20 days." — total-rewards/benefits/general-and-entity-benefits/gitlab-gk.md § "Time Off & Leave Policies" L185; currency evidence: bee431b547 2026-09-13
- current: unresolved by history (same mass-rename commit). In-text: these are different balances. A is GitLab Flexible PTO with no waiting period, and B is a Japan statutory annual-leave waiting period. The pin doesn't say whether Japan's statutory leave runs concurrently with Flexible PTO (Singapore's page says it does, L244).
trap note (T8): no "PTO" vs "paid time off" conflict in the pin. The conflict in the pin is waiting periods: Flexible PTO states no tenure condition (people-group/time-off-and-absence/time-off-types.md L17), while some entity statutory annual leave has one (Japan: from six months, total-rewards/benefits/general-and-entity-benefits/gitlab-gk.md L185; Singapore: from three months). "Available from day one" is inferred from the absence of a condition, not stated.
decision: owner 2026-10-15 — keep D1; trap note rewritten to the conflict actually in the pin.
ref_source: llm-draft, reviewed
notes: Strong distractors: "available from their first day of work" applies to Sick Time (people-group/time-off-and-absence/time-off-types.md L124), Bereavement (L245) and Emergency Leave (people-group/time-off-and-absence/leave-types.md L95), not Flexible PTO. New-hire public holiday balance is pro-rated (people-group/time-off-and-absence/time-off-types.md L97–102). India requires scheduled time off to be entered 30 days ahead (entity/india-pvt-ltd.md L262). Onboarding buddies are asked to be available in the first two weeks (people-group/general-onboarding/onboarding-buddies.md L43), which is not a rule for new hires.

### Row 100 — contradiction · single-fact · trap T8
Q: Does unused PTO carry over into next year?
expected_docs: people-group/time-off-and-absence/time-off-types.md
citation: "Overview" under "Flexible Paid Time Off (PTO)" (people-group/time-off-and-absence/time-off-types.md); "Global Statutory Requirements" (people-group/time-off-and-absence/time-off-types.md); "Overview" under "Public Holiday" (people-group/time-off-and-absence/time-off-types.md)
facts:
- F1. GitLab Flexible PTO has no annual limit and no balance to carry over. Germany's page states GitLab PTO "does not accrue". — people-group/time-off-and-absence/time-off-types.md § "Overview" L18; entity/gmbh-germany.md § "Vacation Entitlement" L554
- F2. Carryover rules for statutory leave depend on location and are on the entity pages. — people-group/time-off-and-absence/time-off-types.md § "Global Statutory Requirements" L47
- F3. Unused public holiday balance does not roll over to the next calendar year. — people-group/time-off-and-absence/time-off-types.md § "Overview" (Public Holiday) L58
- F4. [variant: Germany] Statutory vacation must be taken in the calendar year. It can carry over to March 31 only in special circumstances. — entity/gmbh-germany.md § "Vacation Entitlement" L552–553
- F5. [variant: Netherlands] Unused days carry over but expire July 1. — total-rewards/benefits/general-and-entity-benefits/bv-benefits-netherlands.md § "Vacation Time" L533
- F6. [variant: Belgium / Ireland / Japan / India] Belgium: no carryover (total-rewards/benefits/general-and-entity-benefits/bv-benefits-belgium.md § "Vacation Leave" L217). Ireland: only with written approval (total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md § "Time Off Policies" L402). Japan: carries over up to two years (total-rewards/benefits/general-and-entity-benefits/gitlab-gk.md § "Time Off & Leave Policies" L189). India: individual contributors carry over up to 30 days, the excess is encashed, and people managers can't carry over (entity/india-pvt-ltd.md § "Statutory Leave Entitlement" L268–269).
conflict:
- A: "GitLab does not set a specific limit on the amount of PTO a team member can take per year." — people-group/time-off-and-absence/time-off-types.md § "Overview" L18; currency evidence: bee431b547 2026-09-13
- B: "Unused days carry over to the next calendar year but expire July 1st" — total-rewards/benefits/general-and-entity-benefits/bv-benefits-netherlands.md § "Vacation Time" L533; currency evidence: bee431b547 2026-09-13
- current: unresolved by history (same mass-rename commit). Not a currency conflict: A (Flexible PTO, nothing accrues) and B (Netherlands statutory vacation) are different balances that both apply. A correct answer separates them.
- intra-page (Singapore): "Team members are allowed to carry over unused vacation up to the statutory accrual limit based on tenure." (total-rewards/benefits/general-and-entity-benefits/singapore-pte-ltd.md § "Annual Leave" L234) vs "Unused leave requires approval to carry forward" (same section L247); currency: bee431b547 2026-09-13 (same file). Unresolved.
trap note (T8): the conflict in the pin is terminology. Global "PTO" means non-accruing Flexible PTO, so there is nothing to carry over (people-group/time-off-and-absence/time-off-types.md L18). Entity pages log statutory vacation as "Paid Time Off" in Workday, each with its own carryover rule (e.g. Netherlands: carries over, expires July 1, total-rewards/benefits/general-and-entity-benefits/bv-benefits-netherlands.md L533). The Singapore page also contradicts itself (L234 vs L247).
decision: owner 2026-10-15 — keep D1; trap note rewritten to the conflict actually in the pin.
ref_source: llm-draft, reviewed
notes: The minimum correct answer is F1 + F2 (+F3). Entity variants are k-of-n optional. Distractors: FSA/HSA "rollover" (total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md L501–513), Modern Health "Unused sessions do not roll over" (total-rewards/benefits/modern-health.md L86), and India sick/casual leave with no carry forward (entity/india-pvt-ltd.md L317–319).

## 2. Flags (non-trap, resolved)

### Row 87 — synthesis · list · trap –
Q: who are our competitiors
expected_docs: marketing/product-and-technical-marketing/product-and-solution-marketing/competitive-intelligence/cicd.md, marketing/product-and-technical-marketing/product-and-solution-marketing/competitive-intelligence/application-security.md, marketing/product-and-technical-marketing/product-and-solution-marketing/usecase-gtm/delivery-automation.md, marketing/product-and-technical-marketing/product-and-solution-marketing/usecase-gtm/devops-platform/_index.md, marketing/corporate-communications/analyst-relations/forrester-tei.md
citation: "Competitor Scope - Continuous Integration" (…/competitive-intelligence/cicd.md); "Competitor Scope" (…/competitive-intelligence/application-security.md); "Competitors" (…/usecase-gtm/delivery-automation.md); "Frequently Asked Questions" (…/analyst-relations/forrester-tei.md)
facts:
- F1. [required] GitLab has many competitors because it operates across many product categories. The handbook has no single company-wide list; competitors are listed per category. — sales/sales-development/tanuki-tech.md § "Curriculum" L62
- F2. [required] GitHub and Atlassian are named as competitors. — marketing/corporate-communications/analyst-relations/forrester-tei.md § "Frequently Asked Questions" L96
- F3. [optional] [variant: CI/CD] CircleCI, Azure DevOps, Jenkins, Travis CI, and Bitbucket are listed as CI competitors. — marketing/product-and-technical-marketing/product-and-solution-marketing/competitive-intelligence/cicd.md § "Competitor Scope - Continuous Integration" L84
- F4. [optional] [variant: automated software delivery] Key competitors are GitHub, Jenkins, JFrog, CircleCI, and Weaveworks Flux CD. — marketing/product-and-technical-marketing/product-and-solution-marketing/usecase-gtm/delivery-automation.md § "Competitors" L185–191
- F5. [optional] [variant: application security] Competitors include BlackDuck, Veracode, IBM AppScan, Fortify, SonarQube, Sonatype, WhiteSource, Snyk, Synopsys, Checkmarx, TwistLock, and Aqua. — marketing/product-and-technical-marketing/product-and-solution-marketing/competitive-intelligence/application-security.md § "Competitor Scope" L54–68
- F6. [optional] [variant: DevOps platform] The nearest platform-level competitor is Microsoft's Azure DevOps; Microsoft is building toward the same vision with GitHub. — marketing/product-and-technical-marketing/product-and-solution-marketing/usecase-gtm/devops-platform/_index.md § "Competitive comparisons" L221
flag: Partial answer only. There's no authoritative, current company-level competitor list. Detailed competitor cards live in Crayon/Highspot, outside the handbook (marketing/product-and-technical-marketing/product-and-solution-marketing/competitive-intelligence/_index.md L29). Several per-category tables look dated (e.g. Travis CI, XebiaLabs, Weaveworks). Owner: keep as answerable synthesis or downgrade.
ref_source: llm-draft, reviewed
decision: owner 2026-10-16 — F1, F2 required (per 2026-10-15), F3–F6 optional; added F6 and devops-platform/_index.md (only company-level competitor statement).
notes: The vocabulary maps directly ("competitors" is used in the pin; the typo in the question doesn't matter). Other per-category lists: marketing/sales-plays/gitops/_index.md L171 (Flux, Argo CD, Terraform Cloud); company/working-groups/ci-build-speed.md L26 (GitHub, Harness.io); marketing/product-and-technical-marketing/product-and-solution-marketing/competitive-intelligence/cicd.md L109 (Spinnaker, Azure DevOps, XebiaLabs, ElectricFlow, CodeFresh).

## 3. Rest: answerable

### Row 5 — synthesis · conditional · trap –
Q: I'm in Germany and off sick — how many days can I take before I need a doctor's note, and is it different in other countries?
expected_docs: entity/gmbh-germany.md, people-group/time-off-and-absence/time-off-types.md
citation: "Sick Leave Protection" (entity/gmbh-germany.md); "For Sick Absences 1-5 Consecutive Days" (people-group/time-off-and-absence/time-off-types.md); "Reporting Procedures" (people-group/time-off-and-absence/time-off-types.md)
facts:
- F1. [required] [variant: Germany] For days 1–3 you notify your manager and enter "Out Sick" in Workday. From day 4 you email leaves@gitlab.com with the dates. — entity/gmbh-germany.md § "Sick Leave Protection" L593–594
- F2. [required] [variant: Germany, private insurance] Private insurance holders must submit an AU certificate by day 4. — entity/gmbh-germany.md § "Sick Leave Protection" L595
- F3. [optional] [variant: Germany, statutory insurance] AU certificate submission is electronic for statutory insurance holders. — entity/gmbh-germany.md § "Sick Leave Protection" L584
- F4. [required] [variant: global default] Under the global policy, an absence of less than 6 consecutive days needs no sick note unless your statutory reporting requirements state otherwise. — people-group/time-off-and-absence/time-off-types.md § "For Sick Absences 1-5 Consecutive Days" L138
- F5. [optional] Statutory reporting requirements vary by country/location and always supersede the global reporting requirements. — people-group/time-off-and-absence/time-off-types.md § "Reporting Procedures" L129
- F6. [optional] [variant: UK] For 4–7 days you complete a self-certification form. For 7+ days you provide a fit note to leaves@gitlab.com. — total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md § "Sick Leave" L663–664
- F7. [optional] [variant: Ireland] A medical certificate is required for absences of 3 or more successive calendar days. — total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md § "Time Off Policies" L412
- F8. [optional] [variant: 6+ days, global] A sick absence of 6 days or more counts as a leave of absence. Eligibility for GitLab's Sick Time policy requires evidence in line with local requirements; the documentation varies by location (e.g. medical certificate, doctor's note, fit note). — people-group/time-off-and-absence/time-off-types.md § "For Sick Absences that Exceed 6+ Consecutive Days" L146–155
- F9. [optional] [variant: Austria] If the absence lasts longer than three consecutive calendar days, a medical certificate (Krankenstandsbestätigung) from a doctor must be provided. — total-rewards/benefits/general-and-entity-benefits/global-expansion.md § "Austria 🇦🇹" L79
flag: none
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — tagged required set (F1, F2, F4); F3/F5/F8 reworded to the pin's wording; added F9 Austria variant from sweep
notes: The pin never expands "AU" (Arbeitsunfähigkeitsbescheinigung = German doctor's sick note). A correct answer should treat the AU certificate as the doctor's note. Germany's page has the 6-weeks-full-pay sick text under the heading "Vacation Entitlement" (entity/gmbh-germany.md L537), which looks like a misplacement and could confuse retrieval. Other variants a grader may accept: Israel requires a medical certificate on return (entity/israel-ltd.md L165). Distractor: Germany "Education Leave (Bildungsurlaub)" certificate (L632). The minimum is F1, F2 and F4; F5 can stand in for F4 as the answer to "is it different in other countries". F6–F9 are k-of-n optional. global-expansion.md, ltd-benefits-uk.md and gitlab-ireland-ltd.md are left out of expected_docs because each is entity- or country-specific.

### Row 9 — lookup · single-fact · trap –
Q: What is the maximum monthly reimbursement for home internet expenses?
expected_docs: finance/expenses.md
citation: "Internet" (finance/expenses.md)
facts:
- F1. [required] The internet policy cap is $100; claims above that amount are not reimbursed. — finance/expenses.md § "Internet" L509–509
- F2. [optional] Exceptions are no longer assessed individually at the claim stage. — finance/expenses.md § "Internet" L509–509
- F3. [optional] Only monthly service charges are reimbursable, expensed monthly. Setup, equipment, change fees and insurance are excluded. — finance/expenses.md § "Internet" L503–504
- F4. [optional] [variant: Netherlands] If you didn't complete it at onboarding, fill in and sign the Regeling Internet Thuis form and send it to the HRSavvy team. Don't expense internet via Navan, because those claims are rejected. — finance/expenses.md § "Internet" L505–506
- F5. [optional] [variant: Germany (GitLab GmbH)] Refer to the payroll page for country-specific guidelines. — finance/expenses.md § "Internet" L514–514
decision: owner 2026-10-15 — D1 → lookup, trap T7 → none. The pin has only the $100 internet cap (finance/expenses.md L509); the $80 cap exists only in git history.
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — tagged required set (F1); F4 reworded to the pin's wording; no sweep additions
notes: Distractors: "Internet - Travelling" L306 ($50/day while traveling), the $80 meal limits, and entity allowances in total-rewards/benefits/general-and-entity-benefits/global-expansion.md (MX 2,200 MXN at L321 and PL 185 PLN at L473 for internet plus electricity), which apply only to those countries. Also "Phone Service" (finance/expenses.md L591) has the same "$100" sentence; a model may conflate it with internet. total-rewards/benefits/general-and-entity-benefits/bv-benefits-netherlands.md § "Internet Support" only links to the internal expense policy and states no amount.

### Row 22 — lookup · conditional · trap –
Q: How do I enroll in the pension plan at our European entity?
expected_docs: entity/gmbh-germany.md, total-rewards/benefits/general-and-entity-benefits/bv-benefits-netherlands.md, total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md, total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md, total-rewards/benefits/general-and-entity-benefits/france-sas.md, total-rewards/benefits/general-and-entity-benefits/bv-benefits-belgium.md
citation: "Retirement Planning - Support Fund & Direct Insurance Plan" (entity/gmbh-germany.md); "Retirement Plan" (total-rewards/benefits/general-and-entity-benefits/bv-benefits-netherlands.md); "Pension Scheme" (total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md); "Pension Plan" (total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md); "Retirement Planning" (total-rewards/benefits/general-and-entity-benefits/france-sas.md); "Government Benefits Integration" (total-rewards/benefits/general-and-entity-benefits/bv-benefits-belgium.md)
facts:
- F1. [required] Pension enrollment is described separately for each entity, with a different provider and process, so the answer depends on which European entity employs you. A correct answer asks which entity, or gives the entity variants. — framing derived from the per-entity sections cited in F2–F6 (no single pin line states it)
- F2. [optional] [variant: Germany, GitLab GmbH] Support Fund enrollment is automatic (opt out via Total-Rewards@gitlab.com). For the Direct Insurance plan, complete the Direct Insurance agreement and submit it to Total-Rewards@gitlab.com and Profion before the 5th of the month. — entity/gmbh-germany.md § "Retirement Planning - Support Fund & Direct Insurance Plan" L132–136
- F3. [optional] [variant: Netherlands, GitLab BV] Team members over 21 on a GitLab BV contract are enrolled automatically on hire in the ASR pension plan. Contact ASR for questions or changes. — total-rewards/benefits/general-and-entity-benefits/bv-benefits-netherlands.md § "Retirement Plan" L169, L175–177, L199–200
- F4. [optional] [variant: UK, GitLab Ltd] Enrollment in the Scottish Widows Group Personal Pension Plan is automatic if you earn over £10,000 a year, are aged 22 or over, and are under State Pension Age. During onboarding, the Payroll Team informs Papaya Payroll, which adds you to the Scottish Widows pension file. — total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md § "Pension Scheme" L237, L242–246, L277–284
- F5. [optional] [variant: Ireland, GitLab Ireland Ltd] New hires are enrolled automatically in the Aviva DC plan (effective 2025-11-01). To enroll or change contributions, submit the Aviva Pension Form. — total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md § "Pension Plan" L110, L137
- F6. [optional] [variant: France / Belgium] There's no supplementary GitLab pension to enroll in. France: team members are enrolled automatically in the state National Pension Scheme. Belgium: no additional pension benefits are planned. — total-rewards/benefits/general-and-entity-benefits/france-sas.md § "Retirement Planning" L134; total-rewards/benefits/general-and-entity-benefits/bv-benefits-belgium.md § "Government Benefits Integration" L251
- F7. [optional] [variant: Denmark] The pension is through TopDanmark (4% team member, 8% employer contribution). TopDanmark contacts team members when they join GitLab to discuss their options. — total-rewards/benefits/general-and-entity-benefits/global-expansion.md § "Denmark 🇩🇰" L127–135
- F8. [optional] [variant: Sweden, via Remote (PEO)] Enrollment in the Nordnet Hållbar/SPP pension plan is mandatory, and the company pays all contributions. — total-rewards/benefits/general-and-entity-benefits/remote-com.md § "**Sweden 🇸🇪**" L176, L182
flag: none
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — F1 reworded (the "no single plan" claim was unsourced); F4 actor fix; tagged required (F1); added F7 Denmark and F8 Sweden variants from sweep
notes: The question's scope is ambiguous ("our European entity"). A good answer either asks which entity or lists the variants. Not covered: Spain (entity/iberia-srl-spain.md has no pension text) and the other PEO countries in remote-com.md (Italy: mandatory social security contributions, supplementary options under review, L264; Switzerland L330+; Hungary L449–451). F8 is a PEO variant, not a GitLab entity. Italy dirigente funds (total-rewards/benefits/general-and-entity-benefits/papaya-global-benefits.md L28–41) describe the funds but give no enrollment step: treat as a distractor. global-expansion.md and remote-com.md are multi-country hubs, so they are not in expected_docs. Israel (entity/israel-ltd.md "Pension" L67–80) isn't in Europe but is a likely retrieval distractor.

### Row 23 — lookup · process · trap –
Q: Describe the approval chain for submitting a promotion for one of my direct reports.
expected_docs: people-group/promotions-transfers.md
citation: "Twice per Year Promotion Calibration Process & Timeline"; "Calibration"; "Exception Approvals"; "Workday Out-of-Cycle Promotion Approval Process" (people-group/promotions-transfers.md)
facts:
- F1. [required] Standard path: promotions run twice a year in three stages: Planning, Calibration, Processing. The manager works with their People Business Partner (PBP) and leadership, prepares a promotion document, and submits the nomination in Workday. Promotion approvals happen during the calibration sessions. — people-group/promotions-transfers.md § "Twice per Year Promotion Calibration Process & Timeline" L100; § "Process for Managers: Requesting a Promotion" L448; § "FY27-Q2 (May 1)" L135–139
- F2. [required] Calibration level depends on the promotion level: under Director is calibrated at Department level, Director/Sr Director at Division level (Sr Director shared with E-Group), and VP at E-Group level. — people-group/promotions-transfers.md § "Calibration" L240–246
- F3. [optional] [variant: out-of-cycle exception] The manager emails their PBP with the promotion document, the justification, and next-level manager approval for any compensation increase recommendation above 10%. Once the PBP approves the exception, the PBP submits it in Workday. — people-group/promotions-transfers.md § "How to Process an Exception: Submitting an out-of-cycle Promotion request in Workday" L309
- F4. [optional] [variant: out-of-cycle, under Director] Approvals: 1) Direct Manager, 2) Department Head, 3) PBP, 4) Total Rewards, 5) FP&A. — people-group/promotions-transfers.md § "Exception Approvals" L313–315
- F5. [optional] [variant: out-of-cycle, Director+] Same chain plus 6) E-Group Leader. — people-group/promotions-transfers.md § "Exception Approvals" L316–318
- F6. [optional] After the PBP submits in Workday, the request routes to the manager, next-level manager, and E-Group leader. Once approved, People Operations stages the Job Change Letter in DocuSign. — people-group/promotions-transfers.md § "Workday Out-of-Cycle Promotion Approval Process" L480–483
flag: none
decision: owner 2026-10-15 — accepted as drafted.
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — tagged required (F1, F2); F1 citation extended to L139 (approvals in calibration window); F3 wording tightened; no sweep additions
notes: The page itself says (L6–8) "This page is currently under review and construction… go to [this Loop page]". There's also an internal inconsistency: the Exception Approvals table (L313–316) lists 5–6 approvers, but the Workday routing (L482) names manager → next-level manager → E-Group leader. Either should get credit if cited. Increases above 10% need extra justification for Total Rewards and the executive approver (L467–468). Calibration structure may vary by division and department (L248). Distractors: people-group/promotion-document-style-guide.md; the Support-team-only processes (support/managers/promoting-a-support-team-member.md, support/workflows/team/promotions.md); company/structure.md L205 (don't discuss promotions until approved).

### Row 26 — lookup · single-fact · trap –
Q: do i have to turn on disk encryption on my laptop
expected_docs: eta/corporate-it/end-user-services/laptop-management/laptop-security/encryption/_index.md
citation: "Overview" (eta/corporate-it/end-user-services/laptop-management/laptop-security/encryption/_index.md); "Apple macOS"; "Linux"
facts:
- F1. Yes. All laptops are required to have disk encryption enabled. — eta/corporate-it/end-user-services/laptop-management/laptop-security/encryption/_index.md § "Overview" L7–7
- F2. [variant: macOS] Jamf enables FileVault automatically, so no configuration is needed, though you are encouraged to verify it is on. — eta/corporate-it/end-user-services/laptop-management/laptop-security/encryption/_index.md § "Apple macOS" L15–15
- F3. [variant: macOS onboarding] FileVault is required. You'll be prompted to enable it at next login and can't proceed without doing so. — eta/corporate-it/end-user-services/onboarding101/_index.md § "MacBook Step 3: System Configuration" L105–105
- F4. [variant: Linux] LUKS full-disk encryption is required and must be enabled when you first set up the OS. — eta/corporate-it/end-user-services/laptop-management/_index.md § "Requirements" L55–55; eta/corporate-it/end-user-services/laptop-management/laptop-security/encryption/_index.md § "Linux" L28–28
- F5. Proof of disk encryption must be provided in the new laptop order or onboarding issue. — eta/corporate-it/end-user-services/laptop-management/laptop-security/encryption/_index.md § "Overview" L9–9
flag: none
ref_source: llm-draft, reviewed
notes: There is a mild tension on macOS: Jamf enables encryption automatically ("No Action Required") while onboarding101 has you click "Enable Now" for FileVault. Either way it is mandatory. Distractors: security/policies_and_standards/cryptographic-standard.md L84 (algorithms) and finance/travel/_index.md L122 (power off before security checkpoints).

### Row 34 — synthesis · list · trap –
Q: What are the requirements for submitting a relocation request?
expected_docs: people-group/relocation.md
citation: "Considerations and Eligibility" (people-group/relocation.md); "Eligibility to Work"; "Team Member"; "Relocations To New Country or Different Location Factor"; "Relocation Within Same Country and Same Location Factor"
facts:
- F1. [required] You must have completed the required one year of tenure. — people-group/relocation.md § "Considerations and Eligibility" L86–86 (also § "Relocations To New Country or Different Location Factor" L124–124)
- F2. [required] The destination must be a country where GitLab has an entity open for hiring with no hiring restrictions or headcount caps (and not a US-embargoed location). — people-group/relocation.md § "Considerations and Eligibility" L80–80; § "Long-Term Relocation Definition" L63–65
- F3. [required] You must already have the right to work there without GitLab visa sponsorship (except the Netherlands). If moving to a different country, upload proof of eligibility to Workday. — people-group/relocation.md § "Eligibility to Work" L90–90; § "Team Member" L98–98
- F4. [optional] Start at least 3 months before the move for a new country, or 30 days for the same country. — people-group/relocation.md § "Team Member" L97–97
- F5. [optional] Submit the Relocation Request Form via Compass. It goes to People Operations, and your manager reviews whether the role works from the new location. — people-group/relocation.md § "Team Member" L99–99
- F6. [optional] The request must be future-dated (no retroactive relocations), state the reason, and confirm whether employer-sponsored visa support is needed. — people-group/relocation.md § "Team Member" L102–102; § "Relocations To New Country or Different Location Factor" L119–123
- F7. [optional] [variant: same country and same location factor] No approval is needed. Update your address in the Contact tab of your Workday profile; a People Operations team member approves the address in Workday. — people-group/relocation.md § "Relocation Within Same Country and Same Location Factor" L110–110
- F8. [optional] [variant: Netherlands] To relocate to the Netherlands you first need relocation approval under the relocation process. You then need the Dutch highly-skilled-migrant salary requirement, one year at GitLab, and not to be on a Performance Improvement Plan. — people-group/visas.md § "Right to Immigrate to the Netherlands" L157–164
flag: none
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — F7 "or form" removed (not in the pin); F3 qualified (new country); tagged required (F1–F3); added F8 Netherlands variant from sweep
notes: Relocation can change compensation and equity (L68). Distractors: short-term stay/digital nomad sections (L24–L52), and the Compass "Relocation Evaluation" request (L78), which is an exploratory request rather than the actual application. people-group/visas.md is Netherlands-specific, so it is covered by optional F8 and kept out of expected_docs. Its tenure waiver for team members in unsafe environments (L166–173) is a further optional detail.

### Row 35 — synthesis · process · trap –
Q: My report is leaving next week — what do I need to kick off to get their app access removed?
expected_docs: people-group/offboarding/_index.md, people-group/offboarding/offboarding_standards.md
citation: "Termination" (people-group/offboarding/_index.md); "Offboarding" (people-group/offboarding/_index.md); "Notice of Offboarding" (people-group/offboarding/offboarding_standards.md); "Offboarding Compliance" (people-group/offboarding/_index.md)
facts:
- F1. [required] Complete the termination in Workday. If they resigned in Workday, act on the prompt in your Workday inbox; otherwise initiate it from their profile via Actions → Job Change → Terminate Employee. — people-group/offboarding/_index.md § "Termination" L66–66
- F2. [optional] Submitting the termination in Workday does not immediately terminate access. The offboarding issue, opened on the team member's last day worked, initiates the deprovisioning process. — people-group/offboarding/_index.md § "Termination" L67–67
- F3. [required] On the last working day, Offboarding Parent and Child Cases are created automatically in Compass, and each system owner (deprovisioner) gets a Child Case to remove the person from their app. — people-group/offboarding/_index.md § "Offboarding" L77–78; people-group/offboarding/offboarding_standards.md § "Notice of Offboarding" L32–32
- F4. [optional] All offboarding tasks by all departments must be completed within 5 days of the offboarding date; critical, time-sensitive systems (e.g. 1Password, Slack) within the first 24 hours. — people-group/offboarding/_index.md § "Offboarding Compliance" L216–216
- F5. [optional] Scheduled offboardings are opened between 4:00–5:00pm in the team member's local timezone, Monday–Friday. If deprovisioning must be initiated outside these times, the team member or their manager should reach out to IT Operations to arrange an alternate time. — people-group/offboarding/offboarding_standards.md § "Notice of Offboarding" L34–36
flag: none
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — F2/F4/F5 reworded to the pin's wording; required set F1, F3; notes path fix; no sweep pages added
notes: Within the pin, "Managing the Offboarding Tasks → Offboarding Issue" (people-group/offboarding/_index.md L311) still says "please open an offboarding issue", while the standards say cases are created automatically in Compass (and people-group/offboarding/offboarding_standards.md L54 flags the manual `/pops` steps as outdated). Not a trap, but a grader should accept the Compass-case answer. people-group/offboarding/faq.md L8–12 (offboarding issue created automatically on the last working day) is a related retrieval, written for the departing team member. Distractors: the "Access Change Request" template (eta/corporate-it/end-user-services/access-requests/access-requests/_index.md L105) applies to role changes, not departures; laptop returns (L313–L319).

### Row 38 — synthesis · list · trap –
Q: which departments own communication during an incident
expected_docs: engineering/infrastructure-platforms/incident-management/_index.md, security/security-operations/sirt/security-incident-communication-plan.md, engineering/infrastructure-platforms/incident-management/roles/communications-lead.md, marketing/corporate-communications/incident-communications-plan.md
citation: "Incident Response Roles", "Tier 2", "Role-Team Mapping", "Status" (engineering/infrastructure-platforms/incident-management/_index.md); "Security team roles and responsibilities", "Designated key approvers" (security/security-operations/sirt/security-incident-communication-plan.md); "Role Assignment", "Internal Communications" (engineering/infrastructure-platforms/incident-management/roles/communications-lead.md); "Core Communication Escalation Response Team Roles and Responsibilities" (marketing/corporate-communications/incident-communications-plan.md)
facts:
- F1. [required] [variant: GitLab.com / production incident] The Communications Lead role owns external communications and status updates. It is needed for S1/S2 incidents or when significant communication is required. — engineering/infrastructure-platforms/incident-management/_index.md § "Incident Response Roles" L106
- F2. [required] [variant: production incident] The Communications Lead is staffed by the Communications Manager On Call (CMOC), which is generally a member of the Support team. — engineering/infrastructure-platforms/incident-management/_index.md § "Tier 2" L136; § "Role-Team Mapping" L148
- F3. [optional] [variant: production incident] The CMOC updates status.io / status.gitlab.com. — engineering/infrastructure-platforms/incident-management/_index.md § "Status" L527
- F4. [optional] [variant: production incident] Infrastructure Leadership (Staff+ or EM in the Infrastructure, Platform department) keeps #cto updated for high-severity incidents. — engineering/infrastructure-platforms/incident-management/_index.md § "Tier 2" L137
- F5. [optional] [variant: security incident] The Security Communications Manager on Call (SecCMOC), who is the SIMOC, Security Incident Commander or Security Assurance Engineer, coordinates external communications. Security External Communications reviews messaging for external audiences and liaises with marketing teams. — security/security-operations/sirt/security-incident-communication-plan.md § "Security team roles and responsibilities" L52–53
- F6. [optional] [variant: security incident] The 4 required approver groups for external communications are Security, Legal, Customer Success, and Investor Relations. The Director of Corp Comms is DRI/Contributor for media responses. — security/security-operations/sirt/security-incident-communication-plan.md § "Designated key approvers" L147, L155
- F7. [optional] [variant: production incident] The Communications Lead is the CMOC for GitLab.com and the GitLab Dedicated Communications Manager On Call (GDCMOC) for Dedicated. It also owns internal communications during incidents, except e-group communications, which the Infrastructure Liaison oversees. — engineering/infrastructure-platforms/incident-management/roles/communications-lead.md § "Role Assignment" L9–12; § "Internal Communications" L27–29
- F8. [optional] [variant: corporate / reputational incident] For a communication escalation, the Corporate Communications team coordinates external communications (and social media), Internal Communications coordinates internal communications, the CLO provides legal input, and the CMO is DRI on the final external message. — marketing/corporate-communications/incident-communications-plan.md § "Core Communication Escalation Response Team Roles and Responsibilities" L49–53
flag: none
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — F5/F6 reworded to the pin; added communications-lead.md (F7) and the corporate comms incident plan (F8); required F1, F2; removed the unsupported "old name" note
notes: The question's scope is ambiguous (production vs. security vs. corporate incidents). A grader should accept a security-scoped answer covering F5 in place of F1–F2. The security plan says "Customer Success" at L147, L153, L168. The security plan L34 points Support/Infrastructure incidents needing external-comms guidance to the corporate communications plan. support/workflows/cmoc_workflows.md L9 (CMOC as "the voice of GitLab") is an acceptable related retrieval. Distractors: people-group/incident-response.md (People incidents), marketing/emergency-response.md, support/support-incident-response.md, and the GitLab Dedicated IMOC page.

### Row 65 — lookup · single-fact · trap –
Recoded from ooc-in-scope, 2026-10-15 (D1 lookup, D2 short-section). Premise correction.
Q: Where's the seating plan for the office floor?
expected_docs: company/culture/inclusion/_index.md, security/corporate/_index.md
citation: "Fully distributed and completely connected" (company/culture/inclusion/_index.md); "Mission" (security/corporate/_index.md)
facts:
- F1. There is no office seating plan because GitLab is all-remote and has no offices. Either citation passes. — company/culture/inclusion/_index.md § "Fully distributed and completely connected" L147; security/corporate/_index.md § "Mission" L25
ref_source: llm-draft, reviewed
notes: Distractors: "open office floor plan" and "hot desking" in all-remote essays (company/culture/all-remote/getting-started.md L70, company/culture/all-remote/workspace.md L215, company/culture/all-remote/stages.md L81); event seating (marketing/growth-marketing/corporate-events.md).

### Row 88 — lookup · process · trap –
Q: what is our appraisal cycle
expected_docs: people-group/talent-assessment.md
citation: "Cadence" (people-group/talent-assessment.md); "Timeline" under "FY26 Talent Assessment" (people-group/talent-assessment.md); "Overview" (people-group/talent-assessment.md)
facts:
- F1. [required] GitLab's appraisal equivalent is the Talent Assessment. It runs once a year, with a recommended informal mid-year check-in. — people-group/talent-assessment.md § "Cadence" L475
- F2. [optional] It uses a Performance/Growth Potential Matrix ("9-Box") completed in Workday, and Key Talent is reviewed annually. — people-group/talent-assessment.md § "Overview" L116, L119
- F3. [optional] The FY26 cycle ran January–April, combined with Q2 promotion nominations, with promotions and compensation changes effective May 1, 2026. — people-group/talent-assessment.md § "Timeline" L443
- F4. [optional] Steps: self-assessment in Workday (opens Jan 12, due Jan 23) → manager ratings via "Assess My Team" (Jan 26–30) → leadership calibration (Feb 2–27) → manager submits the form (Mar 13) → Annual Compensation Review (March) → manager communication window (end of April). — people-group/talent-assessment.md § "Timeline" L449–463
- F5. [optional] Self-evaluations are voluntary but strongly encouraged. — people-group/talent-assessment.md § "Team Member Self-Evaluations" L483
- F6. [optional] The page is under review as the FY27 Check-In cycle launches in August 2026. Current details are on The Loop. — people-group/talent-assessment.md § (top of page, before "Quick Start: What You Need to Know Now") L7–10
flag: none (vocabulary mapped)
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — required set tagged (F1); facts verified, no wording change; no sweep pages added
notes: "Appraisal" maps to "Talent Assessment" (performance/growth potential review). F6 matters for recency: the FY26 dates may already be superseded at the pin date (2026-10). Staff hired too recently are "Too New to Rate" (L127). Distractors: people-group/quarterly-talent-review.md (quarterly reporting, not appraisal), people-group/360-feedback.md, total-rewards/compensation/compensation-review-cycle/_index.md (ACR, downstream of the assessment), Mid-Year Check In (L753–811, recommended and informal; FY27 timeline "to be updated" L811). L123 still says "The FY25 talent assessment should consider performance from the period FY25Q1 - FY25Q4" (stale text in the same page).

### Row 89 — synthesis · process · trap –
Q: whats our exit policy
expected_docs: people-group/offboarding/_index.md, people-group/offboarding/faq.md
citation: "Prior to Resignation" (people-group/offboarding/_index.md); "Resignation" (people-group/offboarding/_index.md); "Involuntary Terminations" (people-group/offboarding/_index.md); "Laptop Wipe" (people-group/offboarding/faq.md)
facts:
- F1. Before resigning, talk to your direct manager about the handover and communication plan, check your location's notice period, and prepare a resignation letter. — people-group/offboarding/_index.md § "Prior to Resignation" L28–30
- F2. [required] You resign by submitting it directly in Workday (via Okta). Your manager then completes the offboarding/termination in Workday, and you receive an offboarding packet (final pay, benefits, device return). — people-group/offboarding/_index.md § "Resignation" L34–35
- F3. Some countries have extra resignation steps, e.g. Germany requires a wet-ink signed resignation letter, and Belgium/France must email the letter to legal-employment@gitlab.com. — people-group/offboarding/_index.md § "Belgium" / "France" / "Germany" L42–50
- F4. [required] Involuntary terminations are handled only by Team Member Relations (TMR), after the underperformance guidelines have been followed. — people-group/offboarding/_index.md § "Involuntary Terminations" L86–87
- F5. Your laptop must be wiped by IT Ops on your last day; you must not wipe it yourself. — people-group/offboarding/faq.md § "Laptop Wipe" L68–70
- F6. Benefits coverage typically ends on your last day (US medical/dental/vision run to the end of that month). — people-group/offboarding/faq.md § "When will my benefits coverage end?" L110
- F7. [optional] Exit interviews take place during a voluntary leaver's last week. — people-group/_index.md § "People Operations Team" L136
flag: none (vocabulary mapped)
ref_source: llm-draft, reviewed
decision: owner 2026-10-16 — F2 and F4 required (voluntary + involuntary exit), the rest optional; added optional F7 (exit interviews). offboarding_standards.md stays a distractor (access-deprovisioning standard); the People Ops offboarding SLA (people-group/_index.md L128) is internal, not a fact.
notes: "Exit policy" maps to Offboarding (voluntary and involuntary). The "notice period" link (L29) points to people-group/contracts-probation-periods.md#probation-period, but that page renders the location tables from Hugo shortcodes that aren't in content/handbook, so per-country notice periods are not answerable from the pin. Other optional facts: final pay varies by location (people-group/offboarding/faq.md L86), final expenses at least one week before departure (people-group/offboarding/faq.md L94), offboarding issue opened on the last day to deprovision access (_index.md L36, L67). Distractor: people-group/offboarding/offboarding_standards.md (internal People Ops procedure). Acceptable optional content: job abandonment, three consecutive workdays absent without contact may lead to termination (people-policies/_index.md § "Job Abandonment" L142–144).

### Row 92 — lookup · process · trap –
Q: Whats our POSH policy
expected_docs: people-policies/india-ltd/india-sexual-harassment-policy.md, people-group/anti-harassment.md
citation: "1.1 Introduction" (people-policies/india-ltd/india-sexual-harassment-policy.md); "1 Internal Committee" (people-policies/india-ltd/india-sexual-harassment-policy.md); "GitLab India Private Limited" (people-group/anti-harassment.md)
facts:
- F1. [required] GitLab's POSH equivalent is the "GitLab India Private Limited Policy Against Sexual Harassment", a framework provided in accordance with the Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act 2013. — people-policies/india-ltd/india-sexual-harassment-policy.md § "1.1 Introduction" L22
- F2. [optional] It has an effective date of 1 November 2025. — people-policies/india-ltd/india-sexual-harassment-policy.md (panel above "Roles and Responsibilities") L6
- F3. [optional] It covers all permanent and temporary team members (including during probation), interns, and contract workers or vendors/consultants, including remote and off-site work interactions. — people-policies/india-ltd/india-sexual-harassment-policy.md § "1.2 Scope" L26–28
- F4. [required] Complaints go to an Internal Committee, which investigates and makes recommendations. The page says GitLab "will" form the committee and will update the policy once members are appointed. — people-policies/india-ltd/india-sexual-harassment-policy.md § "1 Internal Committee" L58–60
- F5. [optional] A formal complaint is made by writing to the Internal Committee or by contacting the Presiding Officer or any committee member. It should be made within 3 months of the incident (or of the last incident in a series). The Internal Committee may extend this by up to 3 more months. — people-policies/india-ltd/india-sexual-harassment-policy.md § "2 Procedures for Resolution, Settlement or Prosecution of Acts of Sexual Harassment" L68–70
- F6. [optional] Inquiries are confidential and retaliation is prohibited. — people-policies/india-ltd/india-sexual-harassment-policy.md § "1.5 Confidentiality" L135; § "1.6 Protection against Retaliation" L141
flag: none (vocabulary mapped)
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — F1/F5 reworded to the pin ("in accordance with"; written or by contacting the Presiding Officer; "should" within 3 months); required F1, F4; no sweep pages added
notes: "POSH" (India term) maps to the India Policy Against Sexual Harassment. The description field (L3) literally says "Prevention of Sexual Harassment Policy". Outside India, the global Anti-Harassment Policy applies: report to the CPO, Team Member Relations or a PBP (people-group/anti-harassment.md § "Reporting Alleged Harassment" L95–100). people-group/anti-harassment.md L241–243 links to the India policy. Distractors: people-policies/india-ltd/india-eop-policy.md; people-policies/_index.md § "Ireland" L332–336 (Ireland Bullying, Harassment, and Sexual Harassment Policy link, a different entity).

### Row 93 — lookup · conditional · trap –
Q: Is there a probation policy
expected_docs: people-group/contracts-probation-periods.md
citation: "Probation Period" (people-group/contracts-probation-periods.md); "Important steps during the Probation Period" (people-group/contracts-probation-periods.md)
facts:
- F1. [required] Yes. Some team members, depending on location, have a probation period of 1 to 9 months. Contracts commonly use the maximum allowed in each country. — people-group/contracts-probation-periods.md § "Probation Period" L80
- F2. [optional] If you relocate or change contract with unbroken service and have already passed probation, you don't do probation again. — people-group/contracts-probation-periods.md § "Probation Period" L80
- F3. [optional] People Operations manages the process, and probation status is recorded in Workday. — people-group/contracts-probation-periods.md § "Probation Period" L81–83
- F4. [optional] Managers review performance halfway through probation and raise underperformance with Team Member Relations right away. Workday reminds them 28 days before the end (14 days for the Netherlands/Austria) to submit the outcome. — people-group/contracts-probation-periods.md § "Important steps during the Probation Period" L91–95
- F5. [optional] Team members who pass receive a probation confirmation letter in Workday. — people-group/contracts-probation-periods.md § "Important steps during the Probation Period" L99–100
- F6. [optional] Ending probation early is an exception request escalated by the manager to a skip-level and the PBP/TMR specialist, with no expectation of approval. — people-group/contracts-probation-periods.md § "Probation Period" L85
flag: none
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — required set tagged (F1); facts verified, no wording change; no sweep pages added
notes: Which locations have probation, and how long, is in "Current Locations With Probationary Periods" / "Locations without Probation Periods" (L102–108). Both are Hugo shortcodes (`{{< people-group/entities-with-probation >}}`) whose data isn't in content/handbook, or anywhere in the repo checkout. A per-country answer is therefore not supported by the pin. people-group/relocation.md L183 restates F2 (an acceptable related retrieval). Distractor: India POSH scope "including during any probation period" (people-policies/india-ltd/india-sexual-harassment-policy.md L26).

### Row 96 — lookup · conditional · trap –
Q: if i work on a public holiday do i get a day back later?
expected_docs: people-group/time-off-and-absence/time-off-types.md, engineering/infrastructure-platforms/incident-management/on-call/tier-2.md, support/support-time-off.md
citation: "Overview" under "Public Holiday" (people-group/time-off-and-absence/time-off-types.md); "Public holidays" (engineering/infrastructure-platforms/incident-management/on-call/tier-2.md)
facts:
- F1. [required] Effectively yes. Public holidays aren't pre-loaded in Workday; you choose which dates to take against a country-specific annual balance, so working a public holiday doesn't use up the balance. — people-group/time-off-and-absence/time-off-types.md § "Overview" L53
- F2. The public holiday balance must be used within the calendar year and does not roll over. — people-group/time-off-and-absence/time-off-types.md § "Overview" L58
- F3. Public holidays are logged as whole days; partial public holidays aren't allowed. — people-group/time-off-and-absence/time-off-types.md § "Frequently Asked Public Holiday Questions" L93
- F4. [variant: on-call engineers] Team members who choose to work a public holiday may move it to a different day under the Public Holiday Policy; this is voluntary. — engineering/infrastructure-platforms/incident-management/on-call/tier-2.md § "Public holidays" L313
- F5. [variant: Support Shift Engineers] Shift Engineers may work a holiday and float it to another day, ideally within one month before or after. — support/support-time-off.md § "Holidays as a Shift Engineer" L350
- F6. [optional] [variant: New Zealand] NZ employment law requires work on a formal public holiday (including on-call) to be compensated with time-in-lieu. — total-rewards/benefits/general-and-entity-benefits/pty-benefits-new-zealand.md § "On-Call Support (Engineering Only)" L126
flag: none
ref_source: llm-draft, reviewed
decision: owner 2026-10-16 — F1 reworded to what L53 states (was an inference) and is the only required fact; F2–F6 optional; added F6 (NZ time-in-lieu); added tier-2.md and support-time-off.md to expected docs (both state the swap literally).
notes: The pin has no "day in lieu" policy for working a public holiday. It works through the flexible-balance model. Distractors: Australia "time in lieu" is for on-call shifts only (total-rewards/benefits/general-and-entity-benefits/pty-benefits-australia.md L208–254). Belgium substitutes holidays that fall on a Sunday (total-rewards/benefits/general-and-entity-benefits/bv-benefits-belgium.md L150). A Global Expansion country gives a substitute day only when a holiday falls on a scheduled day off (total-rewards/benefits/general-and-entity-benefits/global-expansion.md L534). Family & Friends Day overlap rule (company/family-and-friends-day.md L23).

## 4. Rest: out-of-corpus

### Row 14 — ooc-in-scope · single-fact · trap –
Q: What is the coverage amount of the fertility benefit?
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -n -i 'fertility|ivf|carrot|progyny|maven' total-rewards/` → 7 hits: general benefits page § "Fertility & Family Planning" L152–156; total-rewards/benefits/general-and-entity-benefits/korea-ltd-benefits.md L190–197 (fertility treatment leave, 6 days); inc-benefits-us L185, L224.
- `rg -n -i 'fertil|infertil|ivf|in-vitro|assisted reproduct'` (whole handbook) → adds entity/israel-ltd.md L209–211 (treatment leave), entity/india-pvt-ltd.md L50 ("Maternity and Infertility Cover", no amount), company/culture/inclusion/tmrg-tmag/tmrg-caregivers.md L58 (link only).
- `rg -n -i 'lifetime max|fertility.*\$|\$.*fertility|family planning'` → only the general benefits heading and a link. No dollar or lifetime-maximum figure anywhere.
confirmed: nothing in pin answers the question as asked
decision: owner 2026-10-15 — keep ooc-in-scope; nearby excerpts below are distractors.
distractors: "Team Members can refer to their [entity-specific] medical plans to understand the fertility and family planning benefits available to them, as applicable." (total-rewards/benefits/general-and-entity-benefits/_index.md § "Fertility & Family Planning" L154); "Infertility Coverage: California plans cover diagnosis/treatment at 50% coinsurance; Hawaii includes IVF consultation and procedures" (total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md § "Kaiser Medical Plans" L224); "Fertility Coverage: Included Coverage, See SBC for details" (total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md § "Cigna PPO" L185); fertility treatment leave in Korea (total-rewards/benefits/general-and-entity-benefits/korea-ltd-benefits.md L190–197) and Israel (entity/israel-ltd.md L209–211). An answer giving 50% coinsurance as "the" coverage amount is wrong.
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — no change

### Row 16 — ooc-in-scope · process · trap –
Q: One of my reports lost their office badge, who do we tell and what happens next?
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -l -i "badge"` → 73 files. Hits are Credly/certification badges, GitLab.com UI badges and similar; none about office or building ID badges.
- `rg -i "lost (badge|key ?card|access card|id card)"` → 0 files
- `rg -i "lost.{0,30}badge|badge.{0,30}lost|office badge|id badge|security badge"` → 1 hit: finance/procurement/vendor-guidelines/vendor-security-addendum.md L171 (photo-ID badges at *vendor* facilities). Irrelevant.
- `rg -i "key ?card|keycard|access card|building access"` → 5 files: co-working "access cards ... not reimbursable" (finance/expenses.md L380), CEO-scheduling Mission Control building instructions, meetup checklists. None cover a lost badge.
- `rg -i "lost or stolen"` → 9 files. Nearest: people-group/acceptable-use-policy.md § "Lost or Stolen Procedures" L165–167 (email panic@gitlab.com for a lost *device* such as a thumb drive, Yubikey, phone or laptop) and finance/accounts-payable/corp-credit-cards.md § "7.4 Card Lost or Stolen" (corporate credit card). Neither covers office badges.
- `rg -i "physical security"` → 6 files. security/policies_and_standards/physical-security-standard-for-company-assets.md covers devices, vendor data-centre controls and Zero Trust; it has no badge process.
confirmed: nothing in pin answers
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — no change
notes: Strong distractor: the panic@gitlab.com lost-device procedure (people-group/acceptable-use-policy.md L167). A model may stretch it to badges; that should be graded as a wrong answer, not as "I don't know". GitLab is all-remote, so no office-badge process is documented.

### Row 17 — ooc-off-topic · single-fact · trap –
Q: what's the tallest mountain in africa
expected: "Sorry, I don't know how to answer that."
searches:
- `rg -i "kilimanjaro"` → 0 files
- `rg -i "tallest mountain|highest mountain"` → 0 files
confirmed: nothing in pin answers
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — no change
notes: none

### Row 47 — ooc-in-scope · conditional · trap –
Q: For team members employed in France, what is the statutory minimum paid time off entitlement?
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -n -i 'congés payés|conges payes|2\.5 days|2,5 jours|30 (working )?days|25 (working )?days|five weeks|5 weeks' total-rewards/benefits/general-and-entity-benefits/france-sas.md` → parental-leave request deadlines (L147, L180) and sick-pay "first 25 working days" (L346–347, L367) only; no vacation figure
- `rg -l -i france people-group/time-off-and-absence/` → 0 files
- `rg -n -i 'france.{0,80}(days|weeks)|(days|weeks).{0,80}france'` → 1 unrelated hit (people-group/relocation.md L353)
- total-rewards/benefits/general-and-entity-benefits/france-sas.md § "Paid Time Off (Vacation)" L295 → the statutory requirements are on an internal-only page (out of corpus)
- total-rewards/benefits/general-and-entity-benefits/france-sas.md L84 and people-group/time-off-and-absence/time-off-types.md § "Global Statutory Requirements" L47 → link to each other; neither gives a number
confirmed: nothing in pin answers
decision: owner 2026-10-15 — D1 contradiction → ooc-in-scope, trap T8 → none (France's statutory minimum is not in the pin).
ref_source: llm-draft, reviewed
decision: owner 2026-10-16 — confirmed no vacation figure on france-sas.md (L274–295, L80–88, all day/week figures grepped); added two numeric distractors to notes; context note reworded (adding it to the refusal fails exact match).
notes: Distractors: France "Holiday Bonus" (total-rewards/benefits/general-and-entity-benefits/france-sas.md § "Holiday Bonus" L101–130, 1% of gross pay, which is not a time-off entitlement). Other entities' numbers: Germany ≥20 days, Belgium 20, Netherlands ≥20, Ireland 4 weeks, UK 28 incl. 8 public holidays. A model may wrongly carry one over to France. France sick-pay supplement "first 25 working days" (total-rewards/benefits/general-and-entity-benefits/france-sas.md L346) is a strong numeric distractor. Context in the pin (information only; adding it to the refusal fails exact match, diagnostic label `abstain+extra`): France gets statutory vacation plus RTT days and Flexible PTO (total-rewards/benefits/general-and-entity-benefits/france-sas.md § "Paid Time Off (Vacation)" L278, L292–294). More numeric distractors: maternity leave "16 weeks" (total-rewards/benefits/general-and-entity-benefits/france-sas.md L154) and paternity "Total leave: 28 days" (L187).

### Row 60 — ooc-in-scope · single-fact · trap –
Q: Are pet care expenses reimbursable for new team members?
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -i "pet care|pet-care|petcare"` → 0 files
- `rg -i "pet sitter|pet sitting|kennel|dog walk"` → 0 files
- `rg -i "\bpets?\b.{0,60}(expens|reimburs)|(expens|reimburs).{0,60}\bpets?\b"` → 0 files
- `rg -l -i "\bpets?\b"` → 29 files, mostly team-page pet pictures (people-group/offboarding/offboarding_standards.md L89–90) and culture pages. No expense rule.
- `rg -i "pet insurance"` → 1 file: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md § "Pet Insurance" L583–591 (US voluntary MetLife pet insurance enrolment, not an expense reimbursement, and not new-hire specific)
- `rg -n -i "\bpets?\b" finance/expenses.md people-group/relocation.md people-group/general-onboarding/` → 0 hits
confirmed: nothing in pin answers
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — no change
notes: Distractors: US Pet Insurance (benefit enrolment) and the new-hire $1,500 home-office stipend (finance/expenses.md L417), whose approved list doesn't include pet items. A model should not infer "no" from the non-reimbursable list (L423), which doesn't mention pets.

### Row 63 — ooc-in-scope · conditional · trap –
Q: Is a company car allowance provided for team members employed in Germany?
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -n -i 'car allowance|company car|vehicle|dienstwagen|car lease|leasing'` → no "company car" anywhere; "Car Allowance" appears only for the UAE (total-rewards/benefits/general-and-entity-benefits/global-expansion.md L691–693, GX Global). Vehicle hits: Navan personal-vehicle mileage (navan-expense-guide L492), vehicle rental booking (accounts-payable L95), and the general benefits page § "Vehicle Salary Sacrifice & Novated Leasing Programs" L191–207.
- `grep -n '^#' entity/gmbh-germany.md` + `rg -i 'auto|car|mobility|bike|jobrad|fahrrad|transport' entity/gmbh-germany.md` → Germany benefits page has no car or mobility benefit (only health, social insurance, pension, accident/life insurance, leave).
- `rg -n -i 'mileage'` (finance/expenses.md § "Mileage" L253–256) → mileage reimbursement only.
confirmed: nothing in pin answers the question as asked
decision: owner 2026-10-15 — keep ooc-in-scope; nearby excerpts below are distractors.
distractors: "GitLab has evaluated vehicle salary sacrifice and novated leasing programs across multiple regions (including Australia and the UK) and has decided not to offer these benefits at this time." … "This is a company-wide position and is not specific to any single region." (total-rewards/benefits/general-and-entity-benefits/_index.md § "Vehicle Salary Sacrifice & Novated Leasing Programs" L193, L205); "Monthly Car Allowance, see the GX Global UAE Benefits Spreadsheet" (total-rewards/benefits/general-and-entity-benefits/global-expansion.md § "United Arab Emirates" L691–693; UAE only); mileage reimbursement (finance/expenses.md § "Mileage" L253–256). The Germany page (entity/gmbh-germany.md) has no car or mobility benefit.
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — corrected "no car allowance anywhere" search claim (UAE has one); added UAE distractor; re-cited mileage to L253–256

### Row 68 — ooc-off-topic · list · trap –
Q: Provide a recommended reading list of classic science fiction novels.
expected: "Sorry, I don't know how to answer that."
searches:
- `rg -i "science fiction|sci-fi|scifi"` → 2 files: eta/ai/strategy/guiding-principles/_index.md L242 (figure of speech) and legal/readmes/rashmichachra.md L29 (Star Trek/Star Wars fandom). Irrelevant.
- `rg -i "asimov|dune|foundation series"` → 1 file: engineering/readmes/ben-king.md § "Books" L32–38
confirmed: nothing in pin answers
decision: owner 2026-10-15 — keep ooc-off-topic.
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — notes line range corrected to L32–38; no other change
notes: Distractor: ben-king README ("Favourites include: ... Foundation Trilogy by Isaac Asimov ..." engineering/readmes/ben-king.md § "Books" L32–38) (and other personal READMEs with "Books" sections).

### Row 69 — ooc-off-topic · process · trap –
Q: steps to upgrade the raspberry pi cluster in my garage to the latest OS
expected: "Sorry, I don't know how to answer that."
searches:
- `rg -l -i "raspberry ?pi"` → 8 files. Mentions are GitLab Runner/Omnibus support for Raspberry Pi (engineering/infrastructure-platforms/gitlab-delivery/build/_index.md L59; engineering/infrastructure-platforms/gitlab-delivery/build/maintenance/build-infrastructure.md L51), a marketing README and delivery-automation use cases. None covers upgrading a personal Pi OS.
- `rg -i "upgrade (the |your |our )?(kubernetes |k8s |gke )?cluster|cluster upgrade"` → 3 files: engineering/infrastructure-platforms/gitlab-delivery/build/k8s-release-support-policy.md and engineering/infrastructure-platforms/gitlab-delivery/distribution/k8s-release-support-policy.md § "GKE auto-upgrades" L139–141; engineering/architecture/design-documents/gitlab_messaging_layer/_index.md § "Cluster upgrades" L508
- `rg -l -i "upgrade"` with upgrade in the file path → support/workflows/upgrade-assistance.md, support/support-pods/upgrade/_index.md, engineering/data-engineering/database-excellence/database-frameworks/postgresql-upgrade-cadence.md, customer-experience/csm/services/infrastructure-upgrade.md, engineering/workflow/unplanned-upgrade-stop.md
confirmed: nothing in pin answers
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — added arm.md Raspberry Pi packages distractor to notes
notes: Triage alternative wording ("steps to upgrade our cluster to the next version") would be a strong retrieval match for the k8s-release-support-policy pages, the gitlab_messaging_layer "Cluster upgrades" design doc, postgresql-upgrade-cadence, and customer-experience/csm/services/infrastructure-upgrade.md (customer GitLab upgrades). The verbatim question (garage Raspberry Pi) is clearly off-topic. The Raspberry Pi Omnibus/Runner pages (incl. engineering/infrastructure-platforms/gitlab-delivery/build/maintenance/arm.md L30–32, GitLab packages for Raspberry Pi) are a minor lexical distractor.

### Row 70 — ooc-off-topic · conditional · trap –
Q: gonna be in berlin this weekend, is it gonna rain?
expected: "Sorry, I don't know how to answer that."
searches:
- `rg -i 'weather forecast|berlin'` → 5 hits: songbook (Irving Berlin), infra label `europe-berlin`, Slack `#loc_berlin` (communication/chat.md L172), fast-boot in Berlin, local-channels list. None is weather.
- `rg -i '(weather|forecast).{0,40}(rain|berlin)'` → only revenue "forecast" hits in professional-services pages.
confirmed: nothing in pin answers it
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — reworded notes (no "fine" for extra text); added in-person.md distractor
notes: Distractors: `#loc_berlin` Slack channel (communication/chat.md L172); leadership/in-person.md L128 (weather contingencies for events). A reply that adds the Slack channel or anything else beyond the exact refusal fails exact match (`abstain+extra`).

### Row 71 — ooc-off-topic · single-fact · trap –
Q: how much PTO does Atlassian give its employees? I'm a contractor comparing offers
expected: "Sorry, I don't know how to answer that."
searches:
- `rg -l -i 'atlassian'` → 18 files, all Jira/Trello/Atlassian product links (e.g. support/workflows/jira-server.md L11–57, company/culture/all-remote/parenting.md L188).
- `rg -i 'atlassian.{0,60}(pto|vacation|time off|leave)'` → 0 hits.
confirmed: nothing in pin answers it
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — no change
notes: Distractors: Atlassian product mentions (Jira/Trello). GitLab's own Flexible PTO and contractor rules (people-group/time-off-and-absence/time-off-types.md L17–18, L60). A model may answer about GitLab instead, which should be scored as off-target rather than correct.

### Row 72 — ooc-off-topic · list · trap –
Q: Enumerate the ceremonies defined in the Scrum Guide.
expected: "Sorry, I don't know how to answer that."
searches:
- `rg -l -i 'scrum guide'` → 0 files.
- `rg -l -i '\bscrum\b'` → ~10 files, mostly customer-experience/professional-services-engineering delivery methodology pages.
- `rg -i 'sprint review|daily scrum|sprint retrospective'` → 3 files: PS methodology retrospectives/backlog-management pages and marketing marketing/product-and-technical-marketing/product-and-solution-marketing/usecase-gtm/agile/_index.md L177 (product capabilities list).
confirmed: nothing in pin answers it
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — added sm-project-management.md distractor
notes: Strong distractor: customer-experience/professional-services-engineering/professional-services-delivery-methodology/_index.md L70–76 lists GitLab PS's "five key components" of an iteration (Iteration Planning, Daily Standup, Backlog Refinement, Iteration Review, Retrospective). That is GitLab's own PS process, not the Scrum Guide's events. A model may pass it off as the Scrum answer. Also: marketing/product-and-technical-marketing/product-and-solution-marketing/getting-started/sm-project-management.md § "Workflow - Refine, Sprint, Retrospective" L167–176 (PMM team's 2-week sprints; says they do not practice Scrum Events as separate ceremonies) and customer-experience/professional-services-engineering/professional-services-delivery-methodology/backlog-management/_index.md L78–83 (Sprint Planning/Daily Scrum mentions).

### Row 102 — ooc-in-scope · conditional · trap –
Q: I'm in Japan and moving apartments soon. Do we get any extra leave for moving house?
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -i 'moving (day|house|leave)|relocation leave|house ?move|moving'` over total-rewards/benefits, people-group/time-off-and-absence, entity → 2 hits: total-rewards/benefits/general-and-entity-benefits/france-sas.md L348 (EU link text "moving-working-europe") and total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md L126 ("Moving to a different state" as a US benefits qualifying event). Neither is leave.
- `grep '^#' total-rewards/benefits/general-and-entity-benefits/gitlab-gk.md` + `rg -i 'leave' total-rewards/benefits/general-and-entity-benefits/gitlab-gk.md` → Japan leaves: annual/vacation (L185), sick (L203–221), maternity, child care, child nursing care, family care, nursing care (L170–174), menstrual and civil rights (L228–230). No moving leave.
- `rg -i 'relocation'` → people-group/relocation.md covers changing country/location for comp/contract purposes, not leave.
- people-group/time-off-and-absence/* types (PTO, Public Holiday, Sick, Caregiver, Bereavement, Volunteer, Civic; Parental, Emergency, Military) → no moving leave. Emergency Leave covers disasters/catastrophes only (people-group/time-off-and-absence/leave-types.md L95).
confirmed: nothing in pin answers it
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — no change
notes: A helpful answer may point to Flexible PTO (people-group/time-off-and-absence/time-off-types.md L17), but "extra leave for moving" isn't in the pin. Distractors: Japan "Other Protected Leave" (total-rewards/benefits/general-and-entity-benefits/gitlab-gk.md L226–230) and Emergency Leave.

### Row 110 — ooc-in-scope · process · trap –
Q: Manager question: what's the process for requesting a retention bonus for someone on my team who has a competing offer?
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -il "retention (bonus|award|grant|equity)"` → 1 file: acquisitions/acquisition-process/_index.md (L151, retention bonuses in an acquisition term sheet; not for team members)
- `rg -il "counter.?offer"` → 0
- `rg -il "competing offer"` → 0
- `rg -il retention total-rewards people-group` → 4 files: people analytics (retention rate metric, data retention), people-group/talent-assessment.md L900–901 ("retention issue / retention strategy needed", no process), people-group/engagement.md (Summit)
- `rg -iln "off-cycle|out of cycle|off cycle" total-rewards people-group` → total-rewards/compensation/_index.md "Internal Moves" L104–106, people-group/promotions-transfers.md L316–318 (off-cycle promotions; not retention)
confirmed: nothing in pin answers
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — no change
notes: Distractors: discretionary bonuses (total-rewards/incentives.md § "Process for Recommending a Team Member for a Discretionary Bonus" L200 onward), interim bonuses (total-rewards/incentives.md L13–85), off-cycle promotion approvals (people-group/promotions-transfers.md L316–318). A system that answers with the discretionary-bonus process is wrong.

### Row 111 — ooc-in-scope · list · trap –
Q: who else is starting in my onboarding cohort this month?
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -l -i "cohort"` → 68 files: Elevate/ElevatePrep L&D cohorts, Directs-Group cohorts, internship guidance. No new-hire roster.
- `rg -i "new hires? (this|starting this) (month|week)"` → 0 files
- `rg -i "who (else )?is starting"` → 0 files
- `rg -i "new_team_members|#new-team-members|team-member-updates"` → 18 files. communication/chat.md L31/L37 and people-group/general-onboarding/_index.md L62/L67 describe channels where new hires introduce themselves or arrivals are announced. They are channels, not a list of names.
- people-group/general-onboarding/_index.md § "TaNewKi Welcome Call" L24 (a pre-onboarding call to meet other soon-to-onboard team members), which is a way to meet them, not a roster.
confirmed: nothing in pin answers
ref_source: llm-draft, reviewed
decision: owner 2026-10-16 — stays ooc-in-scope (asks for personal state the pin can't hold); notes reworded: helpful additions fail exact match.
notes: The answer requires live personnel data, which can't be in the handbook. Adding a pointer (`#new_team_members`, TaNewKi call) to the refusal fails exact match; diagnostic label `abstain+extra`. Distractor: Elevate "cohort" pages.

### Row 112 — ooc-in-scope · single-fact · trap –
Q: do i still have admin rights on the AWS sandbox acct
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -i "aws sandbox|sandbox (aws )?account"` → 13 files; company/infrastructure-standards/realms/sandbox/_index.md is the main page
- `rg -i "sandbox cloud|sandbox realm"` → 50 files (infrastructure-standards, gitlabsandbox.cloud)
- `rg -i "AdministratorAccess|admin (rights|access|role).{0,40}(aws|sandbox)|(aws|sandbox).{0,40}admin (rights|access|role)"` → 2 files. **company/infrastructure-standards/realms/sandbox/_index.md L121** (see FLAG); security/corporate/systems/_index.md Sysadmin AR links (production AWS, not sandbox)
confirmed: nothing in pin answers the question as asked
decision: owner 2026-10-15 — keep ooc-in-scope; nearby excerpts below are distractors.
distractors: "Your IAM user account has `AdministratorAccess` to be able to perform any action inside of your AWS account. We do not provide team members access to the `root` user account..." (company/infrastructure-standards/realms/sandbox/_index.md § "Accessing your AWS Account" L121); individual sandbox accounts are deprovisioned automatically via Okta on departure (§ "Individual accounts" L207) with a 90-day AWS grace period (L205). The pin can't say whether this user still has access.
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — no change
notes: "acct" is an abbreviation (D4). Distractors: the Admin (Black) Accounts AWS Admin AR template (eta/corporate-it/end-user-services/access-requests/_index.md L88) for corporate AWS admin, and the GCP project "Owner" role (sandbox L128).

### Row 113 — ooc-in-scope · single-fact · trap –
Q: What's next year's hiring plan for the Support team — how many roles are opening?
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -il "hiring plan"` → 13 files; Support ones: support/managers/hiring.md, support/readiness/_index.md; no counts
- `rg -il "headcount plan"` → 9 files; none give Support role counts
- `rg -in "(hiring plan|headcount).{0,80}support|support.{0,80}(hiring plan|headcount)"` → support/managers/hiring.md L81, L85; support/readiness/_index.md L19; security headcount ratio (security/working-in-security.md L7)
- `rg -il "next year.{0,40}(hiring|headcount)"` → 0
- `rg -in "FY2[78].{0,60}(headcount|hiring|roles|hire)"` → 1 unrelated (marketing UserGems campaign)
confirmed: nothing in pin answers (no role count for any year)
ref_source: llm-draft, reviewed
decision: owner 2026-10-16 — stays ooc-in-scope (no role count anywhere in the pin; only the process is documented).
notes: Known distractors (owner decision 2026-10-15): support/managers/hiring.md § "Hiring Plan" L79–81 (VP of Customer Support is DRI; allocates headcount to regions and approximate hiring dates) and § "Vacancies" L83–85 (internal-only Support Hiring Report - Hiring Plan); support/readiness/_index.md § "Hiring Plan" L17–22 (Support Ops ratios 40 Support Engineers : 1 Support Ops Specialist; 10 Specialists : 1 Manager). Owner's note said "Hiring Plan" 79–85; L83–85 is actually under the "Vacancies" heading.

### Row 115 — ooc-off-topic · process · trap –
Q: I'm a backend dev - my python script throws a KeyError when i read a dict from a JSON file, how do i fix it?
expected: "Sorry, I don't know how to answer that."
searches:
- `rg -l 'KeyError'` → 2 files. enterprise-data/platform/ci-jobs/index.md L20 is about a CI/CD variable missing in the data team's pipeline settings. enterprise-data/platform/python-guide.md L861 is an `except KeyError` code sample in the data team's style guide. Neither is general Python debugging help.
- `rg -l -i 'json\.load'` → 1 file (enterprise-data/platform/snowflake/snowpipe/index.md), unrelated.
confirmed: nothing in pin answers. General programming help is off-topic; the KeyError hits are lexical distractors.
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — added distractor headings/lines in notes
notes: Distractors: enterprise-data/platform/ci-jobs/index.md § "Variable Name not found in the CI Pipeline job" L18–22 (KeyError from an undefined CI/CD variable, not a JSON dict fix); enterprise-data/platform/python-guide.md L849–862 (`except KeyError` sample).

### Row 116 — ooc-off-topic · conditional · trap –
Q: How does Google's 20% time work — do engineers there still get it?
expected: "Sorry, I don't know how to answer that."
searches:
- `rg -n -i '20% time|20 percent time|twenty percent'` → 4 hits: company/stewardship.md L160–162 (GitLab doesn't implement "20% time"; links a Business Insider article on Google's 20% policy, calling it "really 120% time"); company/structure.md L202 ("We don't have explicit 20% time at GitLab"); people-group/learning-and-development/internship-for-learning.md L16; customer-experience/csm/csm-internship.md L20 (intern time commitment).
- `rg -n -i 'google.{0,40}20 ?%'` → no relevant hits (Google Cloud URLs only).
confirmed: nothing in pin answers. The pin never describes how Google's 20% time works or whether Google engineers still get it. FLAG (distractor): company/stewardship.md § "How We Think About Contributing More To Open Source" L158–162 references Google's policy only through a link, and company/structure.md § "Management group" L202 covers GitLab's own stance. A model may wrongly answer about GitLab or paraphrase the link. people-group/learning-and-development/internship-for-learning.md L16 ("10% time and 20% time are reasonably common") is generic, not Google-specific.
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — added internship-for-learning.md L16 distractor note; no other change

### Row 117 — ooc-off-topic · single-fact · trap –
Q: Write a haiku about Monday mornings.
expected: "Sorry, I don't know how to answer that."
searches:
- `rg -n -i 'haiku'` → 4 hits: Claude Haiku model references (support/ai/ai-tool-selection.md L99, support/ai/using-ai-in-support.md L125, L133) and a DNS-haiku link in engineering/readmes/ben-king.md L64. None relevant.
- `rg -n -i 'monday morning'` → scheduled-job timing (e.g. business-technology/how-we-work/rolly/index.md L14). Irrelevant.
confirmed: nothing in pin answers. This is a creative-writing request, off-topic.
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — no change

## 5. Cut (owner, 2026-10-15)

### Row 1 — lookup · single-fact · trap –
cut: owner 2026-10-15 — expenses distractors already covered by 9
Q: whats the limit on a work dinner i can expense
expected_docs: finance/expenses.md
citation: "Meals with Clients and Partners" (finance/expenses.md); "Traveling: Team Events and Meals" (finance/expenses.md); "Meals: Company Provided while Traveling" (finance/expenses.md)
facts:
- F1. [variant: dinner with clients/partners] The limit is $80 per person per meal. — finance/expenses.md § "Meals with Clients and Partners" L557–557
- F2. [variant: team meal/event while traveling] The limit is $80 per person per meal. — finance/expenses.md § "Traveling: Team Events and Meals" L245–245
- F3. [variant: your own meals while traveling on company business] Meals are reimbursable up to $120 USD (or local equivalent) per day. — finance/expenses.md § "Meals: Company Provided while Traveling" L231–231
- F4. Tips up to 20% are acceptable but must be included in the final price, within the policy limit. — finance/expenses.md § "Traveling: Team Events and Meals" L246–246
- F5. Limits are in USD; use the local-currency equivalent. — finance/expenses.md § "4. PROCEDURES" L101–101
flag: none
ref_source: llm-draft, unreviewed
notes: The scope is ambiguous: "work dinner" could mean a client dinner, a team dinner while traveling, or your own dinner on a trip. A correct answer gives $80 per person per meal for client/team meals and may add the $120/day travel meal cap. Distractors: legal/policies/gifts-contributions.md L53 (an $80 cap per person per event for foreign *government officials*, which is a different rule; client meals with government officials are prohibited outright, per finance/expenses.md L555); "Team Building" L637 (the amount depends on the department budget); "Team Member Significant Life Events and Team Member Gifts" ($125 gifts).

### Row 6 — synthesis · process · trap –
cut: owner 2026-10-15 — too broad to grade
Q: starting monday, what should i actually get done in my first week
expected_docs: people-group/general-onboarding/tanewki-tips.md, people-group/general-onboarding/_index.md, company/culture/all-remote/onboarding.md
citation: "Getting Started" (people-group/general-onboarding/tanewki-tips.md); "Navigating Onboarding" (people-group/general-onboarding/tanewki-tips.md); "What are onboarding activities?" (company/culture/all-remote/onboarding.md); "Slack Channel Support for New Team Members" (people-group/general-onboarding/_index.md)
facts:
- F1. On day 1, activate your Okta account from the Okta email, set up your laptop (Mac or Linux steps), register your GitLab username via the welcome email, then open your personalized onboarding issue and activate 1Password. — people-group/general-onboarding/tanewki-tips.md § "Getting Started" L44–50
- F2. Work through the onboarding issue. It is self-paced, but items marked 🔴 must be completed on their assigned day. — people-group/general-onboarding/tanewki-tips.md § "Navigating Onboarding" L54–54
- F3. A sample first-week sequence: Day 1 accounts and paperwork, Day 2 remote working and values, Day 3 security and compliance, Day 4 social and benefits, Day 5 Git. — company/culture/all-remote/onboarding.md § "What are onboarding activities?" L140–144
- F4. Don't expect to contribute heavily. Take at least two full weeks for onboarding and start team-specific onboarding in week three. — people-group/general-onboarding/_index.md (intro, no heading) L8–8
- F5. On Day 2 an Access Request for your baseline entitlements is generated (if a template exists for your role). — people-group/general-onboarding/_index.md (intro, no heading) L18–18
- F6. Introduce yourself in `#new_team_members`; you are added to it from day 1. — people-group/general-onboarding/_index.md § "Slack Channel Support for New Team Members" L60–62
flag: none
ref_source: llm-draft, unreviewed
notes: F4 and F5 sit before the first heading of people-group/general-onboarding/_index.md, so they carry no heading; cite the page title "GitLab Onboarding". Other optional true details: onboarding buddy support (L16), and Navan access arrives in week one (people-group/general-onboarding/tanewki-tips.md L134). Distractor: role-specific onboarding pages (engineering/workflow/developer-onboarding, sales/onboarding).

### Row 15 — lookup · conditional · trap –
cut: owner 2026-10-15 — recoded row, weak inference-based answer
Recoded from ooc-in-scope, 2026-10-15 (D1 lookup, D2 short-section). The core fact is on one page; the Brazil facts are supporting.
Q: do we get a cost of living stipend in brazil?
expected_docs: total-rewards/compensation/_index.md, total-rewards/benefits/general-and-entity-benefits/remote-com.md
citation: "Market-Aligned Compensation Ranges" (total-rewards/compensation/_index.md); "Brazil 🇧🇷" (total-rewards/benefits/general-and-entity-benefits/remote-com.md)
facts:
- F1. No: no cost-of-living stipend is described. GitLab pays local market rates based on cost of labor, not cost of living. — total-rewards/compensation/_index.md § "Market-Aligned Compensation Ranges" L132
- F2. [variant: Brazil] Brazil team members' benefits are administered by Remote. — total-rewards/benefits/general-and-entity-benefits/remote-com.md § "Brazil 🇧🇷" L20
- F3. [variant: Brazil] Brazil benefits include a monthly meal voucher and a grocery card (for monthly gross salary of 6,189.94 BRL or less); no cost-of-living item is listed. — total-rewards/benefits/general-and-entity-benefits/remote-com.md § "Brazil 🇧🇷" L72–81
ref_source: llm-draft, unreviewed
notes: Distractors: the new-hire home-office stipend (finance/expenses.md L417) and all-remote essays on moving somewhere cheaper (company/culture/all-remote/getting-started.md L84, company/culture/all-remote/remote-benefits.md L56).

### Row 28 — lookup · single-fact · trap –
cut: owner 2026-10-15 — lower priority; travel covered by 34
Q: Which travel agency or booking tool should I use for my team's business travel?
expected_docs: finance/expenses.md
citation: "Airfare" (finance/expenses.md); "Hotels" (finance/expenses.md); "Requesting Delegate Access to Book for Another Team Member" (business-technology/enterprise-applications/guides/navan-expense-guide/_index.md)
facts:
- F1. Use Navan. All business flights must be booked through Navan and are paid by the GitLab travel card, even if a cheaper fare exists elsewhere. — finance/expenses.md § "Airfare" L107–107
- F2. Hotels should also be booked through Navan Travel, where GitLab pays room and taxes via a central virtual card. — finance/expenses.md § "Hotels" L194–194
- F3. Anything booked outside Navan is flagged Out of Policy and needs manager and AP review or approval. — finance/expenses.md § "Advance Purchase" L115–115; § "Hotels" L199–199
- F4. To book for teammates, request delegate access in Navan (Profile → Delegate info → "I book travel for these users"); the teammate approves. — business-technology/enterprise-applications/guides/navan-expense-guide/_index.md § "Requesting Delegate Access to Book for Another Team Member" L525–527
- F5. [variant: internal events such as SKO or Summit] Follow that event's specific travel guidelines. — finance/expenses.md § "Internal Conferences and Meetings" L298–298
flag: none
ref_source: llm-draft, unreviewed
notes: Navan is also called "Navan Tripactions" (L783). Access is through the Okta Navan tile (L761). Distractors: Zip/Coupa virtual-card guides (procurement, not travel) and CEO Shadow lodging booked by the Executive Admin (ceo/shadow.md L626).

### Row 29 — lookup · conditional · trap –
cut: owner 2026-10-15 — time off over-represented
Q: public holidays in india - which ones do we get off
expected_docs: people-group/time-off-and-absence/time-off-types.md
citation: "Overview" under "Public Holiday" (people-group/time-off-and-absence/time-off-types.md); "General List of Public Holidays" (people-group/time-off-and-absence/time-off-types.md)
facts:
- F1. GitLab does not pre-load a fixed set of public holidays in Workday. Team members choose which public holidays they take, up to their balance. — people-group/time-off-and-absence/time-off-types.md § "Overview" L53
- F2. Each team member has a country-specific public holiday balance in Workday, based on local and/or contractual requirements and reviewed annually. — people-group/time-off-and-absence/time-off-types.md § "Overview" L55–57
- F3. Unused public holiday balance must be used within the calendar year and does not roll over. — people-group/time-off-and-absence/time-off-types.md § "Overview" L58
- F4. For a list of a country's public holidays (e.g. India), use timeanddate.com: Holidays Worldwide → your country → "Public Holidays". — people-group/time-off-and-absence/time-off-types.md § "General List of Public Holidays" L66–71
- F5. The handbook does not list specific Indian public holidays or say how large the India balance is. — (absence; entity/india-pvt-ltd.md § "India Specific Leave" L258–331 covers earned, sick, casual and parental leave only)
flag: none
ref_source: llm-draft, unreviewed
notes: An answer that lists Indian holidays (Republic Day, Diwali, etc.) is answering from model memory and should fail. Distractors: support/support-time-off.md L218 lists "Republic Day (26-January)" as a peak holiday for Support coverage, and support/apac.md L302 lists "India Republic Day". Neither is an entitlement list. India-specific: scheduled time off must be entered 30 days ahead (entity/india-pvt-ltd.md § "India Specific Leave" L262), and public holidays are logged as full days only (people-group/time-off-and-absence/time-off-types.md L93). Both are optional extras.

### Row 33 — synthesis · conditional · trap –
cut: owner 2026-10-15 — weaker than 5 for the conditional synthesis slot
Q: Does the comp review process differ between job families? Asking as a manager prepping for it.
expected_docs: total-rewards/compensation/compensation-review-cycle/_index.md, total-rewards/compensation/_index.md
citation: "Process overview", "Equity" (total-rewards/compensation/compensation-review-cycle/_index.md); "Annual Compensation Review (ACR)", "Director+Bonuses", "Sales Commissions", "Market Data Segmentation" (total-rewards/compensation/_index.md)
facts:
- F1. The Annual Compensation Review (ACR) is a single company-wide review held once a year, effective May 1. The same process applies across job families: talent ratings finalized → ACR launches in Workday → managers propose → executives review → Total Rewards pay equity audit → Comp Group approval → managers inform reports. — total-rewards/compensation/_index.md § "Annual Compensation Review (ACR)" L77–79; total-rewards/compensation/compensation-review-cycle/_index.md § "Process overview" L24–43
- F2. [variant: sales roles] Sales roles are paid as On-Target Earnings (OTE): base plus a commission target tied to quota. The base/commission split varies by role. — total-rewards/compensation/_index.md § "Sales Commissions" L41
- F3. [variant: Director+] Directors and above (except those on a sales commission plan) have a semi-annual bonus target set as a percentage of base salary. — total-rewards/compensation/_index.md § "Director+Bonuses" L33
- F4. Market positioning differs by role: most roles target the 50th percentile, critical technical roles the 75th. — total-rewards/compensation/_index.md § "Market Data Segmentation" L156
- F5. Equity refresh budget is held at Director+ level. Managers below Director don't plan equity in Workday, but should discuss recommendations with their Directors. — total-rewards/compensation/compensation-review-cycle/_index.md § "Equity" L71
flag: none
ref_source: llm-draft, unreviewed
notes: The FY27 budget is 3.5% of TTC for all countries except India at 7% (L61). That's a country difference, not a job-family one; acceptable as context. Both pages defer to "the Loop" for current details (compensation-review-cycle L6, L75; compensation L87). The difference by role is about level and sales vs. non-sales, not job family as such. A correct answer says the process is the same and the pay structure differs. Distractor: the "Sales Development Process" (people-group/promotions-transfers.md L102) is a monthly promotion review, not comp review.

### Row 37 — synthesis · single-fact · trap –
cut: owner 2026-10-15 — single fact, not real synthesis
Q: why is gitlab so big on writing stuff in the handbook first?
expected_docs: about/handbook-usage.md, company/culture/all-remote/handbook-first.md, values/_index.md
citation: "Why handbook first" (about/handbook-usage.md); "Why does handbook-first matter?" (company/culture/all-remote/handbook-first.md); "Write things down", "Single Source of Truth" (values/_index.md)
facts:
- F1. Documenting in the handbook first takes more time at the start but saves time in the long run. It is essential to GitLab's ability to keep scaling and adapting. — about/handbook-usage.md § "Why handbook first" L16
- F2. Changes are communicated through a handbook change, not presentations, email, or chat, because those make the context and implications harder to understand. — about/handbook-usage.md § "Why handbook first" L18
- F3. Handbook first means no duplication: the handbook stays up to date and others can contribute more easily. — about/handbook-usage.md § "Why handbook first" L20
- F4. The handbook gives everyone a single source of truth, so people don't have to keep asking for the same information, which makes the company more efficient. — company/culture/all-remote/handbook-first.md § "Why does handbook-first matter?" L34; values/_index.md § "Single Source of Truth" L841
- F5. [rewording: which value] It is tied to the values of Transparency (single source of truth, public handbook first) and Efficiency ("Write things down": reading a document is more efficient than asking). The handbook-usage page says it supports transparency, efficiency, and results. — about/handbook-usage.md § "Why handbook first" L22; values/_index.md § "Write things down" L344–346
flag: none
ref_source: llm-draft, unreviewed
notes: Sid's "brick laying" quote (about/handbook-usage.md L32–44) is a good supporting excerpt. Distractor: company/culture/all-remote/the-gitlab-test-remote-work.md L65 (a test for other companies).

### Row 39 — synthesis · conditional · trap –
cut: owner 2026-10-15 — overlaps 32
Q: Are there entity-specific differences in the expense policy for team members employed through the UK entity?
expected_docs: finance/expenses.md, total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md
citation: "Internet" (finance/expenses.md); "3. General Guidelines" (finance/expenses.md); "Legal entities" (finance/expenses.md); "How Mileage Rates are Based" (finance/expenses.md); "Vision" (total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md)
facts:
- F1. Mostly no. UK team members follow the global Travel & Expense policy, with a few UK-specific points (F2–F5). — finance/expenses.md § "1. POLICY" L10–10 (global scope)
- F2. Home internet reimbursement is a taxable expense for GitLab Ltd (UK) team members, on the assumption the connection is partly personal. — finance/expenses.md § "Internet" L508–508
- F3. As non-US team members, UK staff must provide receipts for all expenses (the US-only $50 receipt threshold does not apply). — finance/expenses.md § "3. General Guidelines" L53–53
- F4. GitLab Ltd (UK) expenses are reimbursed via Navan within 7 business days (in policy) or after AP approval (out of policy). — finance/expenses.md § "Legal entities" L698–698
- F5. Mileage is reimbursed at your legal entity's rates for the current year. — finance/expenses.md § "How Mileage Rates are Based" L263–263
- F6. UK-specific benefit claims go through Navan: up to £30 for eye exams and £120 for screen-use corrective lenses, after Total Rewards approval via Compass. — total-rewards/benefits/general-and-entity-benefits/ltd-benefits-uk.md § "Vision" L112–121
flag: none
ref_source: llm-draft, unreviewed
notes: F1 is a framing fact; graders may drop it. Distractors: Netherlands and Germany internet carve-outs (finance/expenses.md L505–L514), which are not UK; GitLab LTD (Ireland), which appears in the same entity list as GitLab Ltd (UK).

### Row 45 — contradiction · process · trap T2
cut: owner 2026-10-15 — HelpLab has 0 hits in the pin; ungradable.
Q: What's the HelpLab workflow for requesting access to something?
expected_docs: eta/corporate-it/compass/compass-guide/_index.md, eta/corporate-it/end-user-services/access-requests/_index.md
citation: "How to get help: 3 ways to reach Compass" (eta/corporate-it/compass/compass-guide/_index.md); "What Compass can resolve automatically" (same); "Requesting Access in Lumos" / "Create an access request" (eta/corporate-it/end-user-services/access-requests/_index.md)
facts:
- F1. "HelpLab" does not appear anywhere in the pin. The current support tool is called Compass (GitLab's internal name for the Serval platform). — eta/corporate-it/compass/compass-guide/_index.md § "What is Compass?" L18–18
- F2. [Compass route] Request access via the Compass Slack app DM, the Compass portal/Okta tile, or email (it_help@gitlab.com) as a fallback. — eta/corporate-it/compass/compass-guide/_index.md § "How to get help: 3 ways to reach Compass" L68–72
- F3. [Compass route] For app access requests, Compass grants time-bound access via Okta SSO or direct provisioning, based on your team's policy. — eta/corporate-it/compass/compass-guide/_index.md § "What Compass can resolve automatically" L109–109
- F4. [Lumos route] Most access requests are made in the Lumos App Store. Lumos routes the request to your manager, the system owner and other approvers, and auto-provisions where automation exists. — eta/corporate-it/end-user-services/access-requests/_index.md § "Requesting Access in Lumos" L17–17
- F5. [Lumos route] Open Lumos from Okta or Slack, select the app, and give who it's for, the permission, the access length and a business justification. Track status in the Lumos Slack app's Messages tab. — eta/corporate-it/end-user-services/access-requests/_index.md § "Create an access request" L21–27; § "Check the status of a request" L33–33
- F6. Apps not yet in Lumos use the access-request issue templates. — eta/corporate-it/end-user-services/access-requests/_index.md § "Approve a request" L39–39
conflict:
- A: "One place for access requests | Submit and track access requests directly through Compass instead of separate tools." — eta/corporate-it/compass/compass-guide/_index.md § "What you gain" L41–41; currency evidence: bee431b547 2026-09-13 (page created in this commit, "Rename HelpLab to Compass across handbook content"; the deleted helplab-guide did not mention access requests)
- B: "Most access requests are now made through the [Lumos App Store](https://app.lumosidentity.com/app_store) rather than by opening an issue." — eta/corporate-it/end-user-services/access-requests/_index.md § "Requesting Access in Lumos" L17–17; currency evidence: 8f22e33fea 2026-07-28
- current: unresolved, leaning A. The Compass guide is newer (2026-09-13) and claims to replace separate access-request tools. But the access-requests page, a controlled document, still names Lumos, and the two pages may describe a front end (Compass) and a back end (Lumos) rather than true alternatives.
flag: trap T2. Old name: "HelpLab" has zero hits in the pin. The HelpLab→Compass mapping is evidenced only by git history (commit message bee431b547), not by pin text, so a model can't map the old name from the corpus alone. Compass vs Lumos is a real conflict in the pin.
ref_source: llm-draft, unreviewed
notes: An acceptable answer either says HelpLab isn't in the handbook excerpts, or describes the Compass and/or Lumos workflow and notes that the two pages conflict. Distractors: security/corporate/systems/lumos/ar/_index.md (the full Lumos guide, consistent with B), the issue-template workflow in eta/corporate-it/end-user-services/access-requests/access-requests/_index.md, and company/infrastructure-standards/tutorials/groups/access-request.md.

### Row 54 — recency · list · trap T6
cut: owner 2026-10-15 — near-duplicate of 44 (44 is contradiction, must stay)
Q: customer success - what teams are in it
expected_docs: customer-experience/_index.md
citation: "Customer Experience Teams", "Digital Strategy", "Demo Systems" (customer-experience/_index.md)
facts:
- F1. Customer Success is now called Customer Experience (CX), a department within the Sales function. — customer-experience/_index.md (intro) L2, L6
- F2. The Customer Success Managers (CSM) team is part of it. — customer-experience/_index.md § "Customer Experience Teams" L31
- F3. The Customer Success Engineers (CSE) team is part of it. — customer-experience/_index.md § "Customer Experience Teams" L32
- F4. The Customer Success Architects (CSA) team is part of it. — customer-experience/_index.md § "Customer Experience Teams" L33
- F5. The Renewals Managers team is part of it. — customer-experience/_index.md § "Customer Experience Teams" L34
- F6. The CX index also lists Digital Strategy and Demo Systems. — customer-experience/_index.md § "Digital Strategy" L38; § "Demo Systems" L42
conflict:
- A: "[VP, Customer Success]" listed among those reporting to the CRO — sales/_index.md § "Who We Are" L75, L80; "The different groups within CX also have standing meetings, including meetings for the Customer Success teams and Renewal Managers…" — customer-experience/_index.md § "Customer Experience Meetings" L165; currency evidence: 968e3521af 2026-09-24
- B: "The Customer Experience department is part of the [GitLab Sales](/handbook/sales/) function…" — customer-experience/_index.md (intro) L6; currency evidence: 968e3521af 2026-09-24 "Rename Customer Success handbook to Customer Experience, delete the stale CX handbook"
- current: B. The department is Customer Experience, per the rename commit. "Customer Success" survives in pinned text as role and sub-team names (CSM/CSE/CSA), so a mapping answer is correct.
flag: T6 trap. Owner review requested: both names are used throughout the pin (≈303 files mention "Customer Success", 20 mention "Customer Experience"). Whether Digital Strategy / Demo Systems / Professional Services count as CX "teams" is ambiguous.
ref_source: llm-draft, unreviewed
notes: Distractors: customer-experience/apj-customer-success.md (one regional team); sales/field-operations/customer-success-operations/ (CS Ops sits under Field Operations); customer-experience/professional-services-engineering/ (in the CX directory, but roles-overview treats PS as distinct from "Customer Success roles", L26).

### Row 56 — lookup · single-fact · trap –
cut: owner 2026-10-15 — duplicate of 9
Q: how much do we get back for internet now? I'm in canada
expected_docs: finance/expenses.md
citation: "Internet" (finance/expenses.md); "4. PROCEDURES" (finance/expenses.md)
facts:
- F1. Home internet is capped at $100 per month; claims above that are not reimbursed and exceptions are no longer assessed at claim time. — finance/expenses.md § "Internet" L509–509
- F2. Limits are in USD; Canadian team members use the CAD equivalent. — finance/expenses.md § "4. PROCEDURES" L101–101
- F3. Only monthly service charges are covered, with an itemized receipt. No setup, equipment, router or extender costs. Bundled bills are pro-rated to the internet portion. — finance/expenses.md § "Internet" L503–503, L510–512
- F4. There are no Canada-specific carve-outs (special rules exist only for the Netherlands, UK tax and Germany). GitLab Canada Corp expenses are reimbursed via Navan. — finance/expenses.md § "Internet" L505–514; § "Legal entities" L698–698
decision: owner 2026-10-15 — D1 → lookup, trap T7 → none. The pin has only the $100 internet cap (finance/expenses.md L509); the $80 cap exists only in git history.
ref_source: llm-draft, unreviewed
notes: Distractors: total-rewards/benefits/general-and-entity-benefits/canada-corp-benefits.md (no internet content), the $50/day "Internet - Travelling" limit (L306), the $80 meal limits (L245, L557), and the "Co-Working Space" rule against claiming home internet in a month with full-month coworking (L381/L513). Also "Phone Service" (finance/expenses.md L591) has the same "$100" sentence; a model may conflate it with internet.

### Row 61 — synthesis · list · trap –
cut: owner 2026-10-15 — recoded row, answer spread over many leave types
Recoded from ooc-in-scope, 2026-10-15 (D1 synthesis, D2 several-pages).
Q: What are the eligibility criteria for a sabbatical or leave of absence?
expected_docs: people-policies/leave-of-absence/_index.md, people-policies/leave-of-absence/us.md, people-group/time-off-and-absence/leave-types.md, people-group/time-off-and-absence/time-off-types.md, total-rewards/benefits/general-and-entity-benefits/global-expansion.md
citation: "Company-Wide Leave of Absence Policies" (people-policies/leave-of-absence/_index.md); "Which leave is right for me?" (people-policies/leave-of-absence/us.md); "Eligibility, Entitlement and Planning Your Leave" (people-group/time-off-and-absence/leave-types.md); "Overview" (people-group/time-off-and-absence/time-off-types.md); "United Arab Emirates 🇦🇪" (total-rewards/benefits/general-and-entity-benefits/global-expansion.md)
facts:
- F1. There is no general sabbatical policy. The only sabbatical in the handbook is UAE statutory paid sabbatical leave for Emirati citizens doing national service. — total-rewards/benefits/general-and-entity-benefits/global-expansion.md § "United Arab Emirates 🇦🇪" L762–764
- F2. Leave of absence covers recovering from your own serious health condition, caring for a family member with one, bonding with a new child, and military service. — people-policies/leave-of-absence/_index.md § "Company-Wide Leave of Absence Policies" L8
- F3. [variant: US] FMLA eligibility: 1 year of service and 1,250 hours worked in the year before the leave. — people-policies/leave-of-absence/us.md § "Which leave is right for me?" L31
- F4. [variant: US, California] CFRA eligibility: the same 1 year of service and 1,250 hours. — people-policies/leave-of-absence/us.md § "Which leave is right for me?" L32
- F5. Parental leave is open to all active team members who become a parent while at GitLab, from the first day of employment. — people-group/time-off-and-absence/leave-types.md § "Eligibility, Entitlement and Planning Your Leave" L12
- F6. Time off over 25 consecutive calendar days needs special approval from your manager, People Business Partner and the Absence Management Team. — people-group/time-off-and-absence/time-off-types.md § "Overview" L18
ref_source: llm-draft, unreviewed
notes: The UAE sabbatical fact (F1) was found during recoding; the earlier draft said the pin has no sabbatical at all. The leave-of-absence page's country-to-provider list (L28–29) is stale (see row 58). Graders may accept F3/F4 as one fact.

### Row 62 — ooc-in-scope · process · trap –
Q: how do i enroll my personal phone in device management as a contractor?
cut: owner 2026-10-16 — the pin partly answers (phones are enrolled in Okta Verify and must pass Okta posture checks; MDM is for GitLab laptops), so a reasonable answer would fail the exact-string check; out-of-corpus rule: partial → cut. Found in the 8-row sample review.
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -i "personal (phone|mobile|device)"` → 16 files. Nearest: finance/procurement/tips-for-submitting-a-zip-request.md L116 ("Access to GitLab resources via personal devices is not permitted. Is the contingent worker issued a vendor-managed laptop?") and people-group/acceptable-use-policy.md § "Personal Mobile Phone and Tablet Usage" L133 (personal mobiles accessing GitLab data must be passcode-enabled and patched; 2FA enforced for employee and contractor accounts)
- `rg -i "BYOD|bring your own device"` → 5 files; people-group/acceptable-use-policy.md § "Bring-Your-Own-Device (BYOD)" L125–133 (no MDM enrolment step)
- `rg -i "(mobile|phone).{0,40}(MDM|device management|enroll)"` → 4 files. eta/corporate-it/end-user-services/onboarding101/onboarding-mobile-devices.md L5 (to use Okta apps on a mobile device, enroll it in **Okta Verify** and save a passkey, which is not MDM); eta/corporate-it/end-user-services/laptop-management/laptop-security/management/_index.md § "Mobile Device Management (MDM)" L13–23 (MDM covers GitLab-purchased devices; "Your personal laptop should not be enrolled in MDM")
- `rg -i "(MDM|enroll).{0,60}(mobile|phone|iOS|android)"` → 3 files (Jamf laptop enrolment, Okta Verify help). No phone MDM enrolment procedure.
- `rg -i "contractor.{0,80}(device|phone|laptop|MDM|enroll)"` → 2 files (physical-security standard scope; hiring-contractors laptop requirement). No phone enrolment procedure.
confirmed: nothing in pin answers the question as asked
decision: owner 2026-10-15 — keep ooc-in-scope; nearby excerpts below are distractors.
distractors: "Your personal laptop should not be enrolled in MDM, and cannot be used for accessing GitLab accounts or business data." (eta/corporate-it/end-user-services/laptop-management/laptop-security/management/_index.md § "Mobile Device Management (MDM)" L23); "the device needs to be enrolled in Okta Verify, and a passkey needs to be saved on the device" (eta/corporate-it/end-user-services/onboarding101/onboarding-mobile-devices.md L5; Okta Verify, not MDM); "Access to GitLab resources via personal devices is not permitted." (finance/procurement/tips-for-submitting-a-zip-request.md § "How to Submit a Zip Request for a Contractor" L116, contingent workers); personal mobile phones must be passcode-enabled and patched (people-group/acceptable-use-policy.md § "Personal Mobile Phone and Tablet Usage" L133).
ref_source: llm-draft, unreviewed
notes: D4 is ambiguous-scope ("contractor" could mean a GitLab contractor via PEO/iiPay or a contingent worker via a vendor). The Okta Verify page is the most likely retrieval and isn't "device management".

### Row 64 — lookup · single-fact · trap –
cut: owner 2026-10-15 — recoded row, no new failure mode
Recoded from ooc-in-scope, 2026-10-15 (D1 lookup, D2 short-section).
Q: is there a dress code i should be enforcing for my team
expected_docs: communication/_index.md
citation: "Video calls" (communication/_index.md)
facts:
- F1. There is no strict dress code policy. — communication/_index.md § "Video calls" L636
- F2. Team members should be properly dressed on all video calls, meaning clothing that covers the top and bottom of the body. — communication/_index.md § "Video calls" L636
- F3. For customer, candidate or partner calls, don't wear or present anything you wouldn't at their office in person. — communication/_index.md § "Video calls" L641
ref_source: llm-draft, unreviewed
notes: "Enforcing" goes beyond the pin: nothing gives managers an enforcement duty. An answer that invents one should fail.

### Row 86 — lookup · single-fact · trap –
cut: owner 2026-10-15 — short-section single fact, easy retrieval, low signal
Q: who's our CEO
expected_docs: ceo/_index.md, eba/_index.md
citation: (front matter) (ceo/_index.md); "Executive Business Administrator Team" (eba/_index.md)
facts:
- F1. GitLab's CEO is Bill Staples. — ceo/_index.md (front matter) L3; eba/_index.md § "Executive Business Administrator Team" L15
flag: none
ref_source: llm-draft, unreviewed
notes: Strong distractor: Sid Sijbrandij, the co-founder, who is called CEO on older pages (e.g. marketing/…/dod12/2019-best-executive.md L19; company/working-groups/tiering.md L24). company/still-a-startup.md L8 calls him GitLab's "then CEO". The CEO's Staff EBA is Jeanne Rotenberry (eba L15). The "CEO" vocabulary matches the handbook; no mapping needed.

### Row 91 — lookup · single-fact · trap –
cut: owner 2026-10-15 — same vocabulary-mapping test as 88
Q: Who is our HR head
expected_docs: eba/_index.md, eba/e-group-scheduling.md
citation: "Executive Business Administrator Team" (eba/_index.md); "Scheduling for Rob Allen, Chief People Officer" (eba/e-group-scheduling.md)
facts:
- F1. The handbook's equivalent of "HR head" is the Chief People Officer (CPO), the C-level executive for the People function. — company/structure.md § "Executives" L147
- F2. The Chief People Officer is Rob Allen. — eba/_index.md § "Executive Business Administrator Team" L29; eba/e-group-scheduling.md § "Scheduling for Rob Allen, Chief People Officer" L38
flag: none
ref_source: llm-draft, unreviewed
notes: Vocabulary mapping: "HR head" → "Chief People Officer" (the People group is GitLab's HR). Distractor: Wendy Barnes, named as Chief People Officer on older pages (company/culture/all-remote/mental-health.md L73; legal/esg/fy23-esg-report.md L109). legal/ethics-compliance-program/_index.md L92 links the CPO to rallen@gitlab.com, which agrees with Rob Allen. Allia McCrank (VP of Total Rewards) and Marcy Tavano (VP People Business Partners) are People VPs, not the head (eba L29–30).

### Row 95 — lookup · single-fact · trap –
cut: owner 2026-10-15 — short-section single fact in handbook terms, low signal
Q: what are family and friends days?
expected_docs: company/family-and-friends-day.md
citation: "What is a Family and Friends Day?" (company/family-and-friends-day.md); "FY'27 Family and Friends Days" (company/family-and-friends-day.md)
facts:
- F1. Family & Friends Days are shared company-wide days off for spending time with family and friends, volunteering, self-care, or anything else. — company/family-and-friends-day.md (front-matter description) L3; § "What is a Family and Friends Day?" L10
- F2. They started in early 2020 to help team members cope with COVID-19 and have been kept as a benefit, in a different form each fiscal year. — company/family-and-friends-day.md § "What is a Family and Friends Day?" L8
- F3. [frequency] There is no fixed cadence. The dates are set per fiscal year; FY27 has four: 2026-12-28, 2026-12-29, 2026-12-30, 2026-12-31. — company/family-and-friends-day.md § "FY'27 Family and Friends Days" L16–21
- F4. If a Family & Friends Day falls on a public holiday, team members are encouraged to use that public holiday on another day within the same calendar year. — company/family-and-friends-day.md § "FY'27 Family and Friends Days" L23
flag: none
ref_source: llm-draft, unreviewed
notes: F1 is mostly from the front-matter description (L3). Body L10 adds that taking the day off is strongly encouraged and sharing in #family-and-friends-day is optional. Distractor/variant: Support keeps operating on those days. In FY26 Support staff could take 4 days at their convenience instead (support/support-time-off.md § "How Support Handles Family and Friends Days" L146–147). For the "how often" rewording: there is no fixed frequency (the FY27 dates are one block of 4 days).

### Row 97 — synthesis · process · trap –
cut: owner 2026-10-15 — time off over-represented
Q: I'm a manager and someone on my team wants three weeks of vacation over the end-of-year holidays. What do I need to check or do before I say yes?
expected_docs: people-group/time-off-and-absence/time-off-types.md, people-group/time-off-and-absence/time-away-philosophy.md
citation: "PTO Protocols (Planning and Coordination)" (people-group/time-off-and-absence/time-off-types.md); "Overview" under "Flexible Paid Time Off (PTO)" (people-group/time-off-and-absence/time-off-types.md)
facts:
- F1. Evaluate the request against team deliverables and business needs, and coordinate cover, especially in popular holiday periods. — people-group/time-off-and-absence/time-off-types.md § "PTO Protocols (Planning and Coordination)" L26–27
- F2. If you need changes, ask within 48 hours and name the goal or result that would be affected. If you can't agree, escalate to your manager's manager. — people-group/time-off-and-absence/time-off-types.md § "PTO Protocols (Planning and Coordination)" L28–29
- F3. Check whether your department has windows when team presence is critical. — people-group/time-off-and-absence/time-off-types.md § "PTO Protocols (Planning and Coordination)" L30
- F4. Make sure there is a coverage plan. Under Flexible PTO, time off is approved once it has been coordinated with the manager and a coverage plan exists. — people-group/time-off-and-absence/time-off-types.md § "Overview" L17
- F5. Check the length: more than 25 consecutive calendar days (including weekends and holidays) needs special permission from the manager, the People Business Partner and the Absence Management Team (leaves@gitlab.com). Three weeks (21 days) is under that threshold unless it runs longer. — people-group/time-off-and-absence/time-off-types.md § "Overview" L18
- F6. Check notice: at least twice as many days as the time off (about 30 business days for 3 weeks). — people-group/time-off-and-absence/time-off-types.md § "PTO Protocols (Planning and Coordination)" L25
flag: none
ref_source: llm-draft, unreviewed
notes: Extra credit: FY27 Family & Friends Days fall on 2026-12-28 to 2026-12-31, inside the end-of-year window (company/family-and-friends-day.md L18–21). The time off must be logged in Workday (people-group/time-off-and-absence/time-off-types.md L37). Manager Toolkit is on The Loop (out of corpus). Distractors: Support's holiday-season process and capacity calendar (support/support-time-off.md L74–82, L155–157), which is team-specific. The entity benefits index says "option to take up to 25 consecutive calendar days" (total-rewards/benefits/general-and-entity-benefits/_index.md L239), which a model might read as a hard cap.

### Row 98 — synthesis · process · trap –
cut: owner 2026-10-15 — time off over-represented
Q: how do i actually log a day off so it shows up for my team, like which tool, and does it need to go on my calendar too
expected_docs: people-group/time-off-and-absence/time-off-types.md, people-group/time-off-and-absence/time-away-philosophy.md
citation: "How to Enter PTO in Workday" (people-group/time-off-and-absence/time-off-types.md); "Workday to Time Off by Deel Integration" (people-group/time-off-and-absence/time-away-philosophy.md); "Calendar and Meeting Management" (people-group/time-off-and-absence/time-away-philosophy.md)
facts:
- F1. Log it in Workday, in the app or through the Workday Slack integration: select the day(s) → "Time-Off" → "Paid Time Off" → optional comment → "Submit". — people-group/time-off-and-absence/time-off-types.md § "How to Enter PTO in Workday" L34–35
- F2. Workday is the single source of truth. All team members, including PEO staff and independent contractors, must log time away there. — people-group/time-off-and-absence/time-away-philosophy.md § "Overview" L187–189
- F3. Workday entries flow to Time Off by Deel, which syncs to your Google Calendar and Slack. Managers get calendar invites to track team absences. — people-group/time-off-and-absence/time-away-philosophy.md § "Workday to Time Off by Deel Integration" L201–203
- F4. You don't need to add the time off to your calendar by hand, but you still need to decline meetings you'll miss; the OOO event doesn't auto-decline them. — people-group/time-off-and-absence/time-away-philosophy.md § "Calendar and Meeting Management" L93
- F5. Teammates can see who's out via Time Off by Deel in Slack → "Who's Out?". — people-group/time-off-and-absence/time-away-philosophy.md § "Checking Team Availability" L230–232
- F6. Time Off by Deel doesn't sync with GitLab.com. For absences over 48 hours, set your GitLab.com status by hand. — people-group/time-off-and-absence/time-away-philosophy.md § "Time Off by Deel Features" L220
flag: none
ref_source: llm-draft, unreviewed
notes: Optional extras: Gmail out-of-office reply and team scheduling calendar if your team has one (people-group/time-off-and-absence/time-away-philosophy.md § "Communication Checklist" L81, L85). Distractor: Support's own OOO calendars and the Support rule that under half a day needs no Workday entry (support/support-time-off.md L24, L94). Unplanned absences say Slack/Calendar update "should occur automatically" with the Deel integration (L154), which agrees with F3.

### Row 101 — ooc-in-scope · single-fact · trap –
cut: owner 2026-10-15 — partial answer in pin; ungradable as ooc.
Q: can i buy extra vacation days or sell back the ones i didnt use
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -i 'buy (extra|additional) (vacation|days|holiday)|purchase (additional|extra) (vacation|leave|days)'` → 0 hits. No leave-purchase scheme.
- `rg -i 'sell (back|unused)'` → 0 hits.
- `rg -i 'encash'` → 4 hits, all entity/india-pvt-ltd.md (L268–269, L317, L319).
- `rg -i 'paid out|payout' | rg -i 'vacation|leave|pto|holiday'` → total-rewards/benefits/general-and-entity-benefits/pty-benefits-new-zealand.md L189 (sick leave not paid out). people-group/time-off-and-absence/time-off-types.md L119: sick time not paid out on termination.
- `rg -i 'payment (for|of) unused|unused (vacation|pto|leave)'` → total-rewards/benefits/general-and-entity-benefits/gitlab-gk.md L198 "No payment for unused leave upon termination". Singapore L247 carry-forward approval.
FLAG: partially answerable (sell-back side, entity-specific):
- "Workers (indiviual contributors) can accrue up to a maximum of 45 days. However, workers can only carry over 30 days per year. Any days in excess of that will need to be encashed at the end of each calendar year." / "People managers ... are ineligible to carry over or encash any days in excess of that." — entity/india-pvt-ltd.md § "Statutory Leave Entitlement" L268–269
- "No payment for unused leave upon termination" — total-rewards/benefits/general-and-entity-benefits/gitlab-gk.md § "Time Off & Leave Policies" L198
- "GitLab does not set a specific limit on the amount of PTO a team member can take per year." — people-group/time-off-and-absence/time-off-types.md § "Overview" L18 (makes "buying" days moot, though the pin never says so)
Nothing in the pin covers buying extra days. Recommendation: keep as ooc-in-scope only if the grader accepts "not stated generally; India encashes excess earned leave" as a pass. Otherwise re-tag as conditional.
ref_source: llm-draft, unreviewed
notes: Distractor: offboarding FAQ "Other Reimbursements, Refunds or Repurchasements" (people-group/offboarding/faq.md L100–104), which is about loans and shares, not leave.

### Row 103 — lookup · process · trap –
cut: owner 2026-10-15 — time off over-represented; contractors covered by 13, 48
Q: contractor here - what's the process when i want to take a holiday?
expected_docs: people-group/time-off-and-absence/time-away-philosophy.md, people-group/time-off-and-absence/time-off-types.md
citation: "Overview" under "Workday: Single Source of Truth for Absence" (people-group/time-off-and-absence/time-away-philosophy.md); "Overview" under "Public Holiday" (people-group/time-off-and-absence/time-off-types.md); "Contractor Benefits" (total-rewards/benefits/general-and-entity-benefits/_index.md)
facts:
- F1. Contractors follow the same process: log time away (PTO, Public Holiday, etc.) in Workday. Independent contractors are explicitly included. — people-group/time-off-and-absence/time-away-philosophy.md § "Overview" L187
- F2. Agree it with your manager first and give at least twice as many days of notice as the time off. — people-group/time-off-and-absence/time-off-types.md § "PTO Protocols (Planning and Coordination)" L25
- F3. In Workday: select the day(s) → "Time-Off" → "Paid Time Off" (or "Public Holiday") → "Submit". — people-group/time-off-and-absence/time-off-types.md § "How to Enter PTO in Workday" L35; § "How to Enter Public Holidays in Workday" L80
- F4. Contractors are eligible for company-wide benefits (which include Flexible PTO) but not entity-specific benefits. — total-rewards/benefits/general-and-entity-benefits/_index.md § "Contractor Benefits" L426; § "Flexible Paid Time Off" L237–239
- F5. [if "holiday" = public holiday] GitLab GSI contractors get a standard allocation of 12 public holidays. — people-group/time-off-and-absence/time-off-types.md § "Overview" (Public Holiday) L60
flag: none (T5 naming drift noted below; row is not trap-tagged)
ref_source: llm-draft, unreviewed
notes: "Holiday" is ambiguous (vacation vs public holiday). Facts cover both. Contractor type is also ambiguous (GSI independent/C2C vs PEO vs CXC). The pin has no contractor-specific holiday process beyond F1–F5. Entity naming drift (T5-related): "GitLab IT BV contractors" (total-rewards/benefits/general-and-entity-benefits/_index.md L426, f96a52e199 2026-09-28) vs "Contractors of GitLab GSI (previously IT BV)" (people-group/time-off-and-absence/time-off-types.md L60, bee431b547 2026-09-13) and "GitLab Services Inc Entity" (people-group/employment-solutions.md § "Team Members Hired as Contractors via our GitLab Services Inc Entity" L67–69, 7593cd32dc 2026-04-09). The "previously IT BV" wording marks GSI as current. Distractor: offboarding FAQ "CXC & GitLab Contractors (only)" final-pay invoice (people-group/offboarding/faq.md L80–82).

### Row 108 — ooc-in-scope · conditional · trap –
cut: owner 2026-10-15 — partial answer in pin; ungradable as ooc.
Q: does gitlab pay for childcare when i travel for work, or does it depend on the country?
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -i "child ?care|childcare"` → 18 files. Mostly all-remote parenting culture pages. **ceo/shadow.md § "Childcare" L616–620** is a hit (see FLAG).
- `rg -i "babysit|nanny|daycare|day care|dependent care"` → 10 files. US Dependent Care FSA (total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md L493–495, pre-tax employee money, not travel); Korea leave for daycare closures (total-rewards/benefits/general-and-entity-benefits/korea-ltd-benefits.md L170); CEO Shadow daycare (L620).
- `rg -i "(child|dependent).{0,60}(travel|trip)|(travel|trip).{0,60}(child|dependent)"` → 4 files; finance/travel/_index.md L83 (business travel insurance covers family travelling with you), which is not childcare.
- `rg -n -i "child|famil" finance/expenses.md` → L223 (host gift when staying with family), L488 (gift example), L595 (family phone plan). The global travel & expense policy has no childcare rule.
confirmed: FLAG (partial). The general Global Travel & Expense Policy is silent and there is no country-dependent rule. But the pin does say childcare is reimbursed for one travel program: "Childcare is provided during the active shadowing period and will be reimbursed through an expense report. You must book the childcare yourself..." — ceo/shadow.md § "Childcare" L618–618; "If you're traveling for the CEO Shadow Program, depending on your hotel accommodations, finding a nearby daycare is most convenient." — L620. Suggest keeping ooc-in-scope for general business travel, but accept an answer that says the handbook only mentions childcare reimbursement for the CEO Shadow Program. Alternatively, re-tag the row as answerable (conditional).
ref_source: llm-draft, unreviewed
notes: Distractors: US Dependent Care FSA (employee pre-tax), finance/travel business travel insurance family coverage (L83), and "Supporting nursing mothers" (finance/expenses.md L323–331, a travel-related parental expense but not childcare).

### Row 109 — synthesis · conditional · trap –
cut: owner 2026-10-15 — partial answer; benefits covered by 13, 22
Recoded from ooc-in-scope, 2026-10-15 (now D1 synthesis, D2 several-pages, D3 conditional, no trap).
Q: What employee discounts do we get, like on phone plans or buying a laptop for personal use?
expected_docs: total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md, total-rewards/benefits/general-and-entity-benefits/_index.md, total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md
citation: "Team Member Discounts" (total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md); "HealthKick Well-being Platform" (total-rewards/benefits/general-and-entity-benefits/_index.md); "Additional Aviva Benefits" (total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md)
facts:
- F1. [variant: US] PerkSpot gives US team members discounts on 10,000+ brands across 25+ categories — total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md § "Team Member Discounts" L606–612
- F2. [variant: US] ADP LifeMart is an additional discount platform, reached through ADP Workforce Now (MYSELF → Benefits → Employee Discounts - Life Mart) — total-rewards/benefits/general-and-entity-benefits/inc-benefits-us/_index.md § "Team Member Discounts" L614–616
- F3. [variant: all] The global wellness platform (HealthKick) gives discounts on fitness, nutrition and wellness services — total-rewards/benefits/general-and-entity-benefits/_index.md § "HealthKick Well-being Platform" L57–59
- F4. [variant: Ireland] Aviva benefits include up to 15% discount on Aviva general insurance — total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md § "Additional Aviva Benefits" L201–206
- F5. The handbook does not describe a discount on phone plans or on buying a laptop for personal use — (absence; searches below)
ref_source: llm-draft, unreviewed
notes: Searches for F5: `rg -il "phone plan|mobile plan|carrier discount|verizon|t-mobile"` → 7 files, none a discount (nearest: support/on-call.md L355, on-call staff may expense their mobile phone service in on-call months). `rg -in "personal (use|purchase).{0,60}(laptop|computer)|…"` → laptop personal-use policy only. Distractors, not discounts: laptop buyback at offboarding (eta/corporate-it/end-user-services/laptop-management/laptop-offboarding-returns/_index.md § "Laptop Buybacks" L36–42); keep laptop at no cost after 3 years (eta/corporate-it/end-user-services/laptop-management/laptop-ordering/_index.md L79); Apple Business Account "corporate discounts" for business purchases (marketing/growth-marketing/regional-marketing/_index.md L1038); SoFi 0.25% loan refinancing discount (inc-benefits-us "Student Loan Support", L601–604), which a reviewer may want to add as a US fact. Page last changed: inc-benefits-us 03d7be6367 2026-09-25; total-rewards/benefits/general-and-entity-benefits/_index.md f96a52e199 2026-09-28; total-rewards/benefits/general-and-entity-benefits/gitlab-ireland-ltd.md f36839dd2f 2026-09-29.

### Row 114 — ooc-in-scope · single-fact · trap –
Q: Can I see my last performance review score somewhere?
cut: auto-review 2026-10-16 — partial answer in pin (ratings communicated by manager in review conversation, optional PDF, assessments in Workday; talent-assessment.md L116, L502, L562–564); grounded answers would fail exact-match abstention
expected: "I don't know based on the provided handbook excerpts."
searches:
- `rg -i '(view|see|find|access).{0,60}(rating|assessment|performance review|9-box|score)'` in people-group, leadership, total-rewards/compensation → people-group/talent-assessment.md L502 "managers can see final assessments for each of their team members in their respective Workday profiles" (manager view, not team member). people-group/promotions-transfers.md L861 suggests sharing "your most recent performance review with your new manager" (implies you have it, doesn't say where).
- `rg -i 'my performance|workday.{0,40}(review|rating)'` → people-group/talent-assessment.md FAQ L653–669 ("Can my performance factor be changed?" etc.). No location for viewing.
- people-group/talent-assessment.md § "Communication" L560–564 → managers communicate ratings in a Zoom review conversation and may share "the PDF of the review" 1–2 days before.
confirmed: nothing in pin says where a team member can look up a past score. Borderline; see notes.
ref_source: llm-draft, auto-reviewed
decision: auto-review 2026-10-16 — CUT (partial answer; exact-match abstention unfair)
notes: Borderline partial. The pin says ratings are communicated by your manager in the review conversation (optionally as a PDF), and assessments live in Workday (people-group/talent-assessment.md L116, L502). An answer of "ask your manager / it's in Workday" would be inference. Owner to decide whether that counts as answerable.
