import uuid

import psycopg
import pytest
from psycopg.pq import TransactionStatus

from handbook_rag.agent import store
from handbook_rag.agent.store import SessionBusy, SessionNotFound
from handbook_rag.db import connect

pytestmark = pytest.mark.integration


def _idle(conn):
    assert conn.info.transaction_status == TransactionStatus.IDLE


@pytest.fixture
def conn():
    try:
        c = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    store.ensure_schema(c)
    ids: list[uuid.UUID] = []
    c.created = ids  # type: ignore[attr-defined]
    yield c
    if c.closed:
        c = connect()
    c.execute("DELETE FROM agent_sessions WHERE session_id = ANY(%s)", (ids,))
    c.commit()
    c.close()


def _new(conn, **extra):
    sid = uuid.uuid4()
    conn.created.append(sid)
    header = {"session_id": str(sid), "user_id": "alice", "n": 1, **extra}
    return store.create(conn, header)


def test_ensure_schema_idempotent(conn):
    """AC-12: re-running the schema is safe; tables exist."""
    store.ensure_schema(conn)
    _idle(conn)
    assert store.tables_exist(conn)
    _idle(conn)


def test_round_trip(conn):
    """AC-12: header and records come back equal and in turn order."""
    s = _new(conn)
    _idle(conn)
    store.save_turn(conn, s.session_id, 2, {"q": "second"})
    _idle(conn)
    store.save_turn(conn, s.session_id, 1, {"q": "first", "steps": [1, 2]})
    got = store.load(conn, s.session_id)
    _idle(conn)
    assert got.header == s.header
    assert got.user_id == "alice"
    assert got.version == 2  # every save bumps the version
    assert got.turns == [{"q": "first", "steps": [1, 2]}, {"q": "second"}]


def test_two_claims_one_wins(conn):
    """AC-13: two sessions at the same version; the loser fails and changes nothing."""
    s = _new(conn)
    a = store.load(conn, s.session_id)
    b = store.load(conn, s.session_id)
    store.claim(conn, a, 60)
    _idle(conn)
    assert a.version == 1
    with pytest.raises(SessionBusy, match="session busy"):
        store.claim(conn, b, 60)
    _idle(conn)
    assert b.version == 0
    assert store.load(conn, s.session_id).version == 1


def test_held_lease_blocks_fresh_claim(conn):
    """AC-13: a live lease blocks a claim even at the right version."""
    s = _new(conn)
    store.claim(conn, s, 60)
    fresh = store.load(conn, s.session_id)
    assert fresh.version == s.version
    with pytest.raises(SessionBusy):
        store.claim(conn, fresh, 60)


def test_expired_lease_can_be_claimed(conn):
    """AC-13: an already-past lease does not block."""
    s = _new(conn)
    store.claim(conn, s, -1)
    store.claim(conn, store.load(conn, s.session_id), 60)
    assert store.load(conn, s.session_id).version == 2


def test_release_clears_lease(conn):
    """AC-13: release lets the next claim through."""
    s = _new(conn)
    store.claim(conn, s, 60)
    store.release(conn, s.session_id)
    _idle(conn)
    store.claim(conn, store.load(conn, s.session_id), 60)


def test_crash_keeps_saved_step(conn):
    """AC-13: a record saved before a crash survives; the lease blocks until it expires."""
    s = _new(conn)
    store.claim(conn, s, 60)
    store.save_turn(conn, s.session_id, 1, {"step": 1})
    conn.close()  # no release
    c2 = connect()
    try:
        got = store.load(c2, s.session_id)
        assert got.turns == [{"step": 1}]
        with pytest.raises(SessionBusy):
            store.claim(c2, got, 60)
        c2.execute(
            "UPDATE agent_sessions SET lease_until = now() - interval '1 second' "
            "WHERE session_id = %s",
            (s.session_id,),
        )
        c2.commit()
        store.claim(c2, got, 60)
    finally:
        c2.close()


def test_reader_before_a_finished_turn_cannot_claim(conn):
    """AC-13 (review fix): a run that read the session during another turn can't claim it after
    that turn finished and released, so it can't overwrite the finished turn."""
    s = _new(conn)
    store.claim(conn, s, 60)  # run A
    stale = store.load(conn, s.session_id)  # run B reads mid-turn, before A's first save
    store.save_turn(conn, s.session_id, 1, {"a": "done"})
    store.release(conn, s.session_id)
    with pytest.raises(SessionBusy):
        store.claim(conn, stale, 60)
    assert store.load(conn, s.session_id).turns == [{"a": "done"}]


def test_save_and_release_after_a_failed_statement(conn):
    """AC-11/AC-13 (review fix): a DB error mid-turn leaves the connection in a failed
    transaction; the error record is still saved and the lease still released."""
    s = _new(conn)
    store.claim(conn, s, 60)
    with pytest.raises(psycopg.errors.UndefinedTable):
        conn.execute("SELECT * FROM no_such_table")
    store.save_turn(conn, s.session_id, 1, {"state": "error"})
    store.release(conn, s.session_id)
    _idle(conn)
    got = store.load(conn, s.session_id)
    assert got.turns == [{"state": "error"}]
    store.claim(conn, got, 60)  # lease was cleared


def test_upsert_overwrites_turn(conn):
    """AC-13: the same turn_no is replaced, not duplicated."""
    s = _new(conn)
    store.save_turn(conn, s.session_id, 1, {"v": 1})
    store.save_turn(conn, s.session_id, 1, {"v": 2})
    assert store.load(conn, s.session_id).turns == [{"v": 2}]


def test_load_unknown_raises(conn):
    """AC-12: an unknown id is SessionNotFound, with no transaction left open."""
    with pytest.raises(SessionNotFound):
        store.load(conn, uuid.uuid4())
    _idle(conn)
