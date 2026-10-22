# 2026-10-22: spec 0007 amendment, admin baseline and controls

Amendment to [spec 0007](../../specs/0007-permission-aware-retrieval.md) before the Part A build, after [ADR-0022](../decisions/0022-adopt-text-embedding-3-large-1536.md) made text-embedding-3-large@1536 the default.

## AC-9 baseline
- The admin top-5 regression now compares against `2026-10-21-d83f3edc` (3-large, retrieval-only), not `2026-10-19-d2625d91` (3-small).
- **Why:** the build runs on the default model. Against a 3-small baseline, every model-driven rank change would read as a permission regression, and the check would fail for reasons unrelated to the filter.
- ADR-0021's consequence line was updated to match.

## Controls (AC-15)
- **Gate catch:** AC-15 listed rows 15, 39 and 109 as v1.2 control rows. They were cut on 15 Oct (eval-set-v1.md § 5), so the candidate list is rows 5, 22, 33, 61 and 92.
- **Re-check under 3-large** (Arun approved, 22 Oct): the remaining dropped candidates, rows 22 and 92, against admin's unfiltered top 20 on `fixed-512-64`. The check was run under 3-small first as a sanity pass: both rows failed, which reproduces the original drop.
  - Under 3-large both still fail. Row 22 misses `france-sas.md` and `bv-benefits-belgium.md`. Row 92 misses both its docs (`india-sexual-harassment-policy.md`, `anti-harassment.md`).
  - Cost: 4 query embeddings, about $0.000003.
- **Result:** controls cover rows 5 and 33 (4 cases). Row 61's P-097 and P-098 stay invalid and are not re-targeted. permissions-v1 is unchanged: 50 of 52 cases valid.

---

Prev: [2026-10-21: embedding model comparison, spec 0008](2026-10-21-embedding-comparison.md)
