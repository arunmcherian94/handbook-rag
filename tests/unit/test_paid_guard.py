import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).parents[2] / ".claude" / "hooks" / "paid_guard.py"


def decide(command: str, raw: str | None = None) -> str | None:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    out = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload) if raw is None else raw,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else None


@pytest.mark.parametrize(
    "command",
    [
        'make ask AS=us-ic Q="x" CONFIRM=1',
        "CONFIRM=1 make eval",
        "make permissions CONFIRM=1 CONFIG=fixed-512-64",
        "PYTHONPATH=src uv run python -m handbook_rag.embed --confirm",
        # Review catches: shell quoting and argparse abbreviations still spend.
        'make ask AS=us-ic Q=x CONFIRM="1"',
        "make eval CONFIRM='1'",
        "uv run python -m handbook_rag.ask --as us-ic --conf q",
    ],
)
def test_paid_commands_need_a_human(command):
    """Spec 0009, AC-2: anything that spends asks the human, in every permission mode."""
    assert decide(command) == "ask"


@pytest.mark.parametrize(
    "command", ["make eval", "make test", 'make ask AS=us-ic Q="x"', "make permissions"]
)
def test_other_commands_pass_silently(command):
    """Spec 0009, AC-2: dry runs and everything else are untouched."""
    assert decide(command) is None


@pytest.mark.parametrize("raw", ["not json", '{"tool_input": null}', '{"tool_input": {}}'])
def test_unreadable_payload_asks(raw):
    """Spec 0009, AC-2: the guard never fails open."""
    assert decide("", raw=raw) == "ask"
