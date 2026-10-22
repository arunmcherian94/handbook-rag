from pathlib import Path

import pytest
from fakes import make_principal

from handbook_rag.constants import PERMISSIONS_KS, PERMISSIONS_SUITE, POLICY_PATH
from handbook_rag.evaluation import permissions as p
from handbook_rag.evaluation.evalset import Fact, Row
from handbook_rag.evaluation.evalset import parse as parse_evalset
from handbook_rag.evaluation.permissions import Case, SuiteError
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
