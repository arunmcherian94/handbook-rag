# 2026-10-27: answer evaluation, spec 0010

Baseline run `2026-10-21-e602bd95` (3-large@1536, `fixed-512-64`, gpt-5.4-mini). It was resolved by the rule in spec 0010 AC-1. The full table is in [answer-eval.md](../eval/results/2026-10-21-e602bd95/answer-eval.md).

## Classification split (n = 10 false abstentions of 33 answerable)
| class | n | rows |
|---|---|---|
| generator_refusal (all required facts in the top 5) | 2 | 58, 100 |
| partial_retrieval | 3 | 8, 49, 89 |
| retrieval_miss | 4 | 53, 55, 65, 92 |
| not_classifiable (no cited required fact) | 1 | 22 |

- **Retrieval-side cause:** 7 of the 9 classifiable rows are missing a required fact from the top 5.
- **Near misses:** in 5 of those 7 (8, 49, 53, 55, 89), every missing fact sits at rank 6–8 of the stored top 20. Only rows 65 and 92 have a required fact outside the top 20. Row 92's cites were checked against the pin and are correct.
- **Implication:** the retrieval side is mostly a ranking or depth problem at k = 5, not a coverage gap. That points at reranking or k before chunking or embedding changes.
- **Generator refusals:** both are time-off questions, and they share the same two `time-off-types.md` chunks in their top 5. Row 58 is `conflict_unscored`, and its F1 is the "depends on your entity" framing. With n = 2 in one topic, the evidence for prompt work is weak.
- **Row 22:** none of its facts, optional ones included, is in the top 5. It behaves like a retrieval miss, but the spec classes it as not classifiable.
- **Row 65:** it answered with the off-topic string, not the not-found string.

## Answer-content check
- **Scores:** `answer_content_fact_pass` 0.403 ± 0.079 and `answer_content_row_pass` 0.258 ± 0.079, both n = 31. That is 66 expressible facts across 33 eligible rows. Rows 22 and 26 have no expressible fact.
- **What drives the score:**
  - The 11 rows that abstained fail every assertion.
    - **Correction (2026-10-29):** 10 rows abstained on `e602bd95`, not 11; 11 is the 3-small baseline (`18f10293`). 9 of the 10 are scored; row 22 has no expressible fact.
  - Most failures on answered rows are real misses. Rows 32, 59, 38 and 23 answered another path or question, and rows 10 F8, 44 F1 and 52 F2 leave out the newer fact.
- **One known false fail:** row 11 F1. The answer says "request a GitLab-issued laptop", which no variant covers. It was not added, because variants taken from the answers being scored would inflate the score.
- **Limits:**
  - Term rules can't see negation, so in rows 49, 53 and 100 a contradicting answer can still pass.
  - The check means "mentions the key content", not "states it correctly".
  - Paraphrase, extra or wrong claims, and citation support are left to the week 6 judge.

## Assertion provenance
- **Fact lists:** a read-only agent checked the 18 required facts of the 10 auto-reviewed answerable rows against the pin. Arun decided its doubts on rows 22, 23 and 34: keep each fact, and record the doubt in [fact-list-review.md](../eval/fact-list-review.md). v1.3 candidates are in [follow-ups](../follow-ups.md). All 33 answerable rows are eligible.
- **Drafting:** Claude drafted the assertions from each fact's own text only. Abbreviations come from that text, and other variants are paraphrases of it. Arun reviewed every assertion.
- **Five edits, proposed by Claude and approved by Arun:**
  - Variants taken from model memory were removed: DIB, Comms Lead, the DRI expansion, the PTO expansion.
  - Row 65's `no office` variant was removed. It would pass on "no office seating plan".
  - Rows 26 F1 and 13 F1 became `expressible: false`. A yes/no claim can't be checked by terms.
  - Row 59 F4 lost the loose `activity` option.
- **Result:** 7 facts are `expressible: false` and counted for the week 6 judge. They are 13 F1, 22 F1, 26 F1, 50 F1, 58 F1, 87 F1 and 99 F2.

## /code-review catches
- **Fixed:**
  - `--run` on a retrieval-only run crashed with a TypeError, and `--run` never checked for a full run.
  - Duplicate YAML keys silently dropped reviewed assertions.
  - The eval-set SHA was hashed from decoded text, while `run.py` hashes raw bytes, and reads and writes had no explicit UTF-8.
  - A `[rewording: …]` tag stayed in the reference text.
- **Listed for Arun:** see the PR description.

## Spend
- None.
