"""Agent session state in Postgres (spec 0013, AC-6, AC-12, AC-13).

Every write commits, so no transaction stays open across model calls. A turn is claimed by one
UPDATE that checks the version read and an expired or empty lease.
"""

import uuid
from dataclasses import dataclass, field

from psycopg.types.json import Jsonb

from handbook_rag.constants import AGENT_SCHEMA

# The header keys that bind a session (AC-6); resuming with any of them different fails.
BINDING_KEYS = (
    "user_id",
    "policy_version",
    "policy_sha256",
    "identities_version",
    "identities_sha256",
)


class SessionBusy(RuntimeError):
    """Another turn holds the lease, or the session changed since it was read."""


class SessionMismatch(RuntimeError):
    """Resumed as another user, or after the policy or identities file changed (AC-6)."""


class SessionNotFound(LookupError):
    pass


@dataclass
class Session:
    session_id: uuid.UUID
    user_id: str
    header: dict  # JSON-serialisable (AC-12)
    version: int
    turns: list[dict] = field(default_factory=list)  # records ordered by turn_no, from 1


def ensure_schema(conn) -> None:
    """Run AGENT_SCHEMA (idempotent) and commit. The paid path only; the dry run writes nothing."""
    conn.execute(AGENT_SCHEMA.read_text())
    conn.commit()


def tables_exist(conn) -> bool:
    """Both agent tables exist. Read-only (the dry run, AC-16)."""
    row = conn.execute(
        "SELECT to_regclass('agent_sessions') IS NOT NULL "
        "AND to_regclass('agent_turns') IS NOT NULL"
    ).fetchone()
    conn.rollback()  # end the read's transaction
    return bool(row[0])


def create(conn, header: dict) -> Session:
    """Insert a new session (version 0, no lease) and commit. header must hold session_id
    (a uuid string) and user_id."""
    session_id = uuid.UUID(str(header["session_id"]))
    user_id = header["user_id"]
    conn.execute(
        "INSERT INTO agent_sessions (session_id, user_id, header, version, lease_until) "
        "VALUES (%s, %s, %s, 0, NULL)",
        (session_id, user_id, Jsonb(header)),
    )
    conn.commit()
    return Session(session_id=session_id, user_id=user_id, header=header, version=0)


def load(conn, session_id: uuid.UUID | str) -> Session:
    """The session and its turn records. Raises SessionNotFound."""
    sid = uuid.UUID(str(session_id))
    row = conn.execute(
        "SELECT user_id, header, version FROM agent_sessions WHERE session_id = %s", (sid,)
    ).fetchone()
    if row is None:
        conn.rollback()
        raise SessionNotFound(f"no session {sid}")
    turns = conn.execute(
        "SELECT record FROM agent_turns WHERE session_id = %s ORDER BY turn_no", (sid,)
    ).fetchall()
    conn.rollback()  # end the reads' transaction
    return Session(
        session_id=sid,
        user_id=row[0],
        header=row[1],
        version=row[2],
        turns=[t[0] for t in turns],
    )


def check_binding(header: dict, current: dict) -> None:
    """AC-6: raise SessionMismatch, telling the user to start a new session, if any BINDING_KEYS
    value differs between the stored header and the current run."""
    changed = [k for k in BINDING_KEYS if header.get(k) != current.get(k)]
    if changed:
        raise SessionMismatch(
            f"session was started with different {', '.join(changed)}; "
            "start a new session (omit SESSION=)"
        )


def claim(conn, session: Session, lease_s: float) -> None:
    """AC-13: one UPDATE ... SET version = version + 1, lease_until = now() + lease_s seconds
    WHERE session_id AND version = session.version AND (lease_until IS NULL OR < now()).
    Commits. On success session.version is incremented; otherwise raises SessionBusy
    ("session busy; retry") and nothing changes."""
    cur = conn.execute(
        "UPDATE agent_sessions SET version = version + 1, "
        "lease_until = now() + make_interval(secs => %s), updated_at = now() "
        "WHERE session_id = %s AND version = %s AND (lease_until IS NULL OR lease_until < now())",
        (lease_s, session.session_id, session.version),
    )
    claimed = cur.rowcount == 1
    conn.commit()
    if not claimed:
        raise SessionBusy("session busy; retry")
    session.version += 1


def save_turn(conn, session_id: uuid.UUID | str, turn_no: int, record: dict) -> None:
    """Upsert one turn record, bump the session version and commit (after every step, AC-13)."""
    sid = uuid.UUID(str(session_id))
    conn.rollback()  # end any read or failed transaction (a DB error mid-turn); writes commit
    conn.execute(
        "INSERT INTO agent_turns (session_id, turn_no, record) VALUES (%s, %s, %s) "
        "ON CONFLICT (session_id, turn_no) DO UPDATE SET record = EXCLUDED.record",
        (sid, turn_no, Jsonb(record)),
    )
    # Every save bumps the version, so a run that read the session before this turn's records
    # existed can't claim it afterwards and overwrite them (AC-13).
    conn.execute(
        "UPDATE agent_sessions SET version = version + 1, updated_at = now() WHERE session_id = %s",
        (sid,),
    )
    conn.commit()


def release(conn, session_id: uuid.UUID | str) -> None:
    """Clear lease_until and commit (the turn's terminal state, AC-13)."""
    conn.rollback()  # as in save_turn: a failed transaction must not keep the lease held
    conn.execute(
        "UPDATE agent_sessions SET lease_until = NULL WHERE session_id = %s",
        (uuid.UUID(str(session_id)),),
    )
    conn.commit()


__all__ = [
    "AGENT_SCHEMA",
    "BINDING_KEYS",
    "Session",
    "SessionBusy",
    "SessionMismatch",
    "SessionNotFound",
    "check_binding",
    "claim",
    "create",
    "ensure_schema",
    "load",
    "release",
    "save_turn",
    "tables_exist",
]
