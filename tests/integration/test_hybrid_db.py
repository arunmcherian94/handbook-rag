import uuid

import psycopg
import pytest
from fakes import bow_vector, make_principal

from handbook_rag import hybrid
from handbook_rag.constants import BASELINE_CONFIG, CHUNKS_SCHEMA
from handbook_rag.db import connect, vector_literal

pytestmark = pytest.mark.integration

DECOY = "test-hybrid-decoy"
MODEL = "fake:hybrid-test"
TOKEN = "zqxhybridtoken"
OPEN = "test-open"
RESTRICTED = "test-restricted"
INSERT_CHUNK = (
    "INSERT INTO chunks (chunk_id, doc_id, chunk_index, content, token_count, chunk_size, "
    "chunk_overlap, tokenizer, commit_sha, config_id, allowed_groups) "
    "VALUES (%s, %s, %s, %s, 1, 1, 0, 'cl100k_base', 'x', %s, %s)"
)
INSERT_EMBEDDING = (
    "INSERT INTO chunk_embeddings (chunk_id, model, embedding) VALUES (%s, %s, %s::vector)"
)


def _clean(conn):
    conn.execute("DELETE FROM chunk_embeddings WHERE model = %s", (MODEL,))
    conn.execute("DELETE FROM chunks WHERE config_id = %s", (DECOY,))
    conn.execute("DELETE FROM chunk_configs WHERE config_id = %s", (DECOY,))
    conn.commit()


@pytest.fixture
def conn():
    """A connection with an empty decoy config registered; decoy rows are removed afterwards."""
    try:
        conn = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    with conn:
        _clean(conn)
        conn.execute(
            "INSERT INTO chunk_configs (config_id, strategy, params, tokenizer) "
            "VALUES (%s, 'fixed', '{}', 'cl100k_base')",
            (DECOY,),
        )
        conn.commit()
        try:
            yield conn
        finally:
            conn.rollback()
            _clean(conn)


def _doc_id(conn):
    (doc_id,) = conn.execute("SELECT doc_id FROM documents ORDER BY doc_id LIMIT 1").fetchone()
    return doc_id


def _add(conn, content, groups=(OPEN,), chunk_id=None, index=0, embed=False):
    chunk_id = chunk_id or uuid.uuid4()
    conn.execute(
        INSERT_CHUNK,
        (chunk_id, _doc_id(conn), index, content, DECOY, list(groups)),
    )
    if embed:
        conn.execute(INSERT_EMBEDDING, (chunk_id, MODEL, vector_literal(bow_vector(content))))
    return chunk_id


def _column_and_index(conn):
    col = conn.execute(
        "SELECT is_generated, generation_expression FROM information_schema.columns "
        "WHERE table_name = 'chunks' AND column_name = 'fts'"
    ).fetchone()
    idx = conn.execute(
        "SELECT indexdef FROM pg_indexes WHERE indexname = 'chunks_fts_idx'"
    ).fetchone()
    return col, idx


def test_fts_column_and_index(conn):
    """Spec 0011, AC-1: chunks.fts is a generated to_tsvector('english', ...) column with a GIN
    index; applying the schema again changes neither; a plain INSERT fills it."""
    col, idx = _column_and_index(conn)
    assert col[0] == "ALWAYS"
    assert "to_tsvector('english'" in col[1]
    assert idx is not None and "USING gin" in idx[0]

    conn.execute(CHUNKS_SCHEMA.read_text(encoding="utf-8"))
    conn.execute(CHUNKS_SCHEMA.read_text(encoding="utf-8"))
    conn.commit()
    assert _column_and_index(conn) == (col, idx)

    chunk_id = _add(conn, "Paid time off policy for team members")
    (same,) = conn.execute(
        "SELECT fts IS NOT NULL AND fts = to_tsvector('english', content) "
        "FROM chunks WHERE chunk_id = %s",
        (chunk_id,),
    ).fetchone()
    assert same


def test_query_construction(conn):
    """Spec 0011, AC-2 (behaviour needs Postgres, so it is here; the SQL text is pinned in the
    unit tests): operators in the question are plain text, and a stop-word-only question
    yields no query and no results."""
    (text,) = conn.execute(
        f"SELECT ({hybrid.QUERY})::text", {"question": "PTO - paid time off"}
    ).fetchone()
    assert "!" not in text
    assert "'pto'" in text and "'paid'" in text
    p = make_principal(OPEN)
    assert hybrid.search_fts(conn, "what is it?", p, 5, DECOY) == []
    assert hybrid.query_empty(conn, "what is it?") is True
    assert hybrid.query_empty(conn, "paid time off") is False


@pytest.mark.parametrize(
    "question",
    ["it's a o'clock", 'say "hello world"', "back\\slash", "a; DROP TABLE chunks", "cats or dogs"],
)
def test_awkward_questions_run(conn, question):
    """Spec 0011, AC-2: quotes, backslashes, semicolons and `or` don't raise."""
    assert isinstance(hybrid.search_fts(conn, question, make_principal(OPEN), 5, DECOY), list)


def test_fts_ordering_and_ties(conn):
    """Spec 0011, AC-3: results come back by ts_rank_cd descending; identical chunks tie-break
    on chunk_id."""
    hit3 = _add(conn, f"{TOKEN} {TOKEN} {TOKEN}", index=0)
    hit1a = _add(conn, f"{TOKEN} some other words here", chunk_id=uuid.UUID(int=2), index=1)
    hit1b = _add(conn, f"{TOKEN} some other words here", chunk_id=uuid.UUID(int=1), index=2)
    _add(conn, "nothing relevant at all", index=3)
    got = hybrid.search_fts(conn, TOKEN, make_principal(OPEN), 10, DECOY)
    assert [g.chunk_id for g in got] == [hit3, hit1b, hit1a]
    assert [g.fts_rank for g in got] == [1, 2, 3]
    scores = [g.fts_score for g in got]
    assert scores == sorted(scores, reverse=True)
    assert scores[1] == scores[2]
    assert all(g.distance is None for g in got)


def test_fts_scoped_to_config(conn):
    """Spec 0011, AC-3: chunks of another config never come back, and the decoy's own chunk is
    not returned for the baseline."""
    chunk_id = _add(conn, f"{TOKEN} here")
    p = make_principal(OPEN, "people-ops")
    assert hybrid.search_fts(conn, TOKEN, p, 10, BASELINE_CONFIG) == []
    assert [g.chunk_id for g in hybrid.search_fts(conn, TOKEN, p, 10, DECOY)] == [chunk_id]


def test_restricted_chunk_denied_under_fts_and_hybrid(conn):
    """Spec 0011, AC-4: a principal without the chunk's group never gets it from fts or hybrid
    (depth 50); a principal with the group does (positive control)."""
    question = f"{TOKEN} restricted"
    restricted = _add(conn, question, groups=(RESTRICTED,), embed=True)
    q = vector_literal(bow_vector(question))
    staff, insider = make_principal("staff"), make_principal("staff", RESTRICTED)

    assert restricted not in {
        g.chunk_id for g in hybrid.search_fts(conn, question, staff, 50, DECOY)
    }
    for p, expect in ((staff, False), (insider, True)):
        got = hybrid.search(conn, "hybrid", q, question, MODEL, p, 50, DECOY)
        assert (restricted in {g.chunk_id for g in got}) is expect
        got = hybrid.search(conn, "fts", None, question, MODEL, p, 50, DECOY)
        assert (restricted in {g.chunk_id for g in got}) is expect


def test_check_fts_passes_on_real_db(conn):
    """Spec 0011, AC-6: the baseline config passes the stale-FTS check."""
    hybrid.check_fts(conn, BASELINE_CONFIG)


def _rolled_back(conn, statements, match):
    with pytest.raises(hybrid.StaleFTS, match=match):
        with conn.transaction(force_rollback=True):
            for s in statements:
                conn.execute(s)
            hybrid.check_fts(conn, BASELINE_CONFIG)


def test_check_fts_refuses_missing_index_column_and_empty(conn):
    """Spec 0011, AC-6: a missing index, a missing column, and a plain NULL column each raise
    StaleFTS naming the problem; every DDL change is rolled back."""
    before = _column_and_index(conn)
    _rolled_back(conn, ["DROP INDEX chunks_fts_idx"], "chunks_fts_idx")
    assert _column_and_index(conn) == before
    _rolled_back(conn, ["ALTER TABLE chunks DROP COLUMN fts"], r"chunks\.fts")
    assert _column_and_index(conn) == before
    _rolled_back(
        conn,
        [
            "ALTER TABLE chunks DROP COLUMN fts",
            "ALTER TABLE chunks ADD COLUMN fts tsvector",
            "CREATE INDEX chunks_fts_idx ON chunks USING gin (fts)",
        ],
        "no fts",
    )
    assert _column_and_index(conn) == before
