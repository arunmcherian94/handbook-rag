CREATE TABLE IF NOT EXISTS chunks (
    chunk_id      uuid PRIMARY KEY,
    doc_id        uuid NOT NULL REFERENCES documents (doc_id) ON DELETE CASCADE,
    chunk_index   integer NOT NULL,
    content       text NOT NULL,
    token_count   integer NOT NULL,
    heading       text,
    chunk_size    integer NOT NULL,
    chunk_overlap integer NOT NULL,
    tokenizer     text NOT NULL,
    commit_sha    text NOT NULL
);

-- Cascaded document deletes (ingest) look chunks up by doc_id.
CREATE INDEX IF NOT EXISTS chunks_doc_id_idx ON chunks (doc_id);

-- Untyped vector: models of different dimensions coexist. No ANN index (spec 0003).
CREATE TABLE IF NOT EXISTS chunk_embeddings (
    chunk_id  uuid NOT NULL REFERENCES chunks (chunk_id) ON DELETE CASCADE,
    model     text NOT NULL,
    embedding vector NOT NULL,
    PRIMARY KEY (chunk_id, model)
);

-- Chunk configs coexist (spec 0005, AC-1, AC-2; ADR-0020). Idempotent: `make chunk` re-runs it.
-- Configs are defined in code (constants.CHUNK_CONFIGS); chunk.register_config records each
-- one and fails if the stored row differs. The baseline row is seeded here for the backfill.
CREATE TABLE IF NOT EXISTS chunk_configs (
    config_id  text PRIMARY KEY,
    strategy   text NOT NULL,
    params     jsonb NOT NULL,
    tokenizer  text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO chunk_configs (config_id, strategy, params, tokenizer)
VALUES ('fixed-512-64', 'fixed', '{"size": 512, "overlap": 64}', 'cl100k_base')
ON CONFLICT (config_id) DO NOTHING;

-- Only when the columns are missing: ALTER TABLE takes an exclusive lock even when it changes
-- nothing, and chunk.run holds its transaction for the whole chunk run.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'chunks' AND column_name = 'config_id') THEN
        ALTER TABLE chunks ADD COLUMN config_id text REFERENCES chunk_configs (config_id),
                           ADD COLUMN heading_path text[],
                           ADD COLUMN line_start integer,
                           ADD COLUMN line_end integer;
        UPDATE chunks SET config_id = 'fixed-512-64';
        ALTER TABLE chunks ALTER COLUMN config_id SET NOT NULL;
    END IF;
END $$;

-- Every reader filters on config_id (AC-4).
CREATE INDEX IF NOT EXISTS chunks_config_id_idx ON chunks (config_id);

-- Chunks carry their document's allow-list (spec 0007, AC-2); `make chunk` copies it on insert.
-- An empty array matches no `&&` filter, so it fails closed (non-empty is the AC-4 test).
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'chunks' AND column_name = 'allowed_groups') THEN
        ALTER TABLE chunks ADD COLUMN allowed_groups text[];
        UPDATE chunks c SET allowed_groups = d.acl_tags FROM documents d WHERE d.doc_id = c.doc_id;
        ALTER TABLE chunks ALTER COLUMN allowed_groups SET NOT NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS chunks_allowed_groups_idx ON chunks USING gin (allowed_groups);

-- Spec 0011, AC-1: the FTS vector is generated from content, so it can't go stale or be NULL
-- in any config, and no code writes it. Two-argument to_tsvector: independent of
-- default_text_search_config. Guarded like the blocks above (adding it rewrites the table once).
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'chunks' AND column_name = 'fts') THEN
        ALTER TABLE chunks ADD COLUMN fts tsvector
            GENERATED ALWAYS AS (to_tsvector('english', content)) STORED;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS chunks_fts_idx ON chunks USING gin (fts);
