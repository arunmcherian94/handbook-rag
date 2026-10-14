# Eval set: how the candidates were built (2026-10-14)

Status: **82 UNVERIFIED candidates.** No answers or expected docs yet.
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

## Why no corpus access during generation
Questions written from pages reuse the pages' wording, which inflates
retrieval scores. They also favour easy single-section answers, and they
leak answers into the questions. Grounding happens at verification, where
anything that can't be grounded is cut or moved to out-of-corpus.

## Open
- The restricted rule needs exact paths and a fix: "entity-specific benefits"
  would also hide the Contractor Benefits section, which contractors must see.
  It should cover employee-only benefits and compensation pages instead.
- Contradiction (11) and recency (10) are below their pool targets, which is
  fine for a final set needing about 8 each.
- Near-duplicate pairs left for the final cut: 44/54, 19/84/78, 20/79, 18/75.
