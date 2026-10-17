# 2026-10-17: eval harness build, spec 0004

- **Layout:** `src/handbook_rag/evaluation/`, split like `ask.py` into a pure core and an I/O shell.
  - **Pure:** `evalset` (parser), `metrics`, `checks`, `report`.
  - **I/O:** `evidence` (reads the pin and the chunks table, and is the only owner of the relevance rule) and `run` (the CLI).
  - The model ports are reused from `models/`; nothing new was added.
- **Evidence check fails only on required facts** (owner, 16 Oct). The probe found one unmatchable fact, 23 F3, which is optional. Retrieval metrics count only required facts, so an unmatchable optional fact changes no score. It's listed as a warning.
- **Answer-only facts** (owner, 16 Oct). A fact with no citation tests how the answer behaves, so no chunk can satisfy it. There are two: 22 F1 and 58 F1. They're left out of the retrieval denominators and listed in the summary. Row 22 has no cited required fact left, so it has no retrieval score. It's listed under `no_retrieval_facts` and still counts for abstention and the code checks.
- **Span-overlap relevance:** → [ADR-0015](../decisions/0015-span-overlap-relevance.md)
- **Retrieval metrics:** → [ADR-0013](../decisions/0013-retrieval-metrics.md)
- **Code-review catches (fixed):**
  - `make eval CONFIRM=0` (any non-empty value) passed `--confirm` and spent money. Only `1` counts now.
  - Run metadata took chunk parameters and the corpus SHA from constants and the manifest. They're now read from the stored chunks, and a run fails if the chunks don't match the pin.
  - The headings check compared the DB with itself, so it couldn't fail. It now reads the pinned file, keyed by the cited chunk's document; `url_path` isn't unique.
  - A required fact with a malformed citation (a path with no `L<n>`) silently became answer-only. It now fails parsing. Duplicate row or fact ids also fail.
- **Follow-up fixes (owner-approved lower-priority review items, 17 Oct):**
  - **Standard-error formula:** it's set by metric kind, not inferred from the values. Rates use √(p(1−p)/n). Averages (fact recall, MRR, nDCG, tokens) use the sample sd ÷ √n. An unclassified metric name fails the summary.
  - **Retrieved tokens:** these now use the stored `chunks.token_count` instead of re-encoding the chunk text.
  - **Smaller fixes:** an out-of-range citation now produces one message instead of two, and a file's trailing newline no longer counts as an extra line.
  - **Test fix:** the dry-run test fails with "Run `make corpus` first" when the corpus is missing.
- **Code-review catches on the follow-ups (fixed):**
  - **Metric names:** an unclassified metric crashed only after the paid loop, and names were matched loosely. Classification now uses exact patterns, and a unit test classifies every `row_metrics` key, so `make test` catches a new metric before any spend.
- **Follow-ups (not built, lower priority):**
  - a clear error if a retrieved chunk disappears during a run
  - the "no stored chunk" message per page instead of per fact
  - normalise each chunk once per page instead of once per fact
  - token counts come from a second query per row, because `ask.py` is frozen through week 3; select `token_count` in `ask.SEARCH` when it unfreezes

---

Prev: [2026-10-16: eval metric decisions, reading](2026-10-16-eval-metric-decisions.md) · Next: [2026-10-17: subagent orchestration](2026-10-17-subagent-orchestration.md)
