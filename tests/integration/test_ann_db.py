"""Spec 0007 Part B (AC-17) on the live DB: the HNSW copy, its freshness check, its plan, its
predicate, and the production exact path left as it was.

Seeded random vectors under SEED_MODEL, a copy built from them, all inside one rolled-back
transaction: no paid embeddings, and a real schema ann (if `make ann-build` ran) is restored
afterwards. Assumes `make acl` has run, as test_retrieve_db does.
"""

import random

import psycopg
import pytest
from fakes import make_principal

from handbook_rag import acl, identity
from handbook_rag.ask import SEARCH, search
from handbook_rag.constants import BASELINE_CONFIG, DEFAULT_EMBED_MODEL
from handbook_rag.db import connect, vector_literal
from handbook_rag.evaluation import ann

pytestmark = pytest.mark.integration

SEED_MODEL = "test:ann-seed"  # vectors seeded here, never by `make embed`
NARROW = make_principal("new-contractor")
# Random 1536-d vectors for every chunk new-contractor sees plus the first 1500 by chunk_id.
SEED = """
INSERT INTO chunk_embeddings (chunk_id, model, embedding)
SELECT c.chunk_id, %(model)s,
       (SELECT array_agg(random() - 0.5) FROM generate_series(1, 1536) WHERE c.chunk_id IS NOT NULL)
       ::vector
FROM chunks c
WHERE c.config_id = 'fixed-512-64' AND (c.allowed_groups && '{new-contractor}' OR c.chunk_id IN
      (SELECT chunk_id FROM chunks WHERE config_id = 'fixed-512-64' ORDER BY chunk_id LIMIT 1500))
"""


def _q(rng) -> str:
    return vector_literal([rng.uniform(-0.5, 0.5) for _ in range(1536)])


@pytest.fixture(scope="module")
def built():
    """(conn, rng, admin principal) with the copy built from SEED_MODEL; rolled back at the end."""
    try:
        conn = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    with conn, conn.transaction(force_rollback=True):
        conn.execute("SELECT setseed(0.20261024)")
        seeded = conn.execute(SEED, {"model": SEED_MODEL}).rowcount
        assert seeded > 1500, "no chunk visible to new-contractor; run `make acl`"
        stats = ann.build(conn, SEED_MODEL)
        assert stats["rows"] == seeded and stats["m"] == 16 and stats["ef_construction"] == 64
        yield conn, random.Random(20261024), identity.load("admin", acl.load_policy(conn))


def _nodes(plan: dict) -> list[dict]:
    out = [plan]
    for child in plan.get("Plans", ()):
        out += _nodes(child)
    return out


def test_production_search_still_scans_exactly(built):
    """AC-17: with the copy and its HNSW index present, SEARCH sorts a scan of
    public.chunk_embeddings; no index on that table's embedding exists; nothing reads schema ann."""
    conn, rng, admin = built
    params = {
        "q": _q(rng),
        "model": DEFAULT_EMBED_MODEL,
        "k": 5,
        "config_id": BASELINE_CONFIG,
        "groups": admin.group_list,
    }
    (plan,) = conn.execute("EXPLAIN (FORMAT JSON, VERBOSE) " + SEARCH, params).fetchone()
    nodes = _nodes(plan[0]["Plan"])
    assert any("Sort" in n["Node Type"] for n in nodes)
    scans = [n for n in nodes if n.get("Relation Name") == "chunk_embeddings"]
    assert scans and all(n["Node Type"] == "Seq Scan" for n in scans)
    assert all(n.get("Schema", "public") == "public" for n in nodes)
    assert not any("hnsw" in n.get("Index Name", "") for n in nodes)
    indexes = conn.execute(
        "SELECT indexdef FROM pg_indexes WHERE schemaname = 'public' "
        "AND tablename = 'chunk_embeddings'"
    ).fetchall()
    assert not [d for (d,) in indexes if "embedding" in d and "hnsw" in d.lower()]
    assert not [d for (d,) in indexes if "(embedding" in d]


def test_admin_exact_results_unchanged_by_the_copy(built):
    """AC-17 (AC-9 after Part B): admin's exact top 5 is the same with and without schema ann."""
    conn, rng, admin = built
    qs = [_q(rng) for _ in range(5)]
    with_copy = [search(conn, q, SEED_MODEL, admin, 5, BASELINE_CONFIG) for q in qs]
    with conn.transaction(force_rollback=True):
        conn.execute("DROP SCHEMA ann CASCADE")
        without = [search(conn, q, SEED_MODEL, admin, 5, BASELINE_CONFIG) for q in qs]
    assert [[r.chunk_id for r in rs] for rs in with_copy] == [
        [r.chunk_id for r in rs] for rs in without
    ]


@pytest.mark.parametrize("mode", ann.HNSW_ITERATIVE_SCANS)
def test_ann_plan_uses_the_hnsw_index(built, mode):
    """AC-17: under every iterative_scan setting, ANN_SEARCH walks the HNSW index, for a broad and
    a narrow principal."""
    conn, rng, admin = built
    for principal in (admin, NARROW):
        with conn.transaction(force_rollback=True), ann.hnsw_mode(conn, mode):
            nodes = ann.plan_nodes(conn, _q(rng), principal, 20)
        assert ann.uses_hnsw(nodes), nodes


@pytest.mark.parametrize("mode", ann.HNSW_ITERATIVE_SCANS)
def test_ann_results_stay_within_the_principals_groups(built, mode):
    """AC-17 via AC-8: every HNSW result shares a group with the principal."""
    conn, rng, _ = built
    with conn.transaction(force_rollback=True), ann.hnsw_mode(conn, mode):
        got = ann.hnsw_search(conn, _q(rng), NARROW, 10)
    for chunk_id, _ in got:
        (groups,) = conn.execute(
            "SELECT allowed_groups FROM chunks WHERE chunk_id = %s", (chunk_id,)
        ).fetchone()
        assert set(groups) & NARROW.groups


def test_strict_iterative_scan_fills_k_for_a_narrow_principal(built):
    """AC-18 premise: an iterative scan keeps walking until k visible rows are found."""
    conn, rng, _ = built
    with conn.transaction(force_rollback=True), ann.hnsw_mode(conn, "strict_order"):
        assert len(ann.hnsw_search(conn, _q(rng), NARROW, 10)) == 10


def test_unknown_mode_is_refused(built):
    conn, _, _ = built
    with pytest.raises(ValueError), ann.hnsw_mode(conn, "on"):
        pass


def test_check_fresh_passes_after_build(built):
    """AC-17 via AC-4/AC-5: the copy matches its source row for row."""
    conn, _, _ = built
    ann.check_fresh(conn, SEED_MODEL)
    settings = ann.index_settings(conn)
    assert (settings["m"], settings["ef_construction"]) == (16, 64)
    assert settings["build"]["model"] == SEED_MODEL


@pytest.mark.parametrize(
    "tamper",
    [
        "UPDATE ann.hnsw_chunks SET allowed_groups = '{people-ops}' WHERE chunk_id = "
        "(SELECT chunk_id FROM ann.hnsw_chunks WHERE allowed_groups <> '{people-ops}' LIMIT 1)",
        "UPDATE ann.hnsw_chunks SET embedding = array_fill(0.1, ARRAY[1536])::vector "
        "WHERE chunk_id = (SELECT min(chunk_id::text)::uuid FROM ann.hnsw_chunks)",
        "DELETE FROM ann.hnsw_chunks WHERE chunk_id = (SELECT min(chunk_id::text)::uuid "
        "FROM ann.hnsw_chunks)",
        "UPDATE chunks SET allowed_groups = '{people-ops}' WHERE chunk_id = "
        "(SELECT chunk_id FROM ann.hnsw_chunks WHERE allowed_groups <> '{people-ops}' LIMIT 1)",
        "DROP SCHEMA ann CASCADE",
    ],
    ids=["copy-groups", "copy-embedding", "copy-missing-row", "source-groups", "no-copy"],
)
def test_check_fresh_fails_on_drift(built, tamper):
    """AC-17 via AC-4/AC-5: a changed group, a changed embedding, a missing row or no copy at all
    fails the check, naming the command that fixes it."""
    conn, _, _ = built
    with conn.transaction(force_rollback=True):
        conn.execute(tamper)
        with pytest.raises(ann.StaleANN, match="make ann-build"):
            ann.check_fresh(conn, SEED_MODEL)


def test_check_fresh_fails_on_a_new_source_row(built):
    """AC-17: a chunk embedded after the build isn't in the copy."""
    conn, _, _ = built
    with conn.transaction(force_rollback=True):
        conn.execute(
            "INSERT INTO chunk_embeddings (chunk_id, model, embedding) "
            "SELECT chunk_id, %s, array_fill(0.1, ARRAY[1536])::vector FROM chunks "
            "WHERE config_id = 'fixed-512-64' AND chunk_id NOT IN "
            "(SELECT chunk_id FROM ann.hnsw_chunks) LIMIT 1",
            (SEED_MODEL,),
        )
        with pytest.raises(ann.StaleANN, match="make acl"):
            ann.check_fresh(conn, SEED_MODEL)
