"""Trajectory eval collector (spec 0015, AC-1 to AC-8): run the agent over eval set v1.2.

    make agent-eval                    # dry run: no API call, no turn saved (AC-1)
    make paid-agent-eval CAP=<usd>     # spend, with a hard cap and no default (AC-2, AC-5)

Each live row is one turn in a fresh admin session, through `run_turn` as built, with the
guardrails policy as built (AC-3, AC-4): this module has no guardrails switch of any kind.
Scoring is a separate free step, `agent_report` (D6).

Run directory contract (read by agent_report; slice 0)
------------------------------------------------------
runs/eval/<YYYY-MM-DD>-<8 hex>/

rows.jsonl: one JSON object per turn, in eval-set file order, appended after each turn:
    {"row": int,              # Row.id
     "type": str,             # Row.type
     "session_id": str,       # the fresh agent session the turn ran in
     "record": dict}          # the redacted turn record run_turn returned (spec 0014 AC-11),
                              # the same dict it handed to store.save_turn; never unredacted

run.json: one JSON object, written before the first turn and rewritten after every turn:
    every key run.metadata() returns, except eval_depth, with:
        mode                  "agent"
        answer_model          the answer model spec
        system_prompt_sha256  sha256 of AGENT_SYSTEM_PROMPT (overrides the ask prompt's sha)
        rows                  live rows in the eval set (52 for v1.2)
    plus:
        guardrails_version, guardrails_sha256      the policy as built
        tool_sha256                                sha256 of json.dumps(TOOL, sort_keys=True)
        budgets                                    loop.budgets()
        retriever                                  {"kind": "dense", "embed_model", "config_id",
                                                    "k": TOP_K, "pages": AGENT_PAGES}
        prices                                     {"answer_input_usd_per_1m",
                                                    "answer_output_usd_per_1m",
                                                    "embed_usd_per_1m"}
        estimate_usd_per_turn                      agent.__main__.estimate()
        cap_usd                                    float
        actual_usd                                 running tally, float (AC-5)
        turns                                      rows written so far
        complete                                   bool: every row ran
        stopped                                    null | "cap" | "guardrails_sha" | "error"
        refs                                       {"<row id>": {
                                                       "expected_urls": [url_path, ...],
                                                       "relevant": {"<fact id>": [chunk_id, ...]}
                                                   }}
            refs holds, for every row: expected_docs as stored url_paths
            (ingest.derive_url_path), and for each Row.required fact the sorted chunk ids that
            evidence.check marks relevant (ADR-0015). Empty list/dict for ooc rows. The scorer
            reads relevance only from here (Arun, 27 Nov: the scorer stays DB-free).

Actual cost of one turn (AC-5): record tokens.input x answer input price + tokens.output x
answer output price + the cl100k tokens of each accepted query (counted before embedding, by a
wrapper passed as TurnTool's retrieve=) x the embedding price; all per 1M, from the price tables
in code at run time.
"""

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Callable
from pathlib import Path

import tiktoken

from handbook_rag import acl, ask, identity
from handbook_rag.agent import __main__ as agent_cli
from handbook_rag.agent import guardrails, store
from handbook_rag.agent.loop import budgets, run_turn
from handbook_rag.agent.tool import TOOL, TurnTool
from handbook_rag.constants import (
    AGENT_LEASE_MARGIN_S,
    AGENT_PAGES,
    AGENT_TIMEOUT_S,
    BASELINE_CONFIG,
    CORPUS_PREFIX,
    EVAL_RUNS,
    EVAL_SET,
    TOKENIZER,
    TOP_K,
)
from handbook_rag.corpus import read_manifest, verify
from handbook_rag.db import connect
from handbook_rag.evaluation import evidence as evidence_mod
from handbook_rag.evaluation import run as eval_run
from handbook_rag.evaluation.evalset import Row, parse
from handbook_rag.evaluation.evidence import EvidenceError
from handbook_rag.ingest import derive_url_path
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

AGENT_USER = "admin"  # AC-3: the quality set runs as admin, as the ask eval does

# A fake-able turn: row -> (session_id, record, query_tokens), see collect().
TurnFn = Callable[[Row], tuple[str, dict, int]]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def parse_cap(raw: str | None) -> float | None:
    """AC-2: the cap as a float, finite and above zero; None when not given."""
    if raw is None:
        return None
    try:
        cap = float(raw)
    except ValueError:
        raise SystemExit(f"--cap must be a number of USD, got {raw!r}") from None
    if not math.isfinite(cap) or cap <= 0:
        raise SystemExit(f"--cap must be finite and above 0, got {raw!r}")
    return cap


def turn_usd(record: dict, query_tokens: int, prices: dict) -> float:
    """AC-5: one turn's actual cost: model tokens at the answer prices, plus the query tokens
    the retriever embedded at the embedding price."""
    return (
        record["tokens"]["input"] * prices["answer_input_usd_per_1m"]
        + record["tokens"]["output"] * prices["answer_output_usd_per_1m"]
        + query_tokens * prices["embed_usd_per_1m"]
    ) / 1_000_000


class QueryCounter:
    """AC-5: wraps ask.retrieve as TurnTool's retrieve=, counting the cl100k tokens of each
    query it is handed before calling through. Reset per turn."""

    def __init__(self, retrieve: Callable = ask.retrieve):
        self._retrieve = retrieve
        self._enc = tiktoken.get_encoding(TOKENIZER)
        self.tokens = 0

    def reset(self) -> None:
        self.tokens = 0

    def __call__(self, conn, embedder, query, *args, **kwargs):
        # disallowed_special=() as TurnTool._validate: a query the tool accepts never fails here
        # (review fix).
        self.tokens += len(self._enc.encode(query, disallowed_special=()))
        return self._retrieve(conn, embedder, query, *args, **kwargs)


def _write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def collect(
    rows: list[Row],
    turn_fn: TurnFn,
    *,
    cap: float,
    bound: float,
    prices: dict,
    out_dir: Path,
    meta: dict,
) -> dict:
    """AC-5, AC-6, AC-7, AC-8: run turn_fn over rows in order, appending each row to
    out_dir/rows.jsonl and rewriting out_dir/run.json (meta, updated in place and returned)
    before the first turn and after every one.

    Before a turn: stop (stopped "cap") if tally + bound > cap, so the run can't pass the cap.
    After a turn that cost more than bound, stop too (stopped "cap"): the guarantee rests on it.
    After it: add its cost, then stop (stopped "guardrails_sha") if the record's policy sha isn't
    the run's. An unexpected exception records stopped "error" and is re-raised; rows written so
    far are kept either way. meta must carry guardrails_sha256."""
    meta.update(actual_usd=0.0, turns=0, complete=False, stopped=None)
    run_json = out_dir / "run.json"
    _write_json(run_json, meta)
    try:
        with (out_dir / "rows.jsonl").open("a", encoding="utf-8") as f:
            for row in rows:
                if meta["actual_usd"] + bound > cap:
                    meta["stopped"] = "cap"
                    break
                session_id, record, query_tokens = turn_fn(row)
                f.write(
                    json.dumps(
                        {
                            "row": row.id,
                            "type": row.type,
                            "session_id": session_id,
                            "record": record,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                f.flush()
                cost = turn_usd(record, query_tokens, prices)
                meta["actual_usd"] += cost
                meta["turns"] += 1
                if record["guardrails_sha256"] != meta["guardrails_sha256"]:
                    meta["stopped"] = "guardrails_sha"
                    break
                if cost > bound:  # review fix: the cap holds only while no turn passes the bound
                    meta["stopped"] = "cap"
                    break
                _write_json(run_json, meta)
            else:
                meta["complete"] = True
    except BaseException:
        meta["stopped"] = "error"
        raise
    finally:
        _write_json(run_json, meta)
    return meta


def _refs(rows: list[Row], evidence) -> dict:
    """AC-7: per row, expected_docs as stored url_paths and the relevant chunk ids per required
    fact (evidence.check's sets, ADR-0015); empty for ooc rows."""
    return {
        str(r.id): {
            "expected_urls": [derive_url_path(CORPUS_PREFIX + p) for p in r.expected_docs],
            "relevant": {
                f.id: sorted(str(c) for c in evidence.relevant[(r.id, f.id)]) for f in r.required
            },
        }
        for r in rows
    }


def agent_meta(
    *,
    eval_set,
    eval_bytes: bytes,
    corpus_sha: str,
    chunk_params: dict,
    embed_spec: str,
    answer_spec: str,
    policy,
    cap: float | None,
    bound: float,
    prices: dict,
    refs: dict,
) -> dict:
    """AC-7: run.json's contents before the first turn (contract: module docstring)."""
    meta = eval_run.metadata(
        eval_set.version,
        eval_bytes,
        corpus_sha,
        chunk_params,
        embed_spec,
        answer_spec,
        len(eval_set.rows),
        None,
        user_id=AGENT_USER,
        policy_version=policy.version,
        policy_sha256=policy.sha256,
    )
    del meta["eval_depth"]
    meta.update(
        mode="agent",
        answer_model=answer_spec,
        system_prompt_sha256=_sha256(AGENT_SYSTEM_PROMPT),
        guardrails_version=guardrails.POLICY.version,
        guardrails_sha256=guardrails.POLICY.sha256(),
        tool_sha256=_sha256(json.dumps(TOOL, sort_keys=True)),
        budgets=budgets(),
        retriever={
            "kind": "dense",
            "embed_model": embed_spec,
            "config_id": BASELINE_CONFIG,
            "k": TOP_K,
            "pages": AGENT_PAGES,
        },
        prices=prices,
        estimate_usd_per_turn=bound,
        cap_usd=cap,
        refs=refs,
    )
    return meta


def make_turn(conn, model, embedder, principal, new_header: Callable[[], dict]) -> TurnFn:
    """AC-3: the per-row turn. Each call makes a fresh session from new_header() (a new session id),
    claims it, runs one turn through run_turn as built, and releases the lease. Returns
    (session_id, record, query tokens embedded)."""
    counter = QueryCounter()

    def turn(row: Row) -> tuple[str, dict, int]:
        session = store.create(conn, new_header())
        store.claim(conn, session, AGENT_TIMEOUT_S + AGENT_LEASE_MARGIN_S)
        sid = str(session.session_id)
        counter.reset()
        try:
            record = run_turn(
                model,
                TurnTool(conn, embedder, principal, retrieve=counter),
                row.question,
                [],
                save=lambda r: store.save_turn(conn, sid, 1, r),
                turn_no=1,
            )
        finally:
            try:
                store.release(conn, sid)
            except Exception as e:  # noqa: BLE001 - the lease expires on its own
                print(f"WARNING: lease not released ({type(e).__name__}: {e})", file=sys.stderr)
        return sid, record, counter.tokens

    return turn


def spend_status(meta: dict) -> str:
    """AC-7: the spend line's status: "ok" every row ran, "stopped" a cap or guardrails-sha stop,
    "failed" an error (or a run that never recorded a stop)."""
    if meta.get("complete"):
        return "ok"
    return "stopped" if meta.get("stopped") in ("cap", "guardrails_sha") else "failed"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the agent over the eval set (spec 0015).")
    ap.add_argument("--cap", help="hard spend cap in USD; required with --confirm (AC-2)")
    ap.add_argument("--confirm", action="store_true", help="spend; without it, a dry run")
    args = ap.parse_args(argv)  # no guardrails or budget flags exist (AC-4)
    cap = parse_cap(args.cap)
    if args.confirm and cap is None:
        raise SystemExit("--confirm needs --cap <usd>: the cap has no default")
    manifest = read_manifest()
    if error := verify(manifest):
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    eval_bytes = EVAL_SET.read_bytes()
    eval_set = parse(eval_bytes.decode("utf-8"))
    rows = list(eval_set.rows)
    answer_spec = resolve_answer_spec()
    try:
        embed_spec = describe_embedder(resolve_embed_spec()).name
        bound = agent_cli.estimate(embed_spec, answer_spec)
        in_price, out_price = answer_usd_per_1m(answer_spec)
        embed_price = embed_usd_per_1m(embed_spec)
    except ValueError as e:
        raise SystemExit(str(e)) from None
    prices = {
        "answer_input_usd_per_1m": in_price,
        "answer_output_usd_per_1m": out_price,
        "embed_usd_per_1m": embed_price,
    }
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
            acl.check_stale(conn, policy)
        except (acl.StaleACL, acl.AclError) as e:
            raise SystemExit(str(e)) from None
        principal = identity.load(AGENT_USER, policy)
        b = budgets()
        print(
            f"agent eval {eval_set.version}: {len(rows)} live rows, as {AGENT_USER}\n"
            f"models: {embed_spec}, {answer_spec}\n"
            f"retriever: dense, {BASELINE_CONFIG}, k {TOP_K}, {AGENT_PAGES} pages\n"
            f"budgets per turn: {b['max_steps']} steps, {b['max_tool_calls']} tool calls, "
            f"{b['max_tokens']} tokens, {b['timeout_s']:.0f} s\n"
            f"guardrails: {guardrails.POLICY.version} {guardrails.POLICY.sha256()}\n"
            f"upper bound per turn ${bound:.4f}, full run ${bound * len(rows):.4f}"
            + (f"\ncap ${cap:.4f}" if cap is not None else "")
        )
        if not paid(args.confirm, "agent-eval"):  # spec 0009, AC-1
            return 0
        chunk_params, corpus_sha = eval_run.stored_chunk_params(conn, manifest.sha, BASELINE_CONFIG)
        try:
            ev = evidence_mod.check(rows, conn, BASELINE_CONFIG)
        except EvidenceError as e:
            raise SystemExit(str(e)) from None
        meta = agent_meta(
            eval_set=eval_set,
            eval_bytes=eval_bytes,
            corpus_sha=corpus_sha,
            chunk_params=chunk_params,
            embed_spec=embed_spec,
            answer_spec=answer_spec,
            policy=policy,
            cap=cap,
            bound=bound,
            prices=prices,
            refs=_refs(rows, ev),
        )
        out_dir = eval_run.new_run_dir(EVAL_RUNS, meta)
        store.ensure_schema(conn)
        bound_session = agent_cli.binding(principal, policy)
        turn = make_turn(
            conn,
            make_chat_model(answer_spec),
            make_embedder(embed_spec),
            principal,
            lambda: agent_cli.header(bound_session, embed_spec, answer_spec, corpus_sha),
        )

        try:
            collect(rows, turn, cap=cap, bound=bound, prices=prices, out_dir=out_dir, meta=meta)
        finally:  # spec 0009, AC-3: logged even when the run fails after spending
            log_spend(
                "agent-eval",
                bound * len(rows),
                run_id=out_dir.name,
                embed_model=embed_spec,
                answer_model=answer_spec,
                status=spend_status(meta),
                actual_usd=meta["actual_usd"],
            )
    print(
        f"run {out_dir.name}: {meta['turns']}/{len(rows)} rows, actual ${meta['actual_usd']:.4f}"
        f", complete {meta['complete']}, stopped {meta['stopped']}"
    )
    return 0 if meta["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
