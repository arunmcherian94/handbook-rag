import psycopg
import pytest
from fakes import FakeEmbedder, bow_vector

from handbook_rag.ask import retrieve
from handbook_rag.db import connect, vector_literal

pytestmark = pytest.mark.integration

INSERT = "INSERT INTO chunk_embeddings (chunk_id, model, embedding) VALUES (%s, %s, %s::vector)"
MODEL = "fake:retrieve-test"
OTHER = "fake:retrieve-other"
TITLE = "fake:retrieve-title"


def _clean(conn):
    conn.execute("DELETE FROM chunk_embeddings WHERE model = ANY(%s)", ([MODEL, OTHER, TITLE],))
    conn.commit()


@pytest.fixture
def seeded():
    """Fake embeddings for 50 chunks under MODEL; decoys under OTHER. Yields (conn, rows, query)."""
    try:
        conn = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    with conn:
        _clean(conn)
        rows = conn.execute(
            "SELECT chunk_id, content, doc_id FROM chunks ORDER BY chunk_id LIMIT 50"
        ).fetchall()
        if len(rows) < 50:
            pytest.fail("chunks table is empty or too small. Run `make chunk` first.")
        target = max(rows, key=lambda r: len(r[1].split()))
        query = " ".join(target[1].split()[:40])
        with conn.cursor() as cur:
            cur.executemany(
                INSERT,
                [(cid, MODEL, vector_literal(bow_vector(content))) for cid, content, _ in rows],
            )
            # Decoys sit exactly on the query: they would win rank 1 if the model filter failed.
            cur.executemany(
                INSERT,
                [(r[0], OTHER, vector_literal(bow_vector(query))) for r in rows[:5] if r != target],
            )
        conn.commit()
        try:
            yield conn, rows, target, query
        finally:
            conn.rollback()
            _clean(conn)


def test_retrieve_exact_order_and_model_filter(seeded):
    """AC-5: target ranks first, distances ascend, only the queried model's rows come back."""
    conn, rows, target, query = seeded
    got = retrieve(conn, FakeEmbedder(name=MODEL), query, k=5)
    assert len(got) == 5
    assert got[0].chunk_id == target[0]
    assert [g.n for g in got] == [1, 2, 3, 4, 5]
    d = [g.distance for g in got]
    assert d == sorted(d)
    assert {g.chunk_id for g in got} <= {r[0] for r in rows}
    for g in got:
        assert g.url_path.startswith("/handbook/")
        (expected,) = conn.execute(
            "SELECT url_path FROM documents WHERE doc_id = %s", (g.doc_id,)
        ).fetchone()
        assert g.url_path == expected


def test_retrieve_respects_k(seeded):
    """AC-5: LIMIT k."""
    conn, _, _, query = seeded
    assert len(retrieve(conn, FakeEmbedder(name=MODEL), query, k=3)) == 3


def test_retrieve_unknown_model_is_empty(seeded):
    """AC-5: a model with no embeddings yields nothing."""
    conn, _, _, query = seeded
    assert retrieve(conn, FakeEmbedder(name="fake:no-rows"), query, k=5) == []


def test_missing_heading_falls_back_to_doc_title(seeded):
    """AC-6: a chunk with no section heading is cited by its document title."""
    conn, _, _, _ = seeded
    chunk_id, content, title = conn.execute(
        """SELECT c.chunk_id, c.content, d.title FROM chunks c JOIN documents d USING (doc_id)
           WHERE c.heading IS NULL ORDER BY c.chunk_id LIMIT 1"""
    ).fetchone()
    conn.execute(INSERT, (chunk_id, TITLE, vector_literal(bow_vector(content))))
    got = retrieve(conn, FakeEmbedder(name=TITLE), content, k=1)
    (hit,) = got
    assert hit.chunk_id == chunk_id
    assert hit.heading == title
