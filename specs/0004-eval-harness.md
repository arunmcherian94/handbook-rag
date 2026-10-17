# 0004: Eval harness (retrieval metrics and code checks)

- Status: draft
- Date: 2026-10-16
- Depends on: 0003, eval set v1.2

## Problem

The frozen baseline (spec 0003) has never been measured. Week 1 ends when baseline numbers are committed, and every week 2+ experiment is reported as a delta against them. Without a harness, nothing later is attributable. This spec is the minimum to get those numbers: retrieval metrics and the checks code can decide, with no LLM judge.

## Acceptance criteria

- AC-1: **Eval set parsing.** The harness reads `docs/eval/eval-set-v1.md` into rows: id, type, question, expected docs, facts (with `[required]`/`[optional]`, cited paths and line ranges), expected abstention string for out-of-corpus rows, `recency_basis`. Cut rows are skipped. A malformed row (no question, an answerable row with no `[required]` fact, an unparseable citation) fails the run with the row id.
- AC-2: **Evidence check before any spend.** For every fact, the cited lines are read from the pinned corpus in `data/handbook`. A chunk is *relevant* to a fact if it comes from a cited page and contains at least one cited non-blank line (whitespace-normalised), either in full or, for a line the chunk window cut, as a piece of at least 40 characters at the chunk's start or end (span overlap, adopted 2026-10-17: 20 of 129 required cited lines straddle a boundary). The run fails, naming the row and fact, if a **required** fact's lines aren't found in any stored chunk of its page. Unmatchable optional facts are listed as warnings, since no retrieval metric uses them (decided 2026-10-16). Relevance is string matching against chunk text, so a fact that can't match would be scored as a retrieval miss on every run without any error. Causes the pin doesn't prevent:
  - chunks are token windows, so a long line straddling a boundary may be in no chunk in full
  - a wrong line range, for example one pointing at front matter, which ingest strips
  - week 2 changes to the stored text
- AC-3: **Retrieval metrics, answerable rows only**, at k = 1, 3, 5:
  - **Chunk level (headline):**
    - **fact recall@k** = required facts with at least one relevant chunk in the top k ÷ the row's required facts. A fact counts once however many of its chunks are retrieved, and any of its cited sources satisfies it. Required facts with no citation are answer-only. They're excluded from the retrieval denominators and listed. A row with no cited required fact (row 22) has no retrieval score (decided 2026-10-16).
    - **all-required@k** = 1 if every required fact is covered, else 0.
    - hit@k, MRR and binary nDCG@5 over chunks relevant to a required fact.
  - **Page level (diagnostic):** fact recall@k = required facts with at least one cited page in the top k ÷ required facts. hit@k, MRR and binary nDCG@5 over `expected_docs`. Each page counts once, at its best rank.
  - **Retrieved tokens:** the total token count of the top k chunks, averaged over rows, reported next to recall. It matters once chunk size changes, since bigger chunks can raise recall just by covering more text.
  - Rows with a page hit but no relevant chunk at k = 5 are listed (chunking problem).
  - Metrics are pure functions over ranked lists and relevance sets.
- AC-4: **Abstention**, exact string match:
  - out-of-corpus rows pass only if the answer equals the row's expected string (after trimming whitespace)
  - false abstention = answerable rows whose answer is either fixed string
  - diagnostic labels, no score impact: `abstain+extra` (starts with a fixed string, has more text), `wrong-string` (the other fixed string)
- AC-5: **Code checks on answers** (answerable rows, non-abstentions): at least one citation; every cited number in range (from spec 0003's `invalid_citations`); every cited chunk's heading exists in its page at the pin; no URL in the answer. Truncation is reported.
- AC-6: **Run metadata** in every run: eval-set version and sha256 of the eval file, harness git SHA (and whether the tree was dirty), corpus SHA, chunk parameters, embed model, answer model, sha256 of the system prompt, k, timestamp, row count, mode.
- AC-7: **Outputs** in `runs/eval/<YYYY-MM-DD>-<short-id>/`:
  - `rows.jsonl`: one line per row, with retrieved chunk ids, ranks, distances, relevance per chunk, per-row metrics, answer, citations, check results and labels
  - `summary.json` and `summary.md`: every metric overall and by row type and by `recency_basis`; each rate with its standard error and n; the rows whose conflict isn't scored (50, 53, 58) listed
- AC-8: **Cost guard.** `make eval` prints the row count, the mode and an estimated cost, and spends only with `CONFIRM=1`. `LIMIT=n` runs the first n rows. `RETRIEVAL_ONLY=1` skips the answer model (embedding cost only; AC-4 and AC-5 not run).
- AC-9: **Tests.** Unit tests for every metric, including hand-worked cases (one relevant item at rank 3 gives nDCG 0.50; relevant at ranks 1 and 4 out of two gives 0.88), the relevance rule, the parser (one well-formed and one malformed row per field), abstention labels and code checks. The runner is tested with the existing fakes. No test calls an API or needs a key. Existing tests stay green; ruff is clean.

## Out of scope

- LLM judges, fact scoring of answers, faithfulness and answer relevance (after coded traces, per NOTES (f))
- precision@k, MAP@k, graded nDCG, token precision/IoU, equal-token-budget comparison
- trace viewer, observability tooling, dashboards, UI
- leak metric, permissions, ACL cases
- any change to chunking, retrieval, the prompt or models
- editing eval rows

## Decisions

| Decision | Chosen | Rejected alternatives and why |
|---|---|---|
| Relevance | Binary | **Graded:** v1.2 has no grades. Follow-up in NOTES. |
| k | 1, 3, 5 | **Above 5:** nothing past rank 5 is retrieved. |
| Headline level | Chunk; page as diagnostic | **Page only:** hides "right page, wrong chunk" (6 of 10 seed traces). |
| Labels | Text spans (fact → page + lines), fixed across chunkings, mapped onto each chunking by a rule chosen up front (as in Chroma's chunking evaluation) | **Labelled chunk ids** (LlamaIndex, BEIR style): break on any chunking change in week 2. |
| Chunk relevance | Contains a cited evidence line, in full or as a ≥40-character piece of a line cut at the chunk edge (span overlap, 2026-10-17) | **Same heading:** long sections span many chunks. **Full line only:** the first smoke run showed it under-credits 16% of required cited lines that straddle a boundary. Known lenient for facts spanning several chunks and for short cited lines. Kept constant across experiments. |
| Recall unit | Fact recall: required facts, any cited source satisfies (as in RAGAS and DeepEval context recall, computed from labels instead of an LLM) | **Textbook chunk recall:** overlap and alternative pages inflate the denominator, and that denominator shifts with the chunking. **Pages:** a fact can cite two alternative pages; 25 fact citations point outside `expected_docs`. |
| Rank metrics | Over chunks relevant to a required fact | **Any fact:** a row could score hit = 1 with recall = 0. |
| Abstention | Exact match | **Starts with:** passes off-topic answers that add training-knowledge text. |
| Comparability | Compare runs only within one eval-set version and hash | **Compare across versions:** an eval change moves scores of an unchanged system (NOTES (b)). |
| Dependencies | None new | Metrics are a few lines each; no IR library needed. |

## Open questions

None.

## Verification

- `make eval RETRIEVAL_ONLY=1 LIMIT=3` runs and writes a run folder; the evidence check passes on all rows.
- The full run (answers included) happens only after Arun's go-ahead on the printed estimate.
- Spot-check 3 rows of `rows.jsonl` by hand against the retrieved chunks.
- Baseline commit: the full run's `summary.md` and `summary.json` are copied to `docs/eval/results/<run-id>/` (runs/ stays gitignored).
- `make test` and `make lint` pass.

Before the implementation PR:

- [ ] `make test` and `make lint` pass
- [ ] `/code-review` run, findings ranked: must-fix items fixed, lower-priority items confirmed with a human
- [ ] Clean-room verified
- [ ] NOTES.md updated
