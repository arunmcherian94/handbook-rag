# 0020. Chunk configs coexist in one table, keyed by config_id

- **Status:** accepted (2026-10-20, Arun). Built in specs 0005–0006, except `embed_input`, which spec 0006 superseded (below).
- **Date:** 2026-10-19
- **Journal:** [2026-10-19 chunking spec](../journal/2026-10-19-chunking-spec.md)

## Context
Week 2 compares chunkings against the baseline, so the baseline's 22,378 chunks and their embeddings must survive a second config. Today they can't: five places assume one config.
- `make chunk` deletes every chunk not in the current set.
- Its early-exit check compares against global constants.
- The eval refuses to run unless `chunks` holds exactly one parameter set.
- Retrieval (`SEARCH`) filters only on the embedding model, so two configs would mix.
- The evidence check reads every chunk of a page.

## Decision
- **A `chunk_configs` table** (config_id, strategy, params, tokenizer) and `chunks.config_id` as an FK. Code defines the configs; the table records them, and a run fails if the stored params differ from the code's, so an id never changes meaning.
- **Everything that reads chunks takes a config,** defaulting to the baseline `fixed-512-64`. It is never chosen by a global "active" flag, which would make runs depend on order.
- **Per-chunk metadata:** heading path and file line range.
- **Embedding input, planned for the title-chain run** (superseded by [spec 0006](../../specs/0006-packed-sections-and-heading-prefix.md): the prefix is a config param with its own chunk rows, `fixed-512-64-prefixed`, so no `embed_input` column was built): `chunk_embeddings.embed_input` (default `'content'`), PK `(chunk_id, model, embed_input)`. A retrieval index is then `(config_id, model, embed_input)`. Chunk rows and line ranges stay fixed, so scoring is unaffected. Contextual retrieval would also store its generated text, so re-embedding doesn't change it.

Rejected:
- **Configs in a code dict only:** editing params under an existing id silently mislabels rows already chunked.
- **A table per config:** dynamic table names in five places, and cross-config SQL needs generated UNIONs. Nothing gained with exact search.
- **Encoding the recipe in the model string:** overloads a column the embedder parses to call the API.

## Consequences
- One tested `WHERE` per reader. A forgotten filter mixes configs, so tests cover each reader.
- **Revisit when an ANN index arrives.** HNSW over a shared table with a filter loses recall (the same recall-starvation mode as the ACL pre-filter), and HNSW needs a typed `vector(n)`. Then: LIST-partition `chunks` by `config_id` and `chunk_embeddings` by model, with a typed HNSW index per partition. `config_id` is already the partition key.
- **How production does this:**
  - Each index is versioned and built beside the old one, and an alias is flipped once evals pass.
  - The old index is kept warm for a rollback window.
  - Raw documents are the source of truth, so a deleted index is rebuilt from them.
  - An embedding cache keyed by hash(model, input text) makes re-chunking and switching back cheap.
- Here, every config is kept permanently, which is right for experiments at this size. `chunk_id` is position-based, so identical text in two configs is embedded twice (about $0.02 per pass).
