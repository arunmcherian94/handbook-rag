import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).parents[2] / ".claude" / "hooks" / "paid_guard.py"


def decide(command: str) -> str | None:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    out = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
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
