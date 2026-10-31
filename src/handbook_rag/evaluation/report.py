"""Summaries of a run (spec 0004, AC-7). Pure: per-row records in, summary dict and markdown out.

A record is the dict written as one line of rows.jsonl (built by run.py):

    row: int, type: str, recency_basis: str | None, answerable: bool,
    conflict_unscored: bool,
    retrieved: [{rank, chunk_id, doc_id, path, heading, heading_path: [str] | None, distance,
                 tokens, facts: [required fact ids it is relevant to], page_relevant: bool}],
    metrics: dict from metrics.row_metrics (answerable rows; {} for ooc rows),
    page_hit_no_chunk: bool  (page hit at k=5 but no relevant chunk: a chunking problem),
    answer: str | None, citations: [{n, url_path, heading}], invalid_citations: [int],
    truncated: bool | None,
    deep: [{rank, chunk_id, tokens, facts, page_relevant}]  (answerable rows; the depth-20
        retrieval, spec 0006 AC-6; absent in older runs),
    required_facts: sorted required fact ids (the set chunk_fact_recall is over; empty = row
        unscored; absent in older runs),
    near_tie: bool  (the deep list's top 5 chunk_ids differ from `retrieved`'s),
    abstention: asdict(checks.Abstention) | None,
    checks: asdict(checks.CodeChecks) | None  (answerable, non-abstaining rows only)
"""

import math
import re
from collections import Counter

from handbook_rag.constants import (
    HEADROOM_CEILING,
    HEADROOM_FLOOR,
    RERANK_CURVE_KS,
    RERANK_ROWS,
    TOP_K,
)
from handbook_rag.evaluation.metrics import (
    best_top_k,
    fact_recall_at,
    matched_k,
    mean_se,
    paired,
)

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

METRICS_LINK = "Metric definitions: [../metrics.md](../metrics.md)"
TAKEAWAYS_TODO = (
    "_To fill before committing the run (LLM-drafted, human-approved): what to improve in the "
    "next iteration, and whether the previous run's fixes worked._"
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


def _at_k(record: dict, k: int) -> dict[str, float]:
    """Recall, hit, page hit and tokens at k (spec 0006 AC-7): from the list the model saw for
    k <= 5, as every k <= 5 metric is (AC-6), so a near-tie row can't disagree with @5."""
    ranked = record["retrieved"] if k <= TOP_K else record["deep"]
    deep, req = ranked[:k], set(record["required_facts"])
    covered = set().union(*(set(c["facts"]) for c in deep)) & req
    return {
        "chunk_fact_recall": len(covered) / len(req),
        "chunk_hit": float(any(c["facts"] for c in deep)),
        "page_hit": float(any(c["page_relevant"] for c in deep)),
        "tokens": float(sum(c["tokens"] for c in deep)),
    }


def _matched(records: list[dict], target: float) -> dict | None:
    scored = [r for r in records if r.get("metrics") and r.get("deep") is not None]
    scored = [r for r in scored if r.get("required_facts")]
    if not scored:
        return None
    k = matched_k([[c["tokens"] for c in r["deep"]] for r in scored], target)
    vals = [_at_k(r, k) for r in scored]
    out: dict = {"k": k, "target_tokens": target}
    for key, name in (("tokens", "retrieved_tokens"), ("chunk_fact_recall",) * 2,
                      ("chunk_hit",) * 2, ("page_hit",) * 2):  # fmt: skip
        out[key] = _stat(f"{name}@{k}", [v[key] for v in vals])
    return out


def summarize(
    records: list[dict], meta: dict, notes: dict, target_tokens: float | None = None
) -> dict:
    """The summary.json content.

    meta: the AC-6 run metadata, copied in as-is.
    notes: {"answer_only_facts": [...], "evidence_warnings": [...]} from the eval set and
        the evidence check, copied in as-is.

    Groups: "overall", "by_type" (row type), "by_recency_basis" (rows with one). Each group
    maps metric name -> {mean, se, n} (metrics.mean_se) for every key in the records'
    metrics, plus, when answers exist: ooc_pass (ooc rows), false_abstention (answerable rows),
    code_checks_passed and one rate per check (rows with checks), truncated; and label counts.
    Lists: page_hit_no_chunk rows, conflict_unscored rows, near_ties rows.
    With target_tokens and deep lists in the records: "matched" = {k, target_tokens, tokens,
    chunk_fact_recall, chunk_hit, page_hit} at the matched k (spec 0006 AC-7), stats over the
    scored records.
    """
    summary = {
        "meta": meta,
        "groups": {
            "overall": _group(records),
            "by_type": _by(records, "type"),
            "by_recency_basis": _by(records, "recency_basis"),
        },
        "lists": {
            "page_hit_no_chunk": [r["row"] for r in records if r.get("page_hit_no_chunk")],
            "conflict_unscored": [r["row"] for r in records if r.get("conflict_unscored")],
            "near_ties": [r["row"] for r in records if r.get("near_tie")],
        },
        "notes": notes,
    }
    if target_tokens is not None and (matched := _matched(records, target_tokens)):
        summary["matched"] = matched
    return summary


def _table(group: dict) -> list[str]:
    lines = ["| metric | mean | ± SE | n |", "|---|---|---|---|"]
    for name, s in group.items():
        if name == "labels":
            continue
        if name.startswith("retrieved_tokens") or name == "tokens":
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
    """summary.md: takeaways placeholder, metadata, metrics link, a table per group, the lists."""
    out = ["# Eval summary", "", "## Takeaways", "", TAKEAWAYS_TODO, "", "## Run", ""]
    out += [f"- {k}: {v}" for k, v in summary["meta"].items()]
    out += ["", METRICS_LINK]
    groups = summary["groups"]
    out += ["", "## overall", "", *_table(groups["overall"])]
    for by in ("by_type", "by_recency_basis"):
        for value, group in groups[by].items():
            out += ["", f"## {by}: {value}", "", *_table(group)]
    if m := summary.get("matched"):
        out += ["", f"## Token-matched k = {m['k']} (target {m['target_tokens']:.0f} tokens)", ""]
        out += _table({k: m[k] for k in ("chunk_fact_recall", "chunk_hit", "page_hit", "tokens")})
    out += ["", "## Lists", ""]
    out += [f"- {k}: {_items(v)}" for k, v in summary["lists"].items()]
    for k, v in summary["notes"].items():
        out += ["", f"## {k}", ""]
        out += [f"- {x}" for x in v] if v else ["none"]
    return "\n".join(out) + "\n"


def _fmt(name: str, s: dict | None) -> str:
    if s is None:
        return "—"
    if name.startswith("retrieved_tokens") or name == "tokens":
        return f"{s['mean']:.0f} ± {s['se']:.0f} ({s['n']})"
    return f"{s['mean']:.3f} ± {s['se']:.3f} ({s['n']})"


def _delta(name: str, base: dict | None, new: dict | None) -> str:
    if base is None or new is None:
        return "—"
    d = new["mean"] - base["mean"]
    return f"{d:+.0f}" if name.startswith("retrieved_tokens") or name == "tokens" else f"{d:+.3f}"


def _best_chunk(record: dict | None) -> str:
    """The lowest-ranked retrieved chunk relevant to a fact, as 'rank · heading path'."""
    for hit in (record or {}).get("retrieved") or []:
        if hit.get("facts"):
            path = hit.get("heading_path")
            return f"{hit['rank']} · {' > '.join(path) if path else hit.get('heading')}"
    return "—"


def _cell(record: dict | None, name: str) -> str:
    value = ((record or {}).get("metrics") or {}).get(name)
    return "—" if value is None else f"{value:.3f}"


def _matched_recall(record: dict | None, k: int | None) -> float | None:
    if not record or k is None or not record.get("deep") or not record.get("required_facts"):
        return None
    return _at_k(record, k)["chunk_fact_recall"]


def _matched_cell(record: dict | None, k: int | None) -> str:
    value = _matched_recall(record, k)
    return "—" if value is None else f"{value:.3f}"


def _paired_rows(label: str, deltas: list[float]) -> str:
    s = paired(deltas)
    if s is None:
        return f"| {label} | — | — | — | 0 |"
    ratio = f"{s.mean / s.se:.2f}" if s.se else "—"
    return f"| {label} | {s.mean:+.3f} | {s.se:.3f} | {ratio} | {s.n} |"


def top_k_diff(records: list[dict], base_records: list[dict], k: int = 5) -> tuple[int, list[int]]:
    """Spec 0007, AC-9: (rows compared, sorted row ids whose top-k chunk_ids differ in order).
    Compared rows are the answerable ones (non-empty `retrieved` in the baseline). A baseline
    row missing from this run counts as differing."""
    by_row = {r["row"]: r for r in records}
    compared = 0
    differing: list[int] = []
    for base in base_records:
        if not base.get("retrieved"):
            continue
        compared += 1
        want = [r["chunk_id"] for r in base["retrieved"][:k]]
        run = by_row.get(base["row"])
        got = [r["chunk_id"] for r in (run.get("retrieved") or [])[:k]] if run else None
        if got != want:
            differing.append(base["row"])
    return compared, sorted(differing)


def render_compare(
    summary: dict,
    records: list[dict],
    base_summary: dict,
    base_records: list[dict],
    base_id: str,
    row_ids: tuple[int, ...] | list[int],
) -> str:
    """Markdown section comparing this run with a baseline run (spec 0005, AC-14): the overall
    metrics side by side, then per-row recall, hits and best relevant chunk for row_ids and
    every synthesis row of either run."""
    base_all = base_summary["groups"]["overall"]
    new_all = summary["groups"]["overall"]
    names = {n for n in (*base_all, *new_all) if n != "labels"}
    head = [n for n in ("chunk_fact_recall@5", "retrieved_tokens@5") if n in names]
    ordered = head + sorted(names - set(head))
    change = (summary.get("meta") or {}).get("baseline_change")
    out = [
        f"## Comparison with baseline {base_id}" + (f" (change: {change})" if change else ""),
        "",
    ]
    out += [
        "| metric | baseline mean ± SE (n) | this run mean ± SE (n) | delta |",
        "|---|---|---|---|",
    ]
    for n in ordered:
        b, t = base_all.get(n), new_all.get(n)
        out.append(f"| {n} | {_fmt(n, b)} | {_fmt(n, t)} | {_delta(n, b, t)} |")
    if m := summary.get("matched"):
        k = m["k"]
        out += ["", f"### Token-matched k (baseline k=5, this run k={k})", ""]
        out += ["| metric | baseline @5 | this run @matched | delta |", "|---|---|---|---|"]
        for key, name in (("tokens", "retrieved_tokens@5"), ("chunk_fact_recall",) * 2,
                          ("chunk_hit",) * 2, ("page_hit",) * 2):  # fmt: skip
            b = base_all.get(name if key == "tokens" else f"{key}@5")
            t = m.get(key)
            out.append(f"| {key} | {_fmt(key, b)} | {_fmt(key, t)} | {_delta(key, b, t)} |")
        rb, rt = base_all.get("chunk_fact_recall@5"), new_all.get("chunk_fact_recall@5")
        out.append(
            f"| chunk_fact_recall@5 (both at k=5) | {_fmt('x', rb)} | {_fmt('x', rt)} "
            f"| {_delta('x', rb, rt)} |"
        )
    base_by = {r["row"]: r for r in base_records}
    new_by = {r["row"]: r for r in records}
    if "matched" in summary:
        k = summary["matched"]["k"]
        at_matched: list[float] = []
        at_5: list[float] = []
        for row, t in new_by.items():
            b5 = ((base_by.get(row) or {}).get("metrics") or {}).get("chunk_fact_recall@5")
            t5 = (t.get("metrics") or {}).get("chunk_fact_recall@5")
            tk = _matched_recall(t, k)
            if b5 is None or t5 is None or tk is None:
                continue
            at_matched.append(tk - b5)
            at_5.append(t5 - b5)
        out += ["", "### Paired delta (spec 0008 AC-7)", ""]
        out += ["| comparison | mean delta | paired SE | mean / SE | n |", "|---|---|---|---|---|"]
        out.append(_paired_rows("chunk_fact_recall @matched k vs baseline @5", at_matched))
        out.append(_paired_rows("chunk_fact_recall@5 vs @5", at_5))
        out += ["", "Adopt only if mean / SE > 2 on the matched-k row (spec 0008 AC-9)."]
    synthesis = sorted(
        {r["row"] for r in (*base_records, *records) if r.get("type") == "synthesis"}
    )
    ids = list(dict.fromkeys([*row_ids, *synthesis]))
    out += ["", "| row | metric | baseline | this run |", "|---|---|---|---|"]
    for i in ids:
        b, t = base_by.get(i), new_by.get(i)
        for name in ("chunk_fact_recall@5", "chunk_hit@5", "page_hit@5"):
            out.append(f"| {i} | {name} | {_cell(b, name)} | {_cell(t, name)} |")
        if "matched" in summary:
            cells = (_cell(b, "chunk_fact_recall@5"), _matched_cell(t, summary["matched"]["k"]))
            out.append(f"| {i} | chunk_fact_recall@matched | {cells[0]} | {cells[1]} |")
        out.append(f"| {i} | best relevant chunk | {_best_chunk(b)} | {_best_chunk(t)} |")
    compared, differing = top_k_diff(records, base_records)
    out += ["", "### Top-5 order vs baseline (spec 0007, AC-9)", ""]
    out.append(f"identical on {compared - len(differing)} of {compared} rows")
    if differing:
        out += ["", "differing rows: " + ", ".join(str(i) for i in differing)]
    return "\n".join(out) + "\n"


def _percentile(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile: the value at sorted position ceil(p * n); None for no values."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(math.ceil(p * len(ordered)), 1) - 1]


def _ordered_facts(record: dict, by: str) -> list[set[str]]:
    """Candidate fact sets in dense_rank or rerank_rank order."""
    return [set(c["facts"]) for c in sorted(record["candidates"], key=lambda c: c[by])]


def _best_rank(record: dict, fact: str, by: str) -> int | None:
    ranks = [c[by] for c in record["candidates"] if fact in c["facts"]]
    return min(ranks) if ranks else None


def rerank_summary(records: list[dict]) -> dict:
    """Spec 0012 AC-10 and AC-11, from rows.jsonl records alone (those with "candidates").

    Scored rows: non-empty metrics and required_facts. Keys:
    n; recall {dense, rerank: {k: mean recall@k}} for RERANK_CURVE_KS and TOP_K;
    paired {mean, se, n, delta_se} of per-row (rerank@5 - dense@5), delta_se None if se is 0;
    won, lost, tied; headroom_fixed (against HEADROOM_FLOOR/CEILING); dense_at_5,
    rerank_at_5, ceiling (mean best_top_k over the candidates at TOP_K), headroom_in_run
    (None if the ceiling equals dense@5); targeted {row: {fact: {dense_rank, rerank_rank,
    dense_in_top5, rerank_in_top5}}} for RERANK_ROWS present, ranks None if absent;
    latency_ms {rerank_p50, rerank_p95, dense_p50} (nearest-rank percentiles);
    truncation_share (sum pairs_over / sum pairs); input_tokens_per_pair (None if none).
    """
    cands = [r for r in records if r.get("candidates") is not None]
    scored = [r for r in cands if r.get("metrics") and r.get("required_facts")]
    out: dict = {"n": len(scored)}
    if not scored:
        return out
    ks = sorted({*RERANK_CURVE_KS, TOP_K})
    orders = {"dense": "dense_rank", "rerank": "rerank_rank"}
    per_row = {
        name: [
            {k: fact_recall_at(_ordered_facts(r, by), set(r["required_facts"]), k) for k in ks}
            for r in scored
        ]
        for name, by in orders.items()
    }
    out["recall"] = {
        name: {k: sum(v[k] for v in rows) / len(rows) for k in ks} for name, rows in per_row.items()
    }
    deltas = [b[TOP_K] - a[TOP_K] for a, b in zip(per_row["dense"], per_row["rerank"], strict=True)]
    stat = paired(deltas)
    out["paired"] = {
        "mean": stat.mean,
        "se": stat.se,
        "n": stat.n,
        "delta_se": stat.mean / stat.se if stat.se else None,
    }
    out["won"] = sum(d > 0 for d in deltas)
    out["lost"] = sum(d < 0 for d in deltas)
    out["tied"] = sum(d == 0 for d in deltas)
    dense5, rerank5 = out["recall"]["dense"][TOP_K], out["recall"]["rerank"][TOP_K]
    ceilings = [
        best_top_k(_ordered_facts(r, "dense_rank"), set(r["required_facts"]), TOP_K) for r in scored
    ]
    ceiling = sum(ceilings) / len(ceilings)
    out["dense_at_5"], out["rerank_at_5"], out["ceiling"] = dense5, rerank5, ceiling
    out["headroom_fixed"] = (rerank5 - HEADROOM_FLOOR) / (HEADROOM_CEILING - HEADROOM_FLOOR)
    gap = ceiling - dense5
    out["headroom_in_run"] = (rerank5 - dense5) / gap if gap else None
    targeted: dict = {}
    for r in cands:
        if r["row"] not in RERANK_ROWS:
            continue
        facts = {}
        for f in sorted(r.get("required_facts") or []):
            d, rr = _best_rank(r, f, "dense_rank"), _best_rank(r, f, "rerank_rank")
            facts[f] = {
                "dense_rank": d,
                "rerank_rank": rr,
                "dense_in_top5": d is not None and d <= TOP_K,
                "rerank_in_top5": rr is not None and rr <= TOP_K,
            }
        targeted[r["row"]] = facts
    out["targeted"] = targeted
    rerank_ms = [r["latency_ms"]["rerank"] for r in cands if r.get("latency_ms")]
    dense_ms = [r["latency_ms"]["dense"] for r in cands if r.get("latency_ms")]
    out["latency_ms"] = {
        "rerank_p50": _percentile(rerank_ms, 0.5),
        "rerank_p95": _percentile(rerank_ms, 0.95),
        "dense_p50": _percentile(dense_ms, 0.5),
    }
    meta = [r["rerank"] for r in cands if r.get("rerank")]
    pairs = sum(m["pairs"] for m in meta)
    out["truncation_share"] = sum(m["pairs_over"] for m in meta) / pairs if pairs else None
    counted = [m for m in meta if m["input_tokens"] is not None]
    counted_pairs = sum(m["pairs"] for m in counted)
    out["input_tokens_per_pair"] = (
        sum(m["input_tokens"] for m in counted) / counted_pairs if counted_pairs else None
    )
    return out


def _opt(value: float | None, spec: str = ".3f") -> str:
    return "—" if value is None else format(value, spec)


def render_rerank(summary: dict) -> str:
    """Markdown section for a rerank run (spec 0012 AC-10, AC-11). Numbers only, no verdict."""
    out = ["## Rerank vs in-run dense (spec 0012)", ""]
    if not summary.get("n"):
        return "\n".join([*out, "No scored rows with candidates."]) + "\n"
    p = summary["paired"]
    ratio = _opt(p["delta_se"], ".2f")
    out += [
        f"Paired chunk_fact_recall@5, rerank − dense: {p['mean']:+.3f} ± {p['se']:.3f} SE "
        f"({ratio} SE), n = {p['n']}; won {summary['won']}, lost {summary['lost']}, "
        f"tied {summary['tied']}",
        "",
        f"- Headroom captured (headline, fixed): {_opt(summary['headroom_fixed'])} = "
        f"(rerank@5 {summary['rerank_at_5']:.3f} − {HEADROOM_FLOOR}) / "
        f"({HEADROOM_CEILING} − {HEADROOM_FLOOR})",
        f"- Headroom within this run: {_opt(summary['headroom_in_run'])} = "
        f"(rerank@5 {summary['rerank_at_5']:.3f} − dense@5 {summary['dense_at_5']:.3f}) / "
        f"(ceiling {summary['ceiling']:.3f} − dense@5 {summary['dense_at_5']:.3f})",
        "- A gap between the two figures is query-vector drift. Neither decides adoption.",
        "",
        "| k | dense | rerank |",
        "|---|---|---|",
    ]
    d, r = summary["recall"]["dense"], summary["recall"]["rerank"]
    out += [f"| chunk_fact_recall@{k} | {d[k]:.3f} | {r[k]:.3f} |" for k in RERANK_CURVE_KS]
    if summary["targeted"]:
        out += ["", "| row | fact | dense rank | rerank rank | in top 5 (dense → rerank) |"]
        out += ["|---|---|---|---|---|"]
        for row, facts in summary["targeted"].items():
            for fact, t in facts.items():
                moved = f"{'yes' if t['dense_in_top5'] else 'no'} → "
                moved += "yes" if t["rerank_in_top5"] else "no"
                out.append(
                    f"| {row} | {fact} | {_opt(t['dense_rank'], 'd')} "
                    f"| {_opt(t['rerank_rank'], 'd')} | {moved} |"
                )
    lat = summary["latency_ms"]
    out += [
        "",
        f"- Rerank latency p50 / p95: {_opt(lat['rerank_p50'], '.0f')} / "
        f"{_opt(lat['rerank_p95'], '.0f')} ms; in-run dense search p50: "
        f"{_opt(lat['dense_p50'], '.0f')} ms (nearest-rank percentiles)",
        f"- Truncation share (pairs over the limit): {_opt(summary['truncation_share'])}",
        f"- Input tokens per pair: {_opt(summary['input_tokens_per_pair'], '.1f')}",
    ]
    return "\n".join(out) + "\n"
