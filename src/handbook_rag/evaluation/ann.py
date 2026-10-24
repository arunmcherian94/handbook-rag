"""Recall starvation on a separate HNSW path (spec 0007 Part B, AC-17, AC-18). Imperative shell.

`build` copies the fixed-512-64 text-embedding-3-large@1536 embeddings, with each chunk's
allowed_groups, into ann.hnsw_chunks: a typed vector(1536) table with one HNSW index, apart
from the production tables, which are never altered (AC-17). It writes the DB and spends
nothing, like `make acl`.

`run` compares, per persona, the production exact search (ask.search, unchanged) with HNSW at
each hnsw.iterative_scan setting, on the permissions-suite and v1.2 answerable questions
(AC-18). Query vectors are embedded once per unique question and saved; a run embeds only the
missing ones, so only that step spends.
"""

import argparse
import json
import random
import sys
import time
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from psycopg import sql

from handbook_rag import acl, ask, identity
from handbook_rag.constants import (
    ANN_BASELINE,
    ANN_MODEL,
    ANN_RUNS,
    ANN_VECTORS,
    BASELINE_CONFIG,
    EVAL_SET,
    HNSW_EF_CONSTRUCTION,
    HNSW_ITERATIVE_SCANS,
    HNSW_M,
    PERMISSIONS_KS,
    PERMISSIONS_SUITE,
)
from handbook_rag.corpus import read_manifest, verify
from handbook_rag.db import connect, vector_literal
from handbook_rag.embed import embed_with_retry
from handbook_rag.evaluation import evidence as evidence_mod
from handbook_rag.evaluation import permissions
from handbook_rag.evaluation.evalset import Row
from handbook_rag.evaluation.evalset import parse as parse_evalset
from handbook_rag.evaluation.evidence import Evidence, EvidenceError
from handbook_rag.evaluation.metrics import fact_recall_at
from handbook_rag.evaluation.run import stored_chunk_params
from handbook_rag.identity import Principal
from handbook_rag.models import (
    InputTooLong,
    describe_embedder,
    embed_usd_per_1m,
    make_embedder,
)
from handbook_rag.spend import log_spend, paid

DIMS = 1536  # ANN_MODEL's size: HNSW needs a typed column
INDEX = "hnsw_chunks_embedding"
EXACT = "exact"
SETTINGS = (EXACT, *HNSW_ITERATIVE_SCANS)
ADMIN = permissions.ADMIN

CREATE_TABLE = """
CREATE TABLE ann.hnsw_chunks (
    chunk_id uuid PRIMARY KEY REFERENCES chunks ON DELETE CASCADE,
    allowed_groups text[] NOT NULL,
    embedding vector(1536) NOT NULL
)
"""

COPY_ROWS = """
INSERT INTO ann.hnsw_chunks (chunk_id, allowed_groups, embedding)
SELECT c.chunk_id, c.allowed_groups, e.embedding::vector(1536)
FROM chunk_embeddings e JOIN chunks c USING (chunk_id)
WHERE e.model = %(model)s AND c.config_id = %(config_id)s
"""

# No GIN index on allowed_groups, so the planner can't swap the HNSW scan for a filter-first plan.
CREATE_INDEX = (
    "CREATE INDEX " + INDEX + " ON ann.hnsw_chunks USING hnsw (embedding vector_cosine_ops) "
    "WITH (m = {m}, ef_construction = {ef_construction})"
)

# AC-17 via AC-4/AC-5: the copy matches the production rows it was built from, row for row.
FRESH = """
SELECT
  (SELECT count(*) FROM chunk_embeddings e JOIN chunks c USING (chunk_id)
   WHERE e.model = %(model)s AND c.config_id = %(config_id)s),
  (SELECT count(*) FROM ann.hnsw_chunks),
  (SELECT count(*) FROM ann.hnsw_chunks a
   JOIN chunks c USING (chunk_id)
   JOIN chunk_embeddings e ON e.chunk_id = a.chunk_id AND e.model = %(model)s
   WHERE c.config_id = %(config_id)s AND a.allowed_groups = c.allowed_groups
     AND a.embedding = e.embedding::vector(1536))
"""

ANN_SEARCH = """
SELECT a.chunk_id, a.embedding <=> %(q)s::vector(1536) AS distance
FROM ann.hnsw_chunks a
-- Spec 0007, AC-8: the SEARCH predicate. HNSW applies it to the candidates the graph walk
-- returns, so a selective principal can get fewer than k rows; AC-18 measures how many.
WHERE a.allowed_groups && %(groups)s::text[]
-- No chunk_id tiebreak: a second sort key would stop the index from producing the order.
ORDER BY a.embedding <=> %(q)s::vector(1536)
LIMIT %(k)s
"""


class StaleANN(RuntimeError):
    """ann.hnsw_chunks is missing or differs from the production rows: rebuild it."""


# --- build (AC-17) -------------------------------------------------------------------------------


def source_rows(conn, model: str, config_id: str) -> int:
    (n,) = conn.execute(
        "SELECT count(*) FROM chunk_embeddings e JOIN chunks c USING (chunk_id) "
        "WHERE e.model = %s AND c.config_id = %s",
        (model, config_id),
    ).fetchone()
    return n


def build(
    conn,
    model: str,
    config_id: str = BASELINE_CONFIG,
    m: int = HNSW_M,
    ef_construction: int = HNSW_EF_CONSTRUCTION,
    clock=time.perf_counter,
) -> dict:
    """Drop and recreate schema ann with the copy and its HNSW index, in one transaction. The
    stats are stored as the table's comment, so a run records the build it measured."""
    with conn.transaction():
        conn.execute("SELECT set_config('maintenance_work_mem', '1GB', true)")
        conn.execute("DROP SCHEMA IF EXISTS ann CASCADE")
        conn.execute("CREATE SCHEMA ann")
        conn.execute(CREATE_TABLE)
        t0 = clock()
        rows = conn.execute(COPY_ROWS, {"model": model, "config_id": config_id}).rowcount
        t1 = clock()
        conn.execute(CREATE_INDEX.format(m=int(m), ef_construction=int(ef_construction)))
        t2 = clock()
        conn.execute("ANALYZE ann.hnsw_chunks")
        stats = {
            "model": model,
            "config_id": config_id,
            "rows": rows,
            "m": int(m),
            "ef_construction": int(ef_construction),
            "copy_s": round(t1 - t0, 2),
            "index_s": round(t2 - t1, 2),
            **sizes(conn),
        }
        conn.execute(
            sql.SQL("COMMENT ON TABLE ann.hnsw_chunks IS {}").format(sql.Literal(json.dumps(stats)))
        )
    return stats


def sizes(conn) -> dict:
    """The copy's size with its TOAST (the vectors live there), and the HNSW index's."""
    table, index = conn.execute(
        "SELECT pg_table_size('ann.hnsw_chunks'), pg_relation_size('ann." + INDEX + "')"
    ).fetchone()
    return {"table_bytes": table, "index_bytes": index}


def check_fresh(conn, model: str, config_id: str = BASELINE_CONFIG) -> None:
    """Raises StaleANN unless ann.hnsw_chunks holds exactly the production rows of (model,
    config): same count, same allowed_groups, same embedding. Run after acl.check_stale."""
    (exists,) = conn.execute("SELECT to_regclass('ann.hnsw_chunks')").fetchone()
    if exists is None:
        raise StaleANN("ann.hnsw_chunks does not exist. Run `make ann-build CONFIRM=1`.")
    source, copy, same = conn.execute(FRESH, {"model": model, "config_id": config_id}).fetchone()
    if not source:
        raise StaleANN(f"no {model} embeddings for {config_id}")
    if not source == copy == same:
        raise StaleANN(
            f"ann.hnsw_chunks differs from production: {copy} rows for {source} source rows, "
            f"{same} identical. Run `make acl`, then `make ann-build CONFIRM=1`."
        )


def index_settings(conn) -> dict:
    """AC-18: the index parameters as stored, the query-time settings, the build stats."""
    (reloptions,) = conn.execute(
        "SELECT reloptions FROM pg_class WHERE oid = %s::regclass", ("ann." + INDEX,)
    ).fetchone()
    opts = dict(o.split("=", 1) for o in reloptions or ())
    ef_search, max_scan_tuples, version = conn.execute(
        "SELECT current_setting('hnsw.ef_search'), current_setting('hnsw.max_scan_tuples'), "
        "(SELECT extversion FROM pg_extension WHERE extname = 'vector')"
    ).fetchone()
    (comment,) = conn.execute(
        "SELECT obj_description('ann.hnsw_chunks'::regclass, 'pg_class')"
    ).fetchone()
    return {
        "pgvector": version,
        "m": int(opts["m"]),
        "ef_construction": int(opts["ef_construction"]),
        "ef_search": int(ef_search),
        "max_scan_tuples": int(max_scan_tuples),
        "build": json.loads(comment) if comment else None,
    }


# --- query (AC-17, AC-18) ------------------------------------------------------------------------


@contextmanager
def hnsw_mode(conn, mode: str) -> Iterator[None]:
    """One transaction with hnsw.iterative_scan = mode and seq scans off, so ANN_SEARCH walks
    the index. The settings end with the transaction, so call it with none open."""
    if mode not in HNSW_ITERATIVE_SCANS:
        raise ValueError(f"unknown hnsw.iterative_scan {mode!r}")
    with conn.transaction():
        conn.execute(
            "SELECT set_config('hnsw.iterative_scan', %s, true), "
            "set_config('enable_seqscan', 'off', true)",
            (mode,),
        )
        yield


def hnsw_search(conn, q: str, principal: Principal, k: int) -> list[tuple[uuid.UUID, float]]:
    """(chunk_id, distance) of the HNSW top k the principal may see, under the current mode."""
    return conn.execute(ANN_SEARCH, {"q": q, "groups": principal.group_list, "k": k}).fetchall()


def plan_nodes(conn, q: str, principal: Principal, k: int) -> list[str]:
    """ANN_SEARCH's plan as `Node Type[:Index Name]` strings, outermost first."""
    (plan,) = conn.execute(
        "EXPLAIN (FORMAT JSON) " + ANN_SEARCH, {"q": q, "groups": principal.group_list, "k": k}
    ).fetchone()
    out: list[str] = []

    def walk(node: dict) -> None:
        out.append(node["Node Type"] + (f":{node['Index Name']}" if "Index Name" in node else ""))
        for child in node.get("Plans", ()):
            walk(child)

    walk(plan[0]["Plan"])
    return out


def uses_hnsw(nodes: Sequence[str]) -> bool:
    return any(n.endswith(":" + INDEX) for n in nodes)


# --- metrics (AC-18) -----------------------------------------------------------------------------


def ann_recall(got: Sequence, exact: Sequence, k: int) -> float | None:
    """|HNSW ∩ exact| / min(k, |exact|) over the top k; None (n/a) when exact returns nothing.
    The denominator counts only what exact search could return, so a principal who sees fewer
    than k chunks isn't scored as an ANN miss."""
    exact_k = set(exact[:k])
    if not exact_k:
        return None
    return len(set(got[:k]) & exact_k) / min(k, len(exact_k))


def percentile(values: Sequence[float], p: float) -> float | None:
    """Linear interpolation between closest ranks; None for no values."""
    if not values:
        return None
    xs = sorted(values)
    pos = (len(xs) - 1) * p / 100
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def tie_at(distances: Sequence[float], k: int) -> bool:
    """Rank k and rank k+1 sit at exactly the same distance, so the top-k set isn't unique."""
    return len(distances) > k and distances[k - 1] == distances[k]


def _mean(xs: Sequence[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


# --- query vectors -------------------------------------------------------------------------------


def load_vectors(path: Path, model: str) -> dict[str, list[float]]:
    if not path.exists():
        return {}
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["model"] == model:
            out[r["question"]] = r["vector"]
    return out


def query_vectors(
    questions: Sequence[str],
    model: str,
    embed: Callable[[list[str]], list[list[float]]],
    path: Path = ANN_VECTORS,
) -> dict[str, list[float]]:
    """Each question's saved vector; the missing ones embedded in one call and appended first,
    so a failed run never pays for them twice."""
    saved = load_vectors(path, model)
    missing = [q for q in dict.fromkeys(questions) if q not in saved]
    if missing:
        vectors = embed(missing)
        if len(vectors) != len(missing) or any(len(v) != DIMS for v in vectors):
            raise ValueError(f"expected {len(missing)} vectors of {DIMS} dims from {model}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            for q, v in zip(missing, vectors, strict=True):
                f.write(json.dumps({"model": model, "question": q, "vector": v}) + "\n")
                saved[q] = v
    return {q: saved[q] for q in questions}


# --- run (AC-18) ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class Query:
    question: str
    sources: tuple[str, ...]  # suite case ids and "row N"
    row: Row | None  # the v1.2 answerable row, for fact recall


@dataclass
class Setup:
    """Everything computed before any spend."""

    queries: list[Query]
    principals: dict[str, Principal]
    acls: Mapping[str, Sequence[str]]
    ev: Evidence
    missing: list[str]
    cost: dict
    meta: dict


def queries_of(suite: permissions.Suite, rows: Sequence[Row]) -> list[Query]:
    """The unique questions: suite cases first, then v1.2 answerable rows. A row whose question
    is also a case's keeps both sources and adds the row."""
    by_q: dict[str, Query] = {}
    for c in suite.cases:
        old = by_q.get(c.question)
        by_q[c.question] = Query(c.question, (*(old.sources if old else ()), c.id), None)
    for r in rows:
        old = by_q.get(r.question)
        by_q[r.question] = Query(r.question, (*(old.sources if old else ()), f"row {r.id}"), r)
    return list(by_q.values())


def _record(
    persona: str,
    query: Query,
    exact: list[ask.Retrieved],
    results: Mapping[str, Mapping[int, list]],
    timings: Mapping[str, Mapping[int, float]],
    facts: set[str] | None,
    ev: Evidence,
    ks: Sequence[int],
) -> dict:
    exact_ids = [str(r.chunk_id) for r in exact]
    rec: dict = {
        "persona": persona,
        "question": query.question,
        "sources": list(query.sources),
        "exact": exact_ids,
        "ties": {f"@{k}": tie_at([r.distance for r in exact], k) for k in ks},
        "entitled_facts": sorted(facts) if facts is not None else None,
        "settings": {},
    }
    for setting in SETTINGS:
        per_k = {}
        for k in ks:
            ids = [str(i) for i in results[setting][k]]
            fact = None
            if facts:
                chunk_facts = [
                    {f for f in facts if uuid.UUID(i) in ev.relevant[(query.row.id, f)]}
                    for i in ids
                ]
                fact = fact_recall_at(chunk_facts, facts, k)
            per_k[f"@{k}"] = {
                "ids": ids,
                "returned": len(ids),
                "ann_recall": ann_recall(ids, exact_ids, k),
                "fact_recall": fact,
                "ms": round(timings[setting][k], 3),
            }
        rec["settings"][setting] = per_k
    return rec


def measure(
    conn,
    s: Setup,
    vectors: Mapping[str, list[float]],
    *,
    model: str,
    out_root: Path = ANN_RUNS,
    config_id: str = BASELINE_CONFIG,
    baseline: Path = ANN_BASELINE,
    clock=time.perf_counter,
) -> Path:
    """Per persona and question: exact (ask.search) and HNSW at each iterative_scan setting, at
    each k. A warm-up pass, then a timed pass; the timed pass's results are scored."""
    ks = s.meta["ks"]
    depth = max(ks)
    out = out_root / f"{s.meta['timestamp'][:10]}-{uuid.uuid4().hex[:8]}"
    out.mkdir(parents=True)
    conn.commit()
    conn.autocommit = True  # each hnsw_mode block is its own transaction, so SET LOCAL ends there
    lits = {q.question: vector_literal(vectors[q.question]) for q in s.queries}
    first = lits[s.queries[0].question]

    plans = {}
    for persona, principal in s.principals.items():
        for mode in HNSW_ITERATIVE_SCANS:
            with hnsw_mode(conn, mode):
                nodes = plan_nodes(conn, first, principal, depth)
            if not uses_hnsw(nodes):
                raise SystemExit(f"{persona}, {mode}: ANN_SEARCH does not use {INDEX}: {nodes}")
            plans[f"{persona}/{mode}"] = nodes

    def one(setting: str, q: str, principal: Principal, k: int) -> tuple[list, float]:
        t0 = clock()
        if setting == EXACT:
            ids = [r.chunk_id for r in ask.search(conn, q, model, principal, k, config_id)]
        else:
            with hnsw_mode(conn, setting):
                ids = [cid for cid, _ in hnsw_search(conn, q, principal, k)]
        return ids, (clock() - t0) * 1000

    for principal in s.principals.values():  # warm-up: caches and the index pages
        for q in s.queries:
            for setting in SETTINGS:
                one(setting, lits[q.question], principal, depth)

    records = []
    with (out / "queries.jsonl").open("w", encoding="utf-8") as f:
        for persona, principal in s.principals.items():
            for q in s.queries:
                lit = lits[q.question]
                exact = ask.search(conn, lit, model, principal, depth + 1, config_id)
                results: dict = {st: {} for st in SETTINGS}
                timings: dict = {st: {} for st in SETTINGS}
                for k in ks:
                    for setting in SETTINGS:
                        results[setting][k], timings[setting][k] = one(setting, lit, principal, k)
                facts = (
                    permissions.entitled_facts(q.row, s.acls, principal)
                    if q.row is not None
                    else None
                )
                rec = _record(persona, q, exact, results, timings, facts, s.ev, ks)
                records.append(rec)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"{persona}: {len(s.queries)} questions", file=sys.stderr)

    shares = visible_shares(conn, s.principals)
    meta = {**s.meta, "settings": index_settings(conn), "plans": plans, "shares": shares}
    summary = summarize(records, meta, baseline_rows(baseline), ks)
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "summary.md").write_text(render_md(summary, ks), encoding="utf-8")
    return out


def visible_shares(conn, principals: Mapping[str, Principal]) -> dict[str, float]:
    """Percent of the copy's rows each persona may see (the selectivity points)."""
    out = {}
    for persona, p in principals.items():
        seen, total = conn.execute(
            "SELECT count(*) FILTER (WHERE allowed_groups && %s::text[]), count(*) "
            "FROM ann.hnsw_chunks",
            (p.group_list,),
        ).fetchone()
        out[persona] = round(100 * seen / total, 2)
    return out


def baseline_rows(path: Path) -> dict[str, list[str]] | None:
    """question -> the top-5 chunk ids of the AC-9 baseline run; None if the run isn't here
    (runs/ is not committed, so a fresh clone has none)."""
    rows_path = path / "rows.jsonl"
    if not rows_path.exists():
        return None
    by_id = {r.id: r.question for r in parse_evalset(EVAL_SET.read_text(encoding="utf-8")).rows}
    out = {}
    for line in rows_path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        out[by_id[r["row"]]] = [c["chunk_id"] for c in r["retrieved"][:5]]
    return out


def summarize(
    records: list[dict],
    meta: dict,
    baseline: Mapping[str, list[str]] | None,
    ks: Sequence[int] = PERMISSIONS_KS,
) -> dict:
    """Per persona × setting × k: ANN recall (n, n/a), mean returned, how many returned fewer
    than k, fact recall (n), latency p50/p95; per persona × k, exact ties at rank k."""
    personas = list(dict.fromkeys(r["persona"] for r in records))
    groups: dict = {}
    for persona in personas:
        rs = [r for r in records if r["persona"] == persona]
        g: dict = {"questions": len(rs), "ties": {}, "settings": {}}
        for k in ks:
            g["ties"][f"@{k}"] = sum(r["ties"][f"@{k}"] for r in rs)
        for setting in SETTINGS:
            per_k = {}
            for k in ks:
                cells = [r["settings"][setting][f"@{k}"] for r in rs]
                recalls = [c["ann_recall"] for c in cells if c["ann_recall"] is not None]
                facts = [c["fact_recall"] for c in cells if c["fact_recall"] is not None]
                ms = [c["ms"] for c in cells]
                per_k[f"@{k}"] = {
                    "ann_recall": _mean(recalls),
                    "ann_recall_n": len(recalls),
                    "ann_recall_na": len(cells) - len(recalls),
                    "mean_returned": _mean([c["returned"] for c in cells]),
                    "fewer_than_k": sum(c["returned"] < k for c in cells),
                    "fact_recall": _mean(facts),
                    "fact_recall_n": len(facts),
                    "p50_ms": percentile(ms, 50),
                    "p95_ms": percentile(ms, 95),
                }
            g["settings"][setting] = per_k
        groups[persona] = g

    # Admin sees every chunk, so the filter removes nothing and the three HNSW settings must
    # agree; if they don't, something other than the filter is moving recall.
    admin = [r for r in records if r["persona"] == ADMIN]
    admin_differs = sorted(
        {
            r["question"]
            for r in admin
            for k in ks
            if len({tuple(r["settings"][m][f"@{k}"]["ids"]) for m in HNSW_ITERATIVE_SCANS}) > 1
        }
    )
    exact_path = None
    if baseline is not None:
        rows = [r for r in admin if r["question"] in baseline]
        exact_path = {
            "baseline": ANN_BASELINE.name,
            "rows": len(rows),
            "identical_top5": sum(
                r["settings"][EXACT]["@5"]["ids"] == baseline[r["question"]] for r in rows
            ),
        }
    return {
        "meta": meta,
        "groups": groups,
        "admin_hnsw_settings_differ": admin_differs,
        "exact_path": exact_path,
    }


def _f(x: float | None, spec: str = ".3f") -> str:
    return "n/a" if x is None else format(x, spec)


def render_md(summary: dict, ks: Sequence[int] = PERMISSIONS_KS) -> str:
    meta, st = summary["meta"], summary["meta"]["settings"]
    build = st["build"] or {}
    lines = [
        f"# ANN recall starvation ({meta['timestamp'][:10]})",
        "",
        f"- config {meta['config_id']}, embed model {meta['embed_model']}, ks {list(ks)}",
        f"- pgvector {st['pgvector']}: HNSW m {st['m']}, ef_construction {st['ef_construction']}, "
        f"ef_search {st['ef_search']}, max_scan_tuples {st['max_scan_tuples']}",
        f"- build: {build.get('rows')} rows, copy {build.get('copy_s')} s, index "
        f"{build.get('index_s')} s; table {_mb(build.get('table_bytes'))}, index "
        f"{_mb(build.get('index_bytes'))}",
        f"- policy {meta['policy_version']} ({meta['policy_sha256'][:12]}), identities "
        f"{meta['identity_version']} ({meta['identity_sha256'][:12]}), suite "
        f"{meta['suite_version']} ({meta['suite_sha256'][:12]})",
        f"- harness {meta['harness_sha'][:8]}{' (dirty)' if meta['harness_dirty'] else ''}",
        f"- questions per persona: {meta['questions']['total']} ({meta['questions']['suite']} "
        f"permissions-suite, {meta['questions']['v1.2_answerable']} v1.2 answerable)",
        "- admin sees 100% of chunks, so its rows read as permissions off: exact = unfiltered "
        "exact (AC-9), and the HNSW filter removes nothing",
    ]
    ep = summary["exact_path"]
    lines.append(
        "- exact path vs baseline: not available (baseline run not in runs/)"
        if ep is None
        else f"- exact path vs {ep['baseline']}: admin top 5 identical on {ep['identical_top5']} "
        f"of {ep['rows']} rows"
    )
    differ = summary["admin_hnsw_settings_differ"]
    lines.append(
        f"- **FLAG: admin's HNSW settings differ on {len(differ)} questions**"
        if differ
        else "- admin's three HNSW settings return identical results"
    )
    lines.append("")
    for k in ks:
        lines += [
            f"## k={k}",
            "",
            "| persona (visible) | setting | ANN recall (n, n/a) | mean returned | < k "
            "| fact recall (n) | p50 ms | p95 ms |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for persona, g in summary["groups"].items():
            label = f"{persona} ({meta['shares'][persona]}%)"
            if persona == ADMIN:
                label += " ≈ permissions off"
            for setting in SETTINGS:
                a = g["settings"][setting][f"@{k}"]
                lines.append(
                    f"| {label} | {setting} | {_f(a['ann_recall'])} ({a['ann_recall_n']}, "
                    f"{a['ann_recall_na']}) | {_f(a['mean_returned'], '.1f')} "
                    f"| {a['fewer_than_k']} | {_f(a['fact_recall'])} ({a['fact_recall_n']}) "
                    f"| {_f(a['p50_ms'], '.1f')} | {_f(a['p95_ms'], '.1f')} |"
                )
        ties = ", ".join(f"{p} {g['ties'][f'@{k}']}" for p, g in summary["groups"].items())
        lines += ["", f"Exact distance ties at rank {k} (top-k set not unique): {ties}", ""]
    return "\n".join(lines)


def _mb(n: int | None) -> str:
    return "n/a" if n is None else f"{n / 2**20:.0f} MB"


# --- main ----------------------------------------------------------------------------------------


def _setup(conn, m, query_embedder) -> Setup:
    """The checks before any spend, in permissions.main's order, then the cost of the missing
    query vectors."""
    model = query_embedder.name
    suite_bytes = PERMISSIONS_SUITE.read_bytes()
    try:
        suite = permissions.parse_suite(suite_bytes.decode("utf-8"))
        rows = [r for r in parse_evalset(EVAL_SET.read_text(encoding="utf-8")).rows if r.answerable]
    except ValueError as e:
        raise SystemExit(str(e)) from None
    chunk_params, corpus_sha = stored_chunk_params(conn, m.sha, BASELINE_CONFIG)
    policy = acl.load_policy(conn)
    try:  # AC-5, then its AC-17 counterpart over the copy
        acl.check_stale(conn, policy)
        check_fresh(conn, model)
    except (acl.StaleACL, acl.AclError, StaleANN) as e:
        raise SystemExit(str(e)) from None
    acls = acl.expected_acls(conn, policy)
    principals = {u: identity.load(u, policy) for u in identity.user_ids()}
    try:
        ev = evidence_mod.check(rows, conn, BASELINE_CONFIG)
    except EvidenceError as e:
        raise SystemExit(str(e)) from None
    queries = queries_of(suite, rows)
    try:
        query_embedder.prepare([q.question for q in queries])
    except InputTooLong as e:
        raise SystemExit(str(e)) from None
    saved = load_vectors(ANN_VECTORS, model)
    missing = [q.question for q in queries if q.question not in saved]
    cost = permissions.estimate(
        missing, embed_usd_per_1m(model), lambda q: query_embedder.prepare([q])[0]
    )
    meta = permissions.metadata(
        suite, suite_bytes, policy, corpus_sha, chunk_params["config_id"], model
    )
    meta["questions"] = {
        "total": len(queries),
        "suite": sum(any(s.startswith("P-") for s in q.sources) for q in queries),
        "v1.2_answerable": sum(q.row is not None for q in queries),
    }
    return Setup(queries, principals, acls, ev, missing, cost, meta)


def run_main(confirm: bool) -> int:
    m = read_manifest()
    error = verify(m)
    if error:
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    try:
        query_embedder = describe_embedder(ANN_MODEL, kind="query")
    except ValueError as e:
        raise SystemExit(str(e)) from None
    model = query_embedder.name

    with connect() as conn:
        s = _setup(conn, m, query_embedder)
        q = s.meta["questions"]
        print(
            f"ann: {q['total']} questions ({q['suite']} permissions-suite, {q['v1.2_answerable']} "
            f"v1.2 answerable) x {len(s.principals)} personas x {len(SETTINGS)} settings "
            f"({', '.join(SETTINGS)}), ks {list(s.meta['ks'])}"
        )
        print(
            f"query vectors: {q['total'] - len(s.missing)} saved, {len(s.missing)} to embed; "
            f"estimated cost: ${s.cost['embed_usd']:.6f} (embed ~{s.cost['embed_tokens']} tokens)"
        )
        if not paid(confirm, "ann"):  # spec 0009
            return 0

        # Built only after confirm and only if a vector is missing: a dry run needs no API key.
        embedder = make_embedder(ANN_MODEL, kind="query") if s.missing else None
        out, status = None, "failed"
        try:
            vectors = query_vectors(
                [q.question for q in s.queries],
                model,
                lambda texts: embed_with_retry(embedder, texts, time.sleep, random.random),
                ANN_VECTORS,
            )
            out = measure(conn, s, vectors, model=model)
            status = "ok"
        finally:  # spec 0009, AC-3
            log_spend(
                "ann",
                s.cost["embed_usd"],
                run_id=out and out.name,
                embed_model=model,
                answer_model=None,
                status=status,
            )

    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    print(f"wrote {out}")
    print((out / "summary.md").read_text(encoding="utf-8"))
    if summary["admin_hnsw_settings_differ"]:
        print("FLAG: admin's HNSW settings differ; see summary.md", file=sys.stderr)
    return 0


def build_main(confirm: bool) -> int:
    m = read_manifest()
    error = verify(m)
    if error:
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    model = describe_embedder(ANN_MODEL, kind="query").name
    with connect() as conn:
        stored_chunk_params(conn, m.sha, BASELINE_CONFIG)
        policy = acl.load_policy(conn)
        try:  # the copy takes allowed_groups as stored, so they must be fresh first
            acl.check_stale(conn, policy)
        except (acl.StaleACL, acl.AclError) as e:
            raise SystemExit(str(e)) from None
        n = source_rows(conn, model, BASELINE_CONFIG)
        if not n:
            raise SystemExit(f"no {model} embeddings for {BASELINE_CONFIG}; run `make embed`")
        print(
            f"ann-build: copy {n} {model} rows of {BASELINE_CONFIG} into ann.hnsw_chunks "
            f"(vector({DIMS})), HNSW cosine m={HNSW_M} ef_construction={HNSW_EF_CONSTRUCTION}"
        )
        if not confirm:
            print("Dry run: `make ann-build CONFIRM=1` rebuilds schema ann (no spend).")
            return 0
        stats = build(conn, model)
        check_fresh(conn, model)
    print(
        f"built {stats['rows']} rows: copy {stats['copy_s']} s, index {stats['index_s']} s; "
        f"table {_mb(stats['table_bytes'])}, index {_mb(stats['index_bytes'])}"
    )
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Recall starvation on an HNSW path (spec 0007 B).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="rebuild schema ann from the production rows (no spend)")
    b.add_argument("--confirm", action="store_true", help="write the DB")
    r = sub.add_parser("run", help="measure exact vs HNSW per persona")
    r.add_argument("--confirm", action="store_true", help="spend: embed missing query vectors")
    args = ap.parse_args(argv)
    return build_main(args.confirm) if args.cmd == "build" else run_main(args.confirm)


if __name__ == "__main__":
    sys.exit(main())
