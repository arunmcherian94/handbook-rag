"""Spec 0007 Part B (AC-18) arithmetic, the saved query vectors, and the spend gate (spec 0009).
No DB, no API: the DB side is in tests/integration/test_ann_db.py."""

import functools
import json

import pytest
from fakes import FakeEmbedder

from handbook_rag import spend
from handbook_rag.evaluation import ann
from handbook_rag.evaluation import permissions as p
from handbook_rag.evaluation.evalset import Row

MODEL = "openai:text-embedding-3-large@1536"


# --- AC-18: ANN recall, percentiles, ties


def test_ann_recall_counts_overlap_over_k():
    """AC-18: |HNSW ∩ exact| / min(k, |exact|) over the top k."""
    exact = list("abcdefg")
    assert ann.ann_recall(list("abcde"), exact, 5) == 1.0
    assert ann.ann_recall(list("abxyz"), exact, 5) == pytest.approx(2 / 5)
    assert ann.ann_recall(list("edcba"), exact, 5) == 1.0  # a set: order doesn't matter


def test_ann_recall_denominator_is_what_exact_could_return():
    """AC-18: a persona seeing fewer than k chunks isn't scored as an ANN miss."""
    assert ann.ann_recall(["a", "b"], ["a", "b"], 5) == 1.0
    assert ann.ann_recall(["a"], ["a", "b"], 5) == pytest.approx(1 / 2)


def test_ann_recall_short_hnsw_result_is_a_miss():
    """AC-18: HNSW returning fewer than k (starvation) loses recall."""
    assert ann.ann_recall(["a"], list("abcde"), 5) == pytest.approx(1 / 5)
    assert ann.ann_recall([], list("abcde"), 5) == 0.0


def test_ann_recall_empty_exact_is_na():
    """AC-18: an empty exact result is n/a, not 0 or 1."""
    assert ann.ann_recall([], [], 5) is None


def test_percentile():
    """AC-18: latency p50/p95 by linear interpolation."""
    xs = [float(i) for i in range(1, 101)]
    assert ann.percentile(xs, 50) == pytest.approx(50.5)
    assert ann.percentile(xs, 95) == pytest.approx(95.05)
    assert ann.percentile([7.0], 95) == 7.0
    assert ann.percentile([], 50) is None


def test_tie_at_rank_k():
    """AC-18: a tie between rank k and k+1 makes the exact top-k set non-unique."""
    assert ann.tie_at([0.1, 0.2, 0.2], 2)
    assert not ann.tie_at([0.1, 0.2, 0.3], 2)
    assert not ann.tie_at([0.1, 0.2], 2)  # no rank k+1


# --- AC-18: questions and saved vectors


def test_queries_of_merges_a_shared_question():
    """AC-18: the suite's and v1.2's questions, unique; a shared one keeps both sources."""
    case = lambda i, q: p.Case(i, "denied", "us-ic", q, ("a.md",), {"a.md": "denied"}, None, True)  # noqa: E731
    suite = p.Suite("v1", (case("P-001", "q1"), case("P-002", "q1"), case("P-003", "q2")))
    rows = [Row(5, "lookup", "q2"), Row(7, "lookup", "q3")]
    qs = ann.queries_of(suite, rows)
    assert [q.question for q in qs] == ["q1", "q2", "q3"]
    assert qs[0].sources == ("P-001", "P-002") and qs[0].row is None
    assert qs[1].sources == ("P-003", "row 5") and qs[1].row.id == 5


def test_saved_vectors_are_reused(tmp_path):
    """AC-18 amendment: a saved vector is never embedded again."""
    path = tmp_path / "v.jsonl"
    path.write_text(json.dumps({"model": MODEL, "question": "q", "vector": [0.5] * 1536}) + "\n")
    calls = []
    got = ann.query_vectors(["q"], MODEL, lambda qs: calls.append(qs) or [], path)
    assert calls == [] and got == {"q": [0.5] * 1536}


def test_missing_vectors_are_embedded_once_and_appended(tmp_path):
    """AC-18 amendment: only the missing questions are embedded, in one call, and saved; another
    model's vector doesn't count as saved."""
    path = tmp_path / "v.jsonl"
    path.write_text(
        json.dumps({"model": MODEL, "question": "a", "vector": [0.1] * 1536})
        + "\n"
        + json.dumps({"model": "other", "question": "b", "vector": [0.2] * 1536})
        + "\n"
    )
    calls = []

    def embed(qs):
        calls.append(qs)
        return [[0.3] * 1536 for _ in qs]

    got = ann.query_vectors(["a", "b", "b"], MODEL, embed, path)
    assert calls == [["b"]]
    assert got["b"] == [0.3] * 1536
    assert ann.load_vectors(path, MODEL) == {"a": [0.1] * 1536, "b": [0.3] * 1536}
    ann.query_vectors(["a", "b"], MODEL, embed, path)
    assert len(calls) == 1


def test_wrong_dims_are_not_saved(tmp_path):
    """AC-17: the copy is vector(1536); a vector of another size fails before it is saved."""
    path = tmp_path / "v.jsonl"
    with pytest.raises(ValueError, match="1536"):
        ann.query_vectors(["q"], MODEL, lambda qs: [[0.0] * 8], path)
    assert not path.exists()


# --- AC-18: summary


def _cell(ids, k, ms=1.0, fact=None, exact=None):
    return {
        "ids": ids,
        "returned": len(ids),
        "ann_recall": ann.ann_recall(ids, exact if exact is not None else ids, k),
        "fact_recall": fact,
        "ms": ms,
    }


def _rec(persona, question, per_setting, exact):
    return {
        "persona": persona,
        "question": question,
        "sources": ["P-001"],
        "exact": exact,
        "ties": {"@5": False, "@20": False},
        "entitled_facts": None,
        "settings": {
            s: {f"@{k}": _cell(ids[:k], k, exact=exact) for k in (5, 20)}
            for s, ids in per_setting.items()
        },
    }


def test_summarize_reports_starvation_and_flags_admin_drift():
    """AC-18: per persona × setting: recall, mean returned, fewer than k; admin's HNSW settings
    must agree, else the summary flags it; the exact path is compared with the baseline."""
    full = list("abcdefghijklmnopqrst")
    narrow = {"exact": ["a", "b"], "off": [], "strict_order": ["a", "b"], "relaxed_order": ["a"]}
    admin = {s: full for s in ann.SETTINGS} | {"relaxed_order": ["z", *full[1:]]}
    records = [_rec("narrow", "q", narrow, ["a", "b"]), _rec("admin", "q", admin, full)]
    s = ann.summarize(records, {}, {"q": full[:5], "other": []})
    off = s["groups"]["narrow"]["settings"]["off"]["@5"]
    assert off["ann_recall"] == 0.0 and off["mean_returned"] == 0 and off["fewer_than_k"] == 1
    relaxed = s["groups"]["narrow"]["settings"]["relaxed_order"]["@5"]
    assert relaxed["ann_recall"] == pytest.approx(0.5)
    assert s["groups"]["narrow"]["settings"]["exact"]["@5"]["fewer_than_k"] == 1
    assert s["admin_hnsw_settings_differ"] == ["q"]
    assert s["exact_path"] == {"baseline": ann.ANN_BASELINE.name, "rows": 1, "identical_top5": 1}


def test_render_md_labels_admin_as_permissions_off():
    """AC-18 (Arun, 24 Oct): admin reads as permissions off; the settings are printed."""
    full = list("abcdefghijklmnopqrst")
    s = ann.summarize([_rec("admin", "q", {st: full for st in ann.SETTINGS}, full)], {}, None)
    s["meta"] = {
        "timestamp": "2026-10-24T00:00:00",
        "config_id": "fixed-512-64",
        "embed_model": MODEL,
        "policy_version": "policy-v1",
        "policy_sha256": "e" * 64,
        "identity_version": "identities-v1",
        "identity_sha256": "7" * 64,
        "suite_version": "v1",
        "suite_sha256": "9" * 64,
        "harness_sha": "abcdef12",
        "harness_dirty": False,
        "questions": {"total": 1, "suite": 1, "v1.2_answerable": 0},
        "shares": {"admin": 100.0},
        "settings": {
            "pgvector": "0.8.7",
            "m": 16,
            "ef_construction": 64,
            "ef_search": 40,
            "max_scan_tuples": 20000,
            "build": None,
        },
    }
    md = ann.render_md(s)
    assert "admin (100.0%) ≈ permissions off" in md
    assert "ef_search 40" in md and "max_scan_tuples 20000" in md and "m 16" in md
    assert "identical results" in md and "not available" in md
    assert "## k=5" in md and "## k=20" in md


# --- spec 0009: dry run by default, one spend line on confirm


class _Conn:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _main(monkeypatch, tmp_path, *, paid_env, missing=("q",)):
    if paid_env:
        monkeypatch.setenv(spend.PAID_ENV, "1")
    else:
        monkeypatch.delenv(spend.PAID_ENV, raising=False)
    setup = ann.Setup(
        [ann.Query("q", ("P-001",), None)],
        {},
        {},
        None,
        list(missing),
        {"embed_usd": 0.0001, "embed_tokens": 3},
        {
            "questions": {"total": 1, "suite": 1, "v1.2_answerable": 0},
            "ks": [5, 20],
            "timestamp": "2026-10-24T00:00:00",
        },
    )
    monkeypatch.setattr(ann, "read_manifest", lambda: None)
    monkeypatch.setattr(ann, "verify", lambda m: None)
    monkeypatch.setattr(ann, "connect", _Conn)
    monkeypatch.setattr(ann, "_setup", lambda conn, m, e: setup)
    monkeypatch.setattr(ann, "ANN_VECTORS", tmp_path / "v.jsonl")
    built = []
    monkeypatch.setattr(
        ann, "make_embedder", lambda spec, kind: built.append(kind) or FakeEmbedder(dims=1536)
    )
    monkeypatch.setattr(ann, "ANN_RUNS", tmp_path / "runs")

    def measure(conn, s, vectors, model, out):
        (out / "summary.json").write_text(json.dumps({"admin_hnsw_settings_differ": []}))
        (out / "summary.md").write_text("# ANN")
        return out

    monkeypatch.setattr(ann, "measure", measure)
    monkeypatch.setattr(
        ann, "log_spend", functools.partial(spend.log_spend, path=tmp_path / "spend.jsonl")
    )
    return tmp_path / "spend.jsonl", built


def test_dry_run_builds_no_embedder_and_logs_nothing(monkeypatch, tmp_path, capsys):
    """Spec 0009, AC-1: `make ann` prints the estimate and spends nothing."""
    log, built = _main(monkeypatch, tmp_path, paid_env=False)
    assert ann.main(["run"]) == 0
    assert built == [] and not log.exists() and not (tmp_path / "v.jsonl").exists()
    out = capsys.readouterr().out
    assert "1 to embed" in out and "$0.000100" in out and "make paid-ann" in out


def test_confirm_without_paid_target_refuses(monkeypatch, tmp_path):
    """Spec 0009, AC-2: --confirm alone exits, naming the paid target."""
    log, built = _main(monkeypatch, tmp_path, paid_env=False)
    with pytest.raises(SystemExit, match="make paid-ann"):
        ann.main(["run", "--confirm"])
    assert built == [] and not log.exists()


def test_confirm_embeds_missing_and_logs_one_spend_line(monkeypatch, tmp_path):
    """Spec 0009, AC-3; AC-18 amendment: a query embedder, the vector saved, one spend line."""
    log, built = _main(monkeypatch, tmp_path, paid_env=True)
    assert ann.main(["run", "--confirm"]) == 0
    assert built == ["query"]
    assert ann.load_vectors(tmp_path / "v.jsonl", MODEL).keys() == {"q"}
    (line,) = log.read_text().splitlines()
    rec = json.loads(line)
    (folder,) = (tmp_path / "runs").iterdir()
    assert rec["target"] == "ann" and rec["run_id"] == folder.name and rec["status"] == "ok"
    assert rec["est_usd"] == 0.0001 and rec["embed_model"] == MODEL


def test_confirm_with_every_vector_saved_builds_no_embedder(monkeypatch, tmp_path):
    """AC-18 amendment: nothing missing, nothing embedded."""
    log, built = _main(monkeypatch, tmp_path, paid_env=True, missing=())
    (tmp_path / "v.jsonl").write_text(
        json.dumps({"model": MODEL, "question": "q", "vector": [0.0] * 1536}) + "\n"
    )
    assert ann.main(["run", "--confirm"]) == 0
    assert built == [] and len(log.read_text().splitlines()) == 1


def test_failed_run_logs_its_partial_folder(monkeypatch, tmp_path):
    """Spec 0009, AC-3: a run that fails after spending is logged as failed, naming the run
    folder main created before spending."""
    log, _ = _main(monkeypatch, tmp_path, paid_env=True)

    def partial(conn, s, vectors, model, out):
        (out / "queries.jsonl").write_text("{}\n")
        raise RuntimeError("db gone mid-run")

    monkeypatch.setattr(ann, "measure", partial)
    with pytest.raises(RuntimeError):
        ann.main(["run", "--confirm"])
    rec = json.loads(log.read_text())
    (folder,) = (tmp_path / "runs").iterdir()
    assert rec["status"] == "failed" and rec["run_id"] == folder.name
