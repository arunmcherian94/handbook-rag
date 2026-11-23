"""retrieve tool against the real ACL path (spec 0013, AC-2, AC-5). Needs `make acl`."""

import json
from pathlib import Path

import psycopg
import pytest
from fakes import FakeChatModel, FakeEmbedder, bow_vector, final_step, make_principal, tool_step

from handbook_rag import acl, identity
from handbook_rag.agent.loop import run_turn
from handbook_rag.agent.tool import TurnTool
from handbook_rag.constants import BASELINE_CONFIG, CORPUS_PREFIX
from handbook_rag.db import connect, vector_literal
from handbook_rag.evaluation.permissions import parse_suite
from handbook_rag.models import ToolCall

pytestmark = pytest.mark.integration

MODEL = "fake:agent-tool-test"
INSERT = "INSERT INTO chunk_embeddings (chunk_id, model, embedding) VALUES (%s, %s, %s::vector)"
# Spec 0007, AC-8: people-ops is on every policy rule, so it sees every document.
ADMIN_LIKE = make_principal("people-ops")
CONTRACTOR_LIKE = make_principal("staff", "contractor")


@pytest.fixture
def seeded():
    try:
        conn = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    with conn:
        conn.execute("DELETE FROM chunk_embeddings WHERE model = %s", (MODEL,))
        conn.commit()
        restricted = conn.execute(
            "SELECT chunk_id, content, allowed_groups FROM chunks WHERE config_id = 'fixed-512-64' "
            "AND NOT allowed_groups && %s::text[] ORDER BY chunk_id LIMIT 30",
            (list(CONTRACTOR_LIKE.groups),),
        ).fetchall()
        visible = conn.execute(
            "SELECT chunk_id, content, allowed_groups FROM chunks WHERE config_id = 'fixed-512-64' "
            "AND allowed_groups && %s::text[] ORDER BY chunk_id LIMIT 30",
            (list(CONTRACTOR_LIKE.groups),),
        ).fetchall()
        if not restricted or not visible:
            pytest.fail("need chunks restricted from and visible to contractor; run `make acl`")
        try:
            with conn.cursor() as cur:
                cur.executemany(
                    INSERT,
                    [(r[0], MODEL, vector_literal(bow_vector(r[1]))) for r in restricted + visible],
                )
            conn.commit()
            yield conn, restricted, visible
        finally:
            conn.rollback()
            conn.execute("DELETE FROM chunk_embeddings WHERE model = %s", (MODEL,))
            conn.commit()


def _pages(conn, principal, query):
    """Chunk ids returned for pages 1-4 of one query."""
    tool = TurnTool(conn, FakeEmbedder(name=MODEL), principal)
    ids = []
    for page in range(1, 5):
        args = json.dumps({"query": query, "page": page})
        r = tool.execute(ToolCall(f"c{page}", "retrieve", args))
        assert r.accepted
        ids += r.chunk_ids
    return ids


def test_contractor_never_sees_restricted_chunks(seeded):
    """AC-2, AC-5: for a contractor-like principal no page returns a chunk whose allowed_groups
    do not overlap its groups; an admin-like principal does get the restricted chunk."""
    conn, restricted, visible = seeded
    target = restricted[0]
    query = " ".join(target[1].split()[:60])
    got = _pages(conn, CONTRACTOR_LIKE, query)
    assert got
    for cid in got:
        (groups,) = conn.execute(
            "SELECT allowed_groups FROM chunks WHERE chunk_id = %s", (cid,)
        ).fetchone()
        assert set(groups) & CONTRACTOR_LIKE.groups
    assert str(target[0]) not in got
    assert str(target[0]) in _pages(conn, ADMIN_LIKE, query)


# AC-5, spec 0013: the claimed-identity cases through the whole loop.

MODEL_CLAIMS = "fake:agent-claims-test"
CLAIM_IDS = ("P-063", "P-064", "P-065", "P-067")


@pytest.fixture
def claims_db():
    try:
        conn = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    with conn:
        conn.execute("DELETE FROM chunk_embeddings WHERE model = %s", (MODEL_CLAIMS,))
        conn.commit()
        try:
            yield conn
        finally:
            conn.rollback()
            conn.execute("DELETE FROM chunk_embeddings WHERE model = %s", (MODEL_CLAIMS,))
            conn.commit()


def _claim_cases():
    text = Path("docs/eval/permissions-v1.md").read_text()
    cases = {c.id: c for c in parse_suite(text).cases}
    assert all(i in cases for i in CLAIM_IDS), "claimed-identity cases missing from the suite"
    assert all(c.category.startswith("claimed-identity") for c in map(cases.get, CLAIM_IDS))
    return [cases[i] for i in CLAIM_IDS]


@pytest.mark.parametrize("case", _claim_cases(), ids=lambda c: c.id)
def test_claimed_identity_through_the_agent(claims_db, case):
    """AC-5: a question claiming a role the persona lacks never surfaces a chunk outside the
    persona's groups, nor any chunk of a target document the persona cannot see."""
    conn = claims_db
    principal = identity.load(case.persona, acl.load_policy(conn))
    groups = list(principal.group_list)
    paths = [CORPUS_PREFIX + t for t in case.targets]
    targets = conn.execute(
        "SELECT c.chunk_id, c.content, c.doc_id, c.allowed_groups FROM chunks c "
        "JOIN documents d ON d.doc_id = c.doc_id "
        "WHERE c.config_id = %s AND d.path = ANY(%s)",
        (BASELINE_CONFIG, paths),
    ).fetchall()
    assert targets, f"{case.id}: target chunks not ingested"
    others = conn.execute(
        "SELECT chunk_id, content, doc_id, allowed_groups FROM chunks WHERE config_id = %s "
        "AND allowed_groups && %s::text[] ORDER BY chunk_id LIMIT 40",
        (BASELINE_CONFIG, groups),
    ).fetchall()
    with conn.cursor() as cur:
        cur.executemany(
            INSERT,
            [(r[0], MODEL_CLAIMS, vector_literal(bow_vector(r[1]))) for r in targets + others],
        )
    conn.commit()
    hidden_docs = {str(r[2]) for r in targets if not set(r[3]) & principal.groups}
    assert hidden_docs, f"{case.id}: persona can see every target; not a denied case"

    script = [tool_step(case.question, page=p, call_id=f"c{p}") for p in range(1, 5)]
    model = FakeChatModel([*script, final_step("I don't know based on the provided excerpts.")])
    tool = TurnTool(conn, FakeEmbedder(name=MODEL_CLAIMS), principal)
    saved: list[dict] = []
    rec = run_turn(model, tool, case.question, [], saved.append)

    assert rec["state"] != "error", rec["error"]
    returned = [cid for s in rec["steps"] if s["kind"] == "tool" for cid in s["chunk_ids"]]
    assert returned, "the case must retrieve something for the check to mean anything"
    assert {e["chunk_id"] for e in rec["excerpts"]} <= set(returned)
    rows = conn.execute(
        "SELECT chunk_id::text, doc_id::text, allowed_groups FROM chunks "
        "WHERE chunk_id = ANY(%s::uuid[])",
        (list(returned),),
    ).fetchall()
    assert len(rows) == len(set(returned))
    for _, doc_id, allowed in rows:
        assert set(allowed) & principal.groups
        assert doc_id not in hidden_docs
