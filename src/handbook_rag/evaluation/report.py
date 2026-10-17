"""Summaries of a run (spec 0004, AC-7). Pure: per-row records in, summary dict and markdown out.

A record is the dict written as one line of rows.jsonl (built by run.py):

    row: int, type: str, recency_basis: str | None, answerable: bool,
    conflict_unscored: bool,
    retrieved: [{rank, chunk_id, doc_id, path, heading, distance, tokens,
                 facts: [required fact ids it is relevant to], page_relevant: bool}],
    metrics: dict from metrics.row_metrics (answerable rows; {} for ooc rows),
    page_hit_no_chunk: bool  (page hit at k=5 but no relevant chunk: a chunking problem),
    answer: str | None, citations: [{n, url_path, heading}], invalid_citations: [int],
    truncated: bool | None,
    abstention: asdict(checks.Abstention) | None,
    checks: asdict(checks.CodeChecks) | None  (answerable, non-abstaining rows only)
"""

import re
from collections import Counter

from handbook_rag.evaluation.metrics import mean_se

CHECK_FIELDS = ("has_citation", "citations_in_range", "headings_exist", "no_url")
# The SE formula follows the metric's kind, never its values (a continuous metric can be all
# 0/1 in a small slice). Every summarised name must match exactly one entry here: the answer
# rates _group emits, or a metrics.row_metrics key pattern.
BINARY_RATES = frozenset({"ooc_pass", "false_abstention", "code_checks_passed", "truncated"})
BINARY_RATES |= frozenset(CHECK_FIELDS)
BINARY_METRIC = re.compile(r"chunk_(hit|all_required)@\d+|page_hit@\d+")
CONTINUOUS_METRIC = re.compile(
    r"(chunk|page)_fact_recall@\d+|(chunk|page)_mrr|(chunk|page)_ndcg@\d+|retrieved_tokens@\d+"
)


def is_binary(name: str) -> bool:
    """True for 0/1 metrics, False for continuous ones; KeyError for an unclassified name."""
    if name in BINARY_RATES or BINARY_METRIC.fullmatch(name):
        return True
    if CONTINUOUS_METRIC.fullmatch(name):
        return False
    raise KeyError(f"metric {name!r} is not classified as binary or continuous (report.py)")


def _stat(name: str, values: list) -> dict | None:
    stat = mean_se([float(v) for v in values], binary=is_binary(name))
    return None if stat is None else {"mean": stat.mean, "se": stat.se, "n": stat.n}


def _group(records: list[dict]) -> dict:
    """metric -> {mean, se, n}; answer rates and "labels" (counts) only when answers exist."""
    out: dict = {}
    keys = sorted({k for r in records for k in r.get("metrics") or {}})
    rates: dict[str, list] = {
        k: [r["metrics"][k] for r in records if k in (r.get("metrics") or {})] for k in keys
    }
    answered = [r for r in records if r.get("answer") is not None]
    if answered:
        abst = [(r["answerable"], r["abstention"]) for r in answered if r.get("abstention")]
        rates["ooc_pass"] = [a["passed"] for ok, a in abst if not ok]
        rates["false_abstention"] = [a["false_abstention"] for ok, a in abst if ok]
        checks = [r["checks"] for r in answered if r.get("checks")]
        rates["code_checks_passed"] = [all(c[f] for f in CHECK_FIELDS) for c in checks]
        for f in CHECK_FIELDS:
            rates[f] = [c[f] for c in checks]
        rates["truncated"] = [r["truncated"] for r in answered if r.get("truncated") is not None]
    for name, values in rates.items():
        if (stat := _stat(name, values)) is not None:
            out[name] = stat
    if answered:
        labels = Counter(a["label"] for _, a in abst if a.get("label"))
        out["labels"] = dict(sorted(labels.items()))
    return out


def _by(records: list[dict], key: str) -> dict:
    values = sorted({r[key] for r in records if r.get(key) is not None})
    return {v: _group([r for r in records if r.get(key) == v]) for v in values}


def summarize(records: list[dict], meta: dict, notes: dict) -> dict:
    """The summary.json content.

    meta: the AC-6 run metadata, copied in as-is.
    notes: {"answer_only_facts": [...], "evidence_warnings": [...]} from the eval set and
        the evidence check, copied in as-is.

    Groups: "overall", "by_type" (row type), "by_recency_basis" (rows with one). Each group
    maps metric name -> {mean, se, n} (metrics.mean_se) for every key in the records'
    metrics, plus, when answers exist: ooc_pass (ooc rows), false_abstention (answerable rows),
    code_checks_passed and one rate per check (rows with checks), truncated; and label counts.
    Lists: page_hit_no_chunk rows, conflict_unscored rows.
    """
    return {
        "meta": meta,
        "groups": {
            "overall": _group(records),
            "by_type": _by(records, "type"),
            "by_recency_basis": _by(records, "recency_basis"),
        },
        "lists": {
            "page_hit_no_chunk": [r["row"] for r in records if r.get("page_hit_no_chunk")],
            "conflict_unscored": [r["row"] for r in records if r.get("conflict_unscored")],
        },
        "notes": notes,
    }


def _table(group: dict) -> list[str]:
    lines = ["| metric | mean | ± SE | n |", "|---|---|---|---|"]
    for name, s in group.items():
        if name == "labels":
            continue
        if name.startswith("retrieved_tokens"):
            mean, se = f"{s['mean']:.0f}", f"{s['se']:.0f}"
        else:
            mean, se = f"{s['mean']:.3f}", f"{s['se']:.3f}"
        lines.append(f"| {name} | {mean} | {se} | {s['n']} |")
    if "labels" in group:
        counts = ", ".join(f"{k} {v}" for k, v in group["labels"].items()) or "none"
        lines += ["", f"Abstention labels: {counts}"]
    return lines


def _items(values: list) -> str:
    return ", ".join(str(v) for v in values) if values else "none"


def render_md(summary: dict) -> str:
    """summary.md: metadata block, one table per group (metric, mean, ± SE, n), the lists."""
    out = ["# Eval summary", ""]
    out += [f"- {k}: {v}" for k, v in summary["meta"].items()]
    groups = summary["groups"]
    out += ["", "## overall", "", *_table(groups["overall"])]
    for by in ("by_type", "by_recency_basis"):
        for value, group in groups[by].items():
            out += ["", f"## {by}: {value}", "", *_table(group)]
    out += ["", "## Lists", ""]
    out += [f"- {k}: {_items(v)}" for k, v in summary["lists"].items()]
    for k, v in summary["notes"].items():
        out += ["", f"## {k}", ""]
        out += [f"- {x}" for x in v] if v else ["none"]
    return "\n".join(out) + "\n"
