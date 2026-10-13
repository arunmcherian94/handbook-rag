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
