"""Agent trajectory scoring over a stored run (spec 0015, AC-9 to AC-17). No DB, no API key, no
agent loop, no model client: it reads runs/eval/<run>/ (see agent_run for the contract), the
eval set, the assertion and review files, and the comparison runs' metadata and rows, and writes
docs/eval/results/<run>/summary.json and summary.md. Output is deterministic: sorted keys,
eval-set order, no wall-clock values. Must not import handbook_rag.agent, db, ask, models,
evaluation.run or evaluation.checks (AC-9)."""

import argparse
import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from handbook_rag.constants import EVAL_SET
from handbook_rag.evaluation.assertions import (
    ASSERTIONS_PATH,
    FACT_PASS,
    REVIEW_PATH,
    ROW_PASS,
    Assertions,
    ReviewRow,
    load_assertions,
    load_review,
    score,
)
from handbook_rag.evaluation.evalset import EvalSet, Row, parse
from handbook_rag.evaluation.metrics import Stat, fact_recall_at, mean_se

RUNS_ROOT = Path("runs/eval")
RESULTS_ROOT = Path("docs/eval/results")
STATES = ("answered", "abstained", "budget_exhausted", "guardrail_blocked", "error")
# Copied from agent.guardrails.CHECKS so this module never imports the agent package (AC-9);
# a unit test asserts the two agree.
CHECKS = (
    "input_invisible",
    "input_empty",
    "input_length",
    "input_garbage",
    "input_injection",
    "input_pii",
    "excerpt_invisible",
    "excerpt_delimiter",
    "excerpt_injection",
    "output_citation",
    "output_image",
    "output_link",
    "output_pii",
    "persist_pii",
)
BINARY, CONTINUOUS = True, False
# AC-15: each metric's kind, fixed here and never inferred from the values.
KIND: dict[str, bool] = {
    "terminal_state_pass": BINARY,
    "citation_valid": BINARY,
    "model_calls": CONTINUOUS,
    "tool_calls_accepted": CONTINUOUS,
    "input_tokens": CONTINUOUS,
    "output_tokens": CONTINUOUS,
    "latency_ms": CONTINUOUS,
    "ooc_offtopic_searches": CONTINUOUS,
    "rejected_tool_call_share": CONTINUOUS,
    "expected_doc_hit": BINARY,
    "page2_use": BINARY,
    "page2_cited": BINARY,
    "cited_expected_doc": BINARY,
    "retry_rate": BINARY,
    "trajectory_fact_coverage": CONTINUOUS,
    FACT_PASS: CONTINUOUS,
    ROW_PASS: BINARY,
}
WITH_MAX = ("model_calls", "tool_calls_accepted", "input_tokens", "output_tokens", "latency_ms")
SLICES = ("pooled", "answerable", "ooc")
# AC-16a: ask has one fixed top 5, so its AC-13 counterpart is top-5 fact recall (review fix:
# labelled as such, not as trajectory coverage).
ASK_RECALL = "chunk_fact_recall@5"
ASK_METRICS = ("terminal_state_pass", ASK_RECALL, FACT_PASS, ROW_PASS)


class AgentReportError(ValueError):
    """Bad or missing run data; never a silent skip."""


@dataclass(frozen=True)
class Evaluation:
    metrics: dict[str, dict[str, dict | None]]  # metric -> slice -> stat dict (or None)
    counts: dict


def _stat(values: list[float], kind: bool, with_max: bool) -> dict | None:
    s: Stat | None = mean_se(values, binary=kind)
    if s is None:
        return None
    out = {"mean": s.mean, "se": s.se, "n": s.n, "kind": "binary" if kind else "continuous"}
    if with_max:
        out["max"] = max(values)
    return out


def _slices(pairs: list[tuple[bool, float]], name: str) -> dict[str, dict | None]:
    """pairs: (row is answerable, value). pooled, answerable and ooc each get their own stat."""
    kind = CONTINUOUS if name == ASK_RECALL else KIND[name]
    with_max = name in WITH_MAX
    return {
        "pooled": _stat([v for _, v in pairs], kind, with_max),
        "answerable": _stat([v for a, v in pairs if a], kind, with_max),
        "ooc": _stat([v for a, v in pairs if not a], kind, with_max),
    }


def _page(step: dict) -> int:
    try:
        page = json.loads(step.get("arguments") or "{}").get("page", 1)
    except (ValueError, AttributeError):
        return 1
    return page if isinstance(page, int) and not isinstance(page, bool) else 1


def _accepted(record: dict) -> list[dict]:
    return [s for s in record.get("steps", []) if s.get("kind") == "tool" and s.get("accepted")]


def terminal_pass(row: Row, record: dict) -> bool:
    """AC-10: the terminal state against the row's label; retries are ignored."""
    state, answer = record.get("state"), record.get("answer")
    if row.answerable:
        return state == "answered"
    return state == "abstained" and isinstance(answer, str) and answer.strip() == row.expected


def citation_valid(record: dict) -> bool:
    """AC-11: at least one citation and no invalid one (answered rows only)."""
    return bool(record.get("citations")) and not record.get("invalid_citations")


def _check_events(records: list[dict]) -> dict[str, int]:
    counts = Counter({c: 0 for c in CHECKS})
    for rec in records:
        flagged = {e["check"] for e in rec.get("guardrail_events", []) if e.get("action") != "pass"}
        counts.update(flagged)
    return dict(sorted(counts.items()))


def _answer_content(
    evalset: EvalSet,
    assertions: Assertions,
    review: Mapping[int, ReviewRow],
    answers: dict[int, str],
):
    """AC-14: score() over the rows that answered; others are left out, not failed."""
    kept = Assertions(
        assertions.eval_version,
        assertions.eval_sha256,
        {r: e for r, e in assertions.entries.items() if r in answers},
    )
    return score(kept, evalset, review, {r: {"answer": a} for r, a in answers.items()})


def _content_pairs(report, answerable: dict[int, bool]) -> dict[str, list[tuple[bool, float]]]:
    scored = [r for r in report.rows if r.fact_pass is not None]
    return {
        FACT_PASS: [(answerable[r.row], r.fact_pass) for r in scored],
        ROW_PASS: [(answerable[r.row], float(r.row_pass)) for r in scored],
    }


def evaluate(
    evalset: EvalSet,
    run: dict,
    rows: dict[int, dict],
    assertions: Assertions,
    review: Mapping[int, ReviewRow],
) -> Evaluation:
    """AC-10 to AC-15 over one agent run; rows maps row id to its rows.jsonl line."""
    by_id = {r.id: r for r in evalset.rows}
    for rid, line in rows.items():
        if rid not in by_id:
            raise AgentReportError(f"row {rid}: in the run but not in the eval set")
        if line.get("type") != by_id[rid].type:
            raise AgentReportError(
                f"row {rid}: run type {line.get('type')!r}, eval set {by_id[rid].type!r}"
            )
    refs = run.get("refs", {})
    pairs: dict[str, list[tuple[bool, float]]] = {name: [] for name in KIND}
    table: dict[str, Counter] = {}
    retried: Counter = Counter()
    records: list[dict] = []
    answers: dict[int, str] = {}
    for row in evalset.rows:  # eval-set order
        if row.id not in rows:
            continue
        rec = rows[row.id]["record"]
        records.append(rec)
        ref = refs.get(str(row.id))
        if ref is None:
            raise AgentReportError(f"row {row.id}: run.json refs has no entry")
        state = rec.get("state")
        table.setdefault(row.type, Counter())[state] += 1
        add = lambda name, v, a=row.answerable: pairs[name].append((a, float(v)))  # noqa: E731
        add("terminal_state_pass", terminal_pass(row, rec))
        answered = state == "answered"
        if answered:
            add("citation_valid", citation_valid(rec))
            if isinstance(rec.get("answer"), str):
                answers[row.id] = rec["answer"]
        steps = rec.get("steps", [])
        tools = [s for s in steps if s.get("kind") == "tool"]
        accepted = _accepted(rec)
        add("model_calls", sum(s.get("kind") == "model" for s in steps))
        add("tool_calls_accepted", len(accepted))
        add("input_tokens", rec.get("tokens", {}).get("input", 0))
        add("output_tokens", rec.get("tokens", {}).get("output", 0))
        add("latency_ms", rec.get("latency_ms") or 0.0)
        if row.type == "ooc-off-topic":
            add("ooc_offtopic_searches", len(accepted))
        if tools:
            add("rejected_tool_call_share", sum(not s.get("accepted") for s in tools) / len(tools))
        expected = set(ref.get("expected_urls", []))
        if row.answerable:
            urls = {e["url_path"] for e in rec.get("excerpts", [])}
            add("expected_doc_hit", bool(urls & expected))
            if answered:
                add("cited_expected_doc", any(c["url_path"] in expected for c in rec["citations"]))
            required = [f.id for f in row.required]
            if required:
                got = {c for s in accepted for c in s.get("chunk_ids", [])}
                relevant = ref.get("relevant", {})
                add(
                    "trajectory_fact_coverage",
                    sum(bool(got & set(relevant.get(f, []))) for f in required) / len(required),
                )
        deep = [s for s in accepted if _page(s) > 1]
        add("page2_use", bool(deep))
        if deep:
            cited = {c["n"] for c in rec.get("citations", [])}
            add("page2_cited", bool(cited & {n for s in deep for n in s.get("numbers", [])}))
        add("retry_rate", rec.get("retries", 0) > 0)
        if rec.get("retries", 0) > 0:
            retried[state] += 1
    if answers:
        report = _answer_content(evalset, assertions, review, answers)
        pairs.update(_content_pairs(report, {r.id: r.answerable for r in evalset.rows}))
    counts = {
        "rows": len(records),
        "rows_by_type": {t: sum(c.values()) for t, c in sorted(table.items())},
        "terminal_states": {t: dict(sorted(c.items())) for t, c in sorted(table.items())},
        "retried_terminal_states": dict(sorted(retried.items())),
        "guardrail_nonpass_rows": _check_events(records),
    }
    return Evaluation({n: _slices(p, n) for n, p in pairs.items()}, counts)


def _timestamp(meta: dict) -> datetime:
    return datetime.fromisoformat(meta["timestamp"])


def _read_rows(path: Path) -> dict[int, dict]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["row"]] = rec
    return out


def _read_json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def find_ask_run(runs_root: Path, run: dict) -> Path | None:
    """AC-16a: the latest full ask run on the same eval set, models and config, clean, with rows."""
    want = {k: run.get(k) for k in ("eval_sha256", "answer_model", "embed_model", "config_id")}
    want |= {"mode": "full", "limit": None, "harness_dirty": False}
    found = []
    for summary in sorted(runs_root.glob("*/summary.json")):
        meta = (_read_json(summary) or {}).get("meta", {})
        # Review fix: the agent retrieves dense, so only a dense ask run compares. Runs from
        # before spec 0011 have no retriever key; dense was the only retriever then.
        if (
            all(meta.get(k) == v for k, v in want.items())
            and meta.get("retriever", "dense") == "dense"
            and (summary.parent / "rows.jsonl").is_file()
        ):
            found.append((_timestamp(meta), summary.parent))
    return max(found, key=lambda t: t[0])[1] if found else None


def find_agent_baseline(runs_root: Path, run: dict, run_id: str) -> Path | None:
    """AC-16b: the latest earlier complete agent run with the same eval set, model, retriever
    and guardrails sha."""
    keys = ("eval_sha256", "answer_model", "retriever", "guardrails_sha256")
    found = []
    for path in sorted(runs_root.glob("*/run.json")):
        other = _read_json(path) or {}
        if path.parent.name == run_id or other.get("mode") != "agent" or not other.get("complete"):
            continue
        if all(other.get(k) == run.get(k) for k in keys) and (path.parent / "rows.jsonl").is_file():
            if _timestamp(other) < _timestamp(run):
                found.append((_timestamp(other), path.parent))
    return max(found, key=lambda t: t[0])[1] if found else None


def ask_evaluation(
    evalset: EvalSet,
    rows: dict[int, dict],
    assertions: Assertions,
    review: Mapping[int, ReviewRow],
) -> dict[str, dict[str, dict | None]]:
    """AC-16a: the ask run's AC-10 (answerable: not abstained; ooc: exact expected string),
    AC-13 (top-5 required fact recall) and AC-14 numbers."""
    pairs: dict[str, list[tuple[bool, float]]] = {n: [] for n in ASK_METRICS}
    answers: dict[int, str] = {}
    for row in evalset.rows:
        rec = rows.get(row.id)
        if rec is None:
            continue
        answer = rec.get("answer")
        if row.answerable:
            ok = not rec.get("abstained")
        else:
            ok = isinstance(answer, str) and answer.strip() == row.expected
        pairs["terminal_state_pass"].append((row.answerable, float(ok)))
        required = {f.id for f in row.required}
        if row.answerable and required:
            facts = [set(c["facts"]) for c in rec["retrieved"][:5]]
            pairs[ASK_RECALL].append((True, fact_recall_at(facts, required, 5)))
        if row.answerable and not rec.get("abstained") and isinstance(answer, str):
            answers[row.id] = answer
    if answers:
        report = _answer_content(evalset, assertions, review, answers)
        pairs.update(_content_pairs(report, {r.id: r.answerable for r in evalset.rows}))
    return {n: _slices(p, n) for n, p in pairs.items()}


def _run_facts(run: dict) -> dict:
    keys = (
        "eval_version",
        "eval_sha256",
        "answer_model",
        "embed_model",
        "config_id",
        "corpus_sha",
        "harness_sha",
        "guardrails_version",
        "guardrails_sha256",
        "retriever",
        "budgets",
        "rows",
        "turns",
        "complete",
        "stopped",
        "cap_usd",
        "actual_usd",
    )
    return {k: run.get(k) for k in keys}


def build_summary(
    run_id: str,
    run: dict,
    evaluation: Evaluation,
    assertions_sha: str,
    ask: tuple[str, dict] | None,
    baseline: tuple[str, Evaluation] | None,
) -> dict:
    out = {
        "run_id": run_id,
        "run": _run_facts(run),
        "assertions_sha256": assertions_sha,
        "incomplete": not run.get("complete"),
        "kinds": {n: ("binary" if k else "continuous") for n, k in sorted(KIND.items())},
        "metrics": evaluation.metrics,
        "counts": evaluation.counts,
        "comparisons": {
            "ask": {"run_id": ask[0], "metrics": ask[1]}
            if ask
            else {"run_id": None, "note": "no matching ask run"},
            "agent_baseline": {
                "run_id": baseline[0],
                "metrics": {n: s["pooled"] for n, s in baseline[1].metrics.items()},
            }
            if baseline
            else {"run_id": None, "note": "no earlier agent run"},
        },
    }
    return out


def _fmt(stat: dict | None) -> str:
    if not stat:
        return "n = 0"
    text = f"{stat['mean']:.3f} ± {stat['se']:.3f} (n = {stat['n']})"
    return text + (f", max {stat['max']:.1f}" if "max" in stat else "")


def _usd(value) -> str:
    return "n/a" if value is None else f"${value:.4f}"


def _table(head: list[str], body: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(head) + " |",
        "|" + "---|" * len(head),
        *("| " + " | ".join(r) + " |" for r in body),
    ]


def render_md(summary: dict) -> str:
    run, counts = summary["run"], summary["counts"]
    lines = []
    if summary["incomplete"]:
        lines += [
            f"**INCOMPLETE RUN (stopped: {run['stopped']}; {run['turns']} turns of "
            f"{run['rows']})**",
            "",
        ]
    lines += [
        f"# Agent trajectory evaluation: {summary['run_id']}",
        "",
        "## Run",
        "",
        f"- Eval set: {run['eval_version']}, sha256 {run['eval_sha256']}",
        f"- Answer model: {run['answer_model']}; retriever: {json.dumps(run['retriever'])}",
        f"- Guardrails: {run['guardrails_version']}, sha256 {run['guardrails_sha256']}",
        f"- Turns scored: {counts['rows']} of {run['rows']}; "
        f"cost {_usd(run['actual_usd'])} (cap {_usd(run['cap_usd'])})",
        f"- Assertions sha256: {summary['assertions_sha256']}",
        "",
        "## Terminal state by row type (counts)",
        "",
        *_table(
            ["type", *STATES],
            [
                [t, *(str(by.get(s, 0)) for s in STATES)]
                for t, by in counts["terminal_states"].items()
            ],
        ),
        "",
        "## Metrics (mean ± SE, n)",
        "",
        *_table(
            ["metric", "kind", *SLICES],
            [
                [f"`{n}`", summary["kinds"][n], *(_fmt(s[x]) for x in SLICES)]
                for n, s in summary["metrics"].items()
            ],
        ),
        "",
        "## Counts",
        "",
        f"- Rows by type: {json.dumps(counts['rows_by_type'])}",
        f"- Terminal states of retried turns: {json.dumps(counts['retried_terminal_states'])}",
        "",
        "Rows with a non-pass guardrail event, per check:",
        "",
        *_table(
            ["check", "rows"], [[c, str(n)] for c, n in counts["guardrail_nonpass_rows"].items()]
        ),
        "",
        "## Comparisons",
        "",
    ]
    ask = summary["comparisons"]["ask"]
    lines += [f"### ask: {ask['run_id'] or ask['note']}", ""]
    if ask["run_id"]:
        lines += _table(
            ["metric", *SLICES],
            [[f"`{n}`", *(_fmt(s[x]) for x in SLICES)] for n, s in ask["metrics"].items()],
        )
        lines.append("")
    base = summary["comparisons"]["agent_baseline"]
    lines += [f"### Earlier agent run: {base['run_id'] or base['note']}", ""]
    if base["run_id"]:
        lines += _table(
            ["metric", "pooled"], [[f"`{n}`", _fmt(s)] for n, s in base["metrics"].items()]
        )
        lines.append("")
    lines += ["Metric definitions: [../metrics.md](../metrics.md)", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """AC-9: --run (required), --runs-root, --out-root, --eval-set, --assertions, --review."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", required=True, help="run id under the runs root")
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT)
    ap.add_argument("--out-root", type=Path, default=RESULTS_ROOT)
    ap.add_argument("--eval-set", type=Path, default=EVAL_SET)
    ap.add_argument("--assertions", type=Path, default=ASSERTIONS_PATH)
    ap.add_argument("--review", type=Path, default=REVIEW_PATH)
    args = ap.parse_args(argv)

    eval_bytes = args.eval_set.read_bytes()
    eval_sha = hashlib.sha256(eval_bytes).hexdigest()
    evalset = parse(eval_bytes.decode("utf-8"))
    folder = args.runs_root / args.run
    run = _read_json(folder / "run.json")
    if run is None or not (folder / "rows.jsonl").is_file():
        raise AgentReportError(f"{folder} has no run.json and rows.jsonl")
    if run.get("mode") != "agent":
        raise AgentReportError(f"run {args.run} is {run.get('mode')!r}, not an agent run")
    if run.get("eval_sha256") != eval_sha:
        raise AgentReportError(
            f"run {args.run} used eval set sha256 {run.get('eval_sha256')}, current is {eval_sha}"
        )
    review = load_review(args.review)
    assertions = load_assertions(args.assertions, evalset, eval_sha, review)
    assertions_sha = hashlib.sha256(args.assertions.read_bytes()).hexdigest()

    evaluation = evaluate(evalset, run, _read_rows(folder / "rows.jsonl"), assertions, review)
    ask = None
    if ask_folder := find_ask_run(args.runs_root, run):
        ask = (
            ask_folder.name,
            ask_evaluation(evalset, _read_rows(ask_folder / "rows.jsonl"), assertions, review),
        )
    baseline = None
    if base_folder := find_agent_baseline(args.runs_root, run, args.run):
        base_run = _read_json(base_folder / "run.json")
        baseline = (
            base_folder.name,
            evaluate(evalset, base_run, _read_rows(base_folder / "rows.jsonl"), assertions, review),
        )

    summary = build_summary(args.run, run, evaluation, assertions_sha, ask, baseline)
    out = args.out_root / args.run
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out / "summary.md").write_text(render_md(summary), encoding="utf-8")
    print(out / "summary.json")
    print(out / "summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
