CREATE TABLE IF NOT EXISTS documents (
    doc_id      uuid PRIMARY KEY,
    path        text NOT NULL UNIQUE,
    url_path    text NOT NULL,
    title       text NOT NULL,
    body        text NOT NULL,
    source_type text NOT NULL DEFAULT 'unclassified',
    acl_tags    text[] NOT NULL DEFAULT '{}',
    commit_sha  text NOT NULL,
    commit_date timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now()
);

-- Fail closed (spec 0007, AC-2): a document nobody tagged matches no group. Only ALTER when the
-- default differs: ALTER TABLE takes an exclusive lock even when it changes nothing.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'documents' AND column_name = 'acl_tags'
                 AND column_default IS DISTINCT FROM '''{}''::text[]') THEN
        ALTER TABLE documents ALTER COLUMN acl_tags SET DEFAULT '{}';
    END IF;
END $$;
