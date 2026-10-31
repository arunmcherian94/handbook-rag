import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fakes import FakeEmbedder, FakeReranker, make_principal

from handbook_rag import hybrid
from handbook_rag.constants import PERMISSIONS_KS, PERMISSIONS_SUITE, POLICY_PATH
from handbook_rag.evaluation import permissions as p
from handbook_rag.evaluation.evalset import Fact, Row
from handbook_rag.evaluation.evalset import parse as parse_evalset
from handbook_rag.evaluation.evidence import Evidence
from handbook_rag.evaluation.permissions import Case, Entitlement, SuiteError
from handbook_rag.policy import parse as parse_policy

ACLS = {
    "content/handbook/open.md": ("staff",),
    "content/handbook/uk.md": ("entity:uk-ltd",),
    "content/handbook/mgr.md": ("manager",),
    "content/handbook/other.md": ("staff",),
    "content/handbook/x.md": ("staff",),
}
US = make_principal("staff", "entity:us-inc")
UK_MGR = make_principal("staff", "manager", "entity:uk-ltd")


def case(targets=("open.md",), intent=None, row=None, persona="us-ic", cid="P-900"):
    intent = intent or dict.fromkeys(targets, "allowed")
    return Case(cid, "denied · x", persona, "q?", tuple(targets), intent, row, None)


def suite_text(body: str) -> str:
    return "# Permissions suite v1\n\nStatus.\n\n" + body


def block(extra: str = "", header: str = "### P-900 — denied · cross-entity (uk-ltd)") -> str:
    return (
        f"{header}\n- persona: us-ic\n- question: q?\n- target_docs: a.md, b.md\n"
        f"- intent: denied\n{extra}\n"
    )


# --- AC-10: parsing


def test_parses_the_real_suite():
    """Spec 0007, AC-10: the real suite parses to 52 cases; P-097, P-098 stored invalid."""
    text = Path(PERMISSIONS_SUITE).read_text(encoding="utf-8")
    suite = p.parse_suite(text)
    assert suite.version == "v1"
    assert len(suite.cases) == 52
    assert {c.id for c in suite.cases if c.stored_valid is False} == {"P-097", "P-098"}
    assert all(c.question and c.targets and set(c.intent) == set(c.targets) for c in suite.cases)
    assert {c.row for c in suite.cases if c.row is not None} == {5, 33, 61}


def test_real_suite_categories_are_normalised():
    """Spec 0007, AC-10: categories drop parentheticals; twins and same-question sets collapse."""
    suite = p.parse_suite(Path(PERMISSIONS_SUITE).read_text(encoding="utf-8"))
    cats = {c.category for c in suite.cases}
    assert {"twin", "same-question", "partial", "claimed-identity"} <= cats
    assert "denied · cross-entity" in cats
    assert "agency · in-department" in cats
    assert not any("(" in c for c in cats)


@pytest.mark.parametrize(
    ("header", "category"),
    [
        ("denied · cross-entity (uk-ltd)", "denied · cross-entity"),
        ("twin of P-001 · cross-entity (uk-ltd)", "twin"),
        ("same-question S-1", "same-question"),
        ("control (row 5)", "control"),
        ("claimed-identity (claims manager)", "claimed-identity"),
        ("partial", "partial"),
    ],
)
def test_category_of(header, category):
    """Spec 0007, AC-10: category label normalisation."""
    assert p.category_of(header) == category


def test_parse_fields_and_stored_validity():
    """Spec 0007, AC-10, AC-11: fields, targets, evidence row and the stored validity field."""
    text = suite_text(
        block("- evidence: row 5 facts F1–F9\n- validity: invalid (x not in top 20)\n")
    )
    (c,) = p.parse_suite(text).cases
    assert (c.id, c.category, c.persona, c.question) == (
        "P-900",
        "denied · cross-entity",
        "us-ic",
        "q?",
    )
    assert c.targets == ("a.md", "b.md")
    assert c.row == 5
    assert c.stored_valid is False
    assert c.intent == {"a.md": "denied", "b.md": "denied"}


def test_parse_errors_name_the_case():
    """Spec 0007, AC-10: a missing required field, unknown field or duplicate id fails by id."""
    with pytest.raises(SuiteError, match="P-900.*missing"):
        p.parse_suite(suite_text("### P-900 — partial\n- persona: x\n"))
    with pytest.raises(SuiteError, match="P-900.*unknown field"):
        p.parse_suite(suite_text(block("- bogus: 1\n")))
    with pytest.raises(SuiteError, match="duplicate"):
        p.parse_suite(suite_text(block() + block()))
    with pytest.raises(SuiteError, match="header"):
        p.parse_suite("no header")


T3 = ("a.md", "b.md", "c.md")


@pytest.mark.parametrize(
    ("raw", "targets", "expected"),
    [
        ("allowed", T3[:1], {"a.md": "allowed"}),
        ("denied", T3[:2], {"a.md": "denied", "b.md": "denied"}),
        ("allowed (a.md), denied (b.md)", T3[:2], {"a.md": "allowed", "b.md": "denied"}),
        ("allowed (both)", T3[:2], {"a.md": "allowed", "b.md": "allowed"}),
        ("denied (both)", T3[:2], {"a.md": "denied", "b.md": "denied"}),
        ("denied (b.md), allowed (all except b.md)", T3,
         {"a.md": "allowed", "b.md": "denied", "c.md": "allowed"}),
        ("denied (a.md, b.md), allowed (the other three)", (*T3, "d.md", "e.md"),
         {"a.md": "denied", "b.md": "denied", "c.md": "allowed", "d.md": "allowed",
          "e.md": "allowed"}),
    ],
)  # fmt: skip
def test_parse_intent_forms(raw, targets, expected):
    """Spec 0007, AC-10: every per-path intent form parses to a per-target intent."""
    assert p.parse_intent("P-1", raw, targets) == expected


@pytest.mark.parametrize(
    "raw",
    ["maybe", "allowed (z.md)", "allowed (both)", "allowed (a.md)", "allowed (a.md) and more"],
)
def test_parse_intent_errors_name_the_case(raw):
    """Spec 0007, AC-10: an unparseable form, unknown path or unassigned target raises by id."""
    with pytest.raises(SuiteError, match="P-7"):
        p.parse_intent("P-7", raw, T3)


# --- AC-10: computed outcome and flags


def test_outcome_allowed_denied_partial():
    """Spec 0007, AC-10: outcome is computed from the policy ACLs and the principal's groups."""
    assert p.entitlement(case(("open.md",)), ACLS, US).outcome == "allowed"
    assert p.entitlement(case(("uk.md",)), ACLS, US).outcome == "denied"
    mixed = p.entitlement(case(("open.md", "uk.md")), ACLS, US)
    assert (mixed.outcome, mixed.entitled) == ("partial", ("open.md",))
    assert p.entitlement(case(("uk.md", "mgr.md")), ACLS, UK_MGR).outcome == "allowed"


def test_disagreement_is_flagged_per_target_not_fixed():
    """Spec 0007, AC-10: intent that differs from the computed entitlement is listed."""
    c = case(("open.md", "uk.md"), {"open.md": "allowed", "uk.md": "allowed"})
    ent = p.entitlement(c, ACLS, US)
    assert ent.disagreements == ("uk.md",)
    ok = case(("open.md", "uk.md"), {"open.md": "allowed", "uk.md": "denied"})
    assert p.entitlement(ok, ACLS, US).disagreements == ()
    wrong = case(("uk.md",), {"uk.md": "denied"})
    assert p.entitlement(wrong, ACLS, UK_MGR).disagreements == ("uk.md",)


def test_unknown_target_doc_raises():
    """Spec 0007, AC-10: a target that is not a corpus document is an error, not 'denied'."""
    with pytest.raises(SuiteError, match="nope.md"):
        p.entitlement(case(("nope.md",)), ACLS, US)


# --- AC-11: validity


def test_validity_needs_every_target_in_admin_top_20():
    """Spec 0007, AC-11: valid iff all target docs are in admin's top 20."""
    c = case(("open.md", "uk.md"))
    assert p.is_valid(c, ["x.md", "open.md", "uk.md"])
    assert not p.is_valid(c, ["x.md", "open.md"])
    assert not p.is_valid(c, ["x.md"] * 20 + ["open.md", "uk.md"])


# --- AC-12: metrics


def test_leak_counts_chunks_whose_parent_doc_is_not_entitled():
    """Spec 0007, AC-12: leak is scored per chunk against the policy ACL, within the top k."""
    docs = ["open.md", "uk.md", "uk.md", "mgr.md", "open.md"]
    assert p.leaked(docs, ACLS, US, 5) == ["uk.md", "uk.md", "mgr.md"]
    assert p.leaked(docs, ACLS, US, 1) == []
    assert p.leaked(docs, ACLS, UK_MGR, 5) == []


def test_authorized_recall_and_na():
    """Spec 0007, AC-12: fraction of entitled targets in the top k; nothing entitled is n/a."""
    docs = ["x.md", "open.md", "y.md", "uk.md"]
    assert p.authorized_recall(("open.md", "uk.md"), docs, 5) == 1.0
    assert p.authorized_recall(("open.md", "uk.md"), docs, 2) == 0.5
    assert p.authorized_recall(("open.md", "uk.md"), docs, 1) == 0.0
    assert p.authorized_recall((), docs, 5) is None


def row_with_facts():
    facts = (
        Fact("F1", True, {"open.md": (1,)}),
        Fact("F2", True, {"uk.md": (2,)}),
        Fact("F3", False, {"uk.md": (3,)}),  # optional: outside the metric
        Fact("F4", True, {}),  # answer-only: outside the metric
    )
    return Row(5, "lookup", "q?", ("open.md", "uk.md"), facts)


def test_authorized_fact_recall_for_controls():
    """Spec 0007, AC-12: a control scores fact recall over required facts with an entitled doc."""
    row = row_with_facts()
    assert p.entitled_facts(row, ACLS, US) == {"F1"}
    assert p.entitled_facts(row, ACLS, UK_MGR) == {"F1", "F2"}
    chunk_facts = [set(), {"F1"}, {"F2"}]
    assert p.authorized_fact_recall(chunk_facts, {"F1"}, 5) == 1.0
    assert p.authorized_fact_recall(chunk_facts, {"F1", "F2"}, 2) == 0.5
    assert p.authorized_fact_recall(chunk_facts, set(), 5) is None


def test_over_block_is_entitled_targets_admin_gets_but_principal_does_not():
    """Spec 0007, AC-12: over-block needs admin to retrieve the entitled doc at k."""
    admin = ["open.md", "uk.md", "x.md"]
    assert p.over_block(("open.md", "uk.md"), admin, ["open.md"], 5) == ["uk.md"]
    assert p.over_block(("open.md", "uk.md"), admin, ["open.md", "uk.md"], 5) == []
    assert p.over_block(("open.md", "uk.md"), admin, [], 1) == ["open.md"]
    assert p.over_block(("other.md",), admin, [], 5) == []


def test_case_metrics_per_k_for_plain_and_control_cases():
    """Spec 0007, AC-12: case_metrics reports leak, authorized recall and over-block at each k."""
    c = case(("open.md", "uk.md"))
    ent = p.entitlement(c, ACLS, US)
    docs = ["uk.md", "open.md"] + ["x.md"] * 4
    m = p.case_metrics(c, ent, docs, ["open.md", "uk.md"], [], set(), ACLS, US)
    assert set(m) == {f"@{k}" for k in PERMISSIONS_KS}
    assert m["@5"]["leaked"] == ["uk.md"] and m["@5"]["authorized_recall"] == 1.0
    ctrl = case(("open.md",), row=5)
    cm = p.case_metrics(
        ctrl,
        p.entitlement(ctrl, ACLS, US),
        ["open.md"],
        ["open.md"],
        [{"F1"}],
        {"F1"},
        ACLS,
        US,
        control=True,
    )
    assert cm["@5"]["authorized_recall"] == 1.0
    na = p.case_metrics(
        ctrl,
        p.entitlement(ctrl, ACLS, US),
        ["open.md"],
        ["open.md"],
        [{"F1"}],
        set(),
        ACLS,
        US,
        control=True,
    )
    assert na["@5"]["authorized_recall"] is None


def rec(cid, category, valid, leaked_n, recall, over=0, stored=None, dis=()):
    m = {"leaked": ["u.md"] * leaked_n, "authorized_recall": recall,
         "over_block": ["o.md"] * over}  # fmt: skip
    return {"id": cid, "category": category, "valid": valid, "stored_valid": stored,
            "disagreements": list(dis),
            "metrics": {"@5": m, "@20": m} if valid else None}  # fmt: skip


META = {"suite_version": "v1", "timestamp": "2026-10-23T00:00:00+00:00", "config_id": "c",
        "embed_model": "m", "policy_version": "policy-v1", "policy_sha256": "a" * 64,
        "identity_version": "identities-v1", "identity_sha256": "b" * 64, "suite_sha256": "c" * 64,
        "harness_sha": "d" * 40, "harness_dirty": False, "ks": [5, 20]}  # fmt: skip


def test_summary_groups_by_category_and_excludes_na_and_invalid():
    """Spec 0007, AC-11, AC-12: per-category; n/a not in the mean; invalid dropped."""
    records = [
        rec("P-1", "denied", True, 0, None),
        rec("P-2", "denied", True, 2, None),
        rec("P-3", "twin", True, 0, 1.0),
        rec("P-4", "twin", True, 0, 0.5, over=1),
        rec("P-5", "twin", False, 9, 0.0, stored=True),
        rec("P-6", "twin", True, 0, 1.0, stored=False, dis=("a.md",)),
    ]
    s = p.summarize(records, META)
    assert s["counts"] == {"total": 6, "valid": 5, "invalid": 1}
    assert s["invalid"] == ["P-5"]
    assert s["validity_mismatch"] == [
        {"id": "P-5", "stored": True, "computed": False},
        {"id": "P-6", "stored": False, "computed": True},
    ]
    assert s["intent_disagreements"] == [{"id": "P-6", "targets": ["a.md"]}]
    overall = s["groups"]["overall"]["@5"]
    assert overall["leaked_chunks"] == 2 and overall["cases_with_leak"] == 1
    assert overall["authorized_recall"] == pytest.approx(5 / 6)
    assert (overall["authorized_recall_n"], overall["authorized_recall_na"]) == (3, 2)
    assert overall["over_block"] == 1
    cats = s["groups"]["categories"]
    assert set(cats) == {"denied", "twin"}
    assert cats["denied"]["@5"]["authorized_recall"] is None
    assert cats["twin"]["cases"] == 3


def test_render_md_prints_recall_next_to_leak():
    """Spec 0007, AC-12: authorized recall always appears beside leak."""
    md = p.render_md(p.summarize([rec("P-1", "denied", True, 0, None)], META))
    assert "leaked chunks" in md and "authorized recall" in md
    assert "n/a" in md and "## k=5" in md and "## k=20" in md


# --- AC-13: metadata and the eval-set rows


def test_metadata_keys(tmp_path, monkeypatch):
    """Spec 0007, AC-13: metadata records policy, fixture and suite versions and hashes, config."""
    monkeypatch.setattr(p, "_git", lambda *a: "abc123\n")
    suite = p.Suite("v1", ())
    policy = type("P", (), {"version": "policy-v1", "sha256": "f" * 64})()
    meta = p.metadata(suite, b"suite", policy, "corpussha", "fixed-512-64", "model@1536")
    assert {
        "suite_version", "suite_sha256", "policy_version", "policy_sha256", "identity_version",
        "identity_sha256", "config_id", "embed_model", "harness_sha", "harness_dirty", "ks",
        "timestamp",
    } <= set(meta)  # fmt: skip
    assert meta["config_id"] == "fixed-512-64" and meta["ks"] == [5, 20]
    assert meta["identity_version"] == "identities-v1"
    assert len(meta["suite_sha256"]) == 64 and meta["harness_dirty"] is True


def test_only_live_eval_rows_make_controls():
    """Spec 0007, AC-12: a case is a control only if its evidence row is a live v1.2 row."""
    suite = p.parse_suite(Path(PERMISSIONS_SUITE).read_text(encoding="utf-8"))
    live = {
        r.id: r for r in parse_evalset(Path("docs/eval/eval-set-v1.md").read_text("utf-8")).rows
    }
    cited = {c.row for c in suite.cases if c.row is not None}
    assert 5 in live and cited - set(live) == {33, 61}


def test_estimate_counts_unique_question_tokens():
    """Spec 0007, AC-13: the dry-run cost is tokens of each unique question at the model price."""
    est = p.estimate(["hello world", "another question"], 1_000_000.0)
    assert est["embed_tokens"] > 0
    assert est["embed_usd"] == pytest.approx(est["embed_tokens"])


def test_suite_controls_are_live_rows_only():
    """Spec 0007, AC-15 (corrected 23 Oct): only row 5's cases are labelled controls; the cases
    drafted on cut rows 33 and 61 are labelled `cut-row targets`."""
    suite = p.parse_suite(Path(PERMISSIONS_SUITE).read_text(encoding="utf-8"))
    controls = {c.id for c in suite.cases if c.category == "control"}
    cut = {c.id for c in suite.cases if c.category == "cut-row targets"}
    assert controls == {"P-087", "P-088"}
    assert cut == {"P-093", "P-094", "P-097", "P-098"}


def test_control_row_missing_from_eval_set_fails():
    """Spec 0007, AC-10: a control whose row isn't a v1.2 row is an error, never silently
    re-scored on target docs."""
    policy = parse_policy(POLICY_PATH.read_text(encoding="utf-8"))
    suite = p.parse_suite(Path(PERMISSIONS_SUITE).read_text(encoding="utf-8"))
    with pytest.raises(SuiteError, match="P-087: control row 5"):
        p.plan_cases(suite, {}, policy, eval_rows={})


# --- spec 0011: the retriever (AC-6, AC-8, AC-11)


def test_retriever_flag_defaults_to_dense_and_rejects_unknown():
    """Spec 0011, AC-8: dense unless asked; a bad choice is refused."""
    ap = p.build_parser()
    assert ap.parse_args([]).retriever == "dense"
    assert ap.parse_args(["--retriever", "hybrid"]).retriever == "hybrid"
    with pytest.raises(SystemExit):
        ap.parse_args(["--retriever", "bm25"])


def _meta(monkeypatch, **kw):
    monkeypatch.setattr(p, "_git", lambda *a: "abc123\n")
    policy = type("P", (), {"version": "policy-v1", "sha256": "f" * 64})()
    return p.metadata(p.Suite("v1", ()), b"s", policy, "sha", "fixed-512-64", "model@1536", **kw)


def test_metadata_records_the_retriever(monkeypatch):
    """Spec 0011, AC-11: retriever always; rrf_k, fusion_depth and fts only where they apply."""
    dense = _meta(monkeypatch)
    assert dense["retriever"] == "dense"
    assert not {"rrf_k", "fusion_depth", "fts"} & set(dense)
    fts = _meta(monkeypatch, retriever="fts")
    assert fts["retriever"] == "fts" and fts["fts"] == hybrid.FTS_SETTINGS
    assert "rrf_k" not in fts
    hyb = _meta(monkeypatch, retriever="hybrid")
    assert hyb["retriever"] == "hybrid" and hyb["fts"] == hybrid.FTS_SETTINGS
    assert hyb["rrf_k"] == 60 and hyb["fusion_depth"] == 50


def test_render_md_names_the_retriever_and_renders_older_summaries():
    """Spec 0011, AC-11: the config line names the retriever; a meta without it still renders."""
    older = p.render_md(p.summarize([rec("P-1", "denied", True, 0, None)], META))
    assert "retriever dense" in older
    s = p.summarize([rec("P-1", "denied", True, 0, None)], {**META, "retriever": "hybrid"})
    assert "retriever hybrid" in p.render_md(s)


def test_fts_estimate_is_free():
    """Spec 0011, AC-9, AC-11: fts embeds nothing, so the dry run costs $0."""
    est = p.estimate(["hello world"], 1_000_000.0, retriever="fts")
    assert est == {"embed_tokens": 0, "embed_usd": 0.0}
    assert p.estimate(["hello world"], 1_000_000.0, retriever="hybrid")["embed_tokens"] > 0


def _drive(tmp_path, monkeypatch, retriever, embedder, reranker=None, cases=None):
    """run() on one case with hybrid.search recorded and the DB lookups stubbed out."""
    calls = []

    def fake_search(conn, mode, q, question, model, principal, k, config_id, reranker=None):
        calls.append((mode, q, question, model, principal, k, config_id, reranker))
        return [SimpleNamespace(n=1, chunk_id="c1", doc_id="d1")]

    monkeypatch.setattr(p.hybrid, "search", fake_search)
    monkeypatch.setattr(
        p, "_doc_paths", lambda conn, retrieved, cache: ["open.md"] * len(retrieved)
    )
    suite = p.Suite("v1", tuple(cases or (case(),)))
    plan = p.Plan(
        suite,
        {"us-ic": US, p.ADMIN: UK_MGR},
        {c.id: Entitlement(("open.md",), "allowed", ()) for c in suite.cases},
    )
    meta = {**META, "retriever": retriever}
    out = tmp_path / "run"
    out.mkdir()
    p.run(
        None,
        plan,
        ACLS,
        Evidence(),
        embedder,
        meta=meta,
        retriever=retriever,
        reranker=reranker,
        out=out,
    )
    return calls, out


def test_run_passes_retriever_and_both_principals_through(tmp_path, monkeypatch):
    """Spec 0011, AC-11: persona and admin are each searched in the chosen mode, with the
    question's vector, to the scored depth; one embedding per unique question."""
    emb = FakeEmbedder(kind="query")
    calls, out = _drive(tmp_path, monkeypatch, "hybrid", emb)
    assert [c[0] for c in calls] == ["hybrid", "hybrid"]
    assert [c[4] for c in calls] == [US, UK_MGR]
    assert all(c[1] and c[2] == "q?" and c[3] == emb.name and c[5] == 20 for c in calls)
    assert len(emb.calls) == 1
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["meta"]["retriever"] == "hybrid"


def test_run_fts_never_embeds(tmp_path, monkeypatch):
    """Spec 0011, AC-9: fts mode needs no embedder and sends no vector."""
    calls, _ = _drive(tmp_path, monkeypatch, "fts", None)
    assert [(c[0], c[1], c[3]) for c in calls] == [("fts", None, "")] * 2
    emb = FakeEmbedder(kind="query")
    (tmp_path / "again").mkdir()
    _drive(tmp_path / "again", monkeypatch, "fts", emb)
    assert emb.calls == []


def test_estimate_fts_never_tokenizes():
    """Spec 0011 AC-9: fts embeds nothing; sent is never called."""

    def boom(_):
        raise AssertionError("sent called")

    est = p.estimate(["hello"], 1.0, sent=boom, retriever="fts")
    assert est == {"embed_tokens": 0, "embed_usd": 0.0}


RERANK = {
    "model": "fake/reranker",
    "endpoint": "https://example.test/rerank",
    "instruction": "rank",
    "max_input_tokens": 32768,
    "template_tokens": 80,
    "usd_per_1m": 0.01,
    "price_source": "test",
}


def test_rerank_metadata_has_the_rerank_block_and_no_fts(monkeypatch):
    """Spec 0012, AC-9: a rerank run records the reranker's settings, no FTS; the others are
    unchanged."""
    meta = _meta(monkeypatch, retriever="rerank", rerank=RERANK)
    assert meta["retriever"] == "rerank"
    assert meta["rerank"]["model"] == "fake/reranker" and meta["rerank"]["template_tokens"] == 80
    assert not {"fts", "rrf_k", "fusion_depth"} & set(meta)
    for other in ("dense", "fts", "hybrid"):
        assert "rerank" not in _meta(monkeypatch, retriever=other)
    with pytest.raises(ValueError):
        _meta(monkeypatch, retriever="rerank")


def test_rerank_needs_no_fts_check(monkeypatch):
    """Spec 0012, AC-5: only fts and hybrid run the stale-FTS check; rerank never calls it."""
    import inspect

    src = inspect.getsource(p.main)
    assert 'args.retriever in ("fts", "hybrid")' in src
    assert 'args.retriever != "dense"' not in src


def test_search_counts_are_unique_persona_question_pairs():
    """Spec 0012, AC-9: acting persona and admin per case, deduplicated like run()'s cache."""
    suite = p.Suite(
        "v1",
        (
            case(cid="P-1"),
            case(cid="P-2"),  # same persona and question: no extra search
            case(cid="P-3", persona=p.ADMIN),  # admin acts: one search, not two
        ),
    )
    assert p.search_counts(suite) == {"q?": 2}


def test_rerank_estimate_prices_searches_times_depth_pairs():
    """Spec 0012, AC-9: searches x 50 pairs x (question + longest chunk + template) tokens."""
    enc_tokens = p.estimate(["hello world"], 1.0)["embed_tokens"]
    est = p.estimate(
        ["hello world"],
        1_000_000.0,
        retriever="rerank",
        rerank={**RERANK, "usd_per_1m": 2.0},
        chunk_tokens=500,
        searches={"hello world": 3},
    )
    assert est["rerank_tokens"] == 3 * 50 * (enc_tokens + 500 + 80)
    assert est["rerank_usd"] == est["rerank_tokens"] * 2.0 / 1_000_000
    assert est["total_usd"] == est["embed_usd"] + est["rerank_usd"]
    assert est["embed_tokens"] == enc_tokens


def test_dense_estimate_is_unchanged_by_the_rerank_params():
    """Spec 0012, AC-9: without rerank the estimate has only the embed keys."""
    assert set(p.estimate(["hello world"], 1.0)) == {"embed_tokens", "embed_usd"}


def test_run_rerank_passes_the_reranker_and_caches_per_persona_question(tmp_path, monkeypatch):
    """Spec 0012, AC-5: hybrid.search gets the reranker at depth 20; two cases with the same
    persona and question search once per principal (persona, admin)."""
    rr = FakeReranker()
    emb = FakeEmbedder(kind="query")
    cases = [case(cid="P-900"), case(cid="P-901")]
    calls, _ = _drive(tmp_path, monkeypatch, "rerank", emb, reranker=rr, cases=cases)
    assert [c[0] for c in calls] == ["rerank", "rerank"]
    assert [c[4] for c in calls] == [US, UK_MGR]
    assert all(c[5] == 20 and c[7] is rr for c in calls)
    assert len(emb.calls) == 1
