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
        # Review catches: other assignment operators, continuations, separators in quotes, gmake.
        'make eval LIMIT="5 --confirm" HANDBOOK_PAID_RUN:=1',
        "make eval HANDBOOK_PAID_RUN?=1",
        "make eval HANDBOOK_PAID_RUN += 1",
        "make \\\n  paid-eval RETRIEVAL_ONLY=1",
        'make AS=us-ic Q="PTO & holidays?" paid-ask',
        "gmake paid-embed",
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
        "cat > docs/x.md <<'EOF'\nthe paid-call guardrails and paid-<target> names\nEOF",
        "git commit -m 'Spec 0009: paid-call guardrails'",
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


def test_targets_come_from_the_makefile(tmp_path):
    """Spec 0009, AC-2: the hook reads the paid-* targets from the Makefile, so a new paid target
    is guarded without editing the hook; a Makefile with none fails closed."""
    sys.path.insert(0, str(HOOK.parent))
    try:
        import paid_guard
    finally:
        sys.path.pop(0)
    assert set(paid_guard.paid_targets()) == {
        "paid-ask",
        "paid-embed",
        "paid-eval",
        "paid-permissions",
    }
    mk = tmp_path / "Makefile"
    mk.write_text("eval:\n\ttrue\npaid-rerank: ## Spend\n\ttrue\n")
    assert paid_guard.is_paid("make paid-rerank", paid_guard.paid_targets(mk))
    mk.write_text("eval:\n\ttrue\n")
    with pytest.raises(ValueError):
        paid_guard.paid_targets(mk)
