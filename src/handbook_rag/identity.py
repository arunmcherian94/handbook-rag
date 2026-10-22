"""Identity: fixture users resolved to groups (spec 0007, AC-6, AC-7; ADR-0021 D2, D3, D6).

The only module that constructs a Principal. The input is a user id, never question text, so no
code path derives groups from a query. A principal with no groups is an error.
"""

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

import yaml

from handbook_rag.constants import IDENTITIES_PATH
from handbook_rag.policy import Policy


class IdentityError(ValueError):
    """Unknown user, invalid attributes, or a group outside the policy vocabulary."""


EMPLOYMENT_TYPES = ("employee", "contractor", "temporary", "agency")
ROLES = ("ic", "people-manager")
_ATTRIBUTE_KEYS = ("employment_type", "role", "function", "entity")
_USER_KEYS = {"id", *_ATTRIBUTE_KEYS}


@dataclass(frozen=True)
class Principal:
    user_id: str
    attributes: Mapping[str, str | None]  # employment_type, role, function, entity
    groups: frozenset[str]

    @property
    def group_list(self) -> list[str]:
        """Sorted, for the SQL `&& %(groups)s::text[]` parameter."""
        return sorted(self.groups)


def resolve_groups(
    attributes: Mapping[str, str | None], vocabulary: frozenset[str]
) -> frozenset[str]:
    """The fixed AC-6 table. people-manager and people-ops resolve for employees only."""
    employment_type = attributes.get("employment_type")
    role = attributes.get("role")
    function = attributes.get("function")
    entity = attributes.get("entity")
    for key, value in attributes.items():
        if value is not None and not isinstance(value, str):
            raise IdentityError(f"attribute {key!r} must be a string, got {value!r}")
    if employment_type not in EMPLOYMENT_TYPES:
        raise IdentityError(f"unknown employment_type {employment_type!r}")
    if role not in ROLES:
        raise IdentityError(f"unknown role {role!r}")
    is_employee = employment_type == "employee"
    if is_employee and not entity:
        raise IdentityError("an employee needs exactly one entity")
    if not is_employee and entity:
        raise IdentityError(f"entity is for employees only, got {entity!r}")

    groups: set[str] = set()
    if employment_type == "employee":
        groups |= {"staff", "employee"}
    elif employment_type == "contractor":
        groups |= {"staff", "contractor"}
    elif employment_type == "temporary":
        groups.add("new-contractor")
    else:
        if not function:
            raise IdentityError("an agency contractor needs a function")
        groups |= {"new-contractor", f"agency:{function}"}
    if is_employee:
        if role == "people-manager":
            groups.add("manager")
        if function == "people-ops":
            groups.add("people-ops")
        groups.add(f"entity:{entity}")

    unknown = groups - vocabulary
    if unknown:
        raise IdentityError(f"groups outside the policy vocabulary: {sorted(unknown)}")
    return frozenset(groups)


def _read(path: Path) -> tuple[str, list[dict]]:
    doc = yaml.safe_load(path.read_bytes())
    if not isinstance(doc, dict) or set(doc) != {"version", "users"}:
        raise IdentityError("identities file must hold exactly `version` and `users`")
    if not isinstance(doc["version"], str):
        raise IdentityError("version must be a string")
    users = doc["users"]
    if not isinstance(users, list):
        raise IdentityError("users must be a list")
    for user in users:
        if not isinstance(user, dict) or not _USER_KEYS >= set(user) or "id" not in user:
            raise IdentityError(f"malformed user entry: {user!r}")
        for key, value in user.items():
            if not isinstance(value, str):
                raise IdentityError(f"user attribute {key!r} must be a string, got {value!r}")
    return doc["version"], users


def fixture_version(path: Path = IDENTITIES_PATH) -> tuple[str, str]:
    """(version, sha256 of the file bytes), for run metadata."""
    version, _ = _read(path)
    return version, hashlib.sha256(path.read_bytes()).hexdigest()


def user_ids(path: Path = IDENTITIES_PATH) -> list[str]:
    """The fixture's user ids, in file order (the `make acl` dry run reports each persona)."""
    _, users = _read(path)
    return [u["id"] for u in users]


def load(user_id: str, policy: Policy, path: Path = IDENTITIES_PATH) -> Principal:
    """The fixture user's Principal; raises IdentityError on an unknown user or no groups."""
    _, users = _read(path)
    matches = [u for u in users if u["id"] == user_id]
    if not matches:
        raise IdentityError(f"unknown user {user_id!r}")
    if len(matches) > 1:
        raise IdentityError(f"duplicate user id {user_id!r}")
    attributes = {key: matches[0].get(key) for key in _ATTRIBUTE_KEYS}
    groups = resolve_groups(attributes, policy.groups)
    if not groups:
        raise IdentityError(f"user {user_id!r} resolves to no groups")
    return Principal(user_id, MappingProxyType(attributes), groups)
