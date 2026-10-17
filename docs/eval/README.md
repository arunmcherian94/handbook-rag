# Eval set: how the candidates were built (2026-10-14)

Status: **eval set v1.2** ([eval-set-v1.md](eval-set-v1.md), [CHANGELOG](CHANGELOG.md)):
52 rows, 33 answerable / 19 out-of-corpus. Built from the 76 candidates below
(+20 parked permission cases).

## Inputs
- Failure patterns from the seed error analysis
  ([../error-analysis/2026-10-13-seed-traces.md](../error-analysis/2026-10-13-seed-traces.md)):
  retrieved but not used (7/10), answer in a section that starts mid-chunk
  (6/10), right page wrong chunk (6/10), plausible distractors (5/10), stale
  corpus statements (5/10).
- Method from Husain & Shankar (see [../reading/week-01.md](../reading/week-01.md),
  14 Oct): dimensions first, seed tuples, more tuples from an LLM, then
  questions from tuples in a separate prompt.

## Steps
1. **Dimensions brief** ([2026-10-14-dimensions.md](2026-10-14-dimensions.md)):
   six dimensions:
   - question type: the six coverage strata, with out-of-corpus split into
     "in scope but not found" and "off-topic"
   - answer location
   - answer shape
   - phrasing
   - persona, including `unstated`
   - topic

   It also has eight named traps (renames, stale vs current statements,
   "PTO" vs "paid time off"), invalid combinations, target counts and 20 seed
   tuples. Reviewed before generation.
2. **Tuples** ([2026-10-14-tuples.md](2026-10-14-tuples.md)): a fresh
   subagent with only the brief, no corpus access, wrote 65 more tuples
   (85 in total).
3. **Questions:** a second fresh subagent with only the tuples file wrote
   one question per tuple. The split keeps question wording independent of
   the tuple writer.
4. **Additions:**
   - 8 questions written by the owner (rows 86–93, kept verbatim)
   - 10 PTO and holiday questions
   - persona re-tagged: 41 questions don't say who is asking, because real
     users rarely do
5. **First triage:** a third fresh subagent cut 103 → 82.
   - Cuts were duplicates, double-barrelled questions, vague wording and
     invented abbreviations; each cut is listed with its reason.
   - 18 rows were reworded, including 7 restricted questions that no longer
     state the role: access must come from the user's role, not from what
     they type.
   - Mix: 60% answerable / 21% out-of-corpus / 20% restricted.

6. **ACLs deferred (2026-10-15):** the quality set ignores ACLs and runs as
   an all-access user, so it stays identical to the baseline. Permission
   cases (16 restricted, plus 4 role-conflict cases a fresh subagent wrote)
   are parked for week 2. The mix moved to 60 / 40 answerable /
   out-of-corpus, and a fresh subagent added 10 out-of-corpus candidates.
   The quality pool is 76.
7. **References and cut (2026-10-15):** Claude, in a fresh session, drafted
   reference answers for all 76 from the pinned corpus only (fact lists tied
   to excerpts). The owner decided the flagged rows, checked every trap
   verdict, and cut to 54. Details in the CHANGELOG.
8. **Review (2026-10-16):** blind sweep of the 38 unreviewed rows
   ([sweep-2026-10-16.md](sweep-2026-10-16.md)); owner hand-reviewed a seeded
   8-row sample plus 3 more rows, then Claude auto-reviewed the remaining 26 on
   the owner's standing approval. Cut to 52 (v1.1).
9. **Markers (2026-10-16):** `[required]` / `[optional]` on every answerable
   row, owner-approved, so spec 0004 can compute recall over required facts
   (v1.2).

## Why no corpus access during generation
Questions written from pages reuse the pages' wording, which inflates
retrieval scores. They also favour easy single-section answers, and they
leak answers into the questions. Grounding happens at verification, where
anything that can't be grounded is cut or moved to out-of-corpus.

## Open
- Week 2: the restricted rule must not hide the Contractor Benefits
  section; restrict employee-only benefits and compensation pages instead.
- Contradiction (11) and recency (10) leave little slack for a final set
  needing about 8 each.
- Near-duplicate pair left for the final cut: 44/54.
