"""The agent eval collector (spec 0015, AC-1 to AC-8): no DB, corpus or API."""

import inspect
import json
import math
import uuid
from types import SimpleNamespace

import pytest
from fakes import FakeChatModel, final_step, make_principal, tool_step

from handbook_rag import spend
from handbook_rag.agent import guardrails, store
from handbook_rag.agent.loop import run_turn
from handbook_rag.agent.tool import TurnTool
from handbook_rag.ask import Retrieved
from handbook_rag.evaluation import agent_run as ar
from handbook_rag.evaluation.evalset import Row

P = make_principal("staff")
PRICES = {
    "answer_input_usd_per_1m": 2.0,
    "answer_output_usd_per_1m": 10.0,
    "embed_usd_per_1m": 0.5,
}
SHA = "s" * 64


class Conn:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, *args):
        return SimpleNamespace(fetchone=lambda: (True,))


def dry_env(monkeypatch, tmp_path, paid=False):
    monkeypatch.delenv("ANSWER_MODEL", raising=False)
    monkeypatch.delenv("EMBED_MODEL", raising=False)
    if paid:
        monkeypatch.setenv(spend.PAID_ENV, "1")
    else:
        monkeypatch.delenv(spend.PAID_ENV, raising=False)
    calls: list[str] = []

    def spy(name):
        return lambda *a, **k: calls.append(name)

    def boom(*a, **k):
        raise AssertionError("built a model client")

    policy = SimpleNamespace(version="policy-v1", sha256="p" * 64)
    monkeypatch.setattr(ar, "read_manifest", lambda: SimpleNamespace(sha="abc"))
    monkeypatch.setattr(ar, "verify", lambda m: None)
    monkeypatch.setattr(ar, "connect", Conn)
    monkeypatch.setattr(ar.acl, "load_policy", lambda conn: policy)
    monkeypatch.setattr(ar.acl, "check_stale", lambda conn, policy: None)
    monkeypatch.setattr(ar.identity, "load", lambda user_id, policy: P)
    monkeypatch.setattr(ar, "make_chat_model", boom)
    monkeypatch.setattr(ar, "make_embedder", boom)
    monkeypatch.setattr(ar, "run_turn", boom)
    for name in ("ensure_schema", "create", "claim", "save_turn", "release"):
        monkeypatch.setattr(store, name, spy(name))
    monkeypatch.setattr(ar, "log_spend", spy("log_spend"))
    return calls


def test_dry_run_prints_the_fields_and_spends_nothing(monkeypatch, tmp_path, capsys):
    """AC-1: no model, embedder, session or turn save, no schema, no spend line; prints the
    eval version, row count, models, retriever, budgets, guardrails sha, bounds and the cap."""
    calls = dry_env(monkeypatch, tmp_path)
    assert ar.main(["--cap", "1.5"]) == 0
    out = capsys.readouterr().out
    eval_set = ar.parse(ar.EVAL_SET.read_text(encoding="utf-8"))
    bound = ar.agent_cli.estimate(
        ar.describe_embedder(ar.resolve_embed_spec()).name, ar.resolve_answer_spec()
    )
    b = ar.budgets()
    assert f"{eval_set.version}: {len(eval_set.rows)} live rows" in out
    assert (
        ar.resolve_answer_spec() in out
        and ar.describe_embedder(ar.resolve_embed_spec()).name in out
    )
    assert "retriever: dense" in out
    assert f"{b['max_steps']} steps, {b['max_tool_calls']} tool calls" in out
    assert guardrails.POLICY.version in out and guardrails.POLICY.sha256() in out
    assert f"upper bound per turn ${bound:.4f}" in out
    assert f"full run ${bound * len(eval_set.rows):.4f}" in out
    assert "cap $1.5000" in out and "Dry run: `make paid-agent-eval` spends." in out
    assert calls == []


@pytest.mark.parametrize("cap", ["0", "-1", "abc", "nan", "inf", ""])
def test_bad_cap_refused(monkeypatch, tmp_path, cap):
    """AC-2: a cap that isn't a finite number above 0 exits, with or without --confirm."""
    calls = dry_env(monkeypatch, tmp_path, paid=True)
    for extra in ([], ["--confirm"]):
        with pytest.raises(SystemExit, match="--cap"):
            ar.main(["--cap", cap, *extra])
    assert calls == []


def test_confirm_without_cap_refused(monkeypatch, tmp_path):
    """AC-2: --confirm with no --cap exits before any spend."""
    calls = dry_env(monkeypatch, tmp_path, paid=True)
    with pytest.raises(SystemExit, match="--cap"):
        ar.main(["--confirm"])
    assert calls == []


def test_parse_cap():
    """AC-2: valid caps parse as floats."""
    assert ar.parse_cap("1.00") == 1.0 and ar.parse_cap(None) is None
    assert not math.isfinite(float("nan"))


def retrieved(query: str) -> list[Retrieved]:
    return [
        Retrieved(
            n=i,
            chunk_id=uuid.uuid5(uuid.NAMESPACE_URL, f"{query}/{i}"),
            doc_id=uuid.uuid4(),
            url_path=f"/handbook/x/{i}/",
            heading=f"H{i}",
            content=f"content {i}",
            distance=i / 10,
            chunk_size=512,
            chunk_overlap=64,
            tokenizer="cl100k_base",
            commit_sha="abc",
        )
        for i in range(1, 6)
    ]


def test_answered_turn_carries_all_guardrail_events():
    """AC-4: a real run_turn answers with the policy as built, and its record has an event for
    every one of the 14 checks."""
    seen: list[str] = []

    def fake_retrieve(conn, embedder, query, principal, k, config_id=None, **kw):
        seen.append(query)
        return retrieved(query)

    counter = ar.QueryCounter(fake_retrieve)
    model = FakeChatModel([tool_step("how much leave"), final_step("Take leave [1].")])
    rec = run_turn(model, TurnTool(None, None, P, retrieve=counter), "How much leave?", [], dict)
    assert rec["state"] == "answered"
    assert {e["check"] for e in rec["guardrail_events"]} == set(guardrails.CHECKS)
    assert len(guardrails.CHECKS) == 14
    assert rec["guardrails_sha256"] == guardrails.POLICY.sha256()
    assert seen == ["how much leave"] and counter.tokens == 3


def test_query_counter_accepts_special_token_text():
    """AC-3, AC-5 (review fix): a query the tool accepts, special-token text included, is counted
    and passed through; the counter never turns it into an error turn."""
    seen: list[str] = []

    def fake_retrieve(conn, embedder, query, principal, k, config_id=None, **kw):
        seen.append(query)
        return retrieved(query)

    counter = ar.QueryCounter(fake_retrieve)
    model = FakeChatModel([tool_step("what is <|endoftext|>"), final_step("It is [1].")])
    rec = run_turn(model, TurnTool(None, None, P, retrieve=counter), "Q?", [], dict)
    assert rec["state"] == "answered"
    assert seen == ["what is <|endoftext|>"] and counter.tokens > 0


def test_no_guardrails_switch_in_the_collector():
    """AC-4: no public signature has a guardrail-ish parameter, and the module never reads the
    environment."""
    for fn in vars(ar).values():
        if inspect.isfunction(fn) and fn.__module__ == ar.__name__:
            assert not [p for p in inspect.signature(fn).parameters if "guard" in p.lower()]
    src = inspect.getsource(ar)
    assert "environ" not in src and "getenv" not in src


def row(i: int, typ: str = "lookup") -> Row:
    return Row(id=i, type=typ, question=f"question {i}")


def rec(inp=1000, out=200, sha=SHA) -> dict:
    return {"tokens": {"input": inp, "output": out}, "guardrails_sha256": sha}


def run_collect(tmp_path, records, rows, cap, bound=0.01, tokens=7):
    meta = {"guardrails_sha256": SHA}
    it = iter(records)

    def turn(r):
        return f"s{r.id}", next(it), tokens

    ar.collect(rows, turn, cap=cap, bound=bound, prices=PRICES, out_dir=tmp_path, meta=meta)
    return meta


def lines(tmp_path):
    return [json.loads(x) for x in (tmp_path / "rows.jsonl").read_text().splitlines()]


def test_tally_is_tokens_times_prices(tmp_path):
    """AC-5, AC-6: the tally is input, output and query tokens at the table prices; one line per
    row in order, with the record as returned; run.json carries the final state."""
    rows = [row(1), row(2, "ooc-off-topic")]
    meta = run_collect(tmp_path, [rec(), rec(500, 100)], rows, cap=1.0)
    want = (1000 * 2 + 200 * 10 + 7 * 0.5 + 500 * 2 + 100 * 10 + 7 * 0.5) / 1e6
    assert meta["actual_usd"] == want
    assert meta["turns"] == 2 and meta["complete"] is True and meta["stopped"] is None
    got = lines(tmp_path)
    assert [(g["row"], g["type"], g["session_id"]) for g in got] == [
        (1, "lookup", "s1"),
        (2, "ooc-off-topic", "s2"),
    ]
    assert got[0]["record"] == rec()
    assert json.loads((tmp_path / "run.json").read_text()) == meta


def test_stops_before_the_turn_that_would_pass_the_cap(tmp_path):
    """AC-5, AC-7: with bound 0.01 and a first turn costing about 0.0042, a cap of 0.012 allows
    row 1 and refuses row 2 (0.0042 + 0.01 > 0.012); row 1 is kept."""
    rows = [row(1), row(2), row(3)]
    meta = run_collect(tmp_path, [rec(), rec(), rec()], rows, cap=0.012)
    assert meta["stopped"] == "cap" and meta["complete"] is False and meta["turns"] == 1
    assert [g["row"] for g in lines(tmp_path)] == [1]
    assert json.loads((tmp_path / "run.json").read_text())["stopped"] == "cap"


def test_a_turn_over_the_bound_stops_the_run(tmp_path):
    """AC-5 (review fix): the cap guarantee assumes no turn costs more than the bound; a turn
    that does (here about 0.0042 against a bound of 0.001) stops the run as "cap", and is kept."""
    rows = [row(1), row(2)]
    meta = run_collect(tmp_path, [rec(), rec()], rows, cap=1.0, bound=0.001)
    assert meta["stopped"] == "cap" and meta["complete"] is False and meta["turns"] == 1
    assert [g["row"] for g in lines(tmp_path)] == [1]


def test_a_cap_below_the_bound_runs_nothing(tmp_path):
    """AC-5: tally 0 + bound > cap stops before the first turn."""
    meta = run_collect(tmp_path, [], [row(1)], cap=0.005)
    assert meta["stopped"] == "cap" and meta["turns"] == 0 and lines(tmp_path) == []


def test_guardrails_sha_change_stops_the_run(tmp_path):
    """AC-8: a record under another policy sha is written, then the run stops."""
    rows = [row(1), row(2), row(3)]
    meta = run_collect(tmp_path, [rec(), rec(sha="other"), rec()], rows, cap=1.0)
    assert meta["stopped"] == "guardrails_sha" and meta["complete"] is False
    assert [g["row"] for g in lines(tmp_path)] == [1, 2]


def test_an_exception_records_error_and_reraises(tmp_path):
    """AC-5, AC-7: an unexpected exception leaves stopped "error", rows kept."""
    meta = {"guardrails_sha256": SHA}
    calls = iter([("s1", rec(), 0)])

    def turn(r):
        if r.id == 2:
            raise RuntimeError("boom")
        return next(calls)

    with pytest.raises(RuntimeError):
        ar.collect(
            [row(1), row(2)], turn, cap=1.0, bound=0.01, prices=PRICES, out_dir=tmp_path, meta=meta
        )
    assert meta["stopped"] == "error" and meta["complete"] is False and meta["turns"] == 1
    assert json.loads((tmp_path / "run.json").read_text())["stopped"] == "error"
    assert ar.spend_status(meta) == "failed"


def test_spend_line_carries_actual_and_estimate(tmp_path):
    """AC-7: the spend line has est_usd (bound x rows) and actual_usd (the tally)."""
    path = tmp_path / "spend.jsonl"
    meta = run_collect(tmp_path, [rec()], [row(1)], cap=1.0)
    spend.log_spend(
        "agent-eval",
        0.01,
        run_id="r",
        embed_model="e",
        answer_model="a",
        status=ar.spend_status(meta),
        path=path,
        actual_usd=meta["actual_usd"],
    )
    line = json.loads(path.read_text())
    assert line["est_usd"] == 0.01 and line["actual_usd"] == meta["actual_usd"]
    assert line["status"] == "ok" and line["target"] == "agent-eval"
