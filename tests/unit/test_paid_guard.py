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
        'make paid-ask AS=us-ic Q="x"',
        "make paid-eval RETRIEVAL_ONLY=1 CONFIG=fixed-512-64",
        "make -C /Users/fci/arun/handbook-rag paid-permissions",
        "cd /tmp && make paid-embed LIMIT=10",
        "HANDBOOK_PAID_RUN=1 PYTHONPATH=src uv run python -m handbook_rag.embed --confirm",
        "export HANDBOOK_PAID_RUN=1; make eval",
    ],
)
def test_paid_runs_need_a_human(command):
    """Spec 0009, AC-2: every route that spends asks the human, in every permission mode."""
    assert decide(command) == "ask"


@pytest.mark.parametrize(
    "command",
    [
        "make eval",
        "make test",
        'make ask AS=us-ic Q="x"',
        "make permissions",
        "make acl CONFIRM=1",  # writes the DB, spends nothing
        "grep -rn CONFIRM src docs",
        "uv run python -m handbook_rag.ask --as us-ic --confirm q",  # refused without the env var
        "cat > docs/x.md <<'EOF'\nrun the paid-eval target\nEOF",
        "grep -n HANDBOOK_PAID_RUN src/handbook_rag/spend.py",
    ],
)
def test_other_commands_pass_silently(command):
    """Spec 0009, AC-2: dry runs, docs and searches don't prompt."""
    assert decide(command) is None


@pytest.mark.parametrize("raw", ["not json", '{"tool_input": null}', '{"tool_input": {}}'])
def test_unreadable_payload_asks(raw):
    """Spec 0009, AC-2: the guard never fails open."""
    assert decide("", raw=raw) == "ask"
