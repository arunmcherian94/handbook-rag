"""Spec 0007 ACL storage, invariants, stale check and persona shares on the live DB.

These assume `make acl` has run (approved 22 Oct, decision 3), as other integration tests assume
`make ingest` and `make chunk`.
"""

import psycopg
import pytest

from handbook_rag import acl, identity
from handbook_rag.constants import BASELINE_CONFIG
from handbook_rag.db import connect

pytestmark = pytest.mark.integration

HINT = "Database unreachable. Run `cp .env.example .env && make up` first."
# Visible share of fixed-512-64 chunks per persona: the `make acl` dry-run figures (journal 20 Oct).
SHARES = {
    "admin": 100.00,
    "us-ic": 98.62,
    "manager": 98.73,
    "contractor": 98.31,
    "narrow": 1.15,
    "agency": 32.46,
}


@pytest.fixture(scope="module")
def conn():
    try:
        c = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"{HINT} ({type(e).__name__}: {e})")
    with c:
        yield c


@pytest.fixture(scope="module")
def policy(conn):
    return acl.load_policy(conn)


def test_restricted_from_staff_at_pin(conn):
    """Spec 0007, AC-2: 46 docs / 379 fixed-512-64 chunks are restricted from staff."""
    docs, chunks = conn.execute(
        "SELECT count(DISTINCT d.doc_id), count(*) FROM chunks c JOIN documents d USING (doc_id) "
        "WHERE c.config_id = %s AND NOT d.acl_tags @> '{staff}'",
        (BASELINE_CONFIG,),
    ).fetchone()
    assert (docs, chunks) == (46, 379)


def test_apply_is_idempotent(conn, policy):
    """Spec 0007, AC-2: re-applying the policy changes no rows."""
    with conn.transaction(force_rollback=True):
        assert acl.apply(conn, acl.expected_acls(conn, policy)) == (0, 0)


def test_every_chunk_has_one_parent(conn):
    """Spec 0007, AC-4: every chunk of every config has exactly one parent document."""
    (orphans,) = conn.execute(
        "SELECT count(*) FROM chunks c LEFT JOIN documents d USING (doc_id) WHERE d.doc_id IS NULL"
    ).fetchone()
    (fk,) = conn.execute(
        "SELECT count(*) FROM pg_constraint WHERE conrelid = 'chunks'::regclass AND contype = 'f' "
        "AND conkey = ARRAY[(SELECT attnum FROM pg_attribute "
        "WHERE attrelid = 'chunks'::regclass AND attname = 'doc_id')]"
    ).fetchone()
    assert orphans == 0
    assert fk == 1


def test_no_chunk_has_empty_groups(conn):
    """Spec 0007, AC-4: no chunk in any config has a null or empty allowed_groups."""
    (bad,) = conn.execute(
        "SELECT count(*) FROM chunks "
        "WHERE allowed_groups IS NULL OR cardinality(allowed_groups) = 0"
    ).fetchone()
    assert bad == 0


def test_chunk_groups_equal_parent_acl(conn):
    """Spec 0007, AC-4: each chunk's allowed_groups equals its parent's acl_tags, every config."""
    (bad,) = conn.execute(
        "SELECT count(*) FROM chunks c JOIN documents d USING (doc_id) "
        "WHERE c.allowed_groups IS DISTINCT FROM d.acl_tags"
    ).fetchone()
    configs = {r[0] for r in conn.execute("SELECT DISTINCT config_id FROM chunks").fetchall()}
    assert bad == 0
    assert len(configs) >= 5


def test_stale_check_passes_after_make_acl(conn, policy):
    """Spec 0007, AC-5: the stored ACLs match the policy file."""
    acl.check_stale(conn, policy)


@pytest.mark.parametrize(
    "tamper",
    [
        "UPDATE chunks SET allowed_groups = '{people-ops}' WHERE chunk_id = "
        "(SELECT chunk_id FROM chunks c JOIN documents d USING (doc_id) "
        "WHERE d.acl_tags @> '{staff}' LIMIT 1)",
        "UPDATE documents SET acl_tags = '{staff}' WHERE doc_id = "
        "(SELECT doc_id FROM documents WHERE NOT acl_tags @> '{staff}' LIMIT 1)",
    ],
    ids=["chunk", "document"],
)
def test_stale_check_detects_drift(conn, policy, tamper):
    """Spec 0007, AC-5: a stored ACL that differs from the policy fails, naming `make acl`."""
    with conn.transaction(force_rollback=True):
        conn.execute(tamper)
        with pytest.raises(acl.StaleACL, match="make acl"):
            acl.check_stale(conn, policy)


def test_redirect_stubs_carry_target_acl(conn, policy):
    """Spec 0007, AC-3: at the pin, each redirect stub stores its final target's allow-list."""
    docs = dict(conn.execute("SELECT path, url_path FROM documents").fetchall())
    stubs = acl.read_redirects(list(docs))
    stored = dict(conn.execute("SELECT url_path, acl_tags FROM documents").fetchall())
    # 6 stub files at the pin; 2 have an empty body, so ingest skips them (spec 0002).
    assert len(stubs) == 4
    for path, target in stubs.items():
        assert stored[docs[path]] == stored[target], path


@pytest.mark.parametrize("user_id", list(SHARES))
def test_persona_visible_share(conn, policy, user_id):
    """Spec 0007, AC-6: each persona's visible fixed-512-64 share, through the stored
    allowed_groups, is within 0.1 pp of the dry-run figure."""
    principal = identity.load(user_id, policy)
    visible, total = conn.execute(
        "SELECT count(*) FILTER (WHERE allowed_groups && %s::text[]), count(*) FROM chunks "
        "WHERE config_id = %s",
        (principal.group_list, BASELINE_CONFIG),
    ).fetchone()
    assert 100 * visible / total == pytest.approx(SHARES[user_id], abs=0.1)
