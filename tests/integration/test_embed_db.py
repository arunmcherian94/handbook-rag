import psycopg
import pytest
from fakes import FakeEmbedder

from handbook_rag.db import connect
from handbook_rag.embed import run

pytestmark = pytest.mark.integration

MODEL = "fake:embed-test"
SCOPE = 300
BATCH = 64


def flat(embedder):
    return [t for call in embedder.calls for t in call]


@pytest.fixture
def conn():
    try:
        conn = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    with conn:
        if conn.execute("SELECT count(*) FROM chunks").fetchone()[0] < SCOPE:
            pytest.fail("Run `make chunk` first.")
        conn.execute("DELETE FROM chunk_embeddings WHERE model = %s", (MODEL,))
        # Temp view shadows `chunks` for this session: run() sees a fixed universe of SCOPE chunks.
        conn.execute(
            "CREATE TEMP VIEW chunks AS SELECT * FROM public.chunks "
            f"ORDER BY chunk_id LIMIT {SCOPE}"
        )
        conn.commit()
        yield conn
        conn.rollback()
        conn.execute("DELETE FROM chunk_embeddings WHERE model = %s", (MODEL,))
        conn.commit()


def test_crash_resume_and_idempotent_rerun(conn):
    """AC-4: committed batches survive a crash; resume sends only the rest; re-run sends nothing."""
    contents = [r[0] for r in conn.execute("SELECT content FROM chunks ORDER BY chunk_id")]
    assert len(contents) == SCOPE
    other = "SELECT count(*) FROM chunk_embeddings WHERE model <> %s"
    others_before = conn.execute(other, (MODEL,)).fetchone()[0]

    crashing = FakeEmbedder(name=MODEL, fail_after=2)
    with pytest.raises(RuntimeError):
        run(conn, crashing, batch=BATCH)
    count = "SELECT count(*) FROM chunk_embeddings WHERE model = %s"
    assert conn.execute(count, (MODEL,)).fetchone()[0] == 2 * BATCH
    assert [t for c in crashing.calls[:2] for t in c] == contents[: 2 * BATCH]

    resumed = FakeEmbedder(name=MODEL)
    s = run(conn, resumed, batch=BATCH)
    assert flat(resumed) == contents[2 * BATCH :]  # nothing re-sent, nothing missed
    assert (s.embedded, s.skipped, s.ok) == (SCOPE - 2 * BATCH, 2 * BATCH, True)
    assert conn.execute(count, (MODEL,)).fetchone()[0] == SCOPE

    third = FakeEmbedder(name=MODEL)
    s = run(conn, third, batch=BATCH)
    assert third.calls == []
    assert (s.embedded, s.skipped) == (0, SCOPE)

    assert conn.execute(other, (MODEL,)).fetchone()[0] == others_before


def test_rows_shape(conn):
    """AC-4: rows record the model and the vector dimension."""
    run(conn, FakeEmbedder(name=MODEL), batch=BATCH, limit=20)
    rows = conn.execute(
        "SELECT model, vector_dims(embedding) FROM chunk_embeddings WHERE model = %s", (MODEL,)
    ).fetchall()
    assert len(rows) == 20 and set(rows) == {(MODEL, 256)}


def test_vector_for_changed_chunk_is_not_stored(conn):
    """AC-2/AC-4: if a chunk's text changes while it is being embedded, its vector is dropped."""
    (target,) = conn.execute("SELECT chunk_id FROM chunks ORDER BY chunk_id LIMIT 1").fetchone()

    class EditingEmbedder(FakeEmbedder):
        def embed(self, texts):  # a concurrent `make chunk` rewrites the chunk mid-request
            other.execute("UPDATE chunks SET content = content || ' (edited)' WHERE chunk_id = %s",
                          (target,))  # fmt: skip
            other.commit()
            return super().embed(texts)

    other = connect()
    try:
        s = run(conn, EditingEmbedder(name=MODEL), batch=BATCH, limit=5)
        stored = conn.execute(
            "SELECT chunk_id FROM chunk_embeddings WHERE model = %s", (MODEL,)
        ).fetchall()
        assert s.embedded == 4 and (target,) not in stored and len(stored) == 4
    finally:
        other.execute(
            "UPDATE chunks SET content = left(content, -length(' (edited)')) WHERE chunk_id = %s",
            (target,),
        )
        other.commit()
        other.close()
