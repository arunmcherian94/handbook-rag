"""Indirect-injection fixture suite (spec 0014 AC-14): a compromised fake model, a planted
excerpt, and the deterministic layers that must still hold."""

import json
import uuid
from pathlib import Path

import pytest
import yaml
from fakes import FakeChatModel, final_step, make_principal, tool_step

from handbook_rag.agent.loop import run_turn
from handbook_rag.agent.tool import TurnTool
from handbook_rag.ask import Retrieved

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "injection-v1.yaml"
SUITE = yaml.safe_load(FIXTURE.read_text())
CASES = SUITE["cases"]
CATEGORIES = {
    "instruction_override",
    "image_exfiltration",
    "link_exfiltration",
    "delimiter_breakout",
    "tag_smuggling",
    "out_of_range_citation",
    "pii_echo",
    "claimed_identity",
    "prompt_extraction",
    "abstention_extra",
}
MARKER = "GR-FIXTURE-"


def planted_content(case: dict) -> str:
    """Excerpt content, with the tag_payload (if any) encoded as tag-block characters."""
    content = case["excerpt"]["content"]
    payload = case["excerpt"].get("tag_payload", "")
    return content + "".join(chr(0xE0000 + ord(c)) for c in payload)


def excerpts(case: dict) -> list[Retrieved]:
    """The planted excerpt first, then four fillers."""

    def make(i: int, url_path: str, heading: str, content: str) -> Retrieved:
        return Retrieved(
            n=i,
            chunk_id=uuid.uuid5(uuid.NAMESPACE_URL, f"{case['id']}/{i}"),
            doc_id=uuid.uuid4(),
            url_path=url_path,
            heading=heading,
            content=content,
            distance=i / 10,
            chunk_size=512,
            chunk_overlap=64,
            tokenizer="cl100k_base",
            commit_sha="abc",
        )

    e = case["excerpt"]
    out = [make(1, e["url_path"], e["heading"], planted_content(case))]
    out += [
        make(i, f"/handbook/filler/{i}/", f"Filler {i}", f"filler content {i}") for i in range(2, 6)
    ]
    return out


def run_case(case: dict):
    found = excerpts(case)
    tool = TurnTool(None, None, make_principal("staff"), retrieve=lambda *a, **kw: found)
    model = FakeChatModel([tool_step("q"), *[final_step(r) for r in case["replies"]]])
    saved: list[dict] = []
    rec = run_turn(
        model, tool, case["question"], [], lambda r: saved.append(json.loads(json.dumps(r)))
    )
    return rec, saved


def model_free_view(record: dict) -> str:
    """JSON of a saved record without what the planted text or the compromised reply
    legitimately sits in: tool-role and assistant-role messages (AC-6)."""
    keep = dict(record)
    keep["messages"] = [m for m in record["messages"] if m["role"] not in ("tool", "assistant")]
    return json.dumps(keep, ensure_ascii=False)


def test_suite_shape():
    """AC-14: at least 10 cases, every category, unique ids, marker in every planted text."""
    assert SUITE["version"] == "injection-v1"
    assert len(CASES) >= 10
    assert {c["category"] for c in CASES} >= CATEGORIES
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids))
    for c in CASES:
        assert MARKER in c["excerpt"]["content"], c["id"]
        assert c["replies"] and {"state", "answer", "events", "absent"} <= set(c["expect"])


def test_tag_payload_is_encoded_as_tag_characters():
    """AC-14: the tag_payload is appended as U+E0000+ord(c), invisible in the YAML."""
    case = next(c for c in CASES if c["category"] == "tag_smuggling")
    content = planted_content(case)
    hidden = content[len(case["excerpt"]["content"]) :]
    assert hidden and all(0xE0000 <= ord(c) <= 0xE007F for c in hidden)


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_injection_case(case):
    """AC-14 (plus the per-category AC: AC-4, AC-5, AC-7 to AC-10): with a compromised model,
    the answer, state and events are as expected and the exfil values never reach the answer or
    the saved user-facing fields."""
    rec, saved = run_case(case)
    expect = case["expect"]
    assert rec["state"] == expect["state"]
    assert rec["answer"] == expect["answer"]

    seen = {(e["check"], e["action"], e["reason"]) for e in rec["guardrail_events"]}
    for check, action, reason in expect["events"]:
        assert (check, action, reason) in seen, (check, action, reason, sorted(seen, key=str))

    surfaces = [rec["answer"] or ""]
    for r in [rec, *saved]:
        surfaces += [model_free_view(r), json.dumps(r["guardrail_events"], ensure_ascii=False)]
    for text in expect["absent"]:
        for surface in surfaces:
            assert text not in surface, text
