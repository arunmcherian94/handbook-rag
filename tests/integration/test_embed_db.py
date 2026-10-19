import hashlib

import psycopg
import pytest
from fakes import FakeEmbedder

from handbook_rag.db import connect
from handbook_rag.embed import _prefix_tokens, embed_text, pending_cost, run

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
            f"WHERE config_id = 'fixed-512-64' ORDER BY chunk_id LIMIT {SCOPE}"
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


def test_run_is_scoped_to_config(conn):
    """AC-4: run(config_id=X) embeds, counts and costs only X's chunks."""
    conn.execute("DROP VIEW chunks")
    # Two fake configs over the same universe: even rows 'cfg-a', odd rows 'cfg-b'.
    conn.execute(
        "CREATE TEMP VIEW chunks AS SELECT chunk_id, doc_id, content, token_count, "
        "heading_path, CASE WHEN rn % 2 = 0 THEN 'cfg-a' ELSE 'cfg-b' END AS config_id FROM ("
        "SELECT *, row_number() OVER (ORDER BY chunk_id) AS rn FROM public.chunks "
        f"WHERE config_id = 'fixed-512-64' ORDER BY chunk_id LIMIT {SCOPE}) t"
    )
    conn.commit()
    want = [
        r[0]
        for r in conn.execute(
            "SELECT content FROM chunks WHERE config_id = 'cfg-a' ORDER BY chunk_id"
        )
    ]
    n, tokens = pending_cost(conn, MODEL, "cfg-a")
    assert n == len(want) == SCOPE // 2 and tokens > 0
    assert pending_cost(conn, MODEL, "cfg-a", 10)[0] == 10  # AC-13: limit matches run()

    first = FakeEmbedder(name=MODEL)
    s = run(conn, first, batch=BATCH, limit=10, config_id="cfg-a")
    assert flat(first) == want[:10] and (s.embedded, s.skipped) == (10, 0)

    second = FakeEmbedder(name=MODEL)
    s = run(conn, second, batch=BATCH, config_id="cfg-a")
    assert flat(second) == want[10:] and s.skipped == 10  # SKIPPED counts cfg-a only
    assert pending_cost(conn, MODEL, "cfg-a") == (0, 0)

    other = FakeEmbedder(name=MODEL)
    s = run(conn, other, batch=BATCH, config_id="cfg-b")
    assert s.skipped == 0 and s.embedded == SCOPE // 2  # cfg-a's rows did not count for cfg-b


def test_prefixed_config_sends_prefixed_text_and_costs_prefix(conn):
    """spec 0006 AC-5/AC-10: prefixed text embedded, md5 guard holds, cost adds prefix."""
    conn.execute("DROP VIEW chunks")
    conn.execute(
        "CREATE TEMP VIEW chunks AS SELECT chunk_id, doc_id, content, token_count, heading_path, "
        "'fixed-512-64-prefixed' AS config_id FROM public.chunks "
        f"WHERE config_id = 'fixed-512-64' ORDER BY chunk_id LIMIT {SCOPE}"
    )
    conn.commit()
    rows = conn.execute(
        "SELECT c.chunk_id, d.title, c.heading_path, c.content, c.token_count FROM chunks c "
        "JOIN documents d USING (doc_id) ORDER BY c.chunk_id LIMIT 10"
    ).fetchall()
    want = [embed_text(t, hp, c, "title-path") for _, t, hp, c, _ in rows]
    extra = sum(_prefix_tokens(t, hp, "title-path") for _, t, hp, _, _ in rows)
    assert all(w != r[3] for w, r in zip(want, rows, strict=True)) and extra > 0

    n, tokens = pending_cost(conn, MODEL, "fixed-512-64-prefixed", 10)
    assert n == 10 and tokens == sum(r[4] for r in rows) + extra  # AC-10

    e = FakeEmbedder(name=MODEL)
    s = run(conn, e, batch=BATCH, limit=10, config_id="fixed-512-64-prefixed")
    assert flat(e) == want and s.embedded == 10  # stored rows passed the md5(content) guard
    stored = conn.execute(
        "SELECT count(*) FROM chunk_embeddings WHERE model = %s", (MODEL,)
    ).fetchone()[0]
    assert stored == 10
    assert hashlib.md5(rows[0][3].encode()).hexdigest()  # guard is on content, not sent text
