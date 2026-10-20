# 2026-10-20: permissions design records, spec 0007

- **Records written; nothing built.** [Spec 0007](../../specs/0007-permission-aware-retrieval.md), [ADR-0021](../decisions/0021-permission-model.md), a reading entry ([week 2](../reading/week-02.md#permission-models-in-production-rag)) and the draft [`acl/policy-v1.yaml`](../../acl/policy-v1.yaml). Design decisions D1–D7 and the identity guardrail are from 20 Oct (Arun). Permission cases come later, from a fresh session after the spec merges (AC-15).
- **Recon at the pin** (`fixed-512-64`, 4,088 docs, 22,378 chunks):
  - pgvector is 0.8.7, so iterative index scans (≥ 0.8.0) are available for Part B.
  - `documents.acl_tags` already exists as a spec 0002 stub (`{public}` everywhere). `chunks` has no ACL column.
  - The draft restricts 46 docs and 379 chunks (1.7%): employee-only (2 docs, 13 chunks: compensation and underperformance); people-manager-only (18, 62); entity-specific (26, 304, across 16 entities and 3 PEOs). These are the figures after the PR review below.
  - Visible share per persona:

    | persona | groups | visible chunks |
    |---|---|---|
    | admin | staff, employee, people-ops, us-inc | 22,378 (100%, via `people-ops`) |
    | US IC | staff, employee, us-inc | 21,999 open + 58 + 13 = 22,070 (98.62%) |
    | manager | staff, employee, manager, uk-ltd | 21,999 + 19 + 13 + 62 = 22,093 (98.73%) |
    | contractor | staff, contractor | 21,999 (98.31%) |
    | narrow | `new-contractor` | 257 (1.15%) |

  - **v1.2 answerable rows with an expected doc in a restricted set:** 5, 15, 22, 33, 39, 61, 92, 109. The quality set runs as admin, so they're unaffected (AC-9).
- **Judgment calls** (plan gate, approved by Arun):
  - **Contractor Benefits is a section, not a page.** It sits at L424 of `general-and-entity-benefits/_index.md`. Under document-level ACLs that whole page stays open, and only the per-entity pages under it are restricted. The provisional rule in ADR-0011 ("entity-specific benefits") would have hidden it.
  - **`people-ops` is on every rule**, so the admin sees everything through the policy, never a code bypass.
  - **The narrow persona** is a temporary service provider (the corpus has a "Temporary Service Provider (Contractor/Consultant) Onboarding" section). It was widened with time off and expenses to reach the 1–2% target, from 0.85% to 1.15%.
  - **Not restricted:** `stock-options.md` and `incentives.md` (no employee-only signal), and legal, security and finance procedures. Their "internal" mentions are links to the internal handbook, which is out of corpus; no page has a page-level audience signal.
  - **No redirect stub targets a restricted path** (6 stubs, all in engineering or product). The inheritance AC is tested on synthetic stubs.
  - **D7 is Part B of spec 0007,** built in its own PR on Friday.
- **Source check:** all nine reading URLs were fetched by a research subagent. Two claims were corrected before citing. Cerbos warns only about leaks through counts and ranking, and Descope says nothing about recall, so the recall cost of post-filtering is stated as my own reasoning. Dates were filled in where the pages show them.
- **Found while validating the policy:** PyYAML isn't a project dependency. The policy was checked with a throwaway `uv run --no-project --with pyyaml`, and the project wasn't touched. Open question 3 in the spec: add `pyyaml`, or switch to TOML.
- **Code-review catches (fixed in the spec and policy before the PR):**
  - **Manager-only doc count:** it was 22; `support/managers/` has 15 docs, not 18, so the set is 19 (the chunk counts were right). The dry-run check against these figures would have failed.
  - **The catch-all `""` contradicted the syntax rule** "anything not ending in `/` is exact". The root prefix is now defined explicitly (AC-1).
  - **NOT NULL `allowed_groups` vs `make chunk`:** the chunker's insert would have failed for any new config. `make chunk` now copies the parent's `acl_tags`, and the `documents.acl_tags` default becomes `{}` (fail closed) instead of `{public}` (AC-2).
  - **The Part B HNSW structure** wasn't bound to the ACL column or the predicate test (AC-17).
  - **The admin's groups** were inconsistent between the journal and AC-6. Admin is now a people-ops IC employee of `us-inc`; employees have exactly one entity.
  - **Redirect normalization** now uses ingestion's `url_path` function (lowercase, trailing slash), follows chains, and fails on cycles (AC-3).
  - **Authorized recall at 0/0** is `n/a`, excluded from the mean (AC-12).
  - **Fetch-by-id outside `evaluation/`** must take a principal too; the eval's scoring reads are an explicit exempt list (AC-8).
  - Not changed: the reading takeaways were drafted by Claude. CLAUDE.md wants them in Arun's words, and the entry is marked "LLM-drafted, Arun to edit" as the brief asked.
- **PR review (Arun, 20 Oct):**
  - **`leadership/underperformance.md` moved from manager-only to employee-only.** It has sections written for the team member: "Team Member: Discuss Circumstances Immediately With Your Manager" (L65), the compensation impact of a PIP (L117), and no transfers during remediation (L121).
  - **`support/managers/` stays manager-only.**
  - **Agreed:** the fail-closed `acl_tags` default, the eval's scoring exemption, the leak and authorized-recall definitions, and the staleness wording.
  - **Part B scope** is revisited on Friday.
  - **YAML stays:** `pyyaml` is approved, loaded with `safe_load`, and every value must be a string.
  - **More cases (AC-15):** at least 26 denied, spread across cross-entity, manager, employee-only and narrow. Plus at least 5 same-question sets, at least 3 partial-entitlement cases, at least 6 claimed-identity cases, and entitled and denied controls on the 8 restricted v1.2 rows. The narrow persona supplies denied targets from the open corpus, which offsets the small restricted set (46 docs).
  - **Narrow persona list checked and kept:**
    - Temporary Service Provider onboarding goes through Procurement (`general-onboarding/_index.md`).
    - Contractors are reimbursed via iiPay (`finance/expenses.md` L693, L729).
    - Independent contractors must log time away (`time-away-philosophy.md` L187).
    - `contingent-worker-policy.md` was not added, because it's written for the people hiring contractors.
  - **Reading takeaways:** Claude writes them at Arun's request, an exception to CLAUDE.md's "in Arun's words" for this entry. Arun reviewed and approved them (20 Oct).
  - **Prompt injection beyond retrieval** is noted as a week 5 [follow-up](../follow-ups.md#from-the-spec-0007-review-2026-10-20).
- **Housekeeping:** removed the AC-8, AC-9 and limitation bullets duplicated in [2026-10-19-packed-build](2026-10-19-packed-build.md), and a duplicated "spec 0006 runs" section in follow-ups.

## Amendment: agency persona and Part B metric

Spec 0007 was amended in place after PR #27: nothing is built and nothing has consumed `policy-v1`. Part A has not started.

- **Why:** the persona shares cluster at ~98% (admin 100, US IC 98.62, manager 98.73, contractor 98.31), plus one point at 1.15% (narrow). Part B needs a point in between to show where HNSW recall degrades. Part B's primary metric also mustn't depend on eval facts: which v1.2 rows a persona is entitled to is a property of the eval set, not of the index, so fact recall can't isolate ANN recall loss. (The worry that narrow has no entitled rows turned out wrong: it has 17, see below.)
- **Recon** (`fixed-512-64`, 22,378 chunks, 33 answerable rows): no second-level directory has both a 15–30% share and at least 5 v1.2 rows inside it. The eval set leans on HR pages: `people-group` holds 9 rows that fall entirely inside it, but only 2.42% of chunks.

  | dept | chunks | share | rows with all expected docs inside | with the onboarding pages: share, rows with ≥ 1 required fact entitled |
  |---|---|---|---|---|
  | engineering | 7,006 | 31.31% | 0 | 32.46%, 18 (1 from engineering itself, row 38) |
  | marketing | 2,558 | 11.43% | 1 | 12.58%, 18 |
  | security | 1,429 | 6.39% | 0 | 7.52%, 19 |
  | people-group | 542 | 2.42% | 9 | n/a |

- **Chosen: engineering** (Arun, 20 Oct). It sits slightly above the band and gets its entitled rows almost entirely from the onboarding pages. That's acceptable, because fact recall is now the secondary metric.
- **Persona `agency`:** `employment_type` agency with `function` engineering resolves to `new-contractor` (the onboarding and contractor pages) plus `agency:engineering`. A new `engineering/` rule allows `[staff, agency:engineering, people-ops]`. The persona isn't in `staff`, so the catch-all doesn't apply to it. The five redirect stubs under `engineering/` all target engineering pages. The sixth (`product/ux/_index.md` → `upstream-studios/`) stays outside, so the share doesn't change.
- **Visible share and entitled v1.2 rows** (a row is entitled when at least one required cited fact's doc is visible: the AC-12 authorized-recall n):

  | persona | groups | visible chunks | entitled rows |
  |---|---|---|---|
  | admin | staff, employee, people-ops, entity:us-inc | 22,378 (100%) | 32 |
  | us-ic | staff, employee, entity:us-inc | 22,070 (98.62%) | 31 |
  | manager | staff, employee, manager, entity:uk-ltd | 22,093 (98.73%) | 31 |
  | contractor | staff, contractor | 21,999 (98.31%) | 31 |
  | agency | new-contractor, agency:engineering | 7,263 (32.46%) | 18 |
  | narrow | new-contractor | 257 (1.15%) | 17 |

  Admin is at 32 rather than 33 because one row's required facts are all answer-only. The narrow persona does have entitled rows (17; 9 with every expected doc entitled), so fact recall is defined for it. It stays secondary anyway.
- **Checks:** a throwaway resolver (`uv run --no-project --with pyyaml`) confirmed `people-ops` on every rule, every group in the vocabulary and no stale rule. No-orphan and one-parent-document scripts don't exist yet. They're AC-4 invariants, built in Part A.
- **Code-review catches (fixed before the PR):**
  - **An agency user with `function` people-ops would have resolved to `people-ops`** (all access) through the existing function row. AC-6 now says the agency row never yields `people-ops`, and `agency:X` must be in the vocabulary.
  - **The catch-all comment** still said 4,042 docs resolve to it. It's 2,770 docs / 14,736 chunks now; 4,042 / 21,999 is what staff can see.
  - **"Restricted" was ambiguous** once `engineering/` narrows non-staff personas. The 46 docs are "restricted from staff" in the policy header and the spec.
  - **This entry's "why"** gave narrow's row count as the reason for the metric change, which contradicted its own table. Reworded.
  - **ADR-0021 D3** didn't list the agency employment type.
  - Lower priority, left for Arun: AC-18 divides by k, not min(k, |exact|). Every persona sees at least 257 chunks, so exact always fills k = 20 at the pin.
  - No change: reading stubs and the Chroma deferral ride in this PR at Arun's request.
- **Statuses:** spec 0007 draft → approved, ADR-0021 proposed → accepted, and the "DRAFT" header dropped from `policy-v1.yaml`. Arun approved all three by merging #27.
- **Spec edits:** AC-6 (six personas, the agency resolution row), AC-15 (at least 4 agency cases, at least 2 in-department allowed and 2 out-of-department denied with twins), AC-18 (primary ANN recall@k against the exact filtered top k plus the results-returned count, at three selectivity points; fact recall secondary with n). Also the Problem section, References (pgvector 0.8.0, Weaviate filtering, Vespa HNSW) and a new History section. ADR-0021 D6 and D7 match.

---

Prev: [2026-10-19: packed sections and prefix build, spec 0006](2026-10-19-packed-build.md)
