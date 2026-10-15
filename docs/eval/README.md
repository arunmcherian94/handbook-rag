# Eval set: how the candidates were built (2026-10-14)

Status: **76 UNVERIFIED quality candidates** (+20 parked permission cases). No answers or expected docs yet.
Next: check answerability against the pinned corpus (SHA 5273b21), cut to
50–60, and write every answer and expected doc by hand.

## Inputs
- Failure patterns from the seed error analysis
  ([../error-analysis/2026-10-13-seed-traces.md](../error-analysis/2026-10-13-seed-traces.md)):
  retrieved but not used (7/10), answer in a section that starts mid-chunk
  (6/10), right page wrong chunk (6/10), plausible distractors (5/10), stale
  corpus statements (5/10).
- Method from Husain & Shankar (see [../reading-log.md](../reading-log.md),
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
