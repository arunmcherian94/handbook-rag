# 0007: Permission-aware retrieval (week 2: synthetic ACLs as a SQL pre-filter)

- Status: approved
- Date: 2026-10-20
- Depends on: 0003–0006, ADR-0011, ADR-0020, eval set v1.2, run `2026-10-19-d2625d91` (depth-20 baseline)

## Problem

The corpus is the public handbook, so every document is `acl_tags = {public}` and retrieval has no notion of who is asking. The project's goal is a permission-aware assistant, so retrieval must return only chunks the asking user may see, and that guarantee must survive the paths added later: week 3 hybrid search, week 5 agents, week 7 caching.

ADR-0011 kept the quality set ACL-free and deferred permission cases until this design existed. This spec settles the design (decisions D1–D7 of 20 Oct, [ADR-0021](../docs/decisions/0021-permission-model.md)) and the suite that tests it. Part A is the pre-filter, the identity guardrail and the permissions suite. Part B is Friday's recall-starvation measurement on a separate HNSW path. Nothing is built from this PR.

The restricted sets are synthetic, derived from audience signals in the content: "apply to all GitLab team members hired through GitLab GmbH", "an important part of being a people manager". They live in the approved [`acl/policy-v1.yaml`](../acl/policy-v1.yaml). Under it, 46 docs (379 of 22,378 `fixed-512-64` chunks, 1.7%) are restricted from staff. The other 4,042 docs are open to every persona except the narrow one and the agency contractor, who sees only the engineering subtree among them (recon, [journal 20 Oct](../docs/journal/2026-10-20-permissions-spec.md)).

## Acceptance criteria

### Part A: pre-filter, identity, permissions suite

Policy and storage

- AC-1: **Policy file.** `acl/policy-v1.yaml` holds a `version`, the group vocabulary, and rules. A rule is a path prefix (ending in `/`), the catch-all (`""`, the root prefix), or an exact path (anything else), relative to `content/handbook/`, with a non-empty group allow-list. There is exactly one explicit catch-all rule. Resolution: an exact path beats any prefix, and among prefixes the longest wins. The loader uses `yaml.safe_load` (PyYAML, an approved dependency). It fails on any value that isn't a string, which guards against YAML's implicit typing (a bare `no` read as a boolean). It also fails on a missing or duplicate catch-all, a group outside the vocabulary, an empty allow-list, a duplicate path, or a rule that matches no document at the pin (a stale rule).
- AC-2: **Document-level ACL (D1).** `make acl` resolves each document's allow-list from the policy into the existing `documents.acl_tags` column (spec 0002 stub). It copies the list to a new `chunks.allowed_groups text[] NOT NULL` for every chunk of every config (ADR-0020), with a GIN index. No re-embedding. It runs in one transaction, is idempotent, and has a dry run that prints per-group doc and chunk counts and the visible chunk share of each fixture persona. Section-level ACLs are out of scope.
  - **New rows fail closed.** The migration changes the `documents.acl_tags` default from `{public}` to `{}`. A newly ingested document is then visible to no one until `make acl` runs, and AC-4/AC-5 flag it. `make chunk` copies the parent's `acl_tags` into `allowed_groups` on insert, so a new config never has a NULL.
- AC-3: **Redirect stubs inherit their target's allow-list.** The target comes from the stub's `redirect_to:` front matter in the pinned file. It is normalized like a stored `url_path`, by the same function as ingestion: an absolute `handbook.gitlab.com` URL is reduced to its path, then lowercased, with a trailing slash. Chains are followed to the final non-stub target; a cycle fails. A target missing from the corpus fails `make acl`. A stub's own rule is ignored.
- AC-4: **Invariants (D5)**, each tested over every config in the DB:
  - every chunk has exactly one parent document (non-null `doc_id` with a foreign key), because inheritance depends on it
  - no chunk has a null or empty `allowed_groups` (a missing field must never mean "visible to all")
  - each chunk's `allowed_groups` equals its parent's `acl_tags`
- AC-5: **Stale-ACL check.** Before any retrieval, an eval run recomputes every document's allow-list from the policy file and compares it with `documents.acl_tags` and `chunks.allowed_groups`. On any difference the run fails and says to run `make acl`.

Identity

- AC-6: **Identity fixture (D2, D3, D6).** `acl/identities-v1.yaml` holds a `version` and six users, each with attributes from the v1 dimensions: `employment_type` (employee / contractor / temporary / agency), `role` (ic / people-manager), `function`, and `entity` (exactly one for employees, none otherwise). Groups are resolved by a fixed table in code:

  | attribute | groups |
  |---|---|
  | employment_type employee | `staff`, `employee` |
  | employment_type contractor | `staff`, `contractor` |
  | employment_type temporary (Temporary Service Provider) | `new-contractor` |
  | employment_type agency, function X (contractor engaged through an agency) | `new-contractor`, `agency:X`; `agency:X` must be in the vocabulary or resolution fails |
  | role people-manager (employees only) | `manager` |
  | function people-ops (employees only) | `people-ops` |
  | entity X | `entity:X` |

  The six personas:
  - `admin`: a people-ops IC employee of `us-inc` (groups `staff`, `employee`, `people-ops`, `entity:us-inc`), sees everything through `people-ops`
  - `us-ic`: an IC employee of `us-inc`
  - `manager`: a people manager employed by `uk-ltd`
  - `contractor`: Contractor Benefits stays visible to them
  - `narrow`: a temporary contractor who sees only onboarding and contractor pages, about 1.2% of chunks
  - `agency`: an agency contractor with `function` engineering (groups `new-contractor`, `agency:engineering`). Not in `staff`, so it sees only the engineering subtree plus the onboarding and contractor pages, about 32.5% of chunks. It is Part B's mid-selectivity point.

  A unit test pins each persona's resolved groups, and an integration test pins each persona's visible chunk share within ±0.1 percentage points of the dry-run figures.
- AC-7: **Principal guardrail.** `Principal` is a frozen type holding the user id, the attributes and the resolved groups.
  - It is constructed only in `src/handbook_rag/identity.py`, by loading the fixture by user id. A test fails if `Principal(` appears anywhere else under `src/`.
  - The resolver's input is a user id, never question text. No code path derives groups from a query.
  - A principal with no groups is an error, never an unfiltered search.
- AC-8: **Every retrieval path requires a Principal.** `ask.retrieve`, `ask.ask` and the eval runner take a required `principal` argument, with no default and no unfiltered overload. Tests may build principals through a test helper.
  - The single `SEARCH` statement adds `AND c.allowed_groups && %(groups)s::text[]` before the cosine `ORDER BY`. A test asserts that every SQL statement in `src/` that ranks embeddings (on `chunk_embeddings` or any Part B structure) includes this predicate.
  - **Fetch by id:** any function outside `src/handbook_rag/evaluation/` that returns chunk content by id also takes a `principal` and applies the predicate. The eval's scoring reads (evidence, record) are exempt: they grade against the full corpus and never return content to a user. The test keeps an explicit exempt list.
  - A restricted user gets the standard `NOT_FOUND` string. No code path emits a permission message, because one would confirm that hidden content exists (ADR-0011).

Quality set and regression

- AC-9: **The quality set runs as `admin`.** Eval set v1.2, its metrics and its scoring are unchanged. **Regression:** a retrieval-only run as `admin` on `fixed-512-64` has a top 5 identical to run `2026-10-19-d2625d91` on all 33 answerable rows, in order. With exact search and an allow-list that admits every document, it must be identical.

Permissions suite

- AC-10: **Separate, versioned suite.** The cases live in `docs/eval/permissions-v1.md`, with their own changelog entry, separate from eval set v1.2. Each case has an id, a question, an acting persona, target doc paths, a category and the drafter's intent (allowed or denied). The expected outcome is computed by code from the policy and the fixture:
  - which target docs are entitled
  - allowed or denied

  The LLM never writes the expected outcome. When the drafter's intent and the computed outcome disagree, the case is flagged for review, not silently fixed.
- AC-11: **Validity.** A case whose target docs don't all appear in `admin`'s top 20 tests nothing and is dropped from scoring. It is listed as `invalid` in the summary.
- AC-12: **Metrics**, computed on retrieval only at k=5 (frozen) and k=20:
  - **Leak:** a retrieved chunk whose parent document's allow-list, recomputed from the policy file rather than read from the DB column, doesn't intersect the principal's groups. It is scored per document, so the same fact on a page the principal may see is not a leak. Reported: leaked chunks, and cases with at least one leak. **Target 0.**
  - **Authorized recall:** recall against only what the principal is entitled to. For a case, it is the fraction of its entitled target docs found in the top k. For a case built on a v1.2 row, it is fact recall over the row's facts whose cited doc is entitled. A case with nothing entitled (a denied case) has no authorized recall: it is excluded from the mean and counted as `n/a`, never 0 or 1. It is always reported next to leak, because deny-all scores zero leaks.
  - **Over-block:** an entitled target doc that `admin` retrieves at k but the entitled principal doesn't. With a correct filter, hiding documents can only move entitled docs up, so this should be 0. A non-zero count points to a policy or fixture bug.
  - Per-category breakdown.
- AC-13: **The run** is retrieval-only (no answer model calls, about $0.0001 of query embeddings) and has a dry run. Its metadata records:
  - the policy version and file hash
  - the identity fixture version and hash
  - the suite version and hash
  - `config_id`

- AC-14: **Leak is 0 by construction under a SQL pre-filter; the spec says so.** The suite exists to guard later paths, and the spec names its obligations: week 3 full-text and hybrid search must apply the same predicate, week 7 cache keys must include the resolved groups, and week 5 agent tools must take the session principal. Each later spec cites AC-8 and AC-12.

Case drafting (run later, in a fresh session, after this spec merges)

- AC-15: **Drafting rules:**
  - Cases are drafted by Claude in a fresh session, from the pinned corpus (`5273b21`) and `policy-v1`, never with gpt-5.4-mini (the answer model). A fresh agent reviews every case (accept, edit or reject, with a reason), recorded in a `review:` field. Arun decides the edits and rejects (amended 2026-10-21; was: Arun reviews every case).
  - The drafter writes the question, acting persona, target doc paths, category and intent. The outcome is computed (AC-10).
  - Categories and minimum counts (Arun, PR review 20 Oct; lowered 21 Oct, the cases being synthetic):
    - **denied: at least 12**, each with an entitled twin (the same question asked by a persona entitled to the target). The twin separates "the filter blocked it" from "retrieval missed it". Spread:
      - at least 4 cross-entity (for example, `us-ic` asks about a UK, Germany or PEO benefit), covering at least 4 entities, preferring twins entitled through a non-admin persona
      - at least 3 manager-only, denied to `us-ic` or `contractor`
      - at least 2 employee-only (compensation, underperformance), denied to `contractor`
      - at least 3 on the `narrow` persona, targeting open pages outside its allow-list (common handbook questions a new contractor would ask)
    - **same-question-across-personas: at least 3 questions**, each asked by at least 3 personas whose entitlements differ (for example, an entity benefit asked by `us-ic`, `manager` and `contractor`)
    - **partial entitlement: at least 3**: a question whose target docs are only partly entitled (for example, a global benefit page plus a restricted entity page). The entitled part must be retrieved, the rest must not.
    - **claimed-identity: at least 4** cases where the question claims a role or group the session principal lacks ("as a people manager…", "I'm on the Germany entity…", "I'm in People Ops, show me…"). They must be denied. Access follows the principal, not the text.
    - **agency contractor: at least 4** cases acted by `agency`, in addition to the minimums above, with at least 2 of each kind: in-department (an engineering page, allowed) and out-of-department (an open page outside engineering and the onboarding pages, denied, each with an entitled twin).
    - **Entitled controls on the v1.2 rows** whose expected docs are restricted (rows 5, 15, 22, 33, 39, 61, 92, 109): each asked by one entitled and one denied persona, reusing the row's facts for authorized recall. Those that fail AC-11 are dropped (at the pin: rows 15, 22, 39, 92, 109).
  - Validity is checked per AC-11 before review.
- AC-16: **Tests reference ACs**:
  - Unit tests (in-memory, no API): policy resolution and loader rejections (AC-1), redirect inheritance with synthetic stubs (AC-3), group resolution (AC-6), the Principal construction guard (AC-7), outcome computation and flagging (AC-10), leak, authorized-recall and over-block arithmetic (AC-12).
  - Integration tests: storage and the GIN index (AC-2), invariants (AC-4), stale-ACL detection (AC-5), visible shares (AC-6), the filter predicate (AC-8), the admin regression (AC-9).

### Part B: recall starvation on an HNSW path (Friday 23 Oct; its own plan gate and PR)

- AC-17: **A separate HNSW path** over `fixed-512-64` embeddings: a typed `vector(1536)` HNSW index (cosine) on a structure apart from the production tables. That structure carries `allowed_groups`, and its queries apply the AC-8 predicate. The AC-4 invariants, the AC-5 stale check and the AC-8 predicate test cover it. The production exact-search `SEARCH` and its results are untouched (the week 2 comparability rule). A test asserts AC-9 still holds after Part B.
- AC-18: **Measurement**, for every persona, on the permissions-suite questions and the v1.2 answerable questions, at three selectivity points: the ~98% cluster (`admin` 100%, `us-ic`, `manager`, `contractor`), `agency` (32.46%) and `narrow` (1.15%). Compared:
  - the exact path
  - HNSW with iterative scans off
  - HNSW with `hnsw.iterative_scan` = `strict_order` and `relaxed_order` (pgvector ≥ 0.8.0; the DB has 0.8.7)

  Reported, per persona and per setting:
  - **Primary: ANN recall@k against the exact filtered top k**, |HNSW_filtered ∩ exact_filtered| / min(k, |exact_filtered|) at k = 5 and 20, plus the number of results returned (and the count of questions returning fewer than k). The denominator counts only what exact search could return, so a persona that sees fewer than k chunks isn't scored as an ANN miss. It needs no eval facts, so it is defined for every persona and question.
  - **Secondary: fact recall** (AC-12 authorized recall), only for rows where the persona is entitled to at least one required fact, with n shown. At the pin, n is 17 v1.2 rows for `narrow`, 18 for `agency`, 31 for `us-ic`, `manager` and `contractor`, and 32 for `admin`.
  - Latency p50/p95. Settings are recorded: `ef_search`, `max_scan_tuples`.
- AC-19: **Write-up:** a journal entry with the numbers and an ADR-0020/0021 consequence: when production gets an ANN index, use iterative scans or partition by group. No production change.

## Out of scope

- **Fetch-time (late-binding) source checks**, as in Slack AI. They need a live source system with ACLs, and the corpus is a static public snapshot. Early binding has a staleness window equal to the sync interval. ADR-0021 states it.
- **Post-retrieval authorization checks** (an authz service filtering the top k): they lose recall (k results shrink to fewer), and post-filtering leaks through counts and ranking.
- **Per-tenant partitioning:** there is one corpus and one tenant. Partition-per-group is revisited only if Part B shows starvation that iterative scans can't fix.
- **Section-level ACLs (D1):** pages mix audiences (Contractor Benefits sits inside the entity benefits page). It would need ACL-aware chunking.
- **Parked dimensions:** tenure, leave status and travel. They have no clear page-level audience signal in the corpus and would multiply personas.
- **Model-based identity-claim detection:** this is week 5 (injection). Here claimed-identity cases are handled by never reading identity from text.
- Restricted pages under legal, security or finance: none has a page-level audience signal. Internal procedures link to the internal handbook, which is out of corpus.
- Changing k, the prompt, the answer model or the eval set v1.2 rows.
- Drafting permission cases in this PR or in the build session.

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| Where ACLs live | Group allow-list copied onto each chunk, GIN index, `&&` pre-filter (Elastic DLS, Azure AI Search security filters) | **Container tags resolved per query** (WorkOS): fewer rewrites on ACL change, but needs a hierarchy service; our path-prefix policy applies the same idea at ingestion. **Post-retrieval check** (Descope ReBAC): a filtered top k returns fewer than k results (our reasoning), and Cerbos warns post-filtering leaks through counts and ranking. **Tenant partitions:** one tenant. |
| Granularity | Document (D1) | **Section:** needs ACL-aware chunking, and mixed-audience pages would need splitting rules. |
| Membership | Resolved per request from the fixture, never stored on chunks | **Users on chunks:** every membership change rewrites the index. |
| Missing ACL | Fail-closed: NOT NULL, non-empty, invariant test | **Missing = public** (Elastic's default for docs without the field): a fail-open path. |
| Admin access | `people-ops` listed on every rule | **A code bypass for admin:** an unfiltered path is exactly what AC-8 forbids. |
| Expected outcomes | Computed from policy and fixture | **LLM-written:** the same model that drafts the case would grade it. |
| Leak ground truth | Recomputed from the policy file | **Read from `allowed_groups`:** a corrupted column would grade itself. |
| Policy format | YAML (as in Cerbos policies and Kubernetes RBAC): rules are data, with comments for the evidence | **A policy engine** (OPA/Rego, SpiceDB): built for logic and relationships, and our rules are a path-to-groups table. **TOML:** stdlib, but nested rule lists read worse. |
| D7 placement | Part B of this spec, built in its own PR | **A separate spec:** splits one design across two documents. |

## Open questions

1. **Restricted path list:** Arun approves or edits `acl/policy-v1.yaml` in this PR's review.
2. **Personas' entities** (`us-inc` for the IC, `uk-ltd` for the manager): approved at the plan gate (20 Oct). Changing them changes only the fixture.
3. ~~**YAML parser.**~~ Resolved 2026-10-20 (Arun): YAML. `pyyaml` is added as a dependency in the build; `safe_load` with strings only (AC-1).

## References

- [ADR-0021: permission model](../docs/decisions/0021-permission-model.md)
- [Reading log, week 2: permission models in production RAG](../docs/reading/week-02.md#permission-models-in-production-rag)
- [ADR-0011: quality set ignores ACLs](../docs/decisions/0011-acls-deferred-from-quality-set.md), [ADR-0020: chunk configs coexist](../docs/decisions/0020-chunk-configs-coexist.md)
- Recon: [journal 20 Oct](../docs/journal/2026-10-20-permissions-spec.md)
- Amendment background, Part B metric (20 Oct):
  - [pgvector 0.8.0 released: iterative index scans](https://www.postgresql.org/about/news/pgvector-0.8.0-released-2952/)
  - [Weaviate, Filtering: recall under restrictive filters](https://weaviate.io/developers/weaviate/concepts/filtering)
  - [Vespa, Additions to HNSW: filtered search](https://blog.vespa.ai/additions-to-hnsw/)

## History

- 2026-10-20: drafted; approved and merged in PR #27 (Arun). Status set to approved with the amendment.
- 2026-10-20, amended in place before any build (nothing had consumed `policy-v1`): persona shares clustered at ~98% plus one point at 1.15%, so Part B had no mid-selectivity point. Added the `agency` persona (engineering, 32.46%) and the `engineering/` rule with the `agency:engineering` group (AC-6). Part B's primary metric is now ANN recall@k against the exact filtered top k, divided by min(k, |exact|) (Arun), with fact recall secondary and n shown (AC-18). At least 4 agency cases added (AC-15). Recon and figures: [journal 20 Oct](../docs/journal/2026-10-20-permissions-spec.md#amendment-agency-persona-and-part-b-metric).
- 2026-10-21, amended on the cases branch: AC-15 minimums lowered (denied 12, same-question 3, claimed-identity 4; agency and partial unchanged) and the review rule changed to a fresh-agent review with Arun deciding the flags (Arun: the cases are synthetic). Cases and counts: [permissions-v1 changelog](../docs/eval/CHANGELOG.md#permissions-v1-2026-10-21).

## Verification

- `make acl` dry run: per-group counts and persona shares match the journal's recon figures.
- `make acl`, then the invariant tests over all five configs.
- The admin regression against `d2625d91` (AC-9).
- After the cases merge: a permissions-suite run with leak 0, over-block 0 and authorized recall reported.
- `make test` and `make lint` pass.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] docs updated: journal entry, an ADR for any decision, follow-ups
