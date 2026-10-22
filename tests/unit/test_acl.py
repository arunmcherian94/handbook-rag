import pytest

from handbook_rag.acl import AclError, resolve_acls
from handbook_rag.policy import parse

POLICY = parse(
    """
version: test
groups: [staff, employee, people-ops, agency:engineering]
rules:
  - path: ""
    allow: [staff, people-ops]
  - path: engineering/
    allow: [staff, agency:engineering, people-ops]
  - path: total-rewards/compensation/
    allow: [employee, people-ops]
  - path: engineering/old.md
    allow: [employee, people-ops]
"""
)
OPEN = ("people-ops", "staff")
COMP = ("employee", "people-ops")
ENG = ("agency:engineering", "people-ops", "staff")


def _docs(*rel: str) -> dict[str, str]:
    return {f"content/handbook/{r}": f"/handbook/{r.removesuffix('.md')}/" for r in rel}


def test_documents_resolve_by_rule():
    """Spec 0007, AC-2: each document takes its winning rule's allow-list."""
    docs = _docs("values.md", "total-rewards/compensation/pay.md", "engineering/a.md")
    acls = resolve_acls(POLICY, docs, {})
    assert acls == {
        "content/handbook/values.md": OPEN,
        "content/handbook/total-rewards/compensation/pay.md": COMP,
        "content/handbook/engineering/a.md": ENG,
    }


def test_stub_inherits_target_and_ignores_own_rule():
    """Spec 0007, AC-3: a stub under engineering/ (own exact rule: employee-only) pointing at a
    compensation page takes the target's allow-list, not its own."""
    docs = _docs("engineering/old.md", "total-rewards/compensation/pay.md")
    stub = {"content/handbook/engineering/old.md": "/handbook/total-rewards/compensation/pay/"}
    assert resolve_acls(POLICY, docs, stub)["content/handbook/engineering/old.md"] == COMP


def test_chain_follows_to_final_target():
    """Spec 0007, AC-3: a chain of stubs resolves to the final non-stub target."""
    docs = _docs("a.md", "b.md", "engineering/c.md")
    stubs = {
        "content/handbook/a.md": "/handbook/b/",
        "content/handbook/b.md": "/handbook/engineering/c/",
    }
    acls = resolve_acls(POLICY, docs, stubs)
    assert acls["content/handbook/a.md"] == ENG
    assert acls["content/handbook/b.md"] == ENG


def test_cycle_fails():
    """Spec 0007, AC-3: a redirect cycle fails `make acl`."""
    docs = _docs("a.md", "b.md")
    stubs = {"content/handbook/a.md": "/handbook/b/", "content/handbook/b.md": "/handbook/a/"}
    with pytest.raises(AclError, match="cycle"):
        resolve_acls(POLICY, docs, stubs)


def test_missing_target_fails():
    """Spec 0007, AC-3: a target missing from the corpus fails `make acl`."""
    docs = _docs("a.md")
    with pytest.raises(AclError, match="not in the corpus"):
        resolve_acls(POLICY, docs, {"content/handbook/a.md": "/handbook/gone/"})
