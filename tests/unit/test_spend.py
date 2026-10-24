import json

from handbook_rag.spend import log_spend


def test_log_spend_appends_one_line_per_call(tmp_path):
    """Spec 0009, AC-3: one JSON line per paid run, with the agreed fields."""
    path = tmp_path / "runs" / "spend.jsonl"
    common = {"embed_model": "openai:m@1536", "answer_model": None, "status": "ok"}
    log_spend("eval", 0.0123, run_id="2026-10-24-abcd1234", **common, path=path)
    log_spend("embed", 0.5, run_id=None, **common, path=path)
    recs = [json.loads(line) for line in path.read_text().splitlines()]
    assert [r["target"] for r in recs] == ["eval", "embed"]
    assert set(recs[0]) == {
        "timestamp",
        "target",
        "run_id",
        "embed_model",
        "answer_model",
        "est_usd",
        "status",
    }
    assert recs[0]["run_id"] == "2026-10-24-abcd1234" and recs[1]["est_usd"] == 0.5
