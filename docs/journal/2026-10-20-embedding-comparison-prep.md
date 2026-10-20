# 2026-10-20: embedding comparison prep, for spec 0008

Planning for Wed 21 Oct's embedding-model comparison, from today's [MTEB reading](../reading/week-02.md#mteb-caveats). Nothing run, nothing paid.

- **Prefix arm only on a winner** (Arun): every candidate runs on `fixed-512-64`. Only a model that beats 3-small then gets a `fixed-512-64-prefixed` run. 3-small already has both arms (spec 0006: +0.036, within the SE, so it's a tie). Skipping the rest loses only a model-by-prefix interaction, which 33 rows couldn't detect. [Follow-ups](../follow-ups.md#from-the-spec-0006-runs-2026-10-19) updated.
- **Leaderboard snapshot, checked 20 Oct 2026 in the browser** (rankings drift, so it's dated). [MTEB(eng, v2)](https://mteb-leaderboard.hf.space/benchmark/MTEB(eng%2C%20v2)), 188 models:

  | rank | model | zero-shot | mean (task) | retrieval |
  |---|---|---|---|---|
  | #1 | ingot-8b-r3 | 82% | 75.98 | 70.00 |
  | #5 | Qwen3-Embedding-8B | 95% | 75.23 | 69.44 |
  | #7 | Qwen3-Embedding-4B | 95% | 74.61 | 68.46 |
  | #9 | gemini-embedding-001 | 95% | 73.30 | 64.35 |
  | #25 | Qwen3-Embedding-0.6B | 95% | 70.47 | 61.83 |
  | #88 | text-embedding-3-large | NA | — | 57.98 |
  | #116 | text-embedding-3-small (ours) | NA | — | 53.48 |

  Voyage-4 isn't on MTEB(eng, v2). On [RTEB(eng, beta)](https://mteb-leaderboard.hf.space/benchmark/RTEB(eng%2C%20beta)) (retrieval only, legal/finance/code/health, scores hidden, ranks shown): voyage-4-large #1, voyage-4 #12, gemini-embedding-001 #13, Qwen3-Embedding-8B #14, text-embedding-3-large #35.
- **Candidates proposed, Arun to pick in spec 0008:** text-embedding-3-large at 1536 dims (same provider and tokenizer, so only the model changes); gemini-embedding-001 or voyage-4-large; Qwen3-Embedding-8B through a hosted API, or 0.6B locally (no API cost, but torch and about 1–3 h on the M2). The retrieval scores step up clearly (53.5 → 58.0 → 64.4 → 69.4), the kind of gap worth trusting directionally on 33 rows. Pre-set decision rule: adopt only a model that beats 3-small by more than about 2 paired SEs at the matched budget.
- **Provider differences to handle in spec 0008:** chunks stay cl100k-sized, so chunk ids and scoring don't change. Each model's own tokenizer counts more tokens, so the adapter must fail rather than truncate silently. The cost estimate is approximate for non-OpenAI models. Query and document input types (Voyage `input_type`, Gemini `task_type`, the Qwen3 query instruction) must be set, or that model is handicapped. The answer model isn't affected: it sees chunk text only.

---

Prev: [2026-10-20: permissions design records, spec 0007](2026-10-20-permissions-spec.md)
