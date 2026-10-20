# Reading log: week 2

Notes from reading done for handbook-rag. Each entry: link, summary,
and what it changes in this project. Newest first within each date.

---

## Tue 20 Oct 2026

### MTEB caveats

For Wed 21 Oct's embedding-model comparison. *Arun's notes, edited by Claude for accuracy at Arun's request (20 Oct). The Maintaining MTEB and Hugging Face notes were taken together.*

Takeaways:
- **A leaderboard rank needs its zero-shot score next to it.** Top models often get there by training on benchmark tasks.
- **Small rank gaps mean little; large ones are worth trusting directionally.** On our 33 rows, only a large difference will show. So pick candidates well above text-embedding-3-small, then decide on our own data.
- **Rank isn't the only criterion:** context window, language coverage and domain fit matter too.
- **Rankings drift.** Record the date of any leaderboard check (snapshot in [embedding comparison prep, 20 Oct](../journal/2026-10-20-embedding-comparison-prep.md)).

| Source | Date | My takeaway | Decisions informed |
|---|---|---|---|
| [MTEB maintainers, Maintaining MTEB (arXiv 2506.21182)](https://arxiv.org/abs/2506.21182), §5.1 "Case Study 1: Assessing zero-shot levels" in the [full text](https://arxiv.org/html/2506.21182) (the abstract page has no sections); Appendix C defines the score | 2025 | MTEB (Massive Text Embedding Benchmark) has a public leaderboard on Hugging Face. The zero-shot score estimates how much of a model's training data overlaps the benchmark's own training splits. Higher means less overlap: 95% means it trained on about 5% of the splits. Top-ranked models often get there by training on benchmark tasks, so check a model's zero-shot score before trusting its rank. | How to read Wednesday's comparison against leaderboard rank |
| [Hugging Face / lyon-nlp, MTEB Leaderboard: user guide and best practices](https://huggingface.co/blog/lyon-nlp-group/mteb-leaderboard-best-practices) | undated | Models close together on the leaderboard are often not meaningfully different, so a small score gap isn't a reliable ranking. text-embedding-3-small ranks fairly low, so pick candidates well above it, where a real difference can show on our 33 rows. Rank isn't the only criterion: weigh the context window (against our 512-token chunks), multilingual support and fit to our domain (models can do better on particular domains, such as legal). | Treating top leaderboard models as statistically equivalent; leakage and overfitting caveats for Wednesday's comparison |
| [ZeroEntropy, MTEB concept page](https://zeroentropy.dev/concepts/mteb/) | undated | Retrieval labels are mostly binary (relevant or not), so the leaderboard rewards finding a relevant doc more than ranking the most relevant one first. Models that look strong on binary labels can order results poorly, and graded labels reshuffle the ranks. Rank doesn't transfer reliably to private corpora; contamination is one cause. Trust large gaps directionally, then evaluate on our own data, which no candidate has trained on. Rankings drift as datasets are added or re-weighted, so record the leaderboard date or version. | Contamination; "trust directionally, evaluate on your data" for Wednesday's comparison |

*Claude's note on the ZeroEntropy row, not Arun's takeaway:* the page says the labels are "binary", but MTEB's headline retrieval metric is nDCG@10, and some of its datasets have graded labels. Our page metrics are binary too, and graded nDCG is a follow-up. *On the zero-shot row:* "trained on about 5% of the splits" is the paper's own reading of e5-mistral's 95% (§5.1).

Reference only: [Muennighoff et al., MTEB: Massive Text Embedding Benchmark (arXiv 2210.07316)](https://arxiv.org/abs/2210.07316) (2022) and the [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard).

### Permission models in production RAG

*LLM-drafted at Arun's request, Arun-approved (20 Oct).* All nine pages were fetched on 20 Oct; the quotes are from the pages.

Takeaways:
- **Index-time ACLs (early binding) are only as fresh as the sync; strong designs add a fetch-time check.** I chose early binding for v1 and can state the staleness window.
- **The production pattern is the same everywhere:** an allow-list field on each indexed item, a filter on the caller's groups inside the search query, and membership kept outside the index (Elastic, Azure, Cerbos). That is our `allowed_groups && :groups`.
- **Missing must fail closed.** Elastic treats a document with no access field as visible to everyone, a convenient default that is dangerous in a permissions system. Hence NOT NULL, non-empty, and an invariant test over every config.
- **The search engine trusts whatever groups it is given.** Azure says the principal "is just a string", so the guarantee depends on the application resolving groups from the session, never from the request. That's why `Principal` has a single constructor.
- **Filter before ranking, not after.** Post-retrieval checks are flexible, but they hand back fewer than k results, and Cerbos warns they leak through counts and ranking. Pre-filtering keeps both the k and the secret.
- **Hierarchy is the cheap way to scale ACLs.** WorkOS tags by container instead of syncing per-document ACLs. Our path-prefix policy is the same idea resolved at ingestion, so a policy change rewrites arrays but a membership change costs nothing.

| Source | Date | My takeaway | Decisions informed |
|---|---|---|---|
| [Elastic, How DLS works](https://www.elastic.co/docs/reference/search-connectors/es-dls-overview) | undated | Each document carries an allow-list of identities. "If the access control field is present but empty, no identities will have access", but a document with no access-control field has "no restrictions on who can view it". A missing field fails open. | D4, D5 (NOT NULL, non-empty, invariant test) |
| [Elastic, DLS in Search Applications](https://www.elastic.co/docs/reference/search-connectors/es-dls-e2e-guide) | undated | The user's access-control document lives in a separate index and is turned into a query (an API key) over the content index. Membership is kept apart from content. | D4 (groups resolved per request, never stored on chunks) |
| [Elastic Search Labs, Adding DLS to your internal knowledge search](https://www.elastic.co/search-labs/blog/dls-internal-knowledge-search) | 22 Jan 2024 | The motivating case is ours: "Tess (from Engineering) shouldn't be looking at Bob's (from HR) notes on performance reviews." Metadata on documents plus a role-based query filter. | D3 (role/function dimension) |
| [Microsoft, Security filter pattern, Azure AI Search](https://learn.microsoft.com/azure/search/search-security-trimming-for-azure-search) | updated 24 Aug 2026 | A `group_ids` string collection plus a `search.in` filter on the caller's groups. "There's no authentication or authorization through the security principal. The principal is just a string." The application must supply trusted groups. | D4; the Principal guardrail (groups only from the session) |
| [WorkOS, Authorization for RAG at scale](https://workos.com/blog/authorization-for-rag-at-scale-why-you-shouldnt-sync-every-document) | 8 Jan 2026 | "Document access usually follows a hierarchy." Tag vectors with their parent container id and filter locally instead of syncing every document's ACL. That's pattern (b); our path-prefix policy applies the same idea at ingestion. | D2 (path-prefix rules); ADR-0021 alternative (b) |
| [Cerbos, RAG authorization](https://www.cerbos.dev/ecosystem/rag) | undated | The policy is compiled into a query plan and applied as metadata pre-filters. Post-filtering "can leak information through result counts and ranking patterns". | Out-of-scope reason for pattern (c) |
| [Descope, Add ReBAC to your RAG pipeline](https://www.descope.com/blog/post/rebac-rag-tutorial) | 23 Apr 2026 | "Authorization happens between retrieval and generation": a relationship check on each retrieved document. It's flexible (relationships, live state). The page doesn't discuss recall; my inference is that a filtered top k returns fewer than k. | ADR-0021 alternative (c) |
| [Tian Pan, The PII leak in your RAG pipeline](https://tianpan.co/blog/2026-04-19-pii-leak-rag-pipeline-access-control) | 19 Apr 2026 | "Every chunk ingested into the vector store should carry an access control list as metadata." Chunks "may span multiple security domains", so a chunk needs exactly one source of truth for its ACL. | D1; the one-parent-document invariant |
| [Slack, How we built Slack AI to be secure and private](https://slack.engineering/how-we-built-slack-ai-to-be-secure-and-private/) | 18 Apr 2024, updated 17 Jul 2025 | "Slack AI only operates on the data that the user can already see", using "the requesting user's Access Control List (ACLs) when fetching the data". Late binding answers freshness. | Out of scope for v1 (no live source system); ADR-0021 consequence |

---

## Mon 19 Oct 2026

### Yang, Structure-Aware Semantic Chunking with Title-Chain Prefixes (arXiv 2608.00824)

https://arxiv.org/abs/2608.00824 (Aug 2026, single author). Abstract only.

Summary:
- **Pipeline:** a header split, then a semantic merge, then a title-chain prefix. The prefix reuses the document's own header hierarchy, so it adds no LLM calls (unlike contextual retrieval).
- **Setup:** a production Markdown knowledge base, with 1,600 stratified queries. This is close to our corpus.
- **Reported result:** MRR@5 rises from 0.374 to 0.463 on the full set (+23.8%), and from 0.828 to 0.925 on the answerable subset (n=563). Our baseline MRR is 0.380, so the starting points are similar. This is one paper's claim, and I've only read the abstract.
- **Main methodological finding:** in a prefix on/off ablation over the same pool, human annotator agreement fell from κ 0.45 to 0.04 under identical prompts. The paper argues this invalidates a common way of evaluating chunking changes, and recommends judging each retrieved candidate at retrieval time instead.

Takeaway: the title-chain experiment we already have planned makes sense. It costs nothing in LLM calls and fits our heading-structured corpus.

What it changes here:
- **No change to spec 0005.** The title-chain prefix stays a later, separate run, so there is one change per run.
- **It backs one design choice.** Our planned title-chain run changes only the text that gets embedded. Stored chunk content and line ranges stay fixed, and relevance comes from fixed text-span labels rather than from annotators rating what they see. So the labelling trap the paper reports doesn't apply to us ([ADR-0020](../decisions/0020-chunk-configs-coexist.md)).
- **Not adopted:** the semantic merge step. Spec 0005 merges tiny sections by heading structure instead ([ADR-0019](../decisions/0019-structural-first-recursive-inside-chunking.md)).
