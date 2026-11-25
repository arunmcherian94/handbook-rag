"""Agent CLI (spec 0013, AC-14, AC-16, AC-17): `make agent` dry-runs, `make paid-agent` spends.

    python -m handbook_rag.agent --as us-ic "question" [--session <id>] [--confirm]

The Principal is bound here, once, from --as, and closed over by the tool (AC-5). Every turn
checks the ACLs are fresh and the session's binding first (AC-6).
"""

import argparse
import hashlib
import json
import sys
import uuid
from datetime import UTC, datetime

from handbook_rag import acl, identity
from handbook_rag.agent import guardrails, store
from handbook_rag.agent.loop import budgets, run_turn
from handbook_rag.agent.tool import TOOL, TurnTool
from handbook_rag.constants import (
    AGENT_LEASE_MARGIN_S,
    AGENT_MAX_QUERY_TOKENS,
    AGENT_MAX_TOKENS,
    AGENT_MAX_TOOL_CALLS,
    AGENT_TIMEOUT_S,
    BASELINE_CONFIG,
)
from handbook_rag.corpus import read_manifest, verify
from handbook_rag.db import connect
from handbook_rag.models import (
    answer_usd_per_1m,
    describe_embedder,
    embed_usd_per_1m,
    make_chat_model,
    make_embedder,
    resolve_answer_spec,
    resolve_embed_spec,
)
from handbook_rag.prompts import AGENT_SYSTEM_PROMPT
from handbook_rag.spend import log_spend, paid


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def estimate(embed_spec: str, answer_spec: str) -> float:
    """AC-16: an upper bound for one turn. max_tool_calls query embeds at the query cap, plus
    max_tokens all priced at the answer model's output rate. Unknown models raise ValueError."""
    embeds = AGENT_MAX_TOOL_CALLS * AGENT_MAX_QUERY_TOKENS * embed_usd_per_1m(embed_spec)
    _, output = answer_usd_per_1m(answer_spec)
    return (embeds + AGENT_MAX_TOKENS * output) / 1_000_000


def binding(principal, policy) -> dict:
    """The values a session is bound to (AC-6)."""
    version, sha = identity.fixture_version()
    return {
        "user_id": principal.user_id,
        "groups": principal.group_list,
        "policy_version": policy.version,
        "policy_sha256": policy.sha256,
        "identities_version": version,
        "identities_sha256": sha,
    }


def header(bound: dict, embed_spec: str, answer_spec: str, corpus_sha: str) -> dict:
    """The session header (AC-12)."""
    return {
        "session_id": str(uuid.uuid4()),
        "created_at": datetime.now(UTC).isoformat(),
        **bound,
        "answer_model": answer_spec,
        "embed_model": embed_spec,
        "config_id": BASELINE_CONFIG,
        "corpus_sha": corpus_sha,
        "system_prompt_sha256": _sha256(AGENT_SYSTEM_PROMPT),
        "tool_sha256": _sha256(json.dumps(TOOL, sort_keys=True)),
        # spec 0014 AC-1: recorded, not bound (D8); every turn records the version it ran
        "guardrails_version": guardrails.POLICY.version,
        "guardrails_sha256": guardrails.POLICY.sha256(),
    }


def format_turn(record: dict, session_id: str) -> str:
    """The answer and its checks, as ask.format_result prints them (AC-15), then the trajectory."""
    state = record["state"]
    if record["answer"] is not None:
        lines = [record["answer"], "", "Sources:"]
        lines += [f"  [{c['n']}] {c['url_path']} — {c['heading']}" for c in record["citations"]]
        if not record["citations"]:
            lines.append("  (none)")
    else:
        lines = [record["stop_message"] or f"(no answer: {record['error']})"]
    warnings = []
    if record["invalid_citations"]:
        warnings.append(f"invalid citations {record['invalid_citations']}")
    if record["truncated"]:
        warnings.append("answer truncated at the output token cap")
    if record["abstention_label"]:
        warnings.append(f"abstention: {record['abstention_label']}")
    if warnings:
        lines += ["", "WARNING: " + "; ".join(warnings)]
    lines += ["", "Steps:"]
    for s in record["steps"]:
        if s["kind"] == "model":
            lines.append(
                f"  model ({s['tool_choice']}): in {s['input_tokens']}, out {s['output_tokens']}, "
                f"{s['finish_reason']}, {s['latency_ms']:.0f} ms"
            )
        else:
            mark = f"-> {s['numbers']}" if s["accepted"] else f"rejected: {s['error']}"
            lines.append(f"  {s['name']} {s['arguments']} {mark}")
    notes = [n for n in (record.get("guardrail_reason"), record["budget"]) if n]
    if record["budget"] and record["forced_final"]:
        notes.append("forced final")
    suffix = f" ({', '.join(notes)})" if notes else ""
    t = record["tokens"]
    lines += [
        "",
        guardrails.format_events(record.get("guardrail_events", [])),  # spec 0014 AC-2
        f"state: {state}{suffix} | tokens: in {t['input']}, "
        f"out {t['output']} | latency {record['latency_ms']:.0f} ms",
        f"session {session_id}, turn {record['turn_no']}: follow up with SESSION={session_id}",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Ask the GitLab handbook agent a question.")
    ap.add_argument("question")
    ap.add_argument("--as", dest="user_id", required=True, help="fixture user to ask as")
    ap.add_argument("--session", help="continue this session (AC-14); omit to start one")
    ap.add_argument("--confirm", action="store_true", help="spend; without it, a dry run")
    args = ap.parse_args(argv)  # no budget flags: budgets change only in constants.py (AC-9)
    manifest = read_manifest()
    if error := verify(manifest):
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    answer_spec = resolve_answer_spec()
    try:  # an unknown model or bad @dims fails the dry run
        embed_spec = describe_embedder(resolve_embed_spec()).name
        usd = estimate(embed_spec, answer_spec)
    except ValueError as e:
        raise SystemExit(str(e)) from None
    with connect() as conn:
        (embedded,) = conn.execute(
            "SELECT EXISTS (SELECT 1 FROM chunk_embeddings WHERE model = %s)", (embed_spec,)
        ).fetchone()
        if not embedded:
            raise SystemExit(
                f"no embeddings for {embed_spec}; run `make embed` for the cost, "
                "then `make paid-embed`"
            )
        policy = acl.load_policy(conn)
        try:
            acl.check_stale(conn, policy)  # AC-6, spec 0007 AC-5: never filter on stale ACLs
        except (acl.StaleACL, acl.AclError) as e:
            raise SystemExit(str(e)) from None
        principal = identity.load(args.user_id, policy)
        bound = binding(principal, policy)
        tables = store.tables_exist(conn)
        session = None
        if args.session:
            if not tables:
                raise SystemExit(f"no session {args.session}: the session tables don't exist")
            try:
                session = store.load(conn, args.session)
                store.check_binding(session.header, bound)  # AC-6: before any call
            except (store.SessionNotFound, store.SessionMismatch) as e:
                raise SystemExit(str(e)) from None
        b = budgets()
        print(
            f"agent as {args.user_id}: {embed_spec}, {answer_spec}, {BASELINE_CONFIG}\n"
            f"budgets per turn: {b['max_steps']} steps, {b['max_tool_calls']} tool calls, "
            f"{b['max_tokens']} tokens, {b['timeout_s']:.0f} s\n"
            + (
                f"session {session.session_id}, turn {len(session.turns) + 1}\n"
                if session
                else "new session\n"
            )
            + f"estimated cost (upper bound, one turn) ${usd:.4f}"
        )
        if not tables:
            print("session tables missing; the first `make paid-agent` creates them")
        if not paid(args.confirm, "agent"):  # spec 0009, AC-1
            return 0
        store.ensure_schema(conn)
        if session is None:
            session = store.create(conn, header(bound, embed_spec, answer_spec, manifest.sha))
        try:
            store.claim(conn, session, AGENT_TIMEOUT_S + AGENT_LEASE_MARGIN_S)  # AC-13
        except store.SessionBusy as e:
            raise SystemExit(str(e)) from None
        turn_no = len(session.turns) + 1
        sid = str(session.session_id)
        status = "failed"
        try:  # everything after the claim sits inside it, so the lease is always released
            # Built only after confirm, so a dry run needs no API key.
            embedder, model = make_embedder(embed_spec), make_chat_model(answer_spec)
            tool = TurnTool(conn, embedder, principal)
            record = run_turn(
                model,
                tool,
                args.question,
                session.turns,
                save=lambda r: store.save_turn(conn, sid, turn_no, r),
                turn_no=turn_no,
            )
            status = record["state"]
        finally:  # spec 0009, AC-3: logged even when the turn fails after spending
            try:
                store.release(conn, sid)
            except Exception as e:  # noqa: BLE001 - the lease expires on its own (AC-13)
                print(f"WARNING: lease not released ({type(e).__name__}: {e})", file=sys.stderr)
            log_spend(
                "agent",
                usd,
                run_id=sid,
                embed_model=embed_spec,
                answer_model=answer_spec,
                status=status,
            )
    print(format_turn(record, sid))
    return 0 if record["state"] != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
