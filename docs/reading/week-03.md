# Reading log: week 3

Notes from reading done for handbook-rag. Each entry: link, summary,
and what it changes in this project. Newest first within each date.

---

## Sat 31 Oct 2026

### Cross-encoder reranking: candidate models, truncation, hosted APIs

For spec 0012, a cross-encoder reranker over dense candidates. Max lengths come from each model's card, `config.json` and `tokenizer_config.json`. API prices come from the vendors' own pages. All were read on 31 Oct; Arun reviews.

**Bi-encoder vs cross-encoder in brief.** A bi-encoder (our 3-large retrieval) embeds the query and each chunk separately. Chunk vectors are computed once at ingest, so a query costs one embedding plus a vector search (~100–225 ms exact). A cross-encoder reads the query and one chunk together as one input, with attention across both, and outputs a single relevance score. Nothing can be precomputed, so every query costs one forward pass per candidate. At depth 50 with ~580-token pairs, that is ~29k tokens through the model per query.

Takeaways:
- **Reranking fixes order, not coverage.** It can only reorder the 50 candidates dense search returns. That matches our diagnosis: the best possible top 5 from dense's top 50 scores 0.875, against 0.583 today (run d83f3edc).
- **Truncation decides the model.** A 512-token cl100k chunk is 540–615 tokens in other models' tokenizers. Every model capped at 512 truncates 82–88% of our candidate pairs and loses the chunk's last 54–111 tokens. Long-context models (8192) truncate none.
- **The cost is CPU time, not money, when self-hosted.** Cost grows with depth × pair length (attention is quadratic in length), so reranking will take longer than retrieval. Depth stays at 50, where the ceiling was measured.
- **Hosted rerank APIs exist and are cheap at our scale**, but they add a paid path, a network hop and a model version the vendor controls (see the API table).

- **Decided (Arun, 31 Oct), with reasons and alternatives in [spec 0012's Decisions table](../../specs/0012-cross-encoder-reranker.md#decisions):**
  - **Hosting:** the DeepInfra API, on the existing account and key. Self-hosting gte-modernbert is a follow-up.
  - **Model:** Qwen3-Reranker-4B. It leads 8B on English MTEB-R, costs half as much, and fits every pair (32k).
  - **Truncation:** none. A pair over the limit fails the run; nothing is silently cut.
  - **Depth:** 50, where the 0.875 ceiling was measured. No sweep.
  - **Text sent:** chunk content only, as dense embeds it.
  - **Instruction:** the model's default, sent explicitly.
  - **Comparison:** paired within one run, on the same query vectors. `d83f3edc` is for continuity only.

#### Candidate local models

| Model | Max length (source) | Pairs over the cap | Tail lost when over | Params / weights | Licence | Pros | Cons |
|---|---|---|---|---|---|---|---|
| [`cross-encoder/ms-marco-MiniLM-L6-v2`](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2) | 512 (config, tokenizer) | 85.5% | ~69 tok | 22M / 91 MB | Apache-2.0 | Standard baseline; fastest; ONNX available | Truncates most pairs; trained on MS MARCO short passages |
| [`mixedbread-ai/mxbai-rerank-base-v1`](https://huggingface.co/mixedbread-ai/mxbai-rerank-base-v1) | 512 (config, tokenizer) | 82.5% | ~54 tok | 184M / 369 MB | Apache-2.0 | Strong for its size | Same truncation |
| [`BAAI/bge-reranker-base`](https://huggingface.co/BAAI/bge-reranker-base) | 512 (tokenizer; config 514) | 87.5% | ~111 tok | 278M / 1.1 GB | MIT | Widely used | Worst truncation; Chinese and English focus |
| [`BAAI/bge-reranker-v2-m3`](https://huggingface.co/BAAI/bge-reranker-v2-m3) | Card states none; config allows 8192; the card's examples use 512 and 1024 | 0% at 1024 | — | 568M / 2.3 GB | Apache-2.0 | Multilingual, strong | Largest; slow on CPU |
| [`jinaai/jina-reranker-v1-turbo-en`](https://huggingface.co/jinaai/jina-reranker-v1-turbo-en) | 8192 (card, ALiBi); tokenizer says 512 | 0% at 1024 | — | 38M / 76 MB | Apache-2.0 | Small and long-context | Needs `trust_remote_code=True`; older (v1) |
| [`Alibaba-NLP/gte-reranker-modernbert-base`](https://huggingface.co/Alibaba-NLP/gte-reranker-modernbert-base) | 8192 (card, config, tokenizer) | 0% at 1024 | — | 149M / 600 MB | Apache-2.0 | All pairs fit; native in transformers ≥ 4.48, no remote code; ONNX available; best MLDR (long-document) score in IBM's comparison table | 5–10× MiniLM's compute |
| [`ibm-granite/granite-embedding-reranker-english-r2`](https://huggingface.co/ibm-granite/granite-embedding-reranker-english-r2) | Card says 8192; tokenizer says 1124 | 0% at 1024 | — | 149M / 600 MB | Apache-2.0 | Same architecture as gte; trained only on permissively licensed data | Mismatch between card and tokenizer; no ONNX |
| [`Qwen/Qwen3-Reranker-0.6B`](https://huggingface.co/Qwen/Qwen3-Reranker-0.6B) | 32k (card) | 0% | — | 0.6B / 1.2 GB | Apache-2.0 | Strongest on general benchmarks | Scores through an LLM prompt template, not a classifier head; slowest |

- **Expected CPU time for 50 pairs on this M2** is estimated from the parameter counts, not measured: MiniLM-L6 ~0.5–1.5 s, the 149M ModernBERT models ~3–6 s, bge-v2-m3 ~10–20 s, Qwen3-0.6B ~15–30 s. The chosen model gets benchmarked after download.
- **How truncation was measured:** with each model's own tokenizer (tokenizer files only, no weights). The pool was the dense top 50 for the 61 cached v1.x question vectors in `runs/ann/query-vectors.jsonl`: 3,050 pairs, no ACL filter, so the real per-user pools differ slightly. Lengths only; no metric was computed. Across all 22,378 `fixed-512-64` chunks the shares are within 3 points of the pool's.

#### Hosted rerank APIs

| Service | Current models | Context per pair | Billing (vendor page, 31 Oct) | Our eval run (~61 queries × 50 docs) |
|---|---|---|---|---|
| [Voyage AI](https://docs.voyageai.com/docs/pricing) ([reranker docs](https://docs.voyageai.com/docs/reranker)) | rerank-3, rerank-3-lite (rerank-2.5 still available) | 32,000 | $0.05 per 1M tokens (lite $0.02). Billed tokens = query tokens × docs + all doc tokens. First 200M tokens free | ~29k tokens/query → ~1.8M tokens ≈ $0.09 (lite $0.04), inside the free tier |
| [Cohere](https://cohere.com/pricing) ([rerank docs](https://docs.cohere.com/docs/rerank)) | Rerank 5 Pro and Fast (4.0 and 3.5 still listed) | 32,768 (v3.5: 4k) | Per "search unit": one query with up to 100 docs, where each doc over 500 tokens (including the query) is split and counted again. The pricing page gives no per-search price, only dedicated instances (Model Vault) | Our ~560-token docs split in two, so 50 docs → 100 → one unit per query. Price unverified; aggregators quote ~$2 per 1k searches → ~$0.12 |
| [Jina AI](https://jina.ai/reranker/) | jina-reranker-v3.5 (listwise) | 131,072 for the query plus all docs | Token-based; no rate shown on the page | Unverified. The weights are CC BY-NC, so self-hosting it commercially needs a licence |
| [DeepInfra](https://deepinfra.com/models/reranker) ([0.6B](https://deepinfra.com/Qwen/Qwen3-Reranker-0.6B), [4B](https://deepinfra.com/Qwen/Qwen3-Reranker-4B), [8B](https://deepinfra.com/Qwen/Qwen3-Reranker-8B/api)) | Qwen3-Reranker 0.6B / 4B / 8B; also Nemotron-3.5-Rerank-8B | 32,768 | $0.010 / $0.025 / $0.050 per 1M tokens. One `queries`/`documents` pair per array element; optional `instruction`; the response example includes `input_tokens`. No model revision shown | See the cost estimate below |

- **DeepInfra cost estimate** (Qwen3 tokenizer: median pair 531 tokens, plus ~80 for the prompt template, so ~600 tokens per pair and ~30k per query at depth 50):

  | Run | Reranked queries | Tokens | 0.6B | 4B | 8B |
  |---|---|---|---|---|---|
  | Eval (33 answerable rows) | 33 | ~1.0M | $0.010 | $0.025 | $0.050 |
  | Permissions suite (52 cases; acting persona + admin, upper bound) | ≤104 | ≤3.1M | $0.031 | $0.078 | $0.16 |
  | One user query | 1 | ~30k | $0.0003 | $0.00075 | $0.0015 |

  - The ~80-token template is an estimate. Whether DeepInfra bills those tokens isn't stated; the response's `input_tokens` field will tell us.
  - Truncation is 0% at 32k.

- **How the DeepInfra models score** (no independent text-reranker leaderboard ranks them on a common setup; these are the vendors' own numbers):

  | Model | MTEB-R (eng) | MLDR (long docs) | MMTEB-R | FollowIR | Source |
  |---|---|---|---|---|---|
  | BGE-reranker-v2-m3 (reference) | 57.03 | 59.51 | 58.36 | −0.01 | Qwen card |
  | Qwen3-Reranker-0.6B | 65.80 | 67.28 | 66.36 | 5.41 | Qwen card |
  | Qwen3-Reranker-4B | **69.76** | 69.97 | 72.74 | **14.84** | Qwen card |
  | Qwen3-Reranker-8B | 69.02 | **70.19** | **72.94** | 8.05 | Qwen card |
  | Nemotron-3.5-Rerank-8B | — | — | — | — | Its card reports only visual-document benchmarks (ViDoRe v3, MIRACL-VISION), so it can't be compared here |

  - Qwen ran these itself, on the retrieval subsets of MTEB, reranking the top 100 from Qwen3-Embedding-0.6B. Sources: the [Qwen3-Reranker-8B card](https://huggingface.co/Qwen/Qwen3-Reranker-8B) and [the paper](https://arxiv.org/abs/2506.05176).
  - On English, 4B is 0.74 points ahead of 8B, at half the price. 8B leads on long documents and multilingual by about 0.2. Neither gap tells us which will do better on our 33 rows.
  - The [Nemotron card](https://huggingface.co/nvidia/Nemotron-3.5-Rerank-8B-BF16) is under the OpenMDW-1.1 licence, and the model is built for multimodal (page-image) retrieval.
- **Self-hosted vs API:**
  - **Self-hosted:**
    - $0 per query.
    - We pin a weights revision, so runs are reproducible.
    - No data leaves the machine.
    - It needs a new dependency (torch through sentence-transformers, or onnxruntime) and costs CPU time.
  - **API:**
    - No dependency and no local compute.
    - It is a paid path behind the `paid-*` guard.
    - It adds a network hop to the latency.
    - The vendor can update the model behind its name, which weakens run-to-run comparisons.
    - Only ACL-pre-filtered candidates would be sent, so permissions aren't affected.
- **What's commonly used:** Cohere Rerank is the best-known hosted reranker. Among open models, `ms-marco-MiniLM` (speed) and `bge-reranker` (quality) are the usual self-hosted defaults. The 8192-context ModernBERT rerankers (gte, granite) are newer.

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
