CREATE TABLE IF NOT EXISTS documents (
    doc_id      uuid PRIMARY KEY,
    path        text NOT NULL UNIQUE,
    url_path    text NOT NULL,
    title       text NOT NULL,
    body        text NOT NULL,
    source_type text NOT NULL DEFAULT 'unclassified',
    acl_tags    text[] NOT NULL DEFAULT '{public}',
    commit_sha  text NOT NULL,
    commit_date timestamptz NOT NULL,
    ingested_at timestamptz NOT NULL DEFAULT now()
);
