# 0002. Ingest mirrors the snapshot; keep redirect stubs, skip drafts

- **Status:** accepted
- **Date:** 2026-10-07
- **Journal:** [2026-10-07 corpus and ingestion](../journal/2026-10-07-corpus-and-ingestion.md)

## Context
- Ingestion (spec 0002) result: 4,177 found, 4,088 ingested, 89 skipped (85 empty_body, 4 draft). It takes ~1.7s, and a re-run is identical.
- Without mirroring, a skip-rule change or a re-pin that drops a page (e.g. a page pulled from public) would leave stale rows that retrieval could still serve.
- Plan-gate catch: the first plan skipped `redirect_to:` stubs as noise. Checking the 6 files showed 4 carry rename knowledge found nowhere else (`production/readiness.md`: "PRR retired, replaced by PREP"), the same class as the HelpLab → Compass eval traps. The other 2 are empty anyway.
- Front matter is metadata, and the title is stored separately.

## Decision
- Each ingest mirrors the snapshot: upsert, then delete rows not in the ingested set, in one transaction.
- The rule to skip redirect stubs was dropped, and redirect stubs with a body are ingested.
- Drafts are skipped because they're unpublished: a citation would 404, and they're templates and WIP.
- `body` stores the markdown after the front matter, unmodified (shortcodes kept).

## Consequences
- If a stub outranks its target, evals will show it, and the fix then is to store `redirect_to` and follow it at retrieval.
- Unverified: that the site's Hugo config doesn't build drafts. The config is outside the sparse checkout.
