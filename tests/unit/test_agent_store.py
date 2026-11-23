import pytest

from handbook_rag.agent.store import BINDING_KEYS, SessionMismatch, check_binding

HEADER = {k: f"{k}-v1" for k in BINDING_KEYS} | {"session_id": "x", "created_at": "t"}


def test_same_binding_passes():
    """AC-6: unchanged binding values resume."""
    check_binding(HEADER, dict(HEADER))
    check_binding(HEADER, {**HEADER, "created_at": "later"})  # non-binding keys are ignored


@pytest.mark.parametrize("key", BINDING_KEYS)
def test_changed_key_raises(key):
    """AC-6: any changed binding key fails and says to start a new session."""
    with pytest.raises(SessionMismatch, match="new session") as e:
        check_binding(HEADER, {**HEADER, key: "other"})
    assert key in str(e.value)
