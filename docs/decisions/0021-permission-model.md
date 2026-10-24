# 0021. Document-level group allow-lists on chunks, filtered in SQL; identity from the session

- **Status:** accepted (2026-10-20, Arun, spec 0007 PR #27)
- **Date:** 2026-10-20
- **Journal:** [2026-10-20 permissions spec](../journal/2026-10-20-permissions-spec.md)
- **Spec:** [0007](../../specs/0007-permission-aware-retrieval.md)

## Context
- The corpus is the public handbook, so every page is visible to everyone. Permissions are synthetic, derived from audience signals in the content: "apply to all GitLab team members hired through GitLab GmbH" (entity), "an important part of being a people manager" (manager), and the compensation pages (employee).
- The restricted set is small: 46 docs, 379 of 22,378 `fixed-512-64` chunks (1.7%).
- Retrieval is exact cosine search in Postgres over one table holding several chunk configs (ADR-0020). An ANN index arrives later.
- Later paths must keep the guarantee: week 3 full-text and hybrid search, week 5 agent tools, week 7 caching.

## Decision
- **D1, granularity:** document-level. Chunks inherit their parent document's ACL. Redirect stubs inherit their target's.
- **D2, model:** user attributes are resolved to groups at session time. Documents get group allow-lists from `acl/policy-v1.yaml`: path-prefix rules, exact-path overrides and an explicit catch-all. Longest prefix wins; an exact path beats a prefix.
- **D3, dimensions (v1):** employment type (employee, contractor, temporary, agency), role/function, entity. An agency contractor's function scopes it to a department (`agency:<function>`). Parked: tenure, leave status, travel.
- **D4, storage:**
  - `make acl` fills `documents.acl_tags` and copies it to `chunks.allowed_groups text[]` (GIN index) for every config, with no re-embedding.
  - Query: `WHERE allowed_groups && :user_groups`, then cosine order.
  - Group membership is never stored on chunks; it is resolved per request.
  - This is the pattern of Elastic DLS and Azure AI Search security filters.
- **D5, no orphans:** NOT NULL, non-empty, and tested over every config. A missing ACL never means public.
- **D6, personas:** six fixture users:
  - all-access people-ops admin
  - US employee IC
  - people manager (UK entity)
  - contractor, who can still see Contractor Benefits
  - narrow temporary contractor who sees only onboarding and contractor pages, about 1.2% of chunks
  - agency contractor in engineering, who sees the engineering subtree plus onboarding and contractor pages, about 32.5% of chunks (added 20 Oct, spec 0007 amendment)
- **D7, recall starvation:** measured on Friday on a separate HNSW path, at three selectivity points (~98%, agency, narrow) with iterative scans on vs off. The primary metric is ANN recall@k against the exact filtered top k, divided by min(k, |exact|). The production exact path is untouched.
- **Guardrail, identity comes from the session and never from the question:**
  - `Principal` is constructed only in the identity module.
  - Every retrieval path requires one, with no default.
  - No code derives groups from query text.
  - A principal with no groups is an error, never an unfiltered search.
  - The admin sees everything through explicit allow-lists (`people-ops` on every rule), not a bypass.

## Alternatives considered
- **(a) Chunk-level ACL copy** [chosen]: the filter is one indexed predicate in the same SQL that ranks, so leak is 0 by construction under exact search. The cost: an ACL change rewrites the chunk arrays.
- **(b) Container tagging plus per-query resolution** (WorkOS): tag chunks with a container id and resolve the user's containers at query time. ACL changes are cheap, but it needs a hierarchy service. Our path-prefix policy applies the same idea once, at ingestion.
- **(c) Post-retrieval authorization check** (Cerbos, Descope ReBAC): fetch the top k, then ask an authz service. It's flexible (relationships, live state), but a filtered top k returns fewer than k results. Cerbos warns that post-filtering leaks through result counts and ranking.
- **(d) Tenant partitioning:** an index per group. It's the strongest isolation, but there's one corpus and one tenant here, and overlapping groups would multiply it. It is revisited only if Part B shows starvation that iterative scans can't fix.

## Consequences
- **ACL changes rewrite chunk arrays** (the CDC staleness problem). A policy edit means re-running `make acl` over every config. Until then the index serves the old ACL, so the eval checks staleness before any retrieval. In production, the staleness window is the sync interval.
- **Membership changes are free:** groups are resolved per request, so adding a user to a group touches no index rows.
- **Early binding only.** Index-time ACLs are only as fresh as the sync. Strong designs add a fetch-time check (Slack AI reuses the user's ACLs when fetching). That is out of scope for v1 because there is no live source system.
- **The filter must follow every new path:** hybrid search applies the same predicate (week 3), cache keys include the resolved groups (week 7), and agent tools take the session principal (week 5).
- **With an ANN index,** a selective filter starves recall: HNSW finds k neighbours, then the filter discards most of them. That's why D7 measures it, and ADR-0020's partitioning note applies.
- **Measured (spec 0007 Part B, [journal 24 Oct](../journal/2026-10-24-part-b.md)):** on an HNSW copy with iterative scans off, the filter starves recall. At k=20, narrow (1.15%) got 3.6 of 20 results (ANN recall 0.178), agency (32.46%) 6.2 (0.311), and even the ~98% personas returned fewer than 20 on about a quarter of questions. **When production gets an ANN index, use `hnsw.iterative_scan = relaxed_order`, with three conditions:**
  - an outer query re-sorts by distance and then `chunk_id`, because relaxed_order can return rows slightly out of order, and citation numbers and rank metrics depend on order
  - the setting is applied with `SET LOCAL` in each query's transaction, so it neither leaks nor gets lost behind a connection pooler
  - a result with fewer than k rows is logged, because the scan stops quietly at `hnsw.max_scan_tuples`

  In the run, relaxed_order returned k every time, with ANN recall within about 0.03 of admin's unfiltered HNSW ceiling (0.981 at ef_search 40) and fact recall equal to exact. Fact recall rests on 17 to 32 rows per persona. At these selectivities, partitioning by group isn't needed. Revisit `max_scan_tuples` or partitioning if the corpus grows (the 20,000-tuple cap covers most of today's 22k-row graph) or a persona's share falls well below 1%, or if the tail latency (narrow p95 18.4 ms vs 1.4–1.8 ms for the ~98% personas, run `2026-10-24-ddf4a2dc`) matters.
- **The quality set stays comparable:** it runs as admin, so with exact search its top 5 is identical to run `2026-10-21-d83f3edc`, the retrieval-only baseline of the default model (ADR-0022; was `2026-10-19-d2625d91` before the model change, spec 0007 amended 22 Oct).

## Informed by
- [Reading log, week 2: permission models in production RAG](../reading/week-02.md#permission-models-in-production-rag)
- [ADR-0011](0011-acls-deferred-from-quality-set.md)
