"""Spec 0015 AC-9 to AC-17: the free agent trajectory scorer, over hand-made records."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from handbook_rag.agent import guardrails
from handbook_rag.evaluation import agent_report as ar
from handbook_rag.evaluation.assertions import (
    FACT_PASS,
    ROW_PASS,
    Assertions,
    Entry,
    Node,
    score,
)
from handbook_rag.evaluation.evalset import parse
from handbook_rag.prompts import NOT_FOUND, OUT_OF_SCOPE

SHA = "a" * 64
URL = "finance/expenses.md"
EVAL_TEXT = f"""# Eval set v1.2 (test)

### Row 1 — lookup · single-fact · trap –
Q: what is the limit?
expected_docs: {URL}
facts:
- F1. [required] The limit is 80 dollars. — {URL} § "Meals" L5–5
- F2. [required] Tips are included. — {URL} § "Meals" L9–9
ref_source: llm-draft, reviewed

### Row 2 — ooc-in-scope · single-fact · trap –
Q: who is in my cohort?
expected: "{NOT_FOUND}"
ref_source: llm-draft, reviewed

### Row 3 — ooc-off-topic · single-fact · trap –
Q: write a haiku
expected: "{OUT_OF_SCOPE}"
ref_source: llm-draft, reviewed

### Row 4 — lookup · single-fact · trap –
Q: second lookup?
expected_docs: {URL}
facts:
- F1. [required] Receipts are needed. — {URL} § "Receipts" L20–20
ref_source: llm-draft, reviewed

## 5. Cut (owner)
"""
EVALSET = parse(EVAL_TEXT)
ASSERTS = Assertions(
    "v1.2",
    SHA,
    {
        1: {
            "F1": Entry(1, "F1", True, node=Node("number", 80.0)),
            "F2": Entry(1, "F2", True, node=Node("term", "tips")),
        },
        4: {"F1": Entry(4, "F1", True, node=Node("term", "receipts"))},
    },
)


def model(inp=10, out=5, ms=100.0):
    return {"kind": "model", "input_tokens": inp, "output_tokens": out, "latency_ms": ms}


def tool(page=1, accepted=True, numbers=(), chunks=()):
    return {
        "kind": "tool",
        "name": "retrieve",
        "arguments": json.dumps({"query": "q", "page": page}),
        "accepted": accepted,
        "error": None if accepted else "bad",
        "numbers": list(numbers),
        "chunk_ids": list(chunks),
    }


def rec(state="answered", answer="x", steps=(), citations=(), invalid=(), excerpts=(), **kw):
    return {
        "state": state,
        "answer": answer,
        "steps": list(steps),
        "citations": [{"n": n, "url_path": u, "heading": "h"} for n, u in citations],
        "invalid_citations": list(invalid),
        "excerpts": [{"n": n, "chunk_id": "c", "url_path": u, "heading": "h"} for n, u in excerpts],
        "tokens": kw.pop("tokens", {"input": 10, "output": 5}),
        "latency_ms": kw.pop("latency_ms", 100.0),
        "retries": kw.pop("retries", 0),
        "guardrail_events": kw.pop("events", []),
    }


def line(row, record):
    rtype = {r.id: r.type for r in EVALSET.rows}[row]
    return {"row": row, "type": rtype, "session_id": "s", "record": record}


REFS = {
    "1": {"expected_urls": [URL], "relevant": {"F1": ["c1", "c2"], "F2": ["c3"]}},
    "2": {"expected_urls": [], "relevant": {}},
    "3": {"expected_urls": [], "relevant": {}},
    "4": {"expected_urls": [URL], "relevant": {"F1": ["c9"]}},
}


def run_json(**over):
    base = {
        "mode": "agent",
        "eval_sha256": SHA,
        "eval_version": "v1.2",
        "answer_model": "m",
        "embed_model": "e",
        "config_id": "cfg",
        "retriever": {"kind": "dense", "k": 5},
        "guardrails_sha256": "g",
        "guardrails_version": "v1",
        "timestamp": "2026-11-27T10:00:00+00:00",
        "rows": 4,
        "turns": 4,
        "complete": True,
        "stopped": None,
        "refs": REFS,
        "actual_usd": 0.1,
        "cap_usd": 1.0,
    }
    return base | over


def ev(records: dict[int, dict], run=None):
    rows = {r: line(r, rc) for r, rc in records.items()}
    return ar.evaluate(EVALSET, run or run_json(), rows, ASSERTS, {})


def pooled(e, name, sl="pooled"):
    return e.metrics[name][sl]


# AC-10


@pytest.mark.parametrize(
    "row,state,answer,ok",
    [
        (1, "answered", "80", True),
        (1, "abstained", NOT_FOUND, False),
        (1, "budget_exhausted", None, False),
        (2, "abstained", NOT_FOUND, True),
        (2, "abstained", OUT_OF_SCOPE, False),
        (2, "answered", "80", False),
        (2, "abstained", NOT_FOUND.replace("'", "’"), False),
        (3, "abstained", OUT_OF_SCOPE, True),
        (3, "abstained", NOT_FOUND, False),
        (3, "guardrail_blocked", "refused", False),
        (3, "error", None, False),
        (2, "abstained", "  " + NOT_FOUND + "\n", True),
    ],
)
def test_ac10_terminal_state(row, state, answer, ok):
    row_obj = next(r for r in EVALSET.rows if r.id == row)
    assert ar.terminal_pass(row_obj, rec(state, answer)) is ok


def test_ac10_retried_then_passed_and_table():
    e = ev(
        {
            1: rec(retries=1),
            2: rec("abstained", NOT_FOUND, retries=2),
            3: rec("budget_exhausted", None, retries=1),
        }
    )
    assert pooled(e, "terminal_state_pass")["mean"] == pytest.approx(2 / 3)
    assert e.counts["terminal_states"]["lookup"] == {"answered": 1}
    assert e.counts["terminal_states"]["ooc-off-topic"] == {"budget_exhausted": 1}
    assert e.counts["retried_terminal_states"] == {
        "abstained": 1,
        "answered": 1,
        "budget_exhausted": 1,
    }
    assert pooled(e, "retry_rate")["mean"] == 1.0


# AC-11


def test_ac11_citation_validity():
    assert not ar.citation_valid(rec(citations=[]))
    assert not ar.citation_valid(rec(citations=[(1, URL)], invalid=[7]))
    assert ar.citation_valid(rec(citations=[(1, URL)]))
    e = ev({1: rec(citations=[(1, URL)]), 4: rec(citations=[]), 2: rec("abstained", NOT_FOUND)})
    assert pooled(e, "citation_valid")["n"] == 2  # answered rows only
    assert pooled(e, "citation_valid")["mean"] == 0.5


# AC-12


def test_ac12_per_turn_counts_and_max():
    r1 = rec(
        steps=[model(), tool(), model(), tool(accepted=False), model()],
        tokens={"input": 100, "output": 20},
        latency_ms=300.0,
    )
    r4 = rec(steps=[model()], tokens={"input": 50, "output": 10}, latency_ms=100.0)
    e = ev({1: r1, 4: r4})
    assert pooled(e, "model_calls")["mean"] == 2.0
    assert pooled(e, "model_calls")["max"] == 3
    assert pooled(e, "tool_calls_accepted")["mean"] == 0.5
    assert pooled(e, "input_tokens")["mean"] == 75
    assert pooled(e, "output_tokens")["max"] == 20
    assert pooled(e, "latency_ms")["mean"] == 200.0
    assert pooled(e, "latency_ms")["kind"] == "continuous"
    share = pooled(e, "rejected_tool_call_share")  # only r1 had tool calls
    assert (share["mean"], share["n"]) == (0.5, 1)


def test_ac12_ooc_offtopic_searches_only_on_that_type():
    e = ev(
        {
            2: rec("abstained", NOT_FOUND, steps=[tool(), tool()]),
            3: rec("abstained", OUT_OF_SCOPE, steps=[tool(), tool(accepted=False)]),
        }
    )
    s = pooled(e, "ooc_offtopic_searches")
    assert (s["mean"], s["n"]) == (1.0, 1)
    assert pooled(e, "ooc_offtopic_searches", "answerable") is None


def test_ac12_expected_doc_hit_and_cited_expected_doc():
    e = ev(
        {
            1: rec(excerpts=[(1, "other.md"), (2, URL)], citations=[(1, "other.md")]),
            4: rec(excerpts=[(1, "other.md")], citations=[(1, "other.md")]),
        }
    )
    assert pooled(e, "expected_doc_hit")["mean"] == 0.5
    assert pooled(e, "cited_expected_doc")["mean"] == 0.0
    e = ev({1: rec(excerpts=[(1, URL)], citations=[(1, URL)])})
    assert pooled(e, "cited_expected_doc")["mean"] == 1.0


def test_ac12_page2_use_and_cited():
    deep = rec(steps=[tool(), tool(page=2, numbers=[6, 7])], citations=[(6, URL)])
    shallow = rec(steps=[tool(numbers=[1])], citations=[(1, URL)])
    ignored = rec(steps=[tool(page=2, numbers=[6])], citations=[(1, URL)])
    e = ev({1: deep, 4: shallow, 3: rec("abstained", OUT_OF_SCOPE, steps=[tool(page=3)])})
    assert pooled(e, "page2_use")["mean"] == pytest.approx(2 / 3)
    assert (pooled(e, "page2_cited")["mean"], pooled(e, "page2_cited")["n"]) == (0.5, 2)
    e = ev({1: ignored})
    assert pooled(e, "page2_cited")["mean"] == 0.0
    rejected = rec(steps=[tool(page=2, accepted=False, numbers=[6])], citations=[(6, URL)])
    assert pooled(ev({1: rejected}), "page2_use")["mean"] == 0.0


def test_ac12_guardrail_nonpass_rows_counts_rows_not_events():
    events = [
        {"check": "input_pii", "action": "redact"},
        {"check": "input_pii", "action": "redact"},
        {"check": "output_link", "action": "pass"},
    ]
    e = ev({1: rec(events=events), 4: rec(events=[{"check": "input_pii", "action": "block"}])})
    counts = e.counts["guardrail_nonpass_rows"]
    assert counts["input_pii"] == 2
    assert counts["output_link"] == 0
    assert set(ar.CHECKS) <= set(counts)


# AC-13


def test_ac13_union_of_searches_and_unretrieved_fact():
    both = rec(steps=[tool(chunks=["c1"]), tool(chunks=["c3"])])  # F1 via c1, F2 via c3
    assert pooled(ev({1: both}), "trajectory_fact_coverage")["mean"] == 1.0
    one = rec(steps=[tool(chunks=["c1"])])
    assert pooled(ev({1: one}), "trajectory_fact_coverage")["mean"] == 0.5
    stray = rec(steps=[tool(chunks=["zz"]), tool(accepted=False, chunks=["c3"])])
    assert pooled(ev({1: stray}), "trajectory_fact_coverage")["mean"] == 0.0
    assert pooled(ev({2: rec("abstained", NOT_FOUND)}), "trajectory_fact_coverage") is None


# AC-14


def test_ac14_parity_with_score_and_answered_only():
    text = "The limit is 80 dollars; tips are included."
    e = ev({1: rec(answer=text), 4: rec("abstained", NOT_FOUND)})
    direct = score(
        Assertions("v1.2", SHA, {1: ASSERTS.entries[1]}), EVALSET, {}, {1: {"answer": text}}
    )
    assert pooled(e, FACT_PASS)["mean"] == direct.fact_pass.mean == 1.0
    assert pooled(e, ROW_PASS)["mean"] == direct.row_pass.mean
    assert pooled(e, FACT_PASS)["n"] == 1  # the abstained row 4 is left out, not failed
    e = ev({1: rec(answer="80 only"), 4: rec(answer="receipts")})
    assert pooled(e, FACT_PASS)["mean"] == 0.75
    assert pooled(e, ROW_PASS)["mean"] == 0.5
    assert pooled(e, ROW_PASS)["kind"] == "binary"


# AC-15


def test_ac15_slices_kinds_and_counts_without_se():
    e = ev(
        {
            1: rec(),
            4: rec("abstained", NOT_FOUND),
            2: rec("abstained", NOT_FOUND),
            3: rec("error", None),
        }
    )
    m = e.metrics["terminal_state_pass"]
    assert (m["pooled"]["n"], m["answerable"]["n"], m["ooc"]["n"]) == (4, 2, 2)
    assert m["pooled"]["se"] == pytest.approx((0.5 * 0.5 / 4) ** 0.5)  # binary: sqrt(p(1-p)/n)
    assert set(ar.KIND) == set(e.metrics)
    assert e.counts["rows_by_type"] == {"lookup": 2, "ooc-in-scope": 1, "ooc-off-topic": 1}
    assert "se" not in json.dumps(e.counts)


def test_ac15_continuous_uses_sample_sd():
    e = ev({1: rec(latency_ms=100.0), 4: rec(latency_ms=300.0)})
    assert pooled(e, "latency_ms")["se"] == pytest.approx(100.0)  # sd 141.4 / sqrt(2)


def test_ac15_incomplete_label_and_n():
    e = ev({1: rec()}, run_json(complete=False, stopped="cap", turns=1))
    summary = ar.build_summary(
        "r", run_json(complete=False, stopped="cap", turns=1), e, "s", None, None
    )
    md = ar.render_md(summary)
    assert md.startswith("**INCOMPLETE RUN (stopped: cap; 1 turns of 4)**")
    assert "n = 1" in md
    full = ar.render_md(ar.build_summary("r", run_json(), e, "s", None, None))
    assert "INCOMPLETE" not in full


def test_summary_md_formats_cost_and_missing_cap():
    """AC-15 (review fix): cost at 4 decimals; a missing cap reads n/a, never $None."""
    e = ev({1: rec()})
    md = ar.render_md(
        ar.build_summary("r", run_json(actual_usd=0.18234567891, cap_usd=None), e, "s", None, None)
    )
    assert "cost $0.1823 (cap n/a)" in md


def test_unknown_row_or_type_mismatch_is_error():
    with pytest.raises(ar.AgentReportError, match="not in the eval set"):
        ar.evaluate(
            EVALSET, run_json(), {99: {"row": 99, "type": "lookup", "record": rec()}}, ASSERTS, {}
        )
    bad = {1: {"row": 1, "type": "synthesis", "record": rec()}}
    with pytest.raises(ar.AgentReportError, match="run type"):
        ar.evaluate(EVALSET, run_json(), bad, ASSERTS, {})


# AC-16


def write_agent(root: Path, name: str, ts: str, rows: dict, **over):
    folder = root / name
    folder.mkdir(parents=True)
    (folder / "run.json").write_text(json.dumps(run_json(timestamp=ts, **over)))
    (folder / "rows.jsonl").write_text(
        "".join(json.dumps(line(r, rc)) + "\n" for r, rc in rows.items())
    )
    return folder


ASK_META = {
    "mode": "full",
    "limit": None,
    "harness_dirty": False,
    "answer_model": "m",
    "embed_model": "e",
    "config_id": "cfg",
    "eval_sha256": SHA,
    "timestamp": "2026-10-01T10:00:00+00:00",
}


def write_ask(root: Path, name: str, rows=True, **over):
    folder = root / name
    folder.mkdir(parents=True)
    (folder / "summary.json").write_text(json.dumps({"meta": ASK_META | over}))
    if rows:
        ask_rows = [
            {
                "row": 1,
                "answer": "The limit is 80 dollars; tips are included.",
                "abstained": False,
                "retrieved": [{"chunk_id": "c1", "facts": ["F1"]}, {"chunk_id": "c2", "facts": []}],
            },
            {"row": 2, "answer": NOT_FOUND, "abstained": True, "retrieved": []},
            {"row": 3, "answer": NOT_FOUND, "abstained": True, "retrieved": []},
        ]
        (folder / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in ask_rows))
    return folder


def test_ac16_ask_picks_latest_matching(tmp_path):
    write_ask(tmp_path, "old", timestamp="2026-10-01T00:00:00+00:00")
    write_ask(tmp_path, "new", timestamp="2026-10-05T00:00:00+00:00")
    write_ask(
        tmp_path, "newer-wrong-model", timestamp="2026-10-09T00:00:00+00:00", answer_model="x"
    )
    write_ask(tmp_path, "newer-wrong-sha", timestamp="2026-10-09T00:00:00+00:00", eval_sha256="b")
    write_ask(tmp_path, "newer-limit", timestamp="2026-10-09T00:00:00+00:00", limit=5)
    write_ask(tmp_path, "newer-dirty", timestamp="2026-10-09T00:00:00+00:00", harness_dirty=True)
    write_ask(tmp_path, "newer-partial", timestamp="2026-10-09T00:00:00+00:00", mode="retrieval")
    write_ask(tmp_path, "newer-norows", rows=False, timestamp="2026-10-09T00:00:00+00:00")
    # review fix: a hybrid or rerank ask run never compares with the dense agent
    write_ask(tmp_path, "newer-hybrid", timestamp="2026-10-09T00:00:00+00:00", retriever="hybrid")
    assert ar.find_ask_run(tmp_path, run_json()).name == "new"
    write_ask(tmp_path, "newest-dense", timestamp="2026-10-10T00:00:00+00:00", retriever="dense")
    assert ar.find_ask_run(tmp_path, run_json()).name == "newest-dense"
    assert ar.find_ask_run(tmp_path / "missing", run_json()) is None


def test_ac16_ask_metrics():
    rows = {
        1: {
            "row": 1,
            "answer": "The limit is 80 dollars; tips are included.",
            "abstained": False,
            "retrieved": [{"chunk_id": "c1", "facts": ["F1"]}, {"chunk_id": "c2", "facts": []}],
        },
        2: {"row": 2, "answer": OUT_OF_SCOPE, "abstained": True, "retrieved": []},
        4: {"row": 4, "answer": NOT_FOUND, "abstained": True, "retrieved": []},
    }
    m = ar.ask_evaluation(EVALSET, rows, ASSERTS, {})
    assert m["terminal_state_pass"]["answerable"]["mean"] == 0.5  # row 4 abstained
    assert m["terminal_state_pass"]["ooc"]["mean"] == 0.0  # row 2 wrong string
    # review fix: labelled as top-5 fact recall, not trajectory coverage
    assert "trajectory_fact_coverage" not in m
    assert m["chunk_fact_recall@5"]["pooled"]["mean"] == 0.25  # (1/2 + 0/1) / 2
    assert m["chunk_fact_recall@5"]["pooled"]["n"] == 2
    assert m["chunk_fact_recall@5"]["pooled"]["kind"] == "continuous"
    assert m[FACT_PASS]["pooled"]["n"] == 1  # abstained row 4 left out


def test_ac16_agent_baseline_latest_earlier_matching(tmp_path):
    this = run_json(timestamp="2026-11-27T10:00:00+00:00")
    write_agent(tmp_path, "a1", "2026-11-20T00:00:00+00:00", {})
    write_agent(tmp_path, "a2", "2026-11-25T00:00:00+00:00", {})
    write_agent(tmp_path, "later", "2026-11-28T00:00:00+00:00", {})
    write_agent(tmp_path, "wrong-sha", "2026-11-26T00:00:00+00:00", {}, guardrails_sha256="z")
    write_agent(tmp_path, "wrong-model", "2026-11-26T00:00:00+00:00", {}, answer_model="z")
    write_agent(tmp_path, "wrong-ret", "2026-11-26T00:00:00+00:00", {}, retriever={"kind": "x"})
    write_agent(tmp_path, "wrong-eval", "2026-11-26T00:00:00+00:00", {}, eval_sha256="z")
    write_agent(tmp_path, "partial", "2026-11-26T00:00:00+00:00", {}, complete=False)
    write_agent(tmp_path, "me", "2026-11-27T10:00:00+00:00", {})
    assert ar.find_agent_baseline(tmp_path, this, "me").name == "a2"
    only_me = tmp_path / "x"
    write_agent(only_me, "me", "2026-11-27T10:00:00+00:00", {})
    assert ar.find_agent_baseline(only_me, this, "me") is None


def test_ac16_summary_says_when_none():
    e = ev({1: rec()})
    s = ar.build_summary("r", run_json(), e, "s", None, None)
    assert s["comparisons"]["ask"]["note"] == "no matching ask run"
    assert s["comparisons"]["agent_baseline"]["note"] == "no earlier agent run"
    md = ar.render_md(s)
    assert "no matching ask run" in md and "no earlier agent run" in md


# AC-9 end to end, AC-16, AC-17


def setup_files(tmp_path, with_ask=True):
    eval_path = tmp_path / "eval.md"
    eval_path.write_text(EVAL_TEXT)
    sha = hashlib.sha256(eval_path.read_bytes()).hexdigest()
    assertions = tmp_path / "assertions.yaml"
    assertions.write_text(
        f"eval_version: v1.2\neval_sha256: {sha}\nrows:\n  1:\n    F1:\n      expressible: true\n"
        "      assert:\n        number: 80\n    F2:\n      expressible: true\n      assert:\n"
        "        term: tips\n  4:\n    F1:\n      expressible: true\n      assert:\n"
        "        term: receipts\n"
    )
    review = tmp_path / "review.md"
    review.write_text("| row | type | checked | changed | note |\n|---|---|---|---|---|\n")
    runs = tmp_path / "runs"
    records = {
        1: rec(
            answer="80 dollars, tips included",
            steps=[model(), tool(chunks=["c1", "c3"], numbers=[1]), model()],
            citations=[(1, URL)],
            excerpts=[(1, URL)],
        ),
        2: rec("abstained", NOT_FOUND, steps=[model()]),
        3: rec("abstained", OUT_OF_SCOPE, steps=[model(), tool()]),
        4: rec("budget_exhausted", None, steps=[model()]),
    }
    write_agent(runs, "agent-run", "2026-11-27T10:00:00+00:00", records, eval_sha256=sha)
    write_agent(runs, "agent-old", "2026-11-20T10:00:00+00:00", records, eval_sha256=sha)
    if with_ask:
        write_ask(runs, "ask-run", eval_sha256=sha)
    argv = [
        "--run", "agent-run",
        "--runs-root", str(runs),
        "--out-root", str(tmp_path / "out"),
        "--eval-set", str(eval_path),
        "--assertions", str(assertions),
        "--review", str(review),
    ]  # fmt: skip
    return argv, tmp_path / "out" / "agent-run", runs


def test_ac9_ac16_end_to_end_and_byte_identical_rerun(tmp_path):
    argv, out, _ = setup_files(tmp_path)
    assert ar.main(argv) == 0
    first = {n: (out / n).read_bytes() for n in ("summary.json", "summary.md")}
    assert ar.main(argv) == 0
    assert first == {n: (out / n).read_bytes() for n in first}
    s = json.loads(first["summary.json"])
    assert s["comparisons"]["ask"]["run_id"] == "ask-run"
    assert s["comparisons"]["agent_baseline"]["run_id"] == "agent-old"
    assert s["metrics"]["terminal_state_pass"]["pooled"]["mean"] == 0.75
    assert "ask-run" in first["summary.md"].decode()


def test_ac9_refuses_wrong_mode_or_eval_sha(tmp_path):
    argv, _, runs = setup_files(tmp_path)
    path = runs / "agent-run" / "run.json"
    data = json.loads(path.read_text())
    path.write_text(json.dumps(data | {"mode": "full"}))
    with pytest.raises(ar.AgentReportError, match="not an agent run"):
        ar.main(argv)
    path.write_text(json.dumps(data | {"eval_sha256": "0" * 64}))
    with pytest.raises(ar.AgentReportError, match="eval set sha256"):
        ar.main(argv)


def test_ac17_metrics_md_defines_every_emitted_metric(tmp_path):
    argv, out, _ = setup_files(tmp_path)
    ar.main(argv)
    names = json.loads((out / "summary.json").read_text())["metrics"]
    text = Path("docs/eval/results/metrics.md").read_text()
    assert [n for n in names if f"`{n}`" not in text] == []
    assert set(names) == set(ar.KIND)


def test_checks_constant_matches_guardrails():
    assert ar.CHECKS == tuple(guardrails.CHECKS)


def test_ac9_imports_no_agent_db_or_model_client():
    code = "import handbook_rag.evaluation.agent_report, sys; print(sorted(sys.modules))"
    env = {**os.environ, "PYTHONPATH": str(Path("src").resolve())}
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True, env=env
    )
    loaded = eval(out.stdout)
    banned = (
        "handbook_rag.agent",
        "handbook_rag.db",
        "handbook_rag.ask",
        "handbook_rag.models",
        "handbook_rag.evaluation.run",
        "handbook_rag.evaluation.checks",
        "psycopg",
        "openai",
    )
    hits = [m for m in loaded if any(m == b or m.startswith(b + ".") for b in banned)]
    assert hits == []
