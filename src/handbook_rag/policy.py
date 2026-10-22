"""ACL policy v1: path rules to group allow-lists (spec 0007, AC-1; ADR-0021 D2).

A rule's path is relative to content/handbook/: a prefix ends in "/", the catch-all is "" (the
root prefix), anything else is an exact path. An exact path beats any prefix; among prefixes the
longest wins.
"""

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import yaml

from handbook_rag.constants import POLICY_PATH


class PolicyError(ValueError):
    """The policy file is malformed, or a rule is stale at the pin."""


@dataclass(frozen=True)
class Rule:
    path: str
    allow: tuple[str, ...]  # sorted, non-empty


@dataclass(frozen=True)
class Policy:
    version: str
    groups: frozenset[str]  # the vocabulary
    rules: tuple[Rule, ...]
    sha256: str  # of the file bytes


def _check_strings(node: object, where: str) -> None:
    """Every scalar, key or value, must be a string: YAML reads a bare `no` as False."""
    if isinstance(node, dict):
        for key, value in node.items():
            _check_strings(key, f"{where} key {key!r}")
            _check_strings(value, f"{where}.{key}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _check_strings(item, f"{where}[{i}]")
    elif not isinstance(node, str):
        raise PolicyError(
            f"{where}: {node!r} is {type(node).__name__}, not a string (quote it in the YAML)"
        )


def _check_keys(node: dict, allowed: set[str], where: str) -> None:
    unknown = sorted(set(node) - allowed)
    if unknown:
        raise PolicyError(f"{where}: unknown key(s) {unknown}")
    missing = sorted(allowed - set(node))
    if missing:
        raise PolicyError(f"{where}: missing key(s) {missing}")


def parse(text: str) -> Policy:
    """yaml.safe_load, then validate. Raises PolicyError on a non-string value, a missing or
    duplicate catch-all, a group outside the vocabulary, an empty allow-list or a duplicate
    path."""
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise PolicyError(f"not valid YAML: {e}") from e
    if not isinstance(doc, dict):
        raise PolicyError("top level must be a mapping")
    _check_strings(doc, "policy")
    _check_keys(doc, {"version", "groups", "rules"}, "policy")

    version = doc["version"]
    if not isinstance(version, str) or not version:
        raise PolicyError(f"version must be a non-empty string, got {version!r}")
    raw_groups = doc["groups"]
    if not isinstance(raw_groups, list) or not raw_groups:
        raise PolicyError("groups must be a non-empty list of strings")
    groups = frozenset(raw_groups)
    if len(groups) != len(raw_groups):
        dupes = sorted({g for g in raw_groups if raw_groups.count(g) > 1})
        raise PolicyError(f"duplicate group in the vocabulary: {dupes}")
    raw_rules = doc["rules"]
    if not isinstance(raw_rules, list):
        raise PolicyError("rules must be a list")

    rules: list[Rule] = []
    seen: set[str] = set()
    for i, raw in enumerate(raw_rules):
        if not isinstance(raw, dict):
            raise PolicyError(f"rule {i}: must be a mapping with path and allow, got {raw!r}")
        _check_keys(raw, {"path", "allow"}, f"rule {i}")
        path, allow = raw["path"], raw["allow"]
        label = f"rule {path!r}"
        if not isinstance(path, str):
            raise PolicyError(f"rule {i}: path must be a string, got {path!r}")
        if path in seen:
            raise PolicyError(f"{label}: duplicate path" + (" (catch-all)" if not path else ""))
        seen.add(path)
        if not isinstance(allow, list) or not allow:
            raise PolicyError(f"{label}: allow must be a non-empty list of groups")
        outside = sorted(set(allow) - groups)
        if outside:
            raise PolicyError(f"{label}: group(s) outside the vocabulary: {outside}")
        rules.append(Rule(path=path, allow=tuple(sorted(allow))))
    if "" not in seen:
        raise PolicyError('no catch-all rule (path: "")')

    return Policy(
        version=version,
        groups=groups,
        rules=tuple(rules),
        sha256=hashlib.sha256(text.encode()).hexdigest(),
    )


def check_stale(policy: Policy, doc_paths: Iterable[str]) -> None:
    """Raises PolicyError naming every rule that matches no document. doc_paths are relative
    to content/handbook/."""
    docs = set(doc_paths)
    stale = [
        r.path
        for r in policy.rules
        if not (any(d.startswith(r.path) for d in docs) if _is_prefix(r.path) else r.path in docs)
    ]
    if stale:
        raise PolicyError(f"stale rule(s) matching no document at the pin: {stale}")


def load(doc_paths: Iterable[str], path: Path = POLICY_PATH) -> Policy:
    """parse() the file, then check_stale() against the documents at the pin."""
    policy = parse(path.read_text(encoding="utf-8"))
    check_stale(policy, doc_paths)
    return policy


def _is_prefix(rule_path: str) -> bool:
    return rule_path == "" or rule_path.endswith("/")


def resolve(policy: Policy, rel_path: str) -> tuple[str, ...]:
    """The allow-list of the winning rule for a path relative to content/handbook/."""
    best: Rule | None = None
    for rule in policy.rules:
        if rule.path == rel_path:
            return rule.allow
        if _is_prefix(rule.path) and rel_path.startswith(rule.path):
            if best is None or len(rule.path) > len(best.path):
                best = rule
    if best is None:  # unreachable for a parsed policy: parse() requires the catch-all
        raise PolicyError(f"no rule matches {rel_path!r}")
    return best.allow
