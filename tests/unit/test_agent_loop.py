"""The agent loop (spec 0013, AC-4, AC-5, AC-7 to AC-11, AC-14, AC-15) with a fake model and a
fake retriever behind a real TurnTool."""

import json
import uuid

import pytest
from fakes import FakeChatModel, final_step, make_principal, raw_tool_step, status_error, tool_step

from handbook_rag import constants
from handbook_rag.agent import loop
from handbook_rag.agent.__main__ import main
from handbook_rag.agent.loop import budgets, replay, run_turn, strip_markers
from handbook_rag.agent.tool import TurnTool
from handbook_rag.ask import Retrieved
from handbook_rag.models import ChatStep, ToolCall
from handbook_rag.prompts import BUDGET_STOPPED, NOT_FOUND, OUT_OF_SCOPE

P = make_principal("staff")


def retrieved(label: str, k: int = 5) -> list[Retrieved]:
    return [
        Retrieved(
            n=i,
            chunk_id=uuid.uuid5(uuid.NAMESPACE_URL, f"{label}/{i}"),
            doc_id=uuid.uuid4(),
            url_path=f"/handbook/{label}/{i}/",
            heading=f"Heading {label} {i}",
            content=f"content {label} {i}",
            distance=i / 10,
            chunk_size=512,
            chunk_overlap=64,
            tokenizer="cl100k_base",
            commit_sha="abc",
        )
        for i in range(1, k + 1)
    ]


class Retriever:
    """Fake ask.retrieve: one distinct chunk set per query; records every call."""

    def __init__(self):
        self.calls: list[dict] = []

    def __call__(self, conn, embedder, query, principal, k, config_id=None, **kw):
        self.calls.append({"query": query, "principal": principal, "k": k})
        return retrieved(query, k=k)


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def make_tool(principal=P):
    r = Retriever()
    return TurnTool(None, None, principal, retrieve=r), r


def run(script, question="Q?", history=(), principal=P, save=None, clock=None, turn_no=1):
    tool, r = make_tool(principal)
    model = FakeChatModel(script)
    saved: list[dict] = []
    kwargs = {"clock": clock} if clock else {}
    rec = run_turn(
        model,
        tool,
        question,
        list(history),
        save or (lambda rec: saved.append(json.loads(json.dumps(rec)))),
        turn_no=turn_no,
        **kwargs,
    )
    return rec, model, r, saved


# AC-7, AC-11, AC-15


def test_tool_then_final_answered():
    """AC-7, AC-11, AC-15: model, tool, model -> answered; citations parse against this turn."""
    rec, model, r, _ = run([tool_step("leave"), final_step("Take leave [1] and [2].")])
    assert rec["state"] == "answered" and rec["budget"] is None and not rec["forced_final"]
    assert [s["kind"] for s in rec["steps"]] == ["model", "tool", "model"]
    assert [s["tool_choice"] for s in rec["steps"] if s["kind"] == "model"] == ["auto", "auto"]
    assert [e["n"] for e in rec["excerpts"]] == [1, 2, 3, 4, 5]
    assert rec["excerpts"][0]["url_path"] == "/handbook/leave/1/"
    assert [c["n"] for c in rec["citations"]] == [1, 2]
    assert rec["invalid_citations"] == [] and rec["abstained"] is False
    assert rec["answer"] == "Take leave [1] and [2]."
    assert rec["tokens"] == {"input": 200, "output": 40}
    assert rec["ended_at"] and rec["error"] is None
    assert [m["role"] for m in model.calls[1]["messages"]][-2:] == ["assistant", "tool"]
    assert r.calls[0]["k"] == 5


@pytest.mark.parametrize("text", [NOT_FOUND, OUT_OF_SCOPE])
def test_fixed_strings_abstain(text):
    """AC-11: a NOT_FOUND or OUT_OF_SCOPE reply is `abstained`."""
    rec, *_ = run([tool_step("x"), final_step(text)])
    assert rec["state"] == "abstained" and rec["abstained"] is True


def test_invalid_citation_beyond_excerpts():
    """AC-15: an [n] beyond this turn's excerpts is invalid."""
    rec, *_ = run([tool_step("x"), final_step("Claim [1] and [9].")])
    assert rec["state"] == "answered"
    assert rec["invalid_citations"] == [9] and [c["n"] for c in rec["citations"]] == [1]


def test_no_tool_call_means_no_valid_citation():
    """AC-15: citing without any retrieval is invalid."""
    rec, *_ = run([final_step("Direct [1].")])
    assert rec["invalid_citations"] == [1] and rec["citations"] == []


def test_truncated_final():
    """AC-11: finish_reason length marks the record truncated."""
    rec, *_ = run([tool_step("x"), final_step("Cut off [1]", finish_reason="length")])
    assert rec["truncated"] is True and rec["state"] == "answered"


@pytest.mark.parametrize(
    "exc", [RuntimeError("boom"), status_error(500)], ids=["runtime", "api-500"]
)
def test_model_error(exc):
    """AC-11: a raising model ends the turn as `error` with type and message, no raise."""
    rec, _, _, saved = run([tool_step("x"), exc])
    assert rec["state"] == "error" and rec["answer"] is None
    assert rec["error"]["type"] == type(exc).__name__
    assert rec["error"]["message"] == str(exc)
    assert saved[-1]["state"] == "error"


def test_save_failure_is_error_and_returns_record():
    """AC-11, AC-13: save raising on the first call ends the turn as error; a record returns."""

    def bad_save(rec):
        raise OSError("db down")

    rec, *_ = run([tool_step("x"), final_step("ok [1]")], save=bad_save)
    assert rec["state"] == "error" and rec["error"] == {"type": "OSError", "message": "db down"}


def test_malformed_calls_recovered():
    """AC-11: bad JSON, unknown tool and an extra user_id get error tool messages; the model
    recovers and answers."""
    rec, model, r, _ = run(
        [
            raw_tool_step("{not json", call_id="a"),
            raw_tool_step("{}", name="delete_all", call_id="b"),
            tool_step("x", call_id="c", user_id="admin"),
            tool_step("ok query", call_id="d"),
            final_step("Fine [1]."),
        ]
    )
    assert rec["state"] == "answered"
    tools = [s for s in rec["steps"] if s["kind"] == "tool"]
    assert [t["accepted"] for t in tools] == [False, False, False, True]
    assert all(t["error"] for t in tools[:3])
    last = model.calls[3]["messages"]
    assert [m["content"].startswith("Error:") for m in last if m["role"] == "tool"] == [
        True,
        True,
        True,
    ]
    assert [c["query"] for c in r.calls] == ["ok query"]


def test_save_after_every_tool_step_and_at_end():
    """AC-13: save runs after each tool step and at the terminal state."""
    _, _, _, saved = run([tool_step("a"), tool_step("b", call_id="c2"), final_step("Done [1].")])
    assert [s["state"] for s in saved] == [None, None, "answered"]
    assert [len(s["steps"]) for s in saved] == [2, 4, 5]


# AC-8, AC-10


def test_step_budget_forces_final():
    """AC-8, AC-10: a model that always calls tools ends at 6 calls, the 6th with tools off."""

    def script(i, messages, tools, tool_choice):
        if tool_choice == "none":
            return final_step("Best effort [1].")
        return tool_step(f"query {i}", call_id=f"c{i}")

    rec, model, r, _ = run(script)
    assert len(model.calls) == 6 == budgets()["max_steps"]
    assert [c["tool_choice"] for c in model.calls] == ["auto"] * 5 + ["none"]
    assert rec["state"] == "budget_exhausted" and rec["budget"] == "steps"
    assert rec["forced_final"] is True and rec["answer"] == "Best effort [1]."
    assert [c["n"] for c in rec["citations"]] == [1]
    assert len(r.calls) == 5


def test_forced_call_tool_use_is_ignored():
    """AC-10: if the model still emits a tool call on the forced call, its text is the answer
    and the call is not executed."""

    def script(i, messages, tools, tool_choice):
        if tool_choice == "none":
            return ChatStep("Text [1]", (ToolCall("z", "retrieve", "{}"),), 10, 5, "stop")
        return tool_step(f"query {i}", call_id=f"c{i}")

    rec, _, r, _ = run(script)
    assert rec["state"] == "budget_exhausted" and rec["answer"] == "Text [1]"
    assert len(r.calls) == 5


def three_calls(tag):
    calls = tuple(
        ToolCall(f"{tag}{j}", "retrieve", json.dumps({"query": f"{tag} q{j}", "page": 1}))
        for j in range(3)
    )
    return ChatStep("", calls, 100, 20, "tool_calls")


def test_tool_call_budget_binds_alone():
    """AC-8, AC-10: 3 calls per step; the 6th is refused without reaching the retriever, and
    the 3rd model call is forced with budget tool_calls."""

    def script(i, messages, tools, tool_choice):
        return final_step("Done [1].") if tool_choice == "none" else three_calls(f"s{i}")

    rec, model, r, _ = run(script)
    assert len(model.calls) == 3 and model.calls[2]["tool_choice"] == "none"
    assert rec["state"] == "budget_exhausted" and rec["budget"] == "tool_calls"
    assert rec["forced_final"] is True
    tools = [s for s in rec["steps"] if s["kind"] == "tool"]
    assert [t["accepted"] for t in tools] == [True] * 5 + [False]
    assert tools[-1]["error"] == "tool-call budget spent"
    assert len(r.calls) == 5
    refused = [m for m in model.calls[2]["messages"] if m["role"] == "tool"][-1]
    assert refused["content"] == loop.TOOL_BUDGET_SPENT


def test_rejected_calls_count_toward_budget():
    """AC-8: rejected calls spend the tool-call budget."""
    bad = ChatStep(
        "",
        tuple(ToolCall(f"b{j}", "nope", "{}") for j in range(3)),
        100,
        20,
        "tool_calls",
    )

    def script(i, messages, tools, tool_choice):
        if tool_choice == "none":
            return final_step("Done.")
        return bad if i == 0 else three_calls("g")

    rec, model, r, _ = run(script)
    assert rec["budget"] == "tool_calls" and len(model.calls) == 3
    assert len(r.calls) == 2  # 3 rejected + 2 executed = 5, the 6th refused


def test_token_budget_stops_before_call():
    """AC-8, AC-10, AC-11: huge reported input tokens stop the next call before it is made."""
    big = ChatStep(
        "", (ToolCall("c", "retrieve", json.dumps({"query": "q", "page": 1})),), 49_000, 20, "x"
    )
    rec, model, *_ = run([big])
    assert len(model.calls) == 1
    assert rec["state"] == "budget_exhausted" and rec["budget"] == "tokens"
    assert rec["answer"] is None and rec["forced_final"] is False
    assert rec["stop_message"] == BUDGET_STOPPED


def test_timeout_stops_before_call_and_passes_remaining():
    """AC-8, AC-10: past 90 s no further model call; the timeout passed is the time left."""
    clock = Clock()

    def script(i, messages, tools, tool_choice):
        clock.t = 30.0 if i == 0 else 100.0
        return tool_step(f"query {i}", call_id=f"c{i}")

    rec, model, *_ = run(script, clock=clock)
    assert [c["timeout"] for c in model.calls] == [90.0, 60.0]
    assert rec["state"] == "budget_exhausted" and rec["budget"] == "timeout"
    assert rec["answer"] is None and rec["stop_message"] == BUDGET_STOPPED
    assert len(model.calls) == 2


# AC-9


def test_record_budgets_equal_constants():
    """AC-9: the record stores the budgets it ran with."""
    rec, *_ = run([final_step("x")])
    assert rec["budgets"] == {
        "max_steps": constants.AGENT_MAX_STEPS,
        "max_tool_calls": constants.AGENT_MAX_TOOL_CALLS,
        "max_tokens": constants.AGENT_MAX_TOKENS,
        "timeout_s": constants.AGENT_TIMEOUT_S,
    }


def test_budgets_ignore_env(monkeypatch):
    """AC-9: no environment variable moves a budget."""
    before = budgets()
    for name in (
        "AGENT_MAX_STEPS",
        "AGENT_MAX_TOOL_CALLS",
        "AGENT_MAX_TOKENS",
        "AGENT_TIMEOUT_S",
        "AGENT_TIMEOUT",
    ):
        monkeypatch.setenv(name, "1")
    assert budgets() == before


def test_cli_has_no_budget_option(capsys):
    """AC-9: the CLI parser rejects a budget flag."""
    with pytest.raises(SystemExit) as e:
        main(["--as", "us-ic", "--max-steps", "9", "q"])
    assert e.value.code == 2
    assert "--max-steps" in capsys.readouterr().err


# AC-5


def test_principal_identity_across_turns():
    """AC-5: every retrieve receives the identical bound Principal object, in every turn."""
    seen = []
    history: list[dict] = []
    for turn in (1, 2):
        rec, _, r, _ = run(
            [tool_step(f"a{turn}"), tool_step(f"b{turn}", call_id="c2"), final_step("ok [1].")],
            question=f"Q{turn}",
            history=history,
            turn_no=turn,
        )
        seen += [c["principal"] for c in r.calls]
        history.append(rec)
    assert len(seen) == 4 and all(p is P for p in seen)


@pytest.mark.parametrize("extra", ["user_id", "groups", "as"])
def test_identity_arguments_never_reach_retriever(extra):
    """AC-5: a user_id/groups/as argument is rejected before the retriever."""
    rec, _, r, _ = run([tool_step("q", **{extra: "admin"}), final_step("No.")])
    (t,) = [s for s in rec["steps"] if s["kind"] == "tool"]
    assert t["accepted"] is False and extra in t["error"]
    assert r.calls == []


# AC-4, AC-14


def test_follow_up_replays_answer_only():
    """AC-4, AC-14: turn 2 uses a new TurnTool; its first call sees turn 1's question and answer
    with [n] stripped and Sources, no tool messages."""
    rec1, *_ = run(
        [tool_step("leave"), final_step("You get 20 days [1] in 2024 [2024], see also [2].")],
        question="How much leave?",
    )
    assert [c["n"] for c in rec1["citations"]] == [1, 2]
    rec2, model2, *_ = run(
        [tool_step("contractors"), final_step("Not for contractors [1].")],
        question="And contractors?",
        history=[rec1],
        turn_no=2,
    )
    first = model2.calls[0]["messages"]
    assert [m["role"] for m in first] == ["system", "user", "assistant", "user"]
    assert first[1]["content"] == "How much leave?"
    assert first[2]["content"] == (
        "You get 20 days in 2024 [2024], see also.\n\n"
        "Sources:\n- /handbook/leave/1/ — Heading leave 1\n- /handbook/leave/2/ — Heading leave 2"
    )
    assert first[3]["content"] == "And contractors?"
    assert not any(m["role"] == "tool" or "tool_calls" in m for m in first)
    assert [e["n"] for e in rec2["excerpts"]][0] == 1  # numbers restart


def test_replay_no_answer_is_question_only():
    """AC-14: a turn with answer None replays as its question alone."""
    msgs = replay([{"question": "Q1", "answer": None, "citations": []}])
    assert msgs == [{"role": "user", "content": "Q1"}]


def test_strip_markers_keeps_years():
    """AC-14: [n] up to 99 is stripped; [2024] stays."""
    assert strip_markers("Fact [1]. In [2024] it, [3] ok.") == "Fact. In [2024] it, ok."


def test_forced_call_with_no_text_is_not_an_answer():
    """AC-10 (review fix): a forced call that returns only a tool call ends like a token or
    time stop: no answer, the fixed message, and replayed as the question only."""

    def script(i, messages, tools, tool_choice):
        if tool_choice == "none":
            return tool_step("still searching", call_id="late")
        return tool_step(f"query {i}", call_id=f"c{i}")

    rec, _, r, _ = run(script)
    assert rec["state"] == "budget_exhausted" and rec["budget"] == "steps"
    assert rec["forced_final"] is True
    assert rec["answer"] is None and rec["stop_message"] == BUDGET_STOPPED
    assert len(r.calls) == 5
    assert replay([rec]) == [{"role": "user", "content": rec["question"]}]


@pytest.mark.parametrize("finish", ["content_filter", "length", "stop"])
def test_empty_reply_is_error(finish):
    """AC-11 (review fix): a normal reply with no text and no tool call is an error, not
    `answered`, and is not replayed as an answer."""
    rec, _, _, _ = run([final_step("", finish_reason=finish)])
    assert rec["state"] == "error" and rec["answer"] is None
    assert rec["error"]["type"] == "EmptyReply" and finish in rec["error"]["message"]
    assert replay([rec]) == [{"role": "user", "content": rec["question"]}]


def test_retry_wait_past_the_turn_time_stops_the_turn():
    """AC-8 (review fix): a query-embed retry wait that would pass the turn's remaining time
    ends the turn as budget_exhausted/timeout instead of sleeping."""
    clock = Clock()
    clock.t = 80.0  # 10 s left when the tool runs (the turn starts at 80)

    class SlowRetriever(Retriever):
        def __call__(self, conn, embedder, query, principal, k, config_id=None, **kw):
            kw["sleep"](100.0)  # a backoff longer than the turn has left
            raise AssertionError("unreachable")

    tool = TurnTool(None, None, P, retrieve=SlowRetriever(), clock=clock)
    model = FakeChatModel([tool_step("q")])
    rec = run_turn(model, tool, "Q?", [], save=lambda r: None, clock=clock)
    assert rec["state"] == "budget_exhausted" and rec["budget"] == "timeout"
    assert rec["answer"] is None and rec["stop_message"] == BUDGET_STOPPED
    assert len(model.calls) == 1
    assert rec["steps"][-1]["kind"] == "tool" and "retry wait" in rec["steps"][-1]["error"]
