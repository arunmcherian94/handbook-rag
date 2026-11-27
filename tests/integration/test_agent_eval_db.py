"""Agent eval collector against the real DB with a fake model and embedder (spec 0015, AC-3,
AC-6, AC-7). Needs `make up`, `make ingest`, `make acl`."""

import json
from types import SimpleNamespace

import psycopg
import pytest
from fakes import FakeChatModel, FakeEmbedder, bow_vector, final_step, tool_step

from handbook_rag import acl, identity
from handbook_rag.agent import __main__ as agent_cli
from handbook_rag.agent import store
from handbook_rag.constants import BASELINE_CONFIG
from handbook_rag.corpus import read_manifest
from handbook_rag.db import connect, vector_literal
from handbook_rag.evaluation import agent_run as ar
from handbook_rag.evaluation import run as eval_run
from handbook_rag.evaluation.evalset import EvalSet, Row
from handbook_rag.prompts import NOT_FOUND, OUT_OF_SCOPE

pytestmark = pytest.mark.integration

MODEL = "fake:agent-eval-test"
INSERT = "INSERT INTO chunk_embeddings (chunk_id, model, embedding) VALUES (%s, %s, %s::vector)"
PRICES = {"answer_input_usd_per_1m": 1.0, "answer_output_usd_per_1m": 1.0, "embed_usd_per_1m": 1.0}
ROWS = [
    Row(id=1, type="lookup", question="How many vacation days do staff get?"),
    Row(id=2, type="ooc-in-scope", question="What is the GitLab sabbatical stipend?"),
    Row(id=3, type="ooc-off-topic", question="What is the capital of France?"),
]


@pytest.fixture
def db():
    try:
        conn = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    sessions: list[str] = []
    with conn:
        conn.execute("DELETE FROM chunk_embeddings WHERE model = %s", (MODEL,))
        store.ensure_schema(conn)
        chunks = conn.execute(
            "SELECT chunk_id, content FROM chunks WHERE config_id = %s ORDER BY chunk_id LIMIT 30",
            (BASELINE_CONFIG,),
        ).fetchall()
        if not chunks:
            pytest.fail("no chunks; run `make ingest`")
        with conn.cursor() as cur:
            cur.executemany(INSERT, [(c, MODEL, vector_literal(bow_vector(t))) for c, t in chunks])
        conn.commit()
        try:
            yield conn, sessions
        finally:
            conn.rollback()
            conn.execute("DELETE FROM chunk_embeddings WHERE model = %s", (MODEL,))
            conn.execute("DELETE FROM agent_turns WHERE session_id = ANY(%s::uuid[])", (sessions,))
            conn.execute(
                "DELETE FROM agent_sessions WHERE session_id = ANY(%s::uuid[])", (sessions,)
            )
            conn.commit()


def test_one_fresh_admin_session_per_row(db, tmp_path):
    """AC-3, AC-6, AC-7: three rows, one fresh admin session each; rows.jsonl holds the records
    the DB holds; run.json has the contract keys and stays in step with the run."""
    conn, sessions = db
    policy = acl.load_policy(conn)
    principal = identity.load("admin", policy)
    manifest = read_manifest()
    chunk_params, corpus_sha = eval_run.stored_chunk_params(conn, manifest.sha, BASELINE_CONFIG)
    bound = 0.01
    meta = ar.agent_meta(
        eval_set=EvalSet("v-test", tuple(ROWS)),
        eval_bytes=b"test",
        corpus_sha=corpus_sha,
        chunk_params=chunk_params,
        embed_spec=MODEL,
        answer_spec="fake:chat",
        policy=policy,
        cap=1.0,
        bound=bound,
        prices=PRICES,
        refs=ar._refs(ROWS, SimpleNamespace(relevant={})),
    )
    model = FakeChatModel(
        [
            tool_step("vacation days"),
            final_step("Staff get leave [1]."),
            tool_step("sabbatical stipend"),
            final_step(NOT_FOUND),
            final_step(OUT_OF_SCOPE),
        ]
    )
    bound_session = agent_cli.binding(principal, policy)
    turn = ar.make_turn(
        conn,
        model,
        FakeEmbedder(name=MODEL),
        principal,
        lambda: agent_cli.header(bound_session, MODEL, "fake:chat", corpus_sha),
    )

    def tracked(row):
        out = turn(row)
        sessions.append(out[0])
        return out

    out_dir = tmp_path
    ar.collect(ROWS, tracked, cap=1.0, bound=bound, prices=PRICES, out_dir=out_dir, meta=meta)

    got = [json.loads(x) for x in (out_dir / "rows.jsonl").read_text().splitlines()]
    assert [g["row"] for g in got] == [1, 2, 3]
    assert [g["type"] for g in got] == [r.type for r in ROWS]
    assert len(set(sessions)) == 3 and [g["session_id"] for g in got] == sessions
    states = [g["record"]["state"] for g in got]
    assert states == ["answered", "abstained", "abstained"]
    for g in got:
        s = store.load(conn, g["session_id"])
        assert s.user_id == "admin" and s.header["guardrails_sha256"] == meta["guardrails_sha256"]
        assert s.turns == [g["record"]]
        assert g["record"]["turn_no"] == 1

    run = json.loads((out_dir / "run.json").read_text())
    contract = {
        "mode", "answer_model", "system_prompt_sha256", "rows", "guardrails_version",
        "guardrails_sha256", "tool_sha256", "budgets", "retriever", "prices",
        "estimate_usd_per_turn", "cap_usd", "actual_usd", "turns", "complete", "stopped", "refs",
        "eval_version", "eval_sha256", "harness_sha", "harness_dirty", "corpus_sha", "config_id",
        "chunk_params", "embed_model", "k", "timestamp", "limit", "user_id", "policy_version",
        "policy_sha256",
    }  # fmt: skip
    assert contract <= set(run) and "eval_depth" not in run
    assert run["mode"] == "agent" and run["user_id"] == "admin" and run["rows"] == 3
    assert run["turns"] == 3 and run["complete"] is True and run["stopped"] is None
    assert run["retriever"]["kind"] == "dense" and set(run["refs"]) == {"1", "2", "3"}
    assert run["actual_usd"] > 0
