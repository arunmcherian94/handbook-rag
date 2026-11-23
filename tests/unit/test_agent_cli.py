"""The agent CLI (spec 0013, AC-16, AC-17, AC-6, AC-13): no DB, corpus or API."""

import json
import uuid
from types import SimpleNamespace

import pytest
from fakes import FakeChatModel, FakeEmbedder, final_step, make_principal

from handbook_rag import constants, spend
from handbook_rag.agent import __main__ as cli
from handbook_rag.agent import store

P = make_principal("staff", user_id="us-ic")
EMBED = "openai:text-embedding-3-large@1536"
ANSWER = constants.DEFAULT_ANSWER_MODEL


class Conn:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, *args):
        return SimpleNamespace(fetchone=lambda: (True,))


class Spies:
    def __init__(self):
        self.calls: list[tuple] = []
        self.spend: list[dict] = []

    def record(self, name):
        def f(*args, **kwargs):
            self.calls.append((name, args, kwargs))

        return f

    def names(self):
        return [c[0] for c in self.calls]


def env(monkeypatch, tmp_path, paid=False, tables=True, session=None):
    """main() up to the gates: everything external is faked; spend goes to tmp_path."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANSWER_MODEL", raising=False)
    monkeypatch.delenv("EMBED_MODEL", raising=False)
    if paid:
        monkeypatch.setenv(spend.PAID_ENV, "1")
    else:
        monkeypatch.delenv(spend.PAID_ENV, raising=False)
    spies = Spies()
    policy = SimpleNamespace(version="policy-v1", sha256="p" * 64)
    monkeypatch.setattr(cli, "read_manifest", lambda: SimpleNamespace(sha="abc"))
    monkeypatch.setattr(cli, "verify", lambda m: None)
    monkeypatch.setattr(cli, "connect", Conn)
    monkeypatch.setattr(cli.acl, "load_policy", lambda conn: policy)
    monkeypatch.setattr(cli.acl, "check_stale", lambda conn, policy: None)
    monkeypatch.setattr(cli.identity, "load", lambda user_id, policy: P)
    monkeypatch.setattr(store, "tables_exist", lambda conn: tables)
    sid = uuid.uuid4()
    sess = session or store.Session(sid, "us-ic", {"session_id": str(sid)}, 0)
    monkeypatch.setattr(
        store, "ensure_schema", lambda conn: spies.calls.append(("ensure_schema", (), {}))
    )
    monkeypatch.setattr(
        store, "create", lambda conn, header: spies.calls.append(("create", (), {})) or sess
    )
    monkeypatch.setattr(store, "load", lambda conn, s: session)
    monkeypatch.setattr(store, "claim", lambda *a: spies.calls.append(("claim", a, {})))
    monkeypatch.setattr(store, "save_turn", lambda *a: spies.calls.append(("save_turn", a, {})))
    monkeypatch.setattr(store, "release", lambda *a: spies.calls.append(("release", a, {})))
    path = tmp_path / "spend.jsonl"

    def log(*a, **kw):
        spies.spend.append(kw)
        spies.calls.append(("log_spend", a, kw))
        return spend.log_spend(*a, path=path, **kw)

    monkeypatch.setattr(cli, "log_spend", log)
    monkeypatch.setattr(cli, "make_embedder", lambda spec: FakeEmbedder(name=spec))
    return spies, sess, path


def no_model(monkeypatch):
    def boom(spec):
        raise AssertionError("built a model client")

    monkeypatch.setattr(cli, "make_embedder", boom)
    monkeypatch.setattr(cli, "make_chat_model", boom)


def test_dry_run_prints_and_writes_nothing(monkeypatch, tmp_path, capsys):
    """AC-16: no key needed; prints models, budgets and the estimate; builds and writes nothing."""
    spies, _, path = env(monkeypatch, tmp_path, tables=False)
    no_model(monkeypatch)
    assert cli.main(["--as", "us-ic", "a question"]) == 0
    out = capsys.readouterr().out
    b = cli.budgets()
    assert EMBED in out and ANSWER in out
    assert f"{b['max_steps']} steps, {b['max_tool_calls']} tool calls" in out
    assert f"{b['max_tokens']} tokens, {b['timeout_s']:.0f} s" in out
    assert f"${cli.estimate(EMBED, ANSWER):.4f}" in out
    assert "Dry run: `make paid-agent` spends." in out and "session tables missing" in out
    assert spies.calls == [] and not path.exists()


def test_unknown_answer_model_exits(monkeypatch, tmp_path):
    """AC-16: an unknown answer model fails the dry run."""
    env(monkeypatch, tmp_path)
    monkeypatch.setenv("ANSWER_MODEL", "openai:nope")
    with pytest.raises(SystemExit, match="no price for answer model"):
        cli.main(["--as", "us-ic", "q"])


def test_estimate_arithmetic():
    """AC-16: query embeds at the cap for each tool call, plus all tokens at the output rate."""
    in_embed = constants.EMBED_MODELS["openai:text-embedding-3-large"]["usd_per_1m"]
    out = constants.ANSWER_MODELS[ANSWER]["output_usd_per_1m"]
    want = (
        constants.AGENT_MAX_TOOL_CALLS * constants.AGENT_MAX_QUERY_TOKENS * in_embed
        + constants.AGENT_MAX_TOKENS * out
    ) / 1e6
    assert cli.estimate(EMBED, ANSWER) == pytest.approx(want)
    with pytest.raises(ValueError):
        cli.estimate(EMBED, "openai:nope")


def test_confirm_without_paid_env_exits(monkeypatch, tmp_path):
    """AC-17: --confirm alone cannot spend."""
    spies, _, path = env(monkeypatch, tmp_path, paid=False)
    no_model(monkeypatch)
    with pytest.raises(SystemExit, match="make paid-agent"):
        cli.main(["--as", "us-ic", "--confirm", "q"])
    assert spies.calls == [] and not path.exists()


def test_paid_path_claims_runs_releases_logs(monkeypatch, tmp_path, capsys):
    """AC-17, AC-13: claim, run, release, then one spend line with run_id=session id and the
    terminal state as status."""
    spies, sess, path = env(monkeypatch, tmp_path, paid=True)
    model = FakeChatModel([final_step("Hello.")])
    monkeypatch.setattr(cli, "make_chat_model", lambda spec: model)
    assert cli.main(["--as", "us-ic", "--confirm", "q"]) == 0
    assert spies.names() == [
        "ensure_schema",
        "create",
        "claim",
        "save_turn",
        "release",
        "log_spend",
    ]
    sid = str(sess.session_id)
    assert spies.calls[3][1][1:3] == (sid, 1)
    (line,) = path.read_text().splitlines()
    rec = json.loads(line)
    assert (rec["target"], rec["run_id"], rec["status"]) == ("agent", sid, "answered")
    out = capsys.readouterr().out
    assert "Hello." in out and f"SESSION={sid}" in out


def test_failed_run_still_logs_spend(monkeypatch, tmp_path):
    """AC-17: when run_turn raises, the lease is released and spend is logged as failed."""
    spies, sess, path = env(monkeypatch, tmp_path, paid=True)
    monkeypatch.setattr(cli, "make_chat_model", lambda spec: FakeChatModel([]))

    def boom(*a, **kw):
        raise RuntimeError("crash")

    monkeypatch.setattr(cli, "run_turn", boom)
    with pytest.raises(RuntimeError):
        cli.main(["--as", "us-ic", "--confirm", "q"])
    assert spies.names()[-2:] == ["release", "log_spend"]
    assert json.loads(path.read_text())["status"] == "failed"
    assert spies.spend[0]["run_id"] == str(sess.session_id)


def test_model_build_failure_releases_lease(monkeypatch, tmp_path):
    """AC-13 (review fix): a failure building the models after the claim still releases the
    lease and logs spend as failed."""
    spies, _, path = env(monkeypatch, tmp_path, paid=True)

    def no_key(spec):
        raise SystemExit("OPENAI_API_KEY is not set")

    monkeypatch.setattr(cli, "make_chat_model", no_key)
    with pytest.raises(SystemExit, match="OPENAI_API_KEY"):
        cli.main(["--as", "us-ic", "--confirm", "q"])
    assert spies.names()[-3:] == ["claim", "release", "log_spend"]
    assert json.loads(path.read_text())["status"] == "failed"


def resumed(monkeypatch, tmp_path, header_patch, paid=False):
    bound = {}
    probe_sid = uuid.uuid4()
    spies, _, path = env(monkeypatch, tmp_path, paid=paid)
    policy = SimpleNamespace(version="policy-v1", sha256="p" * 64)
    bound.update(cli.binding(P, policy))
    header = {**bound, "session_id": str(probe_sid), **header_patch}
    sess = store.Session(probe_sid, "us-ic", header, 1)
    monkeypatch.setattr(store, "load", lambda conn, s: sess)
    return spies, sess, path


def test_mismatched_binding_exits_before_any_model_call(monkeypatch, tmp_path):
    """AC-6, AC-17: resuming with a changed policy exits before any model is built."""
    spies, sess, path = resumed(monkeypatch, tmp_path, {"policy_sha256": "other"}, paid=True)
    no_model(monkeypatch)
    with pytest.raises(SystemExit, match="policy_sha256"):
        cli.main(["--as", "us-ic", "--confirm", "--session", str(sess.session_id), "q"])
    assert spies.calls == [] and not path.exists()


def test_session_busy_exits_before_any_model_call(monkeypatch, tmp_path):
    """AC-13: a busy session exits before any model is built; nothing is spent or logged."""
    spies, sess, path = resumed(monkeypatch, tmp_path, {}, paid=True)
    no_model(monkeypatch)

    def busy(*a):
        raise store.SessionBusy("session busy; retry")

    monkeypatch.setattr(store, "claim", busy)
    with pytest.raises(SystemExit, match="session busy"):
        cli.main(["--as", "us-ic", "--confirm", "--session", str(sess.session_id), "q"])
    assert "log_spend" not in spies.names() and not path.exists()


def test_resume_dry_run_ok(monkeypatch, tmp_path, capsys):
    """AC-14, AC-16: a matching session resumes in the dry run and reports turn 1."""
    spies, sess, _ = resumed(monkeypatch, tmp_path, {})
    no_model(monkeypatch)
    assert cli.main(["--as", "us-ic", "--session", str(sess.session_id), "q"]) == 0
    assert f"session {sess.session_id}, turn 1" in capsys.readouterr().out
