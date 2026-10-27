"""Answer evaluation over a stored run: false-abstention classes and the answer-content check
(spec 0010). No DB, no API key, no model client: it reads runs/eval/<run>/ and writes
docs/eval/results/<run>/. Must not import ask, run or checks (AC-2)."""

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from handbook_rag.constants import (
    BASELINE_CONFIG,
    DEFAULT_ANSWER_MODEL,
    DEFAULT_EMBED_MODEL,
    TOP_K,
)
from handbook_rag.evaluation.assertions import (
    ASSERTIONS_PATH,
    FACT_PASS,
    REVIEW_PATH,
    ROW_PASS,
    ScoreReport,
    load_assertions,
    load_review,
    score,
)
from handbook_rag.evaluation.evalset import EvalSet, Row, parse

CLASSES = ("generator_refusal", "partial_retrieval", "retrieval_miss", "not_classifiable")
RUNS_ROOT = Path("runs/eval")
RESULTS_ROOT = Path("docs/eval/results")
EVAL_SET_PATH = Path("docs/eval/eval-set-v1.md")
OUTPUTS = ("false-abstentions.json", "answer-content.json", "answer-eval.md")
SUMMARY_LINK = "Answer evaluation: [answer-eval.md](answer-eval.md)"


class AnswerEvalError(ValueError):
    """Bad or missing run data; never a silent skip."""


@dataclass(frozen=True)
class Classification:
    row: int
    type: str
    cls: str  # one of CLASSES
    found: tuple[str, ...]  # required fact ids in the top k, eval-set order
    missing: tuple[str, ...]
    total: int  # len(Row.required)
    chunks: tuple[tuple[str, tuple[str, ...]], ...]  # (chunk_id, facts) for ranks 1..k
    conflict_unscored: bool
    recency_basis: str | None


def _meta(folder: Path) -> dict:
    return json.loads((folder / "summary.json").read_text(encoding="utf-8"))["meta"]


def resolve_baseline(runs_root: Path, eval_sha: str) -> Path:
    """AC-1: the latest-timestamp full run on the default models, config and eval set."""
    want = {
        "mode": "full",
        "limit": None,
        "harness_dirty": False,
        "answer_model": DEFAULT_ANSWER_MODEL,
        "embed_model": DEFAULT_EMBED_MODEL,
        "config_id": BASELINE_CONFIG,
        "eval_sha256": eval_sha,
    }
    found: list[tuple[datetime, Path]] = []
    for summary in sorted(runs_root.glob("*/summary.json")):
        folder = summary.parent
        meta = json.loads(summary.read_text(encoding="utf-8")).get("meta", {})
        if all(meta.get(k) == v for k, v in want.items()) and (folder / "rows.jsonl").is_file():
            found.append((datetime.fromisoformat(meta["timestamp"]), folder))
    if not found:
        filters = ", ".join(f"{k} == {v!r}" for k, v in want.items())
        raise AnswerEvalError(f"no run under {runs_root} matches: {filters}, with a rows.jsonl")
    return max(found, key=lambda t: t[0])[1]


def classify(row: Row, run_row: dict, k: int = TOP_K) -> Classification:
    """AC-3: one false-abstention row's class from its stored retrieved[].facts."""
    for key in ("retrieved", "abstention"):
        if key not in run_row:
            raise AnswerEvalError(f"row {row.id}: run data has no {key!r}")
    if (
        not isinstance(run_row["abstention"], dict)
        or "false_abstention" not in run_row["abstention"]
    ):
        raise AnswerEvalError(f"row {row.id}: run data has no abstention.false_abstention")
    known = {f.id for f in row.facts}
    top = sorted((c for c in run_row["retrieved"] if c["rank"] <= k), key=lambda c: c["rank"])
    seen: set[str] = set()
    for chunk in top:
        unknown = set(chunk["facts"]) - known
        if unknown:
            raise AnswerEvalError(
                f"row {row.id}: chunk {chunk['chunk_id']} lists unknown fact ids {sorted(unknown)}"
            )
        seen.update(chunk["facts"])
    required = tuple(f.id for f in row.required)
    found = tuple(f for f in required if f in seen)
    missing = tuple(f for f in required if f not in seen)
    if not required:
        cls = "not_classifiable"
    elif not missing:
        cls = "generator_refusal"
    elif not found:
        cls = "retrieval_miss"
    else:
        cls = "partial_retrieval"
    return Classification(
        row=row.id,
        type=row.type,
        cls=cls,
        found=found,
        missing=missing,
        total=len(required),
        chunks=tuple((c["chunk_id"], tuple(c["facts"])) for c in top),
        conflict_unscored=row.conflict_unscored,
        recency_basis=row.recency_basis,
    )


def classify_run(evalset: EvalSet, run_rows: dict[int, dict]) -> list[Classification]:
    """AC-3, AC-4: every answerable false abstention, eval-set order."""
    out = []
    for row in evalset.rows:
        if not row.answerable:
            continue
        if row.id not in run_rows:
            raise AnswerEvalError(f"row {row.id}: answerable but absent from the run")
        run_row = run_rows[row.id]
        classification = classify(row, run_row)
        if run_row["abstention"]["false_abstention"] is True:
            out.append(classification)
    return out


def _stat(stat) -> str:
    return (
        f"{stat.mean:.3f} ± {stat.se:.3f} (n = {stat.n})" if stat else "n = 0 (no assertions yet)"
    )


def _chunk(chunk_id: str, facts: tuple[str, ...]) -> str:
    return f"{chunk_id[:8]} [{', '.join(facts)}]"


def render_md(
    run_id: str,
    overridden: bool,
    meta: dict,
    classifications: list[Classification],
    report: ScoreReport,
    assertions_sha: str,
) -> str:
    """AC-4, AC-8, AC-9: both tables plus the run id, eval set version/SHA, assertions SHA."""
    counts = {c: sum(x.cls == c for x in classifications) for c in CLASSES}
    lines = [
        f"# Answer evaluation: {run_id}",
        "",
        "## Run",
        "",
        f"- Run: {run_id} ({'overridden with --run' if overridden else 'resolved by rule'})",
        f"- Answer model: {meta['answer_model']}",
        f"- Embed model: {meta['embed_model']}",
        f"- Config: {meta['config_id']}",
        f"- Eval set: {meta['eval_version']}, sha256 {meta['eval_sha256']}",
        f"- Assertions sha256: {assertions_sha}",
        "",
        "## False-abstention classes",
        "",
        f"n = {len(classifications)} false abstentions. "
        + ", ".join(f"{c}: {n}" for c, n in counts.items()),
        "",
        "| row | type | class | found / total | missing | top-k chunks | conflict_unscored "
        "| recency_basis |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in classifications:
        lines.append(
            f"| {c.row} | {c.type} | {c.cls} | {len(c.found)} / {c.total} "
            f"| {', '.join(c.missing) or '-'} "
            f"| {'; '.join(_chunk(*ch) for ch in c.chunks)} "
            f"| {str(c.conflict_unscored).lower()} | {c.recency_basis or '-'} |"
        )
    lines += [
        "",
        "## Answer-content check",
        "",
        f"- {FACT_PASS}: {_stat(report.fact_pass)}",
        f"- {ROW_PASS}: {_stat(report.row_pass)}",
        f"- Rows scored: {report.n_rows_scored}",
        f"- Expressible facts: {report.n_expressible}",
        f"- expressible:false facts: {report.n_not_expressible}",
        "- Eligible rows not in the file: "
        + (", ".join(map(str, report.eligible_not_in_file)) or "none"),
        "",
        "| row | abstained | fact pass | row pass | facts |",
        "|---|---|---|---|---|",
    ]
    for r in report.rows:
        facts = ", ".join(
            f"{f.fact} " + ("n/a" if f.passed is None else "pass" if f.passed else "fail")
            for f in r.facts
        )
        fp = "-" if r.fact_pass is None else f"{r.fact_pass:.2f}"
        rp = "-" if r.row_pass is None else str(r.row_pass).lower()
        lines.append(f"| {r.row} | {str(r.abstained).lower()} | {fp} | {rp} | {facts} |")
    lines += ["", "Metric definitions: [../metrics.md](../metrics.md)", ""]
    return "\n".join(lines)


def _dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _class_json(c: Classification) -> dict:
    return {
        "row": c.row,
        "type": c.type,
        "class": c.cls,
        "found": list(c.found),
        "missing": list(c.missing),
        "found_count": len(c.found),
        "total": c.total,
        "chunks": [{"chunk_id": cid, "facts": list(f)} for cid, f in c.chunks],
        "conflict_unscored": c.conflict_unscored,
        "recency_basis": c.recency_basis,
    }


def main(argv: list[str] | None = None) -> int:
    """AC-2: --run, --runs-root, --out-root, --assertions, --review; writes OUTPUTS."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", help="run id; overrides the baseline rule")
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT)
    ap.add_argument("--out-root", type=Path, default=RESULTS_ROOT)
    ap.add_argument("--eval-set", type=Path, default=EVAL_SET_PATH)
    ap.add_argument("--assertions", type=Path, default=ASSERTIONS_PATH)
    ap.add_argument("--review", type=Path, default=REVIEW_PATH)
    args = ap.parse_args(argv)

    eval_bytes = args.eval_set.read_bytes()  # hashed as run.py hashes it: the raw bytes
    eval_sha = hashlib.sha256(eval_bytes).hexdigest()
    evalset = parse(eval_bytes.decode("utf-8"))

    folder = args.runs_root / args.run if args.run else resolve_baseline(args.runs_root, eval_sha)
    if not (folder / "summary.json").is_file() or not (folder / "rows.jsonl").is_file():
        raise AnswerEvalError(f"{folder} has no summary.json and rows.jsonl")
    meta = _meta(folder)
    if meta.get("eval_sha256") != eval_sha:
        raise AnswerEvalError(
            f"run {folder.name} used eval set sha256 {meta.get('eval_sha256')}, "
            f"current is {eval_sha}"
        )
    if meta.get("mode") != "full":
        raise AnswerEvalError(f"run {folder.name} is {meta.get('mode')!r}, not a full answer run")
    run_rows = {}
    for line in (folder / "rows.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            run_rows[rec["row"]] = rec

    classifications = classify_run(evalset, run_rows)
    review = load_review(args.review)
    assertions = load_assertions(args.assertions, evalset, eval_sha, review)
    report = score(assertions, evalset, review, run_rows)
    assertions_sha = hashlib.sha256(args.assertions.read_bytes()).hexdigest()

    run_id, overridden = folder.name, bool(args.run)
    common = {
        "run_id": run_id,
        "run_override": overridden,
        "eval_version": meta["eval_version"],
        "eval_sha256": eval_sha,
    }
    out = args.out_root / run_id
    out.mkdir(parents=True, exist_ok=True)
    _dump(
        out / OUTPUTS[0],
        {
            **common,
            "n": len(classifications),
            "counts": {c: sum(x.cls == c for x in classifications) for c in CLASSES},
            "rows": [_class_json(c) for c in classifications],
        },
    )
    _dump(
        out / OUTPUTS[1],
        {
            **common,
            "assertions_sha256": assertions_sha,
            "metrics": {
                FACT_PASS: asdict(report.fact_pass) if report.fact_pass else None,
                ROW_PASS: asdict(report.row_pass) if report.row_pass else None,
            },
            "counts": {
                "rows_scored": report.n_rows_scored,
                "expressible_facts": report.n_expressible,
                "not_expressible_facts": report.n_not_expressible,
                "eligible_not_in_file": list(report.eligible_not_in_file),
            },
            "rows": [asdict(r) for r in report.rows],
        },
    )
    (out / OUTPUTS[2]).write_text(
        render_md(run_id, overridden, meta, classifications, report, assertions_sha),
        encoding="utf-8",
    )
    summary = out / "summary.md"
    if summary.is_file():
        text = summary.read_text(encoding="utf-8")
        if SUMMARY_LINK not in text:
            summary.write_text(text + "\n" + SUMMARY_LINK + "\n", encoding="utf-8")
    for name in OUTPUTS:
        print(out / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
