# Reading log: week 3

Notes from reading done for handbook-rag. Each entry: link, summary,
and what it changes in this project. Newest first within each date.

---

## Thu 29 Oct 2026

### Hybrid search: Postgres full-text search, Reciprocal Rank Fusion

For spec 0011, hybrid search. *Arun read all four sources and wrote questions and short takeaways. At his request, Claude read the same sources, answered the questions and added the trade-offs; Arun reviews (29 Oct). The local checks are in the note at the end.*

**RRF in brief.** Reciprocal Rank Fusion merges ranked lists using only each item's rank. Each list adds 1 / (k + rank) to an item's score, and an item missing from a list adds nothing; then the items are sorted by the total. An item ranked well in both lists beats one ranked well in only one. Scores are never compared, so the lists can come from systems whose scores mean different things, such as `ts_rank_cd` and cosine distance.

Takeaways:
- **Hybrid search adds exact-term matching to meaning matching.** Lexical search finds the literal words: acronyms (PTO), names, codes, policy titles. Dense search finds paraphrases and related meaning. Each catches misses the other makes.
- **Postgres FTS gives us lexical search with no new dependency, but it is not BM25.** `ts_rank_cd` scores a chunk from its own text only: term counts and how close the terms sit. It has no IDF, so a common word like "team" counts as much as a rare one like "POSH".
- **Query parsing decides recall before ranking does.** `websearch_to_tsquery` and `plainto_tsquery` both AND every term. On a full question, few chunks hold every word.
- **RRF needs no training data and no score calibration.** That suits us: 32 rows can't train or tune a fusion model.
- **k = 60 is a fixed smoothing constant, not a count of relevant documents.** With only two lists, though, k and the list depth decide which items can reach the top 5 (Q5 below).

| Source | Date | My takeaway | Decisions informed |
|---|---|---|---|
| [PostgreSQL docs, §12.3 Controlling Text Search](https://www.postgresql.org/docs/current/textsearch-controls.html): §12.3.2 Parsing Queries, §12.3.3 Ranking Search Results | current (v18) | There are four query parsers. `to_tsquery` takes operator syntax and errors on raw input. `plainto_tsquery` ANDs the words. `phraseto_tsquery` requires them in sequence. `websearch_to_tsquery` takes search-box syntax (quotes for phrases, `or`, `-` for NOT) and never errors. `ts_rank_cd` adds proximity (cover density) to term frequency and needs positions in the tsvector. The normalization options divide by chunk length or unique words; none uses corpus-wide statistics. | Query parsing (Q1), ranking and normalization (Q2), "not BM25" (Q3) |
| [PostgreSQL docs, §12.2 Tables and Indexes](https://www.postgresql.org/docs/current/textsearch-tables.html), §12.2.2 Creating Indexes | current (v18) | A stored generated `tsvector` column plus a GIN index is the documented pattern. `to_tsvector` must name its config ('english') so the index doesn't depend on a session setting. A stored column is faster to search than an expression index because matches aren't re-parsed on a recheck, and `ts_rank_cd` needs the `tsvector` anyway. | Generated column (Q4) |
| [Cormack, Clarke and Büttcher, Reciprocal Rank Fusion outperforms Condorcet and Individual Rank Learning Methods](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) (SIGIR 2009) | 2009 | RRF score = Σ 1/(k + rank). k = 60 was fixed in a pilot on one TREC collection (30 configurations of one search engine) and not changed afterwards. The pilot's MAP barely moves between k = 10 and 100, and is worse at 0 and at 500. RRF beat Condorcet in every run and the best single system in most. On LETOR 3, fusing the learning-to-rank baselines beat each of them, though CombMNZ was slightly ahead and not significantly. RRF uses ranks only and needs no global information. | RRF over score fusion and learning to rank; k = 60 as an untuned constant (Q5, Q6) |
| [Supabase, Hybrid search](https://supabase.com/docs/guides/ai/hybrid-search) | undated | A clear worked example in one SQL function. It uses a generated `fts` column with a GIN index, `websearch_to_tsquery`, ranks from `row_number()` over `ts_rank_cd` and over vector distance, each list fetched at twice the result count, a full outer join on id, and `1/(k + rank)` summed with an optional weight per list (default k = 50). | SQL shape for the plan gate. Our version adds the ACL filter inside both lists, scoping by `config_id`, and handling for empty queries |

#### Questions and answers

**Q1. Why `websearch_to_tsquery`? What about the other parsers?**

| Parser | Pros | Cons for us |
|---|---|---|
| `to_tsquery` | Full control: AND, OR, NOT, phrase, prefix, weights | Raw user text causes syntax errors, so we would have to build the query string ourselves |
| `plainto_tsquery` | Never errors and ignores operator characters | ANDs every word |
| `phraseto_tsquery` | Exact phrases | Requires the words in sequence, which is stricter still |
| `websearch_to_tsquery` | Never errors; familiar search-box syntax | ANDs unquoted words. A spaced " - " becomes NOT, and "or" becomes OR |
| **OR of the query's lexemes** (built from `to_tsvector` of the question) | Any chunk sharing a term is a candidate, and ranking orders them. Lexical engines such as Lucene/BM25 use OR by default | Many more candidates, so ranking quality matters more; without IDF, common words weigh too much (Q3) |

- **What AND means here:** unquoted words become terms joined by `&` (§12.3.2). After stop words are dropped ("how", "do", "the") and the rest are stemmed ("offices" matches "office"), a chunk must contain every remaining word. That suits short keyword queries ("PTO carryover"), the search-box case `websearch_to_tsquery` was built for. It's too strict for full questions, whose incidental words ("need", "get", "new") rarely all appear in the one chunk that answers. Lexical engines default to OR and let ranking order the candidates; Elasticsearch's `match` query, for example, defaults to OR. A middle option requires a share of the words (Elasticsearch's `minimum_should_match`), but Postgres has no built-in equivalent, and the threshold would be one more constant to tune.
- **Local check on eval v1.2's 33 answerable questions** (match counts only, no scores): with `websearch_to_tsquery`, 18 of the 33 match no chunk at all in `fixed-512-64`, including 65 and 92, the rows FTS was meant to rescue. An FTS list with AND semantics would be empty for most rows, so hybrid would just be dense search.
- **Operator side effects:** "PTO - paid time off" becomes `'pto' & !'paid' & 'time'`. "-pto" alone matches 22,138 of the 22,378 chunks. Row 99 contains "or", which becomes an OR operator.
- **The planned fallback to `plainto_tsquery` never fires usefully.** Both parsers come out empty in exactly the same cases: queries that are only stop words or punctuation ("what is it?", "or", "to be or not to be").
- **Chosen (Arun, 29 Oct):** an OR of the question's lexemes, ranked by `ts_rank_cd`. A question with no lexemes gives an empty FTS list, and hybrid falls back to the dense list, recorded per row. The planned `plainto_tsquery` fallback is dropped.

**Q2. `ts_rank` vs `ts_rank_cd`, and which normalization?**
- `ts_rank_cd` adds proximity to term frequency: chunks where the query terms sit close together score higher. It needs positions in the `tsvector`; `to_tsvector` keeps them.
- Normalization uses the length of the `tsvector` being ranked, which is the chunk. The page length isn't available to it; that is the "no global information" point.
- **Our chunk lengths:** in `fixed-512-64`, the median chunk is 512 tokens and 14.5% are under 400. The short ones are the last chunk of each page.
- **Pick: 0, the default, no length normalization.**
  - Lengths are near-equal, so options 1, 2, 8 and 16 would mostly promote short end-of-page chunks.
  - Option 4 adds a second proximity term on top of cover density, and we have no data to justify it.
  - Option 32 rescales without reordering, and RRF ignores scores anyway.
  - Choosing an option by testing on v1.2 would be tuning.
- *Alternative:* option 1 (divide by 1 + log length) is the mild choice if longer, variable-length chunk configs get FTS later.

**Q3. Global information (IDF), and how this compares with BM25.**
- **What IDF is.** Inverse document frequency gives a term more weight the fewer documents contain it. It is "global" because it needs statistics over the whole corpus, not just the chunk being scored.
- **What Postgres does.** The docs say the ranking functions use no global information. `ts_rank_cd` looks only at the chunk itself.
- **What BM25 adds** on top of term frequency:
  1. **IDF.** In the handbook, "team", "new" and "member" are everywhere; "POSH", "PTO" and "probation" are rare. Without IDF a chunk that repeats "team" can outrank one that mentions "POSH" once. With OR semantics (Q1) this matters more, because every chunk containing "team" becomes a candidate.
  2. **Saturation of term frequency (k1).** The tenth "team" adds little.
  3. **Length normalization against the corpus average (b).**
- **Is BM25 available with pgvector?** Not in pgvector itself, which stores and searches vectors. In Postgres the options are:
  - [ParadeDB `pg_search`](https://www.paradedb.com/blog/introducing-search): built on Tantivy; AGPL licence.
  - [Tiger Data `pg_textsearch`](https://www.postgresql.org/about/news/pg_textsearch-v10-3264): v1.0 in April 2026; PostgreSQL licence.
  - VectorChord-bm25.
  - pgvector's `sparsevec` type (since 0.7.0) holding BM25 or SPLADE term weights computed outside the database.
  - Each of the extensions is a new dependency and needs `shared_preload_libraries`; `sparsevec` needs a weighting pipeline we would build.
- **Decision informed:** spec 0011 uses native FTS, states that it is not BM25, and shows the IDF gap in the diagnosis. A BM25 extension goes to follow-ups if the FTS-only run shows common words crowding out rare ones.

**Q4. A generated column, or a column filled by a script?**

| Option | Pros | Cons |
|---|---|---|
| **Stored generated column** `GENERATED ALWAYS AS (to_tsvector('english', content)) STORED` | Can't go stale or be left NULL; new ingests get it automatically; no ingest code changes; the documented pattern | Computed for every config's rows (about 147k rows, not just the 22k we query); adding it rewrites the table once; changing the expression means dropping and re-adding the column |
| Script-filled column | Can cover just one config; the text can differ by config, e.g. heading weighted higher | Can be NULL or stale after an ingest, so it needs ingest changes plus a stale check |
| Expression index only | No stored column, less disk | Queries must repeat the exact expression; `ts_rank_cd` re-parses each matched chunk |

- **Pick: the generated column on `content`, with a GIN index.**
  - Every chunk config shares one table, so a value derived from the row is the simplest invariant: it is correct for every config by construction.
  - It indexes the same text the `fixed-512-64` dense embedding sees.
  - The stale-FTS check then reduces to "the column and its index exist". An empty column for the active config can only mean the config has no rows.
- *Alternative, not now:* weighting the heading above the body (`setweight(..., 'A')`).

**Q5. Why RRF and not learning to rank? Is k = 60 valid for us?**
- **Learning to rank (LTR)** trains a model on labelled query–document pairs and features. We have 32 eval rows, which is too few to train on, and training on them would leak the eval set.
- **Scope of the paper's LTR result:** the paper fused existing LTR outputs with RRF and beat each one. It did not show RRF replacing LTR trained on raw features.

| Fusion option | Needs | Trade-off |
|---|---|---|
| **RRF** | Nothing; one constant | No training or calibration; ignores score margins |
| Weighted RRF (per-list weights, as in Supabase) | Weights | The weights would have to be tuned |
| Convex combination of normalized scores ([Bruch, Gai and Ingber, TOIS 2023](https://arxiv.org/abs/2210.11934)) | Score normalization plus one weight, tuned on a few examples | They found it beats RRF when tuned, and that RRF is sensitive to k. Tuning on v1.2 would overfit; revisit with the synthetic retrieval set |
| CombMNZ / CombSUM | Score normalization | Higher variance in the paper |
| Condorcet | Pairwise votes | Lost to RRF in every run in the paper |
| Cross-encoder reranking | A model | Complements fusion; spec 0012 |

- **What k is:** a smoothing constant, not the number of relevant documents. Larger k flattens the gap between rank 1 and rank 50; smaller k rewards top ranks more.
- **Where 60 came from:** the paper fixed it in a pilot (one TREC collection, 30 configurations of one engine) and found the results flat between 10 and 100. Supabase defaults to 50. Taking 60 untuned is defensible.
- **What k and depth mean with two lists of 50:** a chunk at rank 1 in one list scores 1/61 ≈ 0.0164. A chunk at rank 50 in both scores 2/110 ≈ 0.0182. So any chunk found by both lists outranks every chunk found by only one. A chunk found only by FTS reaches the fused top 5 only when fewer than five chunks are in both top 50s.
- **Prediction for 65 and 92, written before any run:** even if FTS finds them, they may not make the fused top 5. The targeted table should report both per-list ranks and the fused rank, so the run shows whether this happens.
- **Tie-break.** A dense-only chunk and an FTS-only chunk at the same rank tie exactly (both 1/61 at rank 1). So do mirrored ranks, such as (dense 2, FTS 7) and (dense 7, FTS 2). Every sort needs a final key for the order to be reproducible; Supabase's query has none.
  - **Chosen:** RRF score, then dense rank (a chunk absent from the dense list sorts last), then `chunk_id` (Arun, 29 Oct). Dense is the stronger retriever on our data, so it is the better judge of an exact tie.
  - **Rejected:** `chunk_id` alone. It's deterministic, but which chunk survives at the top-5 boundary would be decided by a UUID.
  - **Dense** here means the embedding list: the question embedded with 3-large and compared with chunk embeddings by cosine distance. The name comes from the vector, 1,536 numbers that are almost all non-zero. Lexical search is the sparse counterpart: one dimension per vocabulary word, almost all zero.
- **Why not weights instead of a tie-break?** Weighted RRF (w_dense/(k + rank) + w_fts/(k + rank)) acts on every chunk, not just ties.
  - With w_fts = 0.5, an FTS-only rank 1 (0.0082) loses even to a dense-only rank 50 (0.0091).
  - That changes the top 5 broadly, and the weight is a constant that would have to be tuned on v1.2.
  - Ties still need a final key with unequal weights.
  - So spec 0011 uses equal weights (plain RRF), and weighted RRF is a follow-up for a larger tuning set.

**Q6. Why ranks and not scores?**
- `ts_rank_cd` is unbounded, depends on the normalization option, and higher is better. Cosine distance runs from 0 to 2, and lower is better.
- Adding the raw scores would mean min-max or z-score normalization per query, which is fragile with a few outliers and unstable when one list is short.
- Ranks are on the same scale by construction, so RRF needs no calibration. The cost is that it ignores margins: a clear winner and a near-tie at rank 1 count the same.

*Claude's note, fact-checks and local checks, not Arun's takeaways:*
- **Sources:** the paper's text, its Table 1 (k sweep) and Table 3 (LETOR 3) were read from the PDF. The Postgres and Supabase pages were fetched on 29 Oct.
- **Postgres docs gap:** the docs don't describe empty queries. The NOTICE "text-search query contains only stop words or doesn't contain lexemes, ignored" was observed locally on Postgres 17.11.
- **Local checks** (match counts, the parsed outputs in Q1, chunk lengths) ran on the local DB, `fixed-512-64`, eval v1.2 questions. They count matches only; no ranking or metric was computed on v1.2.
- **Typo case:** row 87's question contains a typo, "competitior", which can only match the same typo in the corpus. Dense search is robust to spelling; FTS isn't.
- **BM25 extension details** come from secondary sources (search on 29 Oct). Check each project's docs before adopting one.
- **Arun's "contextually related"** was reworded as meaning matching (semantic): it means paraphrase, not surrounding context.
