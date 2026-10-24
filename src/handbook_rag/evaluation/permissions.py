"""Run the permissions suite (spec 0007, AC-10 to AC-13). Retrieval only; imperative shell.

Order: verify the corpus pin, check the stored chunks match it, load the policy, check the
stored ACLs are fresh (AC-5), parse the suite, compute each case's entitlement from the policy
and the fixture, print the counts and the query-embedding cost; spend (embed) only with
--confirm; write the run folder. Leak and entitlement come from the policy file's allow-lists,
never from chunks.allowed_groups.
"""

import argparse
import hashlib
import json
import random
import re
import sys
import time
import uuid
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import tiktoken

from handbook_rag import acl, ask, identity
from handbook_rag.constants import (
    BASELINE_CONFIG,
    CORPUS_PREFIX,
    EVAL_SET,
    IDENTITIES_PATH,
    PERMISSIONS_KS,
    PERMISSIONS_RUNS,
    PERMISSIONS_SUITE,
    TOKENIZER,
)
from handbook_rag.corpus import read_manifest, verify
from handbook_rag.db import connect, vector_literal
from handbook_rag.embed import embed_with_retry
from handbook_rag.evaluation import evidence as evidence_mod
from handbook_rag.evaluation.evalset import Row
from handbook_rag.evaluation.evalset import parse as parse_evalset
from handbook_rag.evaluation.evidence import Evidence, EvidenceError
from handbook_rag.evaluation.metrics import fact_recall_at
from handbook_rag.evaluation.run import _git, stored_chunk_params
from handbook_rag.identity import Principal
from handbook_rag.models import (
    InputTooLong,
    describe_embedder,
    embed_usd_per_1m,
    make_embedder,
    resolve_embed_spec,
)
from handbook_rag.policy import Policy
from handbook_rag.spend import log_spend, paid

ADMIN = "admin"
ADMIN_DEPTH = max(PERMISSIONS_KS)  # AC-11: admin's top 20 is both the validity set and over-block's

HEADER = re.compile(r"^### (P-\d{3}) — (.+)$")
FIELD = re.compile(r"^- (\w+):\s*(.*)$")
VERSION = re.compile(r"^# Permissions suite (v\d+(?:\.\d+)*)\b", re.M)
INTENT_PART = re.compile(r"(allowed|denied)\s*\(([^)]*)\)")
ROW_EVIDENCE = re.compile(r"^row (\d+) facts\b")
FIELDS = (
    "persona",
    "question",
    "target_docs",
    "evidence",
    "intent",
    "twin",
    "entitled_targets",
    "outcome",
    "validity",
    "review",
    "note",
)
REQUIRED = ("persona", "question", "target_docs", "intent")


class SuiteError(ValueError):
    """A malformed case; the message starts with the case id."""


@dataclass(frozen=True)
class Case:
    id: str
    category: str
    persona: str
    question: str
    targets: tuple[str, ...]  # relative to content/handbook/
    intent: dict[str, str]  # target -> "allowed" | "denied", the drafter's
    row: int | None  # the v1.2 row a control reuses, from `evidence: row N facts ...`
    stored_valid: bool | None  # the `validity:` field: True, False, or None if absent/unclear


@dataclass(frozen=True)
class Suite:
    version: str
    cases: tuple[Case, ...]


@dataclass(frozen=True)
class Entitlement:
    entitled: tuple[str, ...]  # targets, in target order
    outcome: str  # "allowed" | "denied" | "partial"
    disagreements: tuple[str, ...]  # targets whose drafter intent differs from entitlement


def category_of(header: str) -> str:
    """Normalised label from the header text after the dash: parentheticals stripped, twins and
    same-question sets collapsed to one label each."""
    text = " ".join(re.sub(r"\([^)]*\)", "", header).split())
    if text.startswith("twin of"):
        return "twin"
    if text.startswith("same-question"):
        return "same-question"
    return text


def parse_intent(case_id: str, raw: str, targets: Sequence[str]) -> dict[str, str]:
    """Per-target intent from `allowed`, `denied`, or the per-path forms `allowed (PATH, ...)`,
    `allowed (both)`, `allowed (all except PATH)`, `denied (the other three)`. Raises
    SuiteError naming the case if a form can't be parsed or leaves a target unassigned."""
    raw = raw.strip()
    if raw in ("allowed", "denied"):
        return dict.fromkeys(targets, raw)
    parts = INTENT_PART.findall(raw)
    if not parts or INTENT_PART.sub("", raw).replace(",", "").strip():
        raise SuiteError(f"{case_id}: cannot parse intent {raw!r}")
    out: dict[str, str] = {}

    def assign(target: str, verdict: str) -> None:
        if out.setdefault(target, verdict) != verdict:
            raise SuiteError(f"{case_id}: intent assigns {target} both ways in {raw!r}")

    deferred: list[tuple[str, str]] = []
    for verdict, body in parts:
        body = body.strip()
        if body == "both" or body.startswith("all except") or body.startswith("the other"):
            deferred.append((verdict, body))
            continue
        for path in (p.strip() for p in body.split(",")):
            if path not in targets:
                raise SuiteError(f"{case_id}: intent names {path!r}, not a target doc")
            assign(path, verdict)
    for verdict, body in deferred:
        if body == "both":
            if len(targets) != 2:
                raise SuiteError(f"{case_id}: 'both' in {raw!r} but {len(targets)} targets")
            chosen = list(targets)
        elif body.startswith("all except"):
            skipped = {p.strip() for p in body.removeprefix("all except").split(",")}
            if not skipped <= set(targets):
                raise SuiteError(f"{case_id}: {body!r} names a path that is not a target doc")
            chosen = [t for t in targets if t not in skipped]
        else:  # "the other three": everything the explicit parts left unassigned
            chosen = [t for t in targets if t not in out]
        for target in chosen:
            assign(target, verdict)
    missing = [t for t in targets if t not in out]
    if missing:
        raise SuiteError(f"{case_id}: intent {raw!r} leaves {missing} unassigned")
    return out


def parse_suite(text: str) -> Suite:
    """AC-10: cases from `### P-NNN — <category>` headers and `- field: value` lines.

    Raises SuiteError naming the case on: a missing required field, an unknown field, a duplicate
    id, or an intent that can't be parsed."""
    version = VERSION.search(text)
    if not version:
        raise SuiteError("no '# Permissions suite vN' header")
    blocks: list[tuple[str, str, dict[str, str]]] = []
    for line in text.splitlines():
        if m := HEADER.match(line):
            blocks.append((m[1], m[2], {}))
        elif blocks and (m := FIELD.match(line)):
            if m[1] not in FIELDS:
                raise SuiteError(f"{blocks[-1][0]}: unknown field {m[1]!r}")
            blocks[-1][2][m[1]] = m[2].strip()
    ids = [b[0] for b in blocks]
    if dupes := sorted({i for i in ids if ids.count(i) > 1}):
        raise SuiteError(f"duplicate case id(s): {dupes}")
    return Suite(version[1], tuple(_case(*b) for b in blocks))


def _case(case_id: str, header: str, fields: dict[str, str]) -> Case:
    missing = [f for f in REQUIRED if not fields.get(f)]
    if missing:
        raise SuiteError(f"{case_id}: missing field(s) {missing}")
    targets = tuple(t.strip() for t in fields["target_docs"].split(",") if t.strip())
    row = ROW_EVIDENCE.match(fields.get("evidence", ""))
    validity = fields.get("validity", "")
    stored = (
        True if validity.startswith("valid") else False if validity.startswith("invalid") else None
    )
    return Case(
        case_id,
        category_of(header),
        fields["persona"],
        fields["question"],
        targets,
        parse_intent(case_id, fields["intent"], targets),
        int(row[1]) if row else None,
        stored,
    )


def _acl(acls: Mapping[str, Sequence[str]], path: str) -> Sequence[str]:
    try:
        return acls[CORPUS_PREFIX + path]
    except KeyError:
        raise SuiteError(f"{path} is not a document in the corpus") from None


def is_entitled(acls: Mapping[str, Sequence[str]], path: str, principal: Principal) -> bool:
    """The allow-list recomputed from the policy intersects the principal's groups."""
    return bool(set(_acl(acls, path)) & principal.groups)


def entitlement(case: Case, acls: Mapping[str, Sequence[str]], principal: Principal) -> Entitlement:
    """AC-10: entitled targets and the outcome, computed from the policy and the fixture. A
    disagreement is a target whose drafter intent differs from its entitlement; flagged, never
    fixed."""
    entitled = tuple(t for t in case.targets if is_entitled(acls, t, principal))
    if len(entitled) == len(case.targets):
        outcome = "allowed"
    elif not entitled:
        outcome = "denied"
    else:
        outcome = "partial"
    disagreements = tuple(
        t for t in case.targets if (case.intent[t] == "allowed") != (t in entitled)
    )
    return Entitlement(entitled, outcome, disagreements)


def is_valid(case: Case, admin_docs: Sequence[str]) -> bool:
    """AC-11: every target doc is in admin's top 20 (admin_docs: one path per rank)."""
    return set(case.targets) <= set(admin_docs[:ADMIN_DEPTH])


def leaked(
    docs: Sequence[str], acls: Mapping[str, Sequence[str]], principal: Principal, k: int
) -> list[str]:
    """AC-12: the parent doc path of each top-k chunk the principal may not see (one entry per
    leaked chunk). docs has one path per rank."""
    return [d for d in docs[:k] if not is_entitled(acls, d, principal)]


def authorized_recall(entitled: Sequence[str], docs: Sequence[str], k: int) -> float | None:
    """AC-12: fraction of the entitled target docs found in the top k; None (n/a) if none."""
    if not entitled:
        return None
    return len(set(entitled) & set(docs[:k])) / len(entitled)


def entitled_facts(row: Row, acls: Mapping[str, Sequence[str]], principal: Principal) -> set[str]:
    """AC-12: ids of the row's required cited facts with at least one cited doc the principal
    may see."""
    return {f.id for f in row.required if any(is_entitled(acls, p, principal) for p in f.cites)}


def authorized_fact_recall(
    chunk_facts: Sequence[set[str]], facts: set[str], k: int
) -> float | None:
    """AC-12, controls: fact recall over the entitled facts (metrics.fact_recall_at); None
    (n/a) if there are none. chunk_facts has one set of fact ids per rank."""
    return fact_recall_at(chunk_facts, facts, k) if facts else None


def over_block(
    entitled: Sequence[str], admin_docs: Sequence[str], docs: Sequence[str], k: int
) -> list[str]:
    """AC-12: entitled target docs admin retrieves in the top k that the principal doesn't."""
    return [t for t in entitled if t in admin_docs[:k] and t not in docs[:k]]


def case_metrics(
    case: Case,
    ent: Entitlement,
    docs: Sequence[str],
    admin_docs: Sequence[str],
    chunk_facts: Sequence[set[str]],
    facts: set[str],
    acls: Mapping[str, Sequence[str]],
    principal: Principal,
    ks: Sequence[int] = PERMISSIONS_KS,
    control: bool = False,
) -> dict[str, dict]:
    """AC-12 per-k metrics of one valid case. A control (a case on a live v1.2 row) scores
    authorized recall as fact recall over `facts`; any other case over its entitled target docs."""
    out = {}
    for k in ks:
        recall = (
            authorized_fact_recall(chunk_facts, facts, k)
            if control
            else authorized_recall(ent.entitled, docs, k)
        )
        out[f"@{k}"] = {
            "leaked": leaked(docs, acls, principal, k),
            "authorized_recall": recall,
            "over_block": over_block(ent.entitled, admin_docs, docs, k),
        }
    return out


def _aggregate(records: list[dict], ks: Sequence[int]) -> dict:
    out: dict = {"cases": len(records)}
    for k in ks:
        ms = [r["metrics"][f"@{k}"] for r in records]
        recalls = [m["authorized_recall"] for m in ms if m["authorized_recall"] is not None]
        out[f"@{k}"] = {
            "leaked_chunks": sum(len(m["leaked"]) for m in ms),
            "cases_with_leak": sum(bool(m["leaked"]) for m in ms),
            "authorized_recall": sum(recalls) / len(recalls) if recalls else None,
            "authorized_recall_n": len(recalls),
            "authorized_recall_na": len(ms) - len(recalls),
            "over_block": sum(len(m["over_block"]) for m in ms),
            "cases_with_over_block": sum(bool(m["over_block"]) for m in ms),
        }
    return out


def summarize(records: list[dict], meta: dict, ks: Sequence[int] = PERMISSIONS_KS) -> dict:
    """AC-12, AC-11: overall and per-category metrics over the valid cases; the invalid cases,
    the intent disagreements and the stored/computed validity mismatches listed."""
    valid = [r for r in records if r["valid"]]
    by_category: dict[str, list[dict]] = defaultdict(list)
    for r in valid:
        by_category[r["category"]].append(r)
    return {
        "meta": meta,
        "counts": {
            "total": len(records),
            "valid": len(valid),
            "invalid": len(records) - len(valid),
        },
        "invalid": [r["id"] for r in records if not r["valid"]],
        "validity_mismatch": [
            {"id": r["id"], "stored": r["stored_valid"], "computed": r["valid"]}
            for r in records
            if r["stored_valid"] is not None and r["stored_valid"] != r["valid"]
        ],
        "intent_disagreements": [
            {"id": r["id"], "targets": r["disagreements"]} for r in records if r["disagreements"]
        ],
        "groups": {
            "overall": _aggregate(valid, ks),
            "categories": {c: _aggregate(rs, ks) for c, rs in sorted(by_category.items())},
        },
    }


def _fmt(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def render_md(summary: dict, ks: Sequence[int] = PERMISSIONS_KS) -> str:
    """summary.md: authorized recall is always printed next to leak."""
    meta, counts = summary["meta"], summary["counts"]
    lines = [
        f"# Permissions {meta['suite_version']} ({meta['timestamp'][:10]})",
        "",
        f"- config {meta['config_id']}, embed model {meta['embed_model']}, ks {list(ks)}",
        f"- policy {meta['policy_version']} ({meta['policy_sha256'][:12]}), identities "
        f"{meta['identity_version']} ({meta['identity_sha256'][:12]}), suite "
        f"{meta['suite_sha256'][:12]}",
        f"- harness {meta['harness_sha'][:8]}{' (dirty)' if meta['harness_dirty'] else ''}",
        f"- cases {counts['total']}: {counts['valid']} scored, {counts['invalid']} invalid",
        "",
    ]
    if summary["invalid"]:
        lines += [f"invalid (dropped from scoring): {', '.join(summary['invalid'])}", ""]
    for m in summary["validity_mismatch"]:
        lines.append(
            f"- validity mismatch {m['id']}: stored {m['stored']}, computed {m['computed']}"
        )
    for d in summary["intent_disagreements"]:
        lines.append(f"- intent disagrees with entitlement {d['id']}: {', '.join(d['targets'])}")
    if summary["validity_mismatch"] or summary["intent_disagreements"]:
        lines.append("")
    for k in ks:
        lines += [
            f"## k={k}",
            "",
            "| group | cases | leaked chunks | cases with leak | authorized recall (n, n/a) "
            "| over-block |",
            "|---|---|---|---|---|---|",
        ]
        groups = {"overall": summary["groups"]["overall"], **summary["groups"]["categories"]}
        for name, g in groups.items():
            a = g[f"@{k}"]
            lines.append(
                f"| {name} | {g['cases']} | {a['leaked_chunks']} | {a['cases_with_leak']} "
                f"| {_fmt(a['authorized_recall'])} ({a['authorized_recall_n']}, "
                f"{a['authorized_recall_na']}) | {a['over_block']} |"
            )
        lines.append("")
    return "\n".join(lines)


def metadata(
    suite: Suite,
    suite_bytes: bytes,
    policy: Policy,
    corpus_sha: str,
    config_id: str,
    embed_model: str,
    ks: Sequence[int] = PERMISSIONS_KS,
    identities_path: Path = IDENTITIES_PATH,
) -> dict:
    """AC-13 run metadata."""
    identity_version, identity_sha = identity.fixture_version(identities_path)
    return {
        "suite_version": suite.version,
        "suite_sha256": hashlib.sha256(suite_bytes).hexdigest(),
        "policy_version": policy.version,
        "policy_sha256": policy.sha256,
        "identity_version": identity_version,
        "identity_sha256": identity_sha,
        "config_id": config_id,
        "corpus_sha": corpus_sha,
        "embed_model": embed_model,
        "harness_sha": _git("rev-parse", "HEAD").strip(),
        "harness_dirty": bool(_git("status", "--porcelain").strip()),
        "ks": list(ks),
        "cases": len(suite.cases),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@dataclass
class Plan:
    """Everything computed before any spend: per case, its entitlement; per persona, its
    principal."""

    suite: Suite
    principals: dict[str, Principal]
    entitlements: dict[str, Entitlement]
    rows: dict[int, Row] = field(default_factory=dict)  # live v1.2 rows the controls reuse


def plan_cases(
    suite: Suite,
    acls: Mapping[str, Sequence[str]],
    policy: Policy,
    eval_rows: Mapping[int, Row],
    identities_path: Path = IDENTITIES_PATH,
) -> Plan:
    """AC-10: load each persona's principal and compute every case's entitlement. Raises
    SuiteError naming the case on an unknown persona or a control row missing from the eval
    set."""
    principals: dict[str, Principal] = {}
    for persona, where in [(ADMIN, "admin"), *((c.persona, c.id) for c in suite.cases)]:
        if persona not in principals:
            try:
                principals[persona] = identity.load(persona, policy, identities_path)
            except identity.IdentityError as e:
                raise SuiteError(f"{where}: {e}") from None
    for c in suite.cases:
        if c.category == "control" and c.row not in eval_rows:
            raise SuiteError(f"{c.id}: control row {c.row} is not a v1.2 eval-set row")
    return Plan(
        suite,
        principals,
        {c.id: entitlement(c, acls, principals[c.persona]) for c in suite.cases},
        {c.row: eval_rows[c.row] for c in suite.cases if c.category == "control"},
    )


def estimate(questions: Sequence[str], usd_per_1m: float, sent=str) -> dict:
    """AC-13: query-embedding cost of the unique questions (one embed each, shared by the acting
    persona and admin)."""
    enc = tiktoken.get_encoding(TOKENIZER)
    tokens = sum(len(enc.encode(sent(q), disallowed_special=())) for q in questions)
    return {"embed_tokens": tokens, "embed_usd": tokens * usd_per_1m / 1_000_000}


def _doc_paths(conn, retrieved: list[ask.Retrieved], cache: dict) -> list[str]:
    """Each chunk's parent document path relative to content/handbook/."""
    unknown = sorted({c.doc_id for c in retrieved} - cache.keys())
    if unknown:
        rows = conn.execute(
            "SELECT doc_id, path FROM documents WHERE doc_id = ANY(%s)", (unknown,)
        ).fetchall()
        cache.update({d: p.removeprefix(CORPUS_PREFIX) for d, p in rows})
    return [cache[c.doc_id] for c in retrieved]


def run(
    conn,
    plan: Plan,
    acls: Mapping[str, Sequence[str]],
    ev: Evidence,
    embedder,
    *,
    meta: dict,
    out_root: Path = PERMISSIONS_RUNS,
    config_id: str = BASELINE_CONFIG,
    sleep=time.sleep,
    rand=random.random,
) -> Path:
    """Retrieve every case's top 20 as its persona and as admin (one query embedding per unique
    question); write the run folder (AC-13). Returns the folder."""
    out = out_root / f"{meta['timestamp'][:10]}-{uuid.uuid4().hex[:8]}"
    out.mkdir(parents=True)
    vectors: dict[str, str] = {}
    searched: dict[tuple[str, str], list[ask.Retrieved]] = {}
    doc_cache: dict = {}
    depth = max(meta["ks"])

    def search(persona: str, question: str) -> list[ask.Retrieved]:
        if question not in vectors:
            vectors[question] = vector_literal(
                embed_with_retry(embedder, [question], sleep, rand)[0]
            )
        if (persona, question) not in searched:
            searched[persona, question] = ask.search(
                conn, vectors[question], embedder.name, plan.principals[persona], depth, config_id
            )
        return searched[persona, question]

    records: list[dict] = []
    with (out / "cases.jsonl").open("w", encoding="utf-8") as f:
        for case in plan.suite.cases:
            principal, ent = plan.principals[case.persona], plan.entitlements[case.id]
            chunks = search(case.persona, case.question)
            admin_chunks = search(ADMIN, case.question)
            docs = _doc_paths(conn, chunks, doc_cache)
            admin_docs = _doc_paths(conn, admin_chunks, doc_cache)
            valid = is_valid(case, admin_docs)
            row = plan.rows.get(case.row) if case.row is not None else None
            facts = entitled_facts(row, acls, principal) if row else set()
            chunk_facts = (
                [{fid for fid in facts if c.chunk_id in ev.relevant[(row.id, fid)]} for c in chunks]
                if row
                else []
            )
            rec = {
                "id": case.id,
                "category": case.category,
                "persona": case.persona,
                "question": case.question,
                "targets": list(case.targets),
                "intent": case.intent,
                "entitled": list(ent.entitled),
                "outcome": ent.outcome,
                "disagreements": list(ent.disagreements),
                "valid": valid,
                "stored_valid": case.stored_valid,
                "row": case.row,
                "entitled_facts": sorted(facts),
                "admin_docs": admin_docs,
                "retrieved": [
                    {"rank": c.n, "chunk_id": str(c.chunk_id), "path": d, "facts": sorted(cf)}
                    for c, d, cf in zip(
                        chunks, docs, chunk_facts or [set()] * len(chunks), strict=True
                    )
                ],
                "metrics": case_metrics(
                    case,
                    ent,
                    docs,
                    admin_docs,
                    chunk_facts,
                    facts,
                    acls,
                    principal,
                    meta["ks"],
                    row is not None,
                )
                if valid
                else None,
            }
            records.append(rec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"{case.id}: {'valid' if valid else 'invalid'}", file=sys.stderr)
    summary = summarize(records, meta, meta["ks"])
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out / "summary.md").write_text(render_md(summary, meta["ks"]), encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the permissions suite (spec 0007).")
    ap.add_argument("--confirm", action="store_true", help="spend: embed the questions")
    ap.add_argument("--config", default=BASELINE_CONFIG, help="chunk config to evaluate")
    args = ap.parse_args(argv)

    m = read_manifest()
    error = verify(m)
    if error:
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    suite_bytes = PERMISSIONS_SUITE.read_bytes()
    try:
        suite = parse_suite(suite_bytes.decode("utf-8"))
        eval_rows = {r.id: r for r in parse_evalset(EVAL_SET.read_text(encoding="utf-8")).rows}
    except ValueError as e:
        raise SystemExit(str(e)) from None

    try:  # an unknown model or bad @dims fails the dry run
        query_embedder = describe_embedder(resolve_embed_spec(), kind="query")
        spec = query_embedder.name
        usd_per_1m = embed_usd_per_1m(spec)
    except ValueError as e:
        raise SystemExit(str(e)) from None

    with connect() as conn:
        chunk_params, corpus_sha = stored_chunk_params(conn, m.sha, args.config)
        policy = acl.load_policy(conn)
        try:  # AC-5: before any retrieval, the dry run included
            acl.check_stale(conn, policy)
        except (acl.StaleACL, acl.AclError) as e:
            raise SystemExit(str(e)) from None
        acls = acl.expected_acls(conn, policy)
        try:
            plan = plan_cases(suite, acls, policy, eval_rows)
        except SuiteError as e:
            raise SystemExit(str(e)) from None
        controls = list(plan.rows.values())
        try:
            ev = evidence_mod.check(controls, conn, args.config)
        except EvidenceError as e:
            raise SystemExit(str(e)) from None

        questions = list(dict.fromkeys(c.question for c in suite.cases))
        try:  # every query as sent is within the limit before anything is spent
            query_embedder.prepare(questions)
        except InputTooLong as e:
            raise SystemExit(str(e)) from None
        cost = estimate(questions, usd_per_1m, lambda q: query_embedder.prepare([q])[0])
        flagged = [c.id for c in suite.cases if plan.entitlements[c.id].disagreements]
        stored_valid = sum(c.stored_valid is True for c in suite.cases)
        print(
            f"permissions {suite.version}, config {args.config}: {len(suite.cases)} cases, "
            f"{stored_valid} valid by stored field, {len(flagged)} intent disagreements"
            + (f" ({', '.join(flagged)})" if flagged else "")
        )
        print(
            f"estimated cost: ${cost['embed_usd']:.6f} (embed ~{cost['embed_tokens']} tokens, "
            f"{len(questions)} unique questions)"
        )
        meta = metadata(suite, suite_bytes, policy, corpus_sha, chunk_params["config_id"], spec)
        if not paid(args.confirm, "permissions"):  # spec 0009
            return 0

        # Built only after confirm, so a dry run needs no API key.
        embedder = make_embedder(spec, kind="query")
        (has_embeddings,) = conn.execute(
            "SELECT EXISTS (SELECT 1 FROM chunk_embeddings e JOIN chunks c USING (chunk_id) "
            "WHERE c.config_id = %s AND e.model = %s)",
            (args.config, embedder.name),
        ).fetchone()
        if not has_embeddings:
            raise SystemExit(
                f"config {args.config!r} has no embeddings for {embedder.name}; "
                f"run `make embed CONFIG={args.config}` for the cost, then `make paid-embed`"
            )
        out, status = None, "failed"
        try:
            out = run(conn, plan, acls, ev, embedder, meta=meta, config_id=args.config)
            status = "ok"
        finally:  # spec 0009, AC-3: logged even when the run fails after spending
            log_spend(
                "permissions",
                cost["embed_usd"],
                run_id=out and out.name,
                embed_model=embedder.name,
                answer_model=None,
                status=status,
            )

    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    print(f"wrote {out}")
    for k in PERMISSIONS_KS:
        a = summary["groups"]["overall"][f"@{k}"]
        print(
            f"  k={k}: leaked chunks {a['leaked_chunks']}, authorized recall "
            f"{_fmt(a['authorized_recall'])} (n={a['authorized_recall_n']}, "
            f"n/a={a['authorized_recall_na']}), over-block {a['over_block']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
