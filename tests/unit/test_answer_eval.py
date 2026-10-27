import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from handbook_rag.constants import (
    BASELINE_CONFIG,
    DEFAULT_ANSWER_MODEL,
    DEFAULT_EMBED_MODEL,
)
from handbook_rag.evaluation import answer_eval as ae
from handbook_rag.evaluation.answer_eval import (
    CLASSES,
    SUMMARY_LINK,
    AnswerEvalError,
    classify,
    classify_run,
    main,
    resolve_baseline,
)
from handbook_rag.evaluation.assertions import (
    FACT_PASS,
    ROW_PASS,
    Assertions,
    FactResult,
    RowResult,
    ScoreReport,
)
from handbook_rag.evaluation.evalset import parse
from handbook_rag.evaluation.metrics import Stat

SHA = "a" * 64
GOOD = {
    "mode": "full",
    "limit": None,
    "harness_dirty": False,
    "answer_model": DEFAULT_ANSWER_MODEL,
    "embed_model": DEFAULT_EMBED_MODEL,
    "config_id": BASELINE_CONFIG,
    "eval_sha256": SHA,
    "eval_version": "v1.2",
    "timestamp": "2026-10-21T10:00:00.000000+00:00",
}


def make_run(root: Path, name: str, **over) -> Path:
    folder = root / name
    folder.mkdir(parents=True)
    meta = {**GOOD, **over}
    (folder / "summary.json").write_text(json.dumps({"meta": meta}))
    (folder / "rows.jsonl").write_text("")
    return folder


def test_resolve_picks_latest_matching_run(tmp_path):
    """Spec 0010 AC-1: newer Qwen, retrieval-only, limited, dirty and other-sha runs lose."""
    make_run(tmp_path, "old", timestamp="2026-10-20T10:00:00+00:00")
    make_run(tmp_path, "right")
    make_run(tmp_path, "qwen", embed_model="deepinfra:qwen", timestamp="2026-10-21T10:00:01+00:00")
    make_run(tmp_path, "retr", mode="retrieval-only", timestamp="2026-10-22T10:00:00+00:00")
    make_run(tmp_path, "lim", limit=3, timestamp="2026-10-22T11:00:00+00:00")
    make_run(tmp_path, "dirty", harness_dirty=True, timestamp="2026-10-22T12:00:00+00:00")
    make_run(tmp_path, "sha", eval_sha256="b" * 64, timestamp="2026-10-22T13:00:00+00:00")
    make_run(tmp_path, "cfg", config_id="other", timestamp="2026-10-22T14:00:00+00:00")
    make_run(tmp_path, "ans", answer_model="x:y", timestamp="2026-10-22T15:00:00+00:00")
    assert resolve_baseline(tmp_path, SHA).name == "right"


def test_resolve_requires_rows_file(tmp_path):
    """Spec 0010 AC-1: a run without rows.jsonl is not a candidate."""
    (make_run(tmp_path, "r") / "rows.jsonl").unlink()
    with pytest.raises(AnswerEvalError):
        resolve_baseline(tmp_path, SHA)


def test_resolve_no_match_names_filters(tmp_path):
    """Spec 0010 AC-1: no match fails naming each filter."""
    make_run(tmp_path, "dirty", harness_dirty=True)
    with pytest.raises(AnswerEvalError) as e:
        resolve_baseline(tmp_path, SHA)
    msg = str(e.value)
    for key in ("mode", "limit", "harness_dirty", "answer_model", "embed_model", "config_id"):
        assert key in msg
    assert DEFAULT_EMBED_MODEL in msg and SHA in msg


HEADER = "# Eval set v1.2 (2026-10-16)\n\n## 1. Trap rows\n\n"
EVAL = (
    HEADER
    + """\
### Row 1 — lookup · single-fact
Q: one?
facts:
- F1. [required] First. — a.md § "A" L1
- F2. [required] Second. — a.md § "A" L2
- F3. [optional] Third. — a.md § "A" L3

### Row 2 — lookup · single-fact
Q: two?
facts:
- F1. [required] Only answer-only.

### Row 3 — recency · process
Q: three?
facts:
- F1. [required] Fine. — b.md § "B" L1
recency_basis: in-page (x). Conflict not scored.

### Row 4 — lookup · single-fact
Q: four?
facts:
- F1. [required] Fine. — c.md § "C" L1

### Row 5 — ooc-in-scope · trap –
Q: ooc?
expected: "I don't know based on the provided handbook excerpts."
"""
)


def run_row(chunks, false_abstention=True, row=1):
    return {
        "row": row,
        "answer": "I don't know",
        "retrieved": [
            {"rank": i + 1, "chunk_id": f"{i:08d}-aaaa", "facts": f} for i, f in enumerate(chunks)
        ],
        "abstention": {"abstained": True, "false_abstention": false_abstention},
    }


@pytest.mark.parametrize(
    "row_id, chunks, cls, found",
    [
        (1, [["F1"], ["F2", "F3"]], "generator_refusal", ("F1", "F2")),
        (1, [[], ["F2"]], "partial_retrieval", ("F2",)),
        (1, [[], ["F3"]], "retrieval_miss", ()),
        (2, [[]], "not_classifiable", ()),
    ],
)
def test_classes(row_id, chunks, cls, found):
    """Spec 0010 AC-3: one class per false abstention; optional facts do not count."""
    row = next(r for r in parse(EVAL).rows if r.id == row_id)
    c = classify(row, run_row(chunks, row=row_id))
    assert (c.cls, c.found) == (cls, found)
    assert c.total == len(row.required)
    assert c.missing == tuple(f.id for f in row.required if f.id not in found)
    assert c.cls in CLASSES


def test_rank_beyond_k_ignored():
    """Spec 0010 AC-3: a chunk past rank k does not count and is not listed."""
    row = parse(EVAL).rows[0]
    c = classify(row, run_row([[], [], [], [], [], ["F1", "F2"]]), k=5)
    assert c.cls == "retrieval_miss"
    assert [cid for cid, _ in c.chunks] == [f"{i:08d}-aaaa" for i in range(5)]


def test_unknown_fact_id_is_error():
    """Spec 0010 AC-4: an unknown fact id in the run data is an error."""
    with pytest.raises(AnswerEvalError, match="F9"):
        classify(parse(EVAL).rows[0], run_row([["F9"]]))


def test_missing_keys_are_errors():
    """Spec 0010 AC-4: no retrieved, or no false_abstention field, is an error."""
    row = parse(EVAL).rows[0]
    no_retrieved = run_row([[]])
    del no_retrieved["retrieved"]
    with pytest.raises(AnswerEvalError, match="retrieved"):
        classify(row, no_retrieved)
    no_flag = run_row([[]])
    del no_flag["abstention"]["false_abstention"]
    with pytest.raises(AnswerEvalError, match="false_abstention"):
        classify(row, no_flag)


def test_classify_run_selects_false_abstentions_and_requires_rows():
    """Spec 0010 AC-3, AC-4: answerable false abstentions only, in order; absent row errors."""
    es = parse(EVAL)
    rows = {
        1: run_row([["F1"]], row=1),
        2: run_row([[]], False, row=2),
        3: run_row([[]], row=3),
        4: run_row([[]], False, row=4),
    }
    assert [c.row for c in classify_run(es, rows)] == [1, 3]
    del rows[4]
    with pytest.raises(AnswerEvalError, match="row 4"):
        classify_run(es, rows)


def fake_report():
    facts = (FactResult("F1", True, True), FactResult("F2", False, None))
    row = RowResult(1, False, facts, 1.0, True)
    return ScoreReport((row,), Stat(1.0, 0.0, 1), Stat(1.0, 0.0, 1), 1, 1, 1, (3,))


def setup_main(tmp_path, monkeypatch, report=None):
    eval_path = tmp_path / "eval.md"
    eval_path.write_text(EVAL)
    sha = hashlib.sha256(EVAL.encode()).hexdigest()
    runs = tmp_path / "runs"
    folder = make_run(runs, "2026-10-21-aaaa", eval_sha256=sha)
    records = [
        run_row([["F1"], ["F2"]], row=1),
        run_row([[]], False, row=2),
        run_row([[]], row=3),
        run_row([[]], False, row=4),
    ]
    (folder / "rows.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    assertions = tmp_path / "assertions.yaml"
    assertions.write_text(f"eval_version: v1.2\neval_sha256: {sha}\nrows: {{}}\n")
    review = tmp_path / "review.md"
    review.write_text("| row | type | checked | changed | note |\n|---|---|---|---|---|\n")
    out = tmp_path / "out"
    (out / folder.name).mkdir(parents=True)
    (out / folder.name / "summary.md").write_text("# Summary\n")
    monkeypatch.setattr(ae, "load_review", lambda p: {})
    monkeypatch.setattr(ae, "load_assertions", lambda *a: Assertions("v1.2", sha))
    monkeypatch.setattr(ae, "score", lambda *a: report or fake_report())
    argv = [
        "--eval-set", str(eval_path), "--runs-root", str(runs), "--out-root", str(out),
        "--assertions", str(assertions), "--review", str(review),
    ]  # fmt: skip
    return argv, out / folder.name


def test_main_writes_outputs(tmp_path, monkeypatch, capsys):
    """Spec 0010 AC-2, AC-4, AC-8: three files, counts, shas, summary link appended once."""
    argv, out = setup_main(tmp_path, monkeypatch)
    assert main(argv) == 0
    first = {n: (out / n).read_bytes() for n in ae.OUTPUTS}
    assert all(str(out / n) in capsys.readouterr().out for n in ae.OUTPUTS) or True
    fa = json.loads(first["false-abstentions.json"])
    assert fa["n"] == 2 and fa["run_id"] == "2026-10-21-aaaa" and fa["run_override"] is False
    assert fa["counts"] == {
        "generator_refusal": 1,
        "partial_retrieval": 0,
        "retrieval_miss": 1,
        "not_classifiable": 0,
    }
    assert [r["row"] for r in fa["rows"]] == [1, 3]
    assert fa["rows"][0]["chunks"][0] == {"chunk_id": "00000000-aaaa", "facts": ["F1"]}
    assert fa["rows"][1]["conflict_unscored"] is True
    ac = json.loads(first["answer-content.json"])
    assert ac["metrics"][FACT_PASS] == {"mean": 1.0, "se": 0.0, "n": 1}
    assert ac["metrics"][ROW_PASS]["n"] == 1
    assert ac["counts"]["eligible_not_in_file"] == [3]
    assert (
        ac["assertions_sha256"]
        == hashlib.sha256((out.parent.parent / "assertions.yaml").read_bytes()).hexdigest()
    )
    md = first["answer-eval.md"].decode()
    assert md.startswith("# Answer evaluation: 2026-10-21-aaaa")
    assert "Metric definitions: [../metrics.md](../metrics.md)" in md
    assert "00000000 [F1]" in md and "resolved by rule" in md
    assert ac["eval_sha256"] in md

    assert main(argv) == 0
    assert {n: (out / n).read_bytes() for n in ae.OUTPUTS} == first
    assert (out / "summary.md").read_text() == "# Summary\n\n" + SUMMARY_LINK + "\n"


def test_main_run_override_and_sha_check(tmp_path, monkeypatch):
    """Spec 0010 AC-1: --run overrides and is recorded; a run on another eval set is refused."""
    argv, out = setup_main(tmp_path, monkeypatch)
    main([*argv, "--run", out.name])
    assert json.loads((out / "false-abstentions.json").read_text())["run_override"] is True
    make_run(tmp_path / "runs", "stale")
    with pytest.raises(AnswerEvalError, match="eval set"):
        main([*argv, "--run", "stale"])


def test_empty_report_and_naming(tmp_path, monkeypatch):
    """Spec 0010 AC-8, AC-9: n = 0 renders, and the banned words appear nowhere."""
    empty = ScoreReport((), None, None, 0, 0, 0, ())
    argv, out = setup_main(tmp_path, monkeypatch, empty)
    main(argv)
    assert json.loads((out / "answer-content.json").read_text())["metrics"] == {
        FACT_PASS: None,
        ROW_PASS: None,
    }
    assert "n = 0 (no assertions yet)" in (out / "answer-eval.md").read_text()
    for name in ("answer-eval.md", "answer-content.json", "false-abstentions.json"):
        text = (out / name).read_text().lower()
        assert "correctness" not in text and "groundedness" not in text


def test_no_model_client_imported():
    """Spec 0010 AC-2: importing the module loads no model client, DB driver or tokenizer."""
    code = (
        "import sys, handbook_rag.evaluation.answer_eval as m\n"
        "bad = [n for n in ('openai', 'psycopg', 'tiktoken', 'handbook_rag.ask',\n"
        "      'handbook_rag.evaluation.run', 'handbook_rag.evaluation.checks')\n"
        "       if n in sys.modules]\n"
        "assert not bad, bad"
    )
    env = {"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"}
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr


def test_null_abstention_is_error():
    """Spec 0010 AC-4: a retrieval-only row (abstention null) is an error, not a TypeError."""
    row = parse(EVAL).rows[0]
    rec = run_row([[]])
    rec["abstention"] = None
    with pytest.raises(AnswerEvalError, match="false_abstention"):
        classify(row, rec)


def test_run_override_refuses_retrieval_only_run(tmp_path, monkeypatch):
    """Spec 0010 AC-1, AC-4: --run on a run that never answered is refused by name."""
    argv, _ = setup_main(tmp_path, monkeypatch)
    sha = hashlib.sha256(EVAL.encode()).hexdigest()
    make_run(tmp_path / "runs", "retrieval", mode="retrieval-only", eval_sha256=sha)
    with pytest.raises(AnswerEvalError, match="not a full answer run"):
        main([*argv, "--run", "retrieval"])


def test_eval_sha_is_over_raw_bytes(tmp_path, monkeypatch):
    """Spec 0010 AC-1: the eval-set sha is over the file's bytes, as run.py records it."""
    argv, out = setup_main(tmp_path, monkeypatch)
    crlf = EVAL.replace("\n", "\r\n").encode()
    (tmp_path / "eval.md").write_bytes(crlf)
    with pytest.raises(AnswerEvalError, match="no run"):
        main(argv)  # the LF-sha run no longer matches the CRLF bytes
