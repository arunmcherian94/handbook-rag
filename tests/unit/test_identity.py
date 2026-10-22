"""Identity fixture and group resolution (spec 0007, AC-6, AC-7). In-memory, no network."""

import dataclasses
from pathlib import Path

import pytest
import yaml

from handbook_rag import identity
from handbook_rag.identity import IdentityError, Principal
from handbook_rag.policy import Policy

ROOT = Path(__file__).resolve().parents[2]
VOCABULARY = frozenset(yaml.safe_load((ROOT / "acl/policy-v1.yaml").read_text())["groups"])
POLICY = Policy("policy-v1", VOCABULARY, (), "")
IDENTITIES = ROOT / "acl/identities-v1.yaml"

PERSONAS = {
    "admin": {"staff", "employee", "people-ops", "entity:us-inc"},
    "us-ic": {"staff", "employee", "entity:us-inc"},
    "manager": {"staff", "employee", "manager", "entity:uk-ltd"},
    "contractor": {"staff", "contractor"},
    "narrow": {"new-contractor"},
    "agency": {"new-contractor", "agency:engineering"},
}


@pytest.mark.parametrize("user_id", PERSONAS)
def test_persona_groups_pinned(user_id):
    """Spec 0007, AC-6: each persona resolves to exactly its pinned groups."""
    assert identity.load(user_id, POLICY).groups == PERSONAS[user_id]


def test_fixture_has_six_users_and_a_version():
    """Spec 0007, AC-6: the fixture holds a version and the six personas."""
    version, digest = identity.fixture_version(IDENTITIES)
    assert version == "identities-v1"
    assert len(digest) == 64
    assert {u["id"] for u in yaml.safe_load(IDENTITIES.read_text())["users"]} == set(PERSONAS)


def _attrs(employment_type, role="ic", function=None, entity=None):
    return {
        "employment_type": employment_type,
        "role": role,
        "function": function,
        "entity": entity,
    }


@pytest.mark.parametrize("employment_type", ["contractor", "agency"])
def test_non_employee_gets_no_manager_or_people_ops(employment_type):
    """Spec 0007, AC-6: manager and people-ops resolve for employees only."""
    groups = identity.resolve_groups(
        _attrs(employment_type, "people-manager", "engineering"), VOCABULARY
    )
    assert not groups & {"manager", "people-ops"}
    if employment_type == "contractor":  # an agency function is an agency:X group, checked below
        groups = identity.resolve_groups(_attrs(employment_type, "ic", "people-ops"), VOCABULARY)
        assert not groups & {"manager", "people-ops"}
    else:
        with pytest.raises(IdentityError):
            identity.resolve_groups(_attrs(employment_type, "ic", "people-ops"), VOCABULARY)


def test_unknown_agency_function_fails():
    """Spec 0007, AC-6: agency:X must be in the vocabulary."""
    with pytest.raises(IdentityError):
        identity.resolve_groups(_attrs("agency", function="marketing"), VOCABULARY)


def test_agency_requires_function():
    """Spec 0007, AC-6: an agency contractor needs a function."""
    with pytest.raises(IdentityError):
        identity.resolve_groups(_attrs("agency"), VOCABULARY)


def test_entity_rules():
    """Spec 0007, AC-6: exactly one entity for employees, none otherwise, and in the vocabulary."""
    with pytest.raises(IdentityError):
        identity.resolve_groups(_attrs("employee"), VOCABULARY)
    with pytest.raises(IdentityError):
        identity.resolve_groups(_attrs("contractor", entity="us-inc"), VOCABULARY)
    with pytest.raises(IdentityError):
        identity.resolve_groups(_attrs("employee", entity="mars-ltd"), VOCABULARY)


def test_unknown_employment_type_and_role_fail():
    """Spec 0007, AC-6: values outside the v1 dimensions are rejected."""
    with pytest.raises(IdentityError):
        identity.resolve_groups(_attrs("volunteer"), VOCABULARY)
    with pytest.raises(IdentityError):
        identity.resolve_groups(_attrs("temporary", role="ceo"), VOCABULARY)


def _write(tmp_path, text):
    path = tmp_path / "ids.yaml"
    path.write_text(text)
    return path


def test_non_string_scalar_rejected(tmp_path):
    """Spec 0007, AC-6: strings only; a YAML boolean or number is rejected."""
    path = _write(
        tmp_path,
        "version: identities-v1\nusers:\n  - id: x\n    employment_type: temporary\n    role: ic\n"
        "    function: 12\n",
    )
    with pytest.raises(IdentityError):
        identity.load("x", POLICY, path)


def test_unknown_user():
    """Spec 0007, AC-7: an unknown user id is an error."""
    with pytest.raises(IdentityError):
        identity.load("nobody", POLICY)


def test_no_groups_is_an_error(monkeypatch):
    """Spec 0007, AC-7: a principal with no groups is an error, never an unfiltered search."""
    monkeypatch.setattr(identity, "resolve_groups", lambda attributes, vocabulary: frozenset())
    with pytest.raises(IdentityError, match="no groups"):
        identity.load("narrow", POLICY)


def test_principal_is_frozen_and_attributes_immutable():
    """Spec 0007, AC-7: Principal is frozen and its attributes cannot be mutated."""
    principal = identity.load("narrow", POLICY)
    with pytest.raises(dataclasses.FrozenInstanceError):
        principal.groups = frozenset({"staff"})  # type: ignore[misc]
    with pytest.raises(TypeError):
        principal.attributes["role"] = "people-manager"  # type: ignore[index]


def test_principal_constructed_only_in_identity_module():
    """Spec 0007, AC-7: `Principal(` appears in no src/ file other than identity.py."""
    offenders = [
        str(path.relative_to(ROOT))
        for path in (ROOT / "src").rglob("*.py")
        if path.name != "identity.py" and "Principal(" in path.read_text()
    ]
    assert offenders == []
    assert Principal  # imported so a rename breaks this test
