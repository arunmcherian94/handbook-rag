import functools
import json
import uuid

import pytest
from fakes import FakeAnswerer, FakeEmbedder, make_principal

from handbook_rag import ask as ask_mod
from handbook_rag import spend
from handbook_rag.ask import (
    Retrieved,
    append_trace,
    ask,
    build_prompt,
    format_result,
    parse_citations,
)
from handbook_rag.prompts import NOT_FOUND, OUT_OF_SCOPE, SYSTEM_PROMPT


def chunks(k=5):
    return [
        Retrieved(
            n=i,
            chunk_id=uuid.uuid4(),
            doc_id=uuid.uuid4(),
            url_path=f"/handbook/doc{i}/",
            heading=f"Heading {i}" if i != 3 else "Doc 3 title",  # title fallback
            content=f"content of chunk {i}",
            distance=i / 10,
            chunk_size=512,
            chunk_overlap=64,
            tokenizer="cl100k_base",
            commit_sha="abc123",
        )
        for i in range(1, k + 1)
    ]


P = make_principal("staff")


def canned(monkeypatch, cs):
    monkeypatch.setattr(
        ask_mod, "retrieve", lambda conn, embedder, q, principal, k=5, config_id=None: cs
    )


def run_ask(monkeypatch, text="Yes [2] and [9].", cs=None, **kw):
    canned(monkeypatch, chunks() if cs is None else cs)
    answerer = FakeAnswerer(text=text, **kw)
    return ask(None, FakeEmbedder(), answerer, "Q?", P), answerer


def test_search_scopes_to_config():
    """AC-4: the query filters on config_id, and ask passes its config through to retrieve."""
    assert "c.config_id = %(config_id)s" in ask_mod.SEARCH


def test_ask_passes_config_id(monkeypatch):
    """AC-4: ask forwards config_id to retrieve; the default is the baseline."""
    seen = []

    def fake(conn, embedder, q, principal, k=5, config_id=None):
        seen.append(config_id)
        return chunks()

    monkeypatch.setattr(ask_mod, "retrieve", fake)
    ask(None, FakeEmbedder(), FakeAnswerer(text="Yes [1]."), "Q?", P)
    ask(None, FakeEmbedder(), FakeAnswerer(text="Yes [1]."), "Q?", P, config_id="structural-v1")
    assert seen == ["fixed-512-64", "structural-v1"]


def test_build_prompt():
    """AC-6: numbered excerpts with url_path, heading, content, in order, then the question."""
    cs = chunks()
    system, user = build_prompt("What is X?", cs)
    assert system == SYSTEM_PROMPT
    pos = -1
    for c in cs:
        head = f"[{c.n}] {c.url_path} — {c.heading}\n{c.content}"
        assert user.index(head) > pos
        pos = user.index(head)
    assert user.index("Question: What is X?") > pos
    assert user.endswith("Question: What is X?")


def test_system_prompt_rules():
    """AC-6: exact refusal strings and the no-outside-knowledge rule are in the prompt."""
    assert NOT_FOUND in SYSTEM_PROMPT
    assert OUT_OF_SCOPE in SYSTEM_PROMPT
    assert "Do not use your own training" in SYSTEM_PROMPT


def test_parse_citations_maps_and_dedupes():
    """AC-6: [n] and [n, m] groups map to url_path + heading, first-seen order, deduped."""
    cs = chunks()
    cites, invalid = parse_citations("A [2]. B [1, 3]. again [2]", cs)
    assert [c.n for c in cites] == [2, 1, 3]
    assert [(c.url_path, c.heading) for c in cites] == [
        (cs[1].url_path, "Heading 2"),
        (cs[0].url_path, "Heading 1"),
        (cs[2].url_path, "Doc 3 title"),
    ]
    assert invalid == []


@pytest.mark.parametrize("text", ["see [9]", "see [0]"])
def test_parse_citations_out_of_range(text):
    """AC-6: out-of-range numbers are flagged, not mapped."""
    cites, invalid = parse_citations(text, chunks(5))
    assert cites == []
    assert invalid == [int(text[5])]


def test_parse_citations_none_and_mixed():
    """AC-6: no brackets gives nothing; mixed groups split into valid and invalid."""
    assert parse_citations("no citations here", chunks()) == ([], [])
    cites, invalid = parse_citations("fact [2,9] and [9]", chunks())
    assert [c.n for c in cites] == [2]
    assert invalid == [9]


@pytest.mark.parametrize(
    "text, valid, invalid",
    [
        ("A [1-3].", [1, 2, 3], []),
        ("A [1–2; 5].", [1, 2, 5], []),
        ("A [4-7].", [4, 5], [6, 7]),
        ("A [ 2 ].", [2], []),
        ("Since [2025] the cap is $100 [1].", [1], []),
    ],
)
def test_parse_citations_ranges_and_separators(text, valid, invalid):
    """AC-6: ranges and ';' map or flag every number; years/amounts in brackets are ignored."""
    cites, bad = parse_citations(text, chunks(5))
    assert [c.n for c in cites] == valid and bad == invalid


def test_ask_flow(monkeypatch):
    """AC-6, AC-7: prompt reaches the answerer, citations mapped, invalid flagged."""
    r, answerer = run_ask(monkeypatch)
    assert [c.n for c in r.citations] == [2]
    assert r.invalid_citations == [9]
    assert answerer.calls == [build_prompt("Q?", r.chunks)]
    assert not r.truncated
    assert set(r.latency_ms) == {"retrieve", "answer", "total"}
    assert set(r.tokens) == {"answer_input", "answer_output", "query_embed"}
    assert r.tokens["answer_input"] == 100 and r.tokens["query_embed"] > 0
    assert (r.embed_model, r.answer_model, r.k) == ("fake:bow", "fake:answer", 5)


def test_ask_truncated(monkeypatch):
    """AC-6: truncation propagates from the completion."""
    r, _ = run_ask(monkeypatch, truncated=True)
    assert r.truncated


def test_ask_empty_retrieval(monkeypatch, tmp_path):
    """Spec 0007, AC-8: nothing visible gives the standard NOT_FOUND reply, no model call and no
    permission message; the trace still writes."""
    answerer = FakeAnswerer(text="x")
    canned(monkeypatch, [])
    r = ask(None, FakeEmbedder(), answerer, "Q?", P)
    assert r.answer == NOT_FOUND and r.chunks == [] and r.citations == []
    assert answerer.calls == []
    assert "permission" not in format_result(r).lower()
    assert append_trace(r, tmp_path / "ask.jsonl")["retrieved"] == []


def test_principal_is_required():
    """Spec 0007, AC-8: retrieve and ask have no default principal and no unfiltered overload."""
    with pytest.raises(TypeError):
        ask_mod.retrieve(None, FakeEmbedder(), "Q?")
    with pytest.raises(TypeError):
        ask(None, FakeEmbedder(), FakeAnswerer(text="x"), "Q?")


def test_cli_requires_as():
    """Spec 0007, AC-8: the CLI has no unfiltered mode; --as is required."""
    with pytest.raises(SystemExit):
        ask_mod.main(["Q?"])


def test_append_trace(monkeypatch, tmp_path):
    """AC-8: one JSON line per ask with every required field, JSON-serialisable."""
    r, _ = run_ask(monkeypatch)
    path = tmp_path / "runs" / "ask.jsonl"
    rec = append_trace(r, path)
    assert len(path.read_text().splitlines()) == 1
    append_trace(r, path)
    lines = path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0]) == json.loads(json.dumps(rec))
    for key in (
        "timestamp", "corpus_sha", "chunk_params", "embed_model", "answer_model", "k",
        "question", "retrieved", "answer", "citations", "invalid_citations", "truncated",
        "tokens", "latency_ms",
    ):  # fmt: skip
        assert key in rec
    assert rec["corpus_sha"] == "abc123"
    assert rec["chunk_params"] == {
        "chunk_size": 512, "chunk_overlap": 64, "tokenizer": "cl100k_base",
    }  # fmt: skip
    assert rec["retrieved"][0] == {"chunk_id": str(r.chunks[0].chunk_id), "distance": 0.1}


def test_format_result(monkeypatch):
    """AC-7: answer, sources, retrieved distances, tokens/latency, invalid-citation warning."""
    r, _ = run_ask(monkeypatch)
    out = format_result(r)
    assert "Yes [2] and [9]." in out
    assert "Sources:" in out and "[2] /handbook/doc2/ — Heading 2" in out
    assert "[3] 0.3000 /handbook/doc3/ — Doc 3 title" in out
    assert "WARNING" in out and "[9]" in out
    assert "tokens:" in out and "latency:" in out


def test_format_result_clean(monkeypatch):
    """AC-7: no warning when citations are valid and the answer is complete."""
    r, _ = run_ask(monkeypatch, text="Fine [1].")
    assert "WARNING" not in format_result(r)


def test_special_token_in_question(monkeypatch):
    """AC-8: a question containing a tokenizer special token still answers and traces."""
    canned(monkeypatch, chunks())
    r = ask_mod.ask(None, FakeEmbedder(), FakeAnswerer("ok [1]"), "what is <|endoftext|>?", P)
    assert r.tokens["query_embed"] > 0


def test_main_refuses_stale_acls(monkeypatch):
    """Spec 0007, AC-5: `make ask` stops on stale ACLs before any retrieval or model call."""

    class Conn:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def execute(self, *args):
            return type("R", (), {"fetchone": lambda self: (True,)})()

    def stale(conn, policy):
        raise ask_mod.acl.StaleACL(
            "stored ACLs differ from policy-v1: 1 documents. Run `make acl`."
        )

    def no_retrieval(*args, **kwargs):
        raise AssertionError("retrieved under stale ACLs")

    monkeypatch.setattr(ask_mod, "read_manifest", lambda: None)
    monkeypatch.setattr(ask_mod, "verify", lambda m: None)
    monkeypatch.setattr(ask_mod, "make_embedder", lambda: FakeEmbedder())
    monkeypatch.setattr(ask_mod, "make_answerer", lambda: FakeAnswerer())
    monkeypatch.setattr(ask_mod, "connect", Conn)
    monkeypatch.setattr(ask_mod.acl, "load_policy", lambda conn: None)
    monkeypatch.setattr(ask_mod.acl, "check_stale", stale)
    monkeypatch.setattr(ask_mod, "retrieve", no_retrieval)
    with pytest.raises(SystemExit, match="make acl"):
        ask_mod.main(["--as", "us-ic", "a question"])


class _Conn:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, *args):
        return type("R", (), {"fetchone": lambda self: (True,)})()


def _main_env(monkeypatch, tmp_path, answerer=None, paid_env=True):
    """main() up to the confirm gate, with no DB, corpus or API; spend and trace go to tmp.
    paid_env sets the env var `make paid-ask` sets."""
    if paid_env:
        monkeypatch.setenv(spend.PAID_ENV, "1")
    else:
        monkeypatch.delenv(spend.PAID_ENV, raising=False)
    monkeypatch.setattr(ask_mod, "read_manifest", lambda: None)
    monkeypatch.setattr(ask_mod, "verify", lambda m: None)
    monkeypatch.setattr(ask_mod, "connect", _Conn)
    monkeypatch.setattr(ask_mod.acl, "load_policy", lambda conn: None)
    monkeypatch.setattr(ask_mod.acl, "check_stale", lambda conn, policy: None)
    monkeypatch.setattr(ask_mod.identity, "load", lambda user_id, policy: P)
    monkeypatch.setattr(ask_mod, "make_embedder", lambda spec: FakeEmbedder())
    monkeypatch.setattr(ask_mod, "make_answerer", lambda spec: answerer or FakeAnswerer("ok"))
    monkeypatch.setattr(
        ask_mod, "log_spend", functools.partial(spend.log_spend, path=tmp_path / "spend.jsonl")
    )
    traces = []
    monkeypatch.setattr(ask_mod, "append_trace", traces.append)
    canned(monkeypatch, chunks())
    return tmp_path / "spend.jsonl", traces


def test_main_dry_run_by_default(monkeypatch, tmp_path, capsys):
    """Spec 0009, AC-1: without --confirm, main prints the estimate and builds no model client,
    writes no trace and no spend line."""
    spend_log, traces = _main_env(monkeypatch, tmp_path)

    def no_client(spec):
        raise AssertionError("built a model client on a dry run")

    monkeypatch.setattr(ask_mod, "make_embedder", no_client)
    monkeypatch.setattr(ask_mod, "make_answerer", no_client)
    assert ask_mod.main(["--as", "us-ic", "a question"]) == 0
    out = capsys.readouterr().out
    assert "estimated cost $0.00" in out and "Dry run: `make paid-ask` spends." in out
    assert not spend_log.exists() and traces == []


def test_main_confirm_without_paid_target_refuses(monkeypatch, tmp_path):
    """Spec 0009, AC-2: --confirm alone (a direct `python -m` call) can't spend; only the
    paid-ask target, which the hook matches, sets the env var."""
    spend_log, traces = _main_env(monkeypatch, tmp_path, paid_env=False)

    def no_client(spec):
        raise AssertionError("built a model client without the paid target")

    monkeypatch.setattr(ask_mod, "make_embedder", no_client)
    with pytest.raises(SystemExit, match="make paid-ask"):
        ask_mod.main(["--as", "us-ic", "--confirm", "a question"])
    assert not spend_log.exists() and traces == []


def test_estimate_prices_embed_and_answer():
    """Spec 0009, AC-1: query-embed tokens at the model's price plus the flat answer cost."""
    usd = ask_mod.estimate("one two three", "openai:text-embedding-3-large@1536")
    assert usd == pytest.approx(3 * 0.13 / 1e6 + ask_mod.EST_ANSWER_USD_PER_ROW)


def test_main_confirm_logs_one_spend_line(monkeypatch, tmp_path):
    """Spec 0009, AC-3: a confirmed ask appends exactly one spend line."""
    spend_log, traces = _main_env(monkeypatch, tmp_path)
    assert ask_mod.main(["--as", "us-ic", "--confirm", "a question"]) == 0
    (line,) = spend_log.read_text().splitlines()
    rec = json.loads(line)
    assert (rec["target"], rec["status"], rec["run_id"]) == ("ask", "ok", None)
    assert rec["est_usd"] > 0 and len(traces) == 1


def test_main_confirm_logs_failed_run(monkeypatch, tmp_path):
    """Spec 0009, AC-3: a run that fails after the confirm gate still logs one line."""

    class Boom(FakeAnswerer):
        def answer(self, system, user):
            raise RuntimeError("provider down")

    spend_log, _ = _main_env(monkeypatch, tmp_path, answerer=Boom())
    with pytest.raises(RuntimeError):
        ask_mod.main(["--as", "us-ic", "--confirm", "a question"])
    (line,) = spend_log.read_text().splitlines()
    assert json.loads(line)["status"] == "failed"
