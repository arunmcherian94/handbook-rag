# 2026-10-20: permissions design records, spec 0007

- **Records written; nothing built.** [Spec 0007](../../specs/0007-permission-aware-retrieval.md), [ADR-0021](../decisions/0021-permission-model.md), a reading entry ([week 2](../reading/week-02.md#permission-models-in-production-rag)) and the draft [`acl/policy-v1.yaml`](../../acl/policy-v1.yaml). Design decisions D1–D7 and the identity guardrail are from 20 Oct (Arun). Permission cases come later, from a fresh session after the spec merges (AC-15).
- **Recon at the pin** (`fixed-512-64`, 4,088 docs, 22,378 chunks):
  - pgvector is 0.8.7, so iterative index scans (≥ 0.8.0) are available for Part B.
  - `documents.acl_tags` already exists as a spec 0002 stub (`{public}` everywhere). `chunks` has no ACL column.
  - The draft restricts 46 docs and 379 chunks (1.7%): compensation, employee-only (1 doc, 6 chunks); people-manager-only (19, 69); entity-specific (26, 304, across 16 entities and 3 PEOs).
  - Visible share per persona:

    | persona | groups | visible chunks |
    |---|---|---|
    | admin | staff, employee, people-ops, us-inc | 22,378 (100%, via `people-ops`) |
    | US IC | staff, employee, us-inc | 21,999 open + 58 + 6 = 22,063 (98.59%) |
    | manager | staff, employee, manager, uk-ltd | 21,999 + 19 + 6 + 69 = 22,093 (98.73%) |
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
- **Housekeeping:** removed the AC-8, AC-9 and limitation bullets that were duplicated in [2026-10-19-packed-build](2026-10-19-packed-build.md).

---

Prev: [2026-10-19: packed sections and prefix build, spec 0006](2026-10-19-packed-build.md)
