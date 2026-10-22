from pathlib import Path

import pytest

from handbook_rag.policy import PolicyError, check_stale, load, parse, resolve

REAL_POLICY = Path(__file__).resolve().parents[2] / "acl" / "policy-v1.yaml"

BASE = """\
version: policy-v1
groups: [staff, employee, manager, people-ops]
rules:
  - path: ""
    allow: [staff, people-ops]
  - path: compensation/
    allow: [employee, people-ops]
  - path: compensation/compensation-review-cycle/
    allow: [manager, people-ops]
  - path: compensation/overview.md
    allow: [manager, employee, people-ops]
"""

DOCS = [
    "compensation/overview.md",
    "compensation/other.md",
    "compensation/compensation-review-cycle/a.md",
    "values/_index.md",
]


def test_parse_valid():
    """Spec 0007, AC-1: a valid policy parses; allow-lists are sorted, sha256 is set."""
    p = parse(BASE)
    assert p.version == "policy-v1"
    assert p.groups == {"staff", "employee", "manager", "people-ops"}
    assert p.rules[0].allow == ("people-ops", "staff")
    assert len(p.sha256) == 64


def test_resolve_order():
    """Spec 0007, AC-1: exact > longest prefix > catch-all."""
    p = parse(BASE)
    assert resolve(p, "compensation/overview.md") == ("employee", "manager", "people-ops")
    assert resolve(p, "compensation/other.md") == ("employee", "people-ops")
    assert resolve(p, "compensation/compensation-review-cycle/a.md") == ("manager", "people-ops")
    assert resolve(p, "values/_index.md") == ("people-ops", "staff")


def test_resolve_exact_does_not_match_as_prefix():
    """Spec 0007, AC-1: an exact rule applies to that path only, not to paths starting with it."""
    p = parse(BASE)
    assert resolve(p, "compensation/overview.md.bak") == ("employee", "people-ops")


def test_resolve_prefix_needs_slash_boundary():
    """Spec 0007, AC-1: a prefix rule ending in "/" does not match a sibling sharing the stem."""
    p = parse(BASE)
    assert resolve(p, "compensation-x/a.md") == ("people-ops", "staff")


@pytest.mark.parametrize(
    ("old", "new", "needle"),
    [
        ("path: compensation/\n", "path: compensation/\n    extra: x\n", "unknown key"),
        ("groups: [staff,", "bogus: x\ngroups: [staff,", "unknown key"),
        ("groups: [staff,", "groups: [staff, staff,", "duplicate group"),
        ("allow: [employee, people-ops]", "allow: [employee, nobody]", "'compensation/'"),
        ("allow: [employee, people-ops]", "allow: []", "'compensation/'"),
        ('  - path: ""\n    allow: [staff, people-ops]\n', "", "no catch-all"),
        (
            "  - path: compensation/\n",
            '  - path: ""\n    allow: [staff]\n  - path: compensation/\n',
            "duplicate path",
        ),
        (
            "  - path: compensation/\n",
            "  - path: compensation/overview.md\n    allow: [staff]\n  - path: compensation/\n",
            "'compensation/overview.md'",
        ),
        ("version: policy-v1", "version: 1", "not a string"),
        ("allow: [employee, people-ops]", "allow: [employee, no]", "not a string"),
        ("allow: [manager, employee, people-ops]", "allow: [manager, 3]", "not a string"),
        ("allow: [employee, people-ops]", "allow: [employee, null]", "not a string"),
        ("allow: [employee, people-ops]", "allow: 1.5", "not a string"),
        ("allow: [employee, people-ops]", "allow: employee", "non-empty list"),
    ],
)
def test_parse_rejections(old, new, needle):
    """Spec 0007, AC-1: the loader rejects each malformed shape, naming the offender."""
    assert old in BASE
    with pytest.raises(PolicyError, match=needle):
        parse(BASE.replace(old, new, 1))


def test_parse_rejects_bare_no():
    """Spec 0007, AC-1: a bare `no` (YAML False) is rejected, not read as the group "no"."""
    with pytest.raises(PolicyError, match="False"):
        parse(BASE.replace("[staff, employee,", "[staff, no,", 1))


def test_parse_rejects_non_mapping():
    """Spec 0007, AC-1: a file that is not a mapping, or not YAML, is a PolicyError."""
    with pytest.raises(PolicyError):
        parse("- a\n- b\n")
    with pytest.raises(PolicyError):
        parse("a: [unclosed")


def test_check_stale_names_every_stale_rule():
    """Spec 0007, AC-1: rules matching no document at the pin are all named."""
    p = parse(BASE)
    check_stale(p, DOCS)
    with pytest.raises(PolicyError) as e:
        check_stale(p, ["values/_index.md", "compensation/other.md"])
    msg = str(e.value)
    assert "compensation/overview.md" in msg
    assert "compensation/compensation-review-cycle/" in msg
    assert "'compensation/'" not in msg


def test_check_stale_matches_means_applies_to():
    """Spec 0007, AC-1: a rule shadowed by a more specific one still applies, so it is not stale."""
    p = parse(BASE)
    docs = ["compensation/overview.md", "compensation/compensation-review-cycle/a.md"]
    check_stale(p, [*docs, "values/_index.md"])  # compensation/ applies to overview.md too


def test_load_checks_stale(tmp_path):
    """Spec 0007, AC-1: load() parses the file and then checks staleness."""
    f = tmp_path / "p.yaml"
    f.write_text(BASE)
    assert load(DOCS, f).sha256 == parse(BASE).sha256
    with pytest.raises(PolicyError, match="stale"):
        load(["values/_index.md"], f)


def test_real_policy_parses():
    """Spec 0007, AC-1: acl/policy-v1.yaml parses; people-ops is on every rule."""
    text = REAL_POLICY.read_text(encoding="utf-8")
    p = parse(text)
    assert p.version == "policy-v1"
    assert all("people-ops" in r.allow for r in p.rules)
    assert any(r.path == "" for r in p.rules)
