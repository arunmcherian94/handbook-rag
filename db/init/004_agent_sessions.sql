-- Agent sessions (spec 0013, AC-12, AC-13). Idempotent: the paid agent path re-runs it, because
-- db/init only runs on a fresh volume.
-- A turn is claimed by one UPDATE that checks version and lease_until; no transaction stays open
-- across model calls. header holds the session's binding (user, policy, identities; AC-6).
CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id  uuid PRIMARY KEY,
    user_id     text NOT NULL,
    header      jsonb NOT NULL,
    version     integer NOT NULL DEFAULT 0,
    lease_until timestamptz,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- One record per turn, upserted after every step, so a crash leaves the last complete step.
CREATE TABLE IF NOT EXISTS agent_turns (
    session_id uuid NOT NULL REFERENCES agent_sessions (session_id) ON DELETE CASCADE,
    turn_no    integer NOT NULL,
    record     jsonb NOT NULL,
    PRIMARY KEY (session_id, turn_no)
);
