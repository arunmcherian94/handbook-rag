import re
import uuid
from pathlib import Path

import psycopg
import pytest
from fakes import FakeEmbedder, bow_vector, make_principal

from handbook_rag import acl, identity
from handbook_rag.ask import SEARCH, retrieve, search
from handbook_rag.db import connect, vector_literal

pytestmark = pytest.mark.integration

# Spec 0007, AC-8: people-ops is on every policy rule, so this principal sees every document
# once `make acl` has run (test chunks below are inserted with the same group).
ADMIN_LIKE = make_principal("people-ops")
SRC = Path(__file__).resolve().parents[2] / "src"
LARGE = "openai:text-embedding-3-large@1536"

INSERT = "INSERT INTO chunk_embeddings (chunk_id, model, embedding) VALUES (%s, %s, %s::vector)"
MODEL = "fake:retrieve-test"
OTHER = "fake:retrieve-other"
TITLE = "fake:retrieve-title"
DECOY = "test-decoy"


def _clean(conn):
    conn.execute("DELETE FROM chunk_embeddings WHERE model = ANY(%s)", ([MODEL, OTHER, TITLE],))
    conn.execute("DELETE FROM chunks WHERE config_id = %s", (DECOY,))
    conn.execute("DELETE FROM chunk_configs WHERE config_id = %s", (DECOY,))
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
            "SELECT chunk_id, content, doc_id FROM chunks WHERE config_id = 'fixed-512-64' "
            "ORDER BY chunk_id LIMIT 50"
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
    got = retrieve(conn, FakeEmbedder(name=MODEL), query, ADMIN_LIKE, k=5)
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
    assert len(retrieve(conn, FakeEmbedder(name=MODEL), query, ADMIN_LIKE, k=3)) == 3


def test_retrieve_unknown_model_is_empty(seeded):
    """AC-5: a model with no embeddings yields nothing."""
    conn, _, _, query = seeded
    assert retrieve(conn, FakeEmbedder(name="fake:no-rows"), query, ADMIN_LIKE, k=5) == []


def test_missing_heading_falls_back_to_doc_title(seeded):
    """AC-6: a chunk with no section heading is cited by its document title."""
    conn, _, _, _ = seeded
    chunk_id, content, title = conn.execute(
        """SELECT c.chunk_id, c.content, d.title FROM chunks c JOIN documents d USING (doc_id)
           WHERE c.heading IS NULL AND c.config_id = 'fixed-512-64' ORDER BY c.chunk_id LIMIT 1"""
    ).fetchone()
    conn.execute(INSERT, (chunk_id, TITLE, vector_literal(bow_vector(content))))
    got = retrieve(conn, FakeEmbedder(name=TITLE), content, ADMIN_LIKE, k=1)
    (hit,) = got
    assert hit.chunk_id == chunk_id
    assert hit.heading == title


def test_other_config_chunks_never_returned(seeded):
    """AC-4: a chunk of another config, embedded exactly on the query, is not returned for the
    baseline config; retrieving with its own config returns it."""
    conn, rows, target, query = seeded
    decoy_id = uuid.uuid4()
    conn.execute(
        "INSERT INTO chunk_configs (config_id, strategy, params, tokenizer) "
        "VALUES (%s, 'fixed', '{}', 'cl100k_base')",
        (DECOY,),
    )
    conn.execute(
        "INSERT INTO chunks (chunk_id, doc_id, chunk_index, content, token_count, chunk_size, "
        "chunk_overlap, tokenizer, commit_sha, config_id, allowed_groups) "
        "VALUES (%s, %s, 0, 'decoy', 1, 1, 0, 'cl100k_base', 'x', %s, '{people-ops}')",
        (decoy_id, target[2], DECOY),
    )
    conn.execute(INSERT, (decoy_id, MODEL, vector_literal(bow_vector(query))))
    embedder = FakeEmbedder(name=MODEL)
    assert decoy_id not in {g.chunk_id for g in retrieve(conn, embedder, query, ADMIN_LIKE, k=10)}
    assert [
        g.chunk_id for g in retrieve(conn, embedder, query, ADMIN_LIKE, k=10, config_id=DECOY)
    ] == [decoy_id]


@pytest.mark.parametrize("config_id", ["structural-v2", "fixed-512-64-prefixed"])
def test_new_configs_are_scoped(seeded, config_id):
    """Spec 0006 AC-1: chunks of a new config, embedded exactly on the query, are returned only
    when retrieving with that config."""
    conn, rows, target, query = seeded
    exists = conn.execute(
        "SELECT 1 FROM chunk_configs WHERE config_id = %s", (config_id,)
    ).fetchone()
    new_id = uuid.uuid4()
    if not exists:
        conn.execute(
            "INSERT INTO chunk_configs (config_id, strategy, params, tokenizer) "
            "VALUES (%s, 'fixed', '{}', 'cl100k_base')",
            (config_id,),
        )
    conn.execute(
        "INSERT INTO chunks (chunk_id, doc_id, chunk_index, content, token_count, chunk_size, "
        "chunk_overlap, tokenizer, commit_sha, config_id, allowed_groups) "
        "VALUES (%s, %s, 0, 'new config', 1, 1, 0, 'cl100k_base', 'x', %s, '{people-ops}')",
        (new_id, target[2], config_id),
    )
    conn.execute(INSERT, (new_id, MODEL, vector_literal(bow_vector(query))))
    embedder = FakeEmbedder(name=MODEL)
    assert new_id not in {g.chunk_id for g in retrieve(conn, embedder, query, ADMIN_LIKE, k=10)}
    assert [
        g.chunk_id for g in retrieve(conn, embedder, query, ADMIN_LIKE, k=10, config_id=config_id)
    ] == [new_id]


# --- Spec 0007, AC-8 / AC-9 ---------------------------------------------------------------------


def _stored_vectors(conn, n):
    """n stored 3-large vectors of fixed-512-64 chunks as query literals (no API call)."""
    rows = conn.execute(
        "SELECT e.embedding::text FROM chunk_embeddings e JOIN chunks c USING (chunk_id) "
        "WHERE e.model = %s AND c.config_id = 'fixed-512-64' ORDER BY c.chunk_id LIMIT %s",
        (LARGE, n),
    ).fetchall()
    if len(rows) < n:
        pytest.fail(f"need {n} stored {LARGE} vectors for fixed-512-64. Run `make embed` first.")
    return [r[0] for r in rows]


def test_search_filters_by_groups():
    """Spec 0007, AC-8: a principal with a group no chunk has gets nothing; every chunk returned
    for a narrow principal has an allowed group in common with it. Assumes `make acl` has run
    (decision approved by Arun): on the old '{public}' data the narrow principal gets [].
    """
    with connect() as conn:
        (q,) = _stored_vectors(conn, 1)
        nobody = make_principal("no-such-group")
        assert search(conn, q, LARGE, nobody, 5, "fixed-512-64") == []
        # Query from a chunk the narrow principal may see, so the result is non-empty.
        narrow = make_principal("new-contractor")
        (visible,) = conn.execute(
            "SELECT e.embedding::text FROM chunk_embeddings e JOIN chunks c USING (chunk_id) "
            "WHERE e.model = %s AND c.config_id = 'fixed-512-64' "
            "AND c.allowed_groups && %s::text[] ORDER BY c.chunk_id LIMIT 1",
            (LARGE, narrow.group_list),
        ).fetchone() or (None,)
        assert visible is not None, "no chunk visible to new-contractor; run `make acl`"
        got = search(conn, visible, LARGE, narrow, 10, "fixed-512-64")
        assert got
        for g in got:
            (groups,) = conn.execute(
                "SELECT allowed_groups FROM chunks WHERE chunk_id = %s", (g.chunk_id,)
            ).fetchone()
            assert set(groups) & narrow.groups


def _sql_literals():
    """(file, string) for every string literal under src/ (SQL lives in plain str constants)."""
    import ast

    for path in sorted(SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                yield path.relative_to(SRC), node.value


def test_every_vector_query_has_the_predicate():
    """Spec 0007, AC-8: every SQL literal that ranks by a pgvector operator filters on
    allowed_groups. The scan must find at least the SEARCH query."""
    found = [(f, t) for f, t in _sql_literals() if re.search(r"<=>|<#>|<->", t)]
    assert any("handbook_rag/ask.py" in str(f) for f, _ in found)
    for f, t in found:
        assert "allowed_groups &&" in t, f"{f}: vector query without the ACL predicate:\n{t}"


# Chunk text selected outside a user-serving path (spec 0007, AC-8; approved by Arun).
EXEMPT_CONTENT_READS = {
    "handbook_rag/chunk.py": "ingestion diff against stored chunks; never serves a user",
    "handbook_rag/embed.py": "pending-chunks query feeding the embedder; never serves a user",
}


def test_chunk_content_reads_have_the_predicate():
    """Spec 0007, AC-8: SQL that selects chunk content FROM chunks (fetch by id, not ranking)
    carries the predicate, except evaluation/ and the explicit exempt list with reasons."""
    pattern = re.compile(r"select\b.*?\bcontent\b.*?\bfrom\s+chunks\b", re.I | re.S)
    exempt_hit = set()
    for f, t in _sql_literals():
        key = str(f)
        if not pattern.search(t) or key.startswith("handbook_rag/evaluation/"):
            continue
        if key in EXEMPT_CONTENT_READS:
            exempt_hit.add(key)
            continue
        assert "allowed_groups &&" in t, f"{f}: chunk content read without the predicate:\n{t}"
    assert exempt_hit == set(EXEMPT_CONTENT_READS), (
        "stale exempt list: remove entries that match nothing"
    )


def test_admin_top5_equals_unfiltered_top5():
    """Spec 0007, AC-9 (free proxy): with exact search and an allow-list admitting every document,
    admin's top 5 equals the top 5 of SEARCH with the predicate removed, in order, for 33 stored
    3-large queries. Needs `make acl`."""
    unfiltered = re.sub(r"\n\s*AND c\.allowed_groups && %\(groups\)s::text\[\]", "", SEARCH)
    assert unfiltered != SEARCH
    with connect() as conn:
        admin = identity.load("admin", acl.load_policy(conn))
        for q in _stored_vectors(conn, 33):
            params = {"q": q, "model": LARGE, "k": 5, "config_id": "fixed-512-64"}
            want = [r[0] for r in conn.execute(unfiltered, params).fetchall()]
            got = [g.chunk_id for g in search(conn, q, LARGE, admin, 5, "fixed-512-64")]
            assert got == want
