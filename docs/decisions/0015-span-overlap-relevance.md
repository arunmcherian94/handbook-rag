# 0015. A chunk is relevant if it holds a cited line or a ≥40-char edge piece

- **Status:** accepted
- **Date:** 2026-10-17
- **Journal:** [2026-10-17 eval harness](../journal/2026-10-17-eval-harness.md)

## Context
Limitation recorded 2026-10-16: a cited line longer than the 64-token overlap that straddles a chunk boundary is in no chunk in full, so it can't match. The AC-2 check fails the run if a fact is left unmatchable. If it fires, the decision then is to loosen the rule to span overlap.

It fired. The first smoke run gave row 51 no credit for F2: its rank-1 chunk held 262 of the 345 characters of L417 (the Navan-claim half), but not the whole line. Across the set, 20 of 129 cited lines for required facts (16%) straddle a chunk boundary, affecting 18 required facts.

## Decision
Span overlap adopted (owner, 17 Oct).
- **Rule:** a chunk is relevant if it holds a cited line in full, or a piece of at least 40 normalised characters (`MIN_PIECE`) of that line at the chunk's start or end.
- **Effect:** 19 chunks gain credit, and 23 F3 now matches, so there are no warnings. Rows 49 and 51 move from 0.50 to 1.00 fact recall@5 in the 3-row smoke run.
- **Fixed** for every later experiment.
- **Short cited lines (follow-up, owner-approved, 17 Oct):** a line under 40 characters, such as `{.h2}` or `good intent.`, now matches only as a whole chunk line, not inside a longer line. At the pin this removes no chunk credit: all 55 short cited lines already matched only as whole lines. It's a guard for the week 2 chunkings.
- **Edge fragments (code-review catch, fixed):** the whole-line rule still accepted a chunk's first or last piece, which is usually a fragment the window cut. Those two pieces are now excluded.

## Consequences
- **Limitation (lenient matching):**
  - A piece can be a small share of a long line: 34 F3 matches on 56 of 1,214 characters.
  - Short cited lines match any chunk of the page that contains them, for example 88 F6 `{.h2}` (optional) and 89 F3 `##### France`.
  - Both raise recall slightly. Token IoU (week 2 follow-up) would replace this.
- **Limitation:** a short cited line at the very start of a page body, or at its end when there is no trailing newline, has no overlapping neighbour chunk, so it can't match. The evidence check fails loudly if a required fact hits this. None does at the pin, and the rule removes no credit there.
