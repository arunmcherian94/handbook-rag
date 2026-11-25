"""The agent's tool loop for one turn (spec 0013, AC-7 to AC-11, AC-14, AC-15), with the spec
0014 guardrails around it: input checks (AC-3, AC-4), excerpt events (AC-5), the final-answer
check with one retry (AC-7, AC-8), link and PII stripping (AC-9, AC-10), redaction before every
save (AC-11) and the guardrail_blocked state (AC-12).

run_turn is a function of (question, earlier turn records, model, tool): it holds no session
state of its own, so a later mode can wrap it or resume it from a saved record. The turn record
is handed to `save` after every step (AC-13); the caller decides where it goes.
"""

import json
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime

import tiktoken

from handbook_rag.agent import guardrails
from handbook_rag.agent.tool import TOOL, ToolTimeout, TurnTool
from handbook_rag.ask import CITATION, parse_citations
from handbook_rag.constants import (
    AGENT_MAX_STEPS,
    AGENT_MAX_TOKENS,
    AGENT_MAX_TOOL_CALLS,
    AGENT_TIMEOUT_S,
    MAX_CITATION,
    MAX_COMPLETION_TOKENS,
    TOKENIZER,
)
from handbook_rag.evaluation.checks import abstention
from handbook_rag.models import ChatModel, ChatStep, ToolCall
from handbook_rag.prompts import AGENT_SYSTEM_PROMPT, BUDGET_STOPPED, GUARDRAIL_REFUSALS

# The terminal states (0013 AC-11, amended by 0014 AC-12) and the budgets that can end a turn.
STATES = ("answered", "abstained", "budget_exhausted", "guardrail_blocked", "error")
BUDGET_NAMES = ("steps", "tool_calls", "tokens", "timeout")
# 0014 AC-3: questions blocked before any call. Not replayed in a follow-up (review fix): a
# replay would carry an over-long or garbage question past the input checks.
INPUT_BLOCKS = ("input_empty", "input_too_long", "input_garbage")
TOOL_BUDGET_SPENT = (
    "Error: the tool-call budget for this question is spent; answer from the excerpts above."
)


def budgets() -> dict:
    """The budgets a turn runs with, read from constants at call time (AC-9): never from a flag,
    an env var or a stored session."""
    return {
        "max_steps": AGENT_MAX_STEPS,
        "max_tool_calls": AGENT_MAX_TOOL_CALLS,
        "max_tokens": AGENT_MAX_TOKENS,
        "timeout_s": AGENT_TIMEOUT_S,
    }


def strip_markers(text: str) -> str:
    """Remove [n] citation markers from a replayed answer (AC-14, D7). Brackets that
    parse_citations ignores (numbers above MAX_CITATION: years, amounts) are kept."""

    def drop(m: re.Match) -> str:
        numbers = [int(x) for x in re.findall(r"\d+", m[1])]
        return m[0] if max(numbers) > MAX_CITATION else ""

    out = CITATION.sub(drop, text)
    out = re.sub(r"[ \t]+([.,;:!?)])", r"\1", out)  # "fact [1]." -> "fact ."  -> "fact."
    return re.sub(r"[ \t]{2,}", " ", out).strip()


def replay(history: list[dict]) -> list[dict]:
    """Earlier turns as question + final answer only, no tool calls or results (AC-14, D5).
    [n] stripped, cited sources appended as plain text. A turn with no answer (stopped by tokens
    or time, or an error) is replayed as its question alone."""
    messages: list[dict] = []
    for record in history:
        if record.get("guardrail_reason") in INPUT_BLOCKS:
            continue  # 0014 review fix: a blocked question never reaches the model, later either
        messages.append({"role": "user", "content": record["question"]})
        answer = record.get("answer")
        if answer is None:
            continue
        text = strip_markers(answer)
        sources = list(
            dict.fromkeys(f"{c['url_path']} — {c['heading']}" for c in record.get("citations", []))
        )
        if sources:
            text += "\n\nSources:\n" + "\n".join(f"- {s}" for s in sources)
        messages.append({"role": "assistant", "content": text})
    return messages


def _tokens(messages: list[dict], tools: list[dict]) -> int:
    """cl100k estimate of a request's input: the JSON of its messages and tools (AC-8)."""
    enc = tiktoken.get_encoding(TOKENIZER)
    blob = json.dumps(messages, ensure_ascii=False) + json.dumps(tools, ensure_ascii=False)
    return len(enc.encode(blob, disallowed_special=()))


def _assistant_message(step: ChatStep) -> dict:
    return {
        "role": "assistant",
        "content": step.text or None,
        "tool_calls": [
            {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": c.arguments}}
            for c in step.tool_calls
        ],
    }


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _excerpt_text(tool: TurnTool) -> str:
    """This turn's excerpt content: PII found verbatim here is handbook text (0014 AC-10)."""
    return "\n".join(e.content for e in tool.excerpts)


def _counts_event(check: str, counts: dict[str, int]) -> dict:
    """A PII check's event: redact with per-entity counts and a total, or pass (0014 AC-2)."""
    if not counts:
        return guardrails.event(check, "pass")
    return guardrails.event(check, "redact", "pii", **counts, count=sum(counts.values()))


def run_turn(
    model: ChatModel,
    tool: TurnTool,
    question: str,
    history: list[dict],
    save: Callable[[dict], None],
    turn_no: int = 1,
    clock: Callable[[], float] = time.monotonic,
) -> dict:
    """Run one turn to exactly one terminal state (AC-11) and return its record (AC-12).

    Never raises for a model, database or store failure: the turn ends as `error` with the
    exception's type and message (a last save is attempted).

    `save` and the caller receive a redacted copy of the record (spec 0014 AC-11); the working
    record, with the text the model saw, never leaves this function.
    """
    limits = budgets()
    policy = guardrails.POLICY
    events: list[dict] = []
    messages: list[dict] = []
    tools = [TOOL]
    record: dict = {
        "turn_no": turn_no,
        "question": question,  # stripped below; redacted in full on save (0014 AC-11)
        "answer_model": model.name,
        "started_at": _now(),
        "ended_at": None,
        "budgets": limits,
        "messages": messages,
        "excerpts": [],
        "steps": [],
        "state": None,
        "budget": None,
        "forced_final": False,
        "answer": None,
        "citations": [],
        "invalid_citations": [],
        "abstained": None,
        "abstention_label": None,
        "truncated": False,
        "tokens": {"input": 0, "output": 0},
        "latency_ms": 0.0,
        # BUDGET_STOPPED when tokens or time end the turn (AC-10); the GUARDRAIL_REFUSALS text
        # for a guardrail_blocked turn (0014 AC-12)
        "stop_message": None,
        "error": None,
        # spec 0014
        "guardrails_version": policy.version,  # AC-1
        "guardrails_sha256": policy.sha256(),
        "excerpt_nonce": tool.nonce,  # AC-5
        "guardrail_events": events,  # AC-2
        "guardrail_reason": None,  # AC-12
        "retries": 0,  # AC-8
    }
    t0 = clock()
    model_calls = tool_calls = 0

    def persist() -> dict:
        """Save and return a redacted copy (0014 AC-11): model text keeps values present in this
        turn's excerpts, user-originated text gets no exemption."""
        out = guardrails.redact_record(record, _excerpt_text(tool))
        save(out)
        return out

    def finish(state: str, budget: str | None = None) -> dict:
        record["state"], record["budget"] = state, budget
        record["excerpts"] = [
            {"n": e.n, "chunk_id": str(e.chunk_id), "url_path": e.url_path, "heading": e.heading}
            for e in tool.excerpts
        ]
        record["ended_at"] = _now()
        record["latency_ms"] = (clock() - t0) * 1000
        return persist()

    def block(reason: str, budget: str | None = None) -> dict:
        record["guardrail_reason"] = reason
        record["stop_message"] = GUARDRAIL_REFUSALS[reason]
        return finish("guardrail_blocked", budget)

    try:
        # Inside the try (review fix), so a failing check still ends the turn as `error`.
        clean, input_events, blocked = guardrails.check_input(question)  # 0014 AC-3, AC-4
        record["question"] = clean
        events.extend(input_events)
        # 0014 D4: the model gets the question with PII redacted, apart from @gitlab.com emails.
        to_model, pii = guardrails.redact_pii(clean, allow_gitlab_email=True)
        events.append(_counts_event("input_pii", pii))
        messages += [
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            *replay(history),
            {"role": "user", "content": to_model},
        ]
        if blocked:  # 0014 AC-3: no model, embedding or tool call
            return block(blocked)
        while True:
            elapsed = clock() - t0
            if elapsed >= limits["timeout_s"]:
                record["stop_message"] = BUDGET_STOPPED
                return finish("budget_exhausted", "timeout")
            # AC-10: the last allowed model call, or no tool calls left: tools off.
            if model_calls == limits["max_steps"] - 1:
                forced = "steps"
            elif tool_calls >= limits["max_tool_calls"]:
                forced = "tool_calls"
            else:
                forced = None
            tool_choice = "none" if forced else "auto"
            spent = record["tokens"]["input"] + record["tokens"]["output"]
            if spent + _tokens(messages, tools) + MAX_COMPLETION_TOKENS > limits["max_tokens"]:
                record["stop_message"] = BUDGET_STOPPED
                return finish("budget_exhausted", "tokens")

            t = clock()
            step = model.complete(
                messages, tools, tool_choice, timeout=limits["timeout_s"] - elapsed
            )
            model_calls += 1
            record["tokens"]["input"] += step.input_tokens
            record["tokens"]["output"] += step.output_tokens
            record["steps"].append(
                {
                    "kind": "model",
                    "tool_choice": tool_choice,
                    "input_tokens": step.input_tokens,
                    "output_tokens": step.output_tokens,
                    "finish_reason": step.finish_reason,
                    "tool_calls": len(step.tool_calls),
                    "latency_ms": (clock() - t) * 1000,
                }
            )

            if step.tool_calls and not forced:
                messages.append(_assistant_message(step))
                for call in step.tool_calls:  # one per step with parallel calls off
                    time_left = limits["timeout_s"] - (clock() - t0)
                    try:
                        messages.append(
                            _run_tool(tool, call, tool_calls, limits, record, time_left)
                        )
                    except ToolTimeout as e:  # AC-8: a retry wait would pass the turn's time
                        record["steps"].append(
                            {
                                "kind": "tool",
                                "id": call.id,
                                "name": call.name,
                                "arguments": call.arguments,
                                "accepted": True,
                                "error": str(e),
                                "numbers": [],
                                "chunk_ids": [],
                                "latency_ms": None,
                            }
                        )
                        record["stop_message"] = BUDGET_STOPPED
                        return finish("budget_exhausted", "timeout")
                    tool_calls += 1
                persist()
                continue

            # The final answer: a reply with no tool call, or the forced call (AC-7, AC-10).
            text = step.text
            if not text.strip():
                # Review fix: no text is not an answer. A forced call that still asked for a tool
                # ends like a token or time stop; an empty normal reply (e.g. content_filter) is
                # an error. Neither is replayed as an answer (AC-14).
                record["truncated"] = step.truncated
                if forced:
                    record["forced_final"] = True
                    record["stop_message"] = BUDGET_STOPPED
                    return finish("budget_exhausted", forced)
                record["error"] = {
                    "type": "EmptyReply",
                    "message": f"no text and no tool call (finish_reason {step.finish_reason})",
                }
                return finish("error")
            citations, invalid = parse_citations(text, tool.excerpts)  # AC-15: this turn only
            check = abstention(text, None)
            record.update(
                citations=[
                    {"n": c.n, "url_path": c.url_path, "heading": c.heading} for c in citations
                ],
                invalid_citations=invalid,
                abstained=check.abstained,
                abstention_label=check.label,
                truncated=step.truncated,
                forced_final=forced is not None,
            )
            failed = guardrails.final_check(len(citations), invalid, check.abstained, check.label)
            if failed:  # 0014 AC-7
                # Links stripped from the stored rejected reply too (review fix, AC-2: removed
                # URLs are never kept in full); PII is redacted on save like any assistant text.
                rejected = {"role": "assistant", "content": guardrails.strip_links(text)[0]}
                feedback = {
                    "role": "user",
                    "content": guardrails.retry_feedback(failed, invalid, len(tool.excerpts)),
                }
                spent = record["tokens"]["input"] + record["tokens"]["output"]
                projected = spent + _tokens([*messages, rejected, feedback], tools)
                can_retry = (  # 0014 AC-8: one retry, only inside the existing budgets
                    record["retries"] < policy.max_retries
                    and not forced
                    and model_calls < limits["max_steps"]
                    and clock() - t0 < limits["timeout_s"]
                    and projected + MAX_COMPLETION_TOKENS <= limits["max_tokens"]
                )
                messages.append(rejected)  # the rejected reply stays in the record (AC-12)
                action = "retry" if can_retry else "block"
                events.extend(guardrails.event("output_citation", action, r) for r in failed)
                if can_retry:
                    record["retries"] += 1
                    messages.append(feedback)
                    # Review fix: the rejected reply's checks must not outlive it.
                    record.update(
                        citations=[],
                        invalid_citations=[],
                        abstained=None,
                        abstention_label=None,
                        truncated=False,
                        forced_final=False,
                    )
                    persist()
                    continue
                # 0014 AC-12: takes precedence over budget_exhausted; budget still names the
                # budget that forced the reply.
                return block("citation_check_failed", forced)
            events.append(guardrails.event("output_citation", "pass"))
            answer, link_events = guardrails.strip_links(text)  # 0014 AC-9
            events.extend(link_events)
            answer, pii = guardrails.redact_pii(answer, keep=_excerpt_text(tool))  # 0014 AC-10
            events.append(_counts_event("output_pii", pii))
            record["answer"] = answer
            if forced:
                return finish("budget_exhausted", forced)
            return finish("abstained" if check.abstained else "answered")
    except Exception as e:  # noqa: BLE001 - AC-11: API, DB and store failures end the turn as error
        record["error"] = {"type": type(e).__name__, "message": str(e)}
        try:
            return finish("error")
        except Exception:  # noqa: BLE001 - the store itself failed; the caller still gets the record
            record["state"] = "error"
            try:
                return guardrails.redact_record(record, _excerpt_text(tool))
            except Exception:  # noqa: BLE001 - review fix: never return unredacted text
                return {**record, "question": "[unavailable]", "messages": [], "steps": []}


def _run_tool(
    tool: TurnTool, call: ToolCall, done: int, limits: dict, record: dict, time_left: float
) -> dict:
    """Execute one call, or refuse it when the tool-call budget is already spent (a parallel
    burst). Either way the model gets a tool message for the call id."""
    entry = {"kind": "tool", "id": call.id, "name": call.name, "arguments": call.arguments}
    if done >= limits["max_tool_calls"]:
        entry.update(
            accepted=False, error="tool-call budget spent", numbers=[], chunk_ids=[], latency_ms=0.0
        )
        content = TOOL_BUDGET_SPENT
    else:
        result = tool.execute(call, time_left=time_left)
        record["guardrail_events"].extend(result.events)  # 0014 AC-4, AC-5
        entry.update(
            accepted=result.accepted,
            error=result.error,
            numbers=list(result.numbers),
            chunk_ids=list(result.chunk_ids),
            latency_ms=result.latency_ms,
        )
        content = result.content
    record["steps"].append(entry)
    return {"role": "tool", "tool_call_id": call.id, "content": content}
