# NOTES

Index of the project notes. The notes themselves live in `docs/`.

| What | Where |
|---|---|
| Weekly summaries | [docs/weekly/](docs/weekly/): [week 1](docs/weekly/week-01.md) |
| Decisions (one ADR each) | [docs/decisions/](docs/decisions/), listed below |
| Dated log: gate catches, findings, limitations | [docs/journal/](docs/journal/), listed below |
| Follow-ups (not built) | [docs/follow-ups.md](docs/follow-ups.md) |
| Corpus: git behaviors, limitations, assumptions | [docs/corpus.md](docs/corpus.md) |
| Reading log | [docs/reading/](docs/reading/): [week 1](docs/reading/week-01.md), [week 2](docs/reading/week-02.md) |
| Eval set, results, metric definitions | [docs/eval/](docs/eval/), [results/metrics.md](docs/eval/results/metrics.md) |

Older specs cite eval decisions by letter. They map to: (a) and (c), (d), (f) → [0016](docs/decisions/0016-code-checks-before-judges.md); (b) → [0012](docs/decisions/0012-eval-versioning.md); (e) → [0011](docs/decisions/0011-acls-deferred-from-quality-set.md); metric questions Q1–Q3 → [0013](docs/decisions/0013-retrieval-metrics.md).

## Decisions

- [0001. Whole handbook at a pinned SHA, blobless sparse clone](docs/decisions/0001-corpus-scope-and-pin.md)
- [0002. Ingest mirrors the snapshot; keep redirect stubs, skip drafts](docs/decisions/0002-ingest-mirrors-snapshot.md)
- [0003. Fixed 512-token chunks with 64 overlap for the baseline](docs/decisions/0003-baseline-chunking-512-64.md)
- [0004. text-embedding-3-small; embeddings keyed (chunk_id, model)](docs/decisions/0004-embedding-model-and-schema.md)
- [0005. gpt-5.4-mini via Chat Completions, frozen through week 3](docs/decisions/0005-answer-model-and-api.md)
- [0006. Strict grounding prompt with two fixed abstention strings](docs/decisions/0006-grounding-prompt-fixed-abstentions.md)
- [0007. Layered embedding failure handling, cheapest isolation first](docs/decisions/0007-embedding-failure-handling.md)
- [0008. Ports and adapters, DI, functional core](docs/decisions/0008-design-patterns.md)
- [0009. Spec-driven workflow with a review gate](docs/decisions/0009-spec-driven-workflow.md)
- [0010. Eval questions human-authored; references from the pin](docs/decisions/0010-eval-questions-human-authored.md)
- [0011. Quality set ignores ACLs; permission cases are a separate suite](docs/decisions/0011-acls-deferred-from-quality-set.md)
- [0012. Versioned eval set; compare runs only within a version](docs/decisions/0012-eval-versioning.md)
- [0013. Chunk-level fact recall@k is the headline retrieval metric](docs/decisions/0013-retrieval-metrics.md)
- [0014. Exact-match abstention scoring with diagnostic labels](docs/decisions/0014-abstention-scoring.md)
- [0015. A chunk is relevant if it holds a cited line or a ≥40-char edge piece](docs/decisions/0015-span-overlap-relevance.md)
- [0016. Grade with code first; judges only for coded failures](docs/decisions/0016-code-checks-before-judges.md)
- [0017. Git history decides currency, never facts](docs/decisions/0017-history-decides-currency.md)
- [0018. Subagents on file-disjoint slices via the orchestrate skill](docs/decisions/0018-subagent-orchestration.md)
- [0019. Structural first, recursive inside: headings bound chunks](docs/decisions/0019-structural-first-recursive-inside-chunking.md) (rejected after spec 0006 runs)
- [0020. Chunk configs coexist in one table, keyed by config_id](docs/decisions/0020-chunk-configs-coexist.md)
- [0021. Document-level group allow-lists on chunks, filtered in SQL; identity from the session](docs/decisions/0021-permission-model.md)
- [0022. Adopt text-embedding-3-large@1536 as the default embedding model (departs from the AC-9 rule)](docs/decisions/0022-adopt-text-embedding-3-large-1536.md)

## Journal

- [2026-10-05: scaffold](docs/journal/2026-10-05-scaffold.md)
- [2026-10-07: corpus and ingestion](docs/journal/2026-10-07-corpus-and-ingestion.md)
- [2026-10-12: baseline decisions, spec 0003](docs/journal/2026-10-12-baseline-decisions.md)
- [2026-10-13: baseline build, spec 0003](docs/journal/2026-10-13-baseline-build.md)
- [2026-10-13: error analysis, seed traces](docs/journal/2026-10-13-error-analysis.md)
- [2026-10-14: eval set design](docs/journal/2026-10-14-eval-set-design.md)
- [2026-10-15: ACLs in evals](docs/journal/2026-10-15-acls-in-evals.md)
- [2026-10-16: eval metric decisions, reading](docs/journal/2026-10-16-eval-metric-decisions.md)
- [2026-10-16: eval set v1.1 review](docs/journal/2026-10-16-eval-set-review.md)
- [2026-10-17: baseline eval numbers](docs/journal/2026-10-17-baseline-numbers.md)
- [2026-10-17: eval harness build, spec 0004](docs/journal/2026-10-17-eval-harness.md)
- [2026-10-17: subagent orchestration](docs/journal/2026-10-17-subagent-orchestration.md)
- [2026-10-19: chunking spec, spec 0005](docs/journal/2026-10-19-chunking-spec.md)
- [2026-10-19: structure-aware chunker build, spec 0005](docs/journal/2026-10-19-chunker-build.md)
- [2026-10-19: packed sections and prefix build, spec 0006](docs/journal/2026-10-19-packed-build.md)
- [2026-10-20: permissions design records, spec 0007](docs/journal/2026-10-20-permissions-spec.md)
- [2026-10-20: embedding comparison prep, for spec 0008](docs/journal/2026-10-20-embedding-comparison-prep.md)
- [2026-10-21: embedding model comparison, spec 0008](docs/journal/2026-10-21-embedding-comparison.md)
