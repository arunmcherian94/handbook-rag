"""`make acl`: resolve the policy onto documents and every config's chunks (spec 0007, AC-2 to
AC-5; ADR-0021 D1, D4, D5). Functional core, imperative shell.

Each document gets its allow-list in documents.acl_tags; chunks copy it to allowed_groups, for
every config, with no re-embedding. A redirect stub ignores its own rule and inherits its final
target's allow-list (AC-3). Dry run by default; --confirm applies in one transaction.
"""

import argparse
import sys
from collections.abc import Mapping
from pathlib import Path

from handbook_rag import identity
from handbook_rag.constants import BASELINE_CONFIG, CHECKOUT, CORPUS_PREFIX
from handbook_rag.corpus import read_manifest, verify
from handbook_rag.db import connect
from handbook_rag.ingest import derive_redirect, split_front_matter
from handbook_rag.policy import Policy, load, resolve


class AclError(ValueError):
    """A redirect chain that cycles or leaves the corpus."""


class StaleACL(RuntimeError):
    """The stored ACLs differ from the policy file: run `make acl`."""


def resolve_acls(
    policy: Policy, url_paths: Mapping[str, str], redirects: Mapping[str, str]
) -> dict[str, tuple[str, ...]]:
    """documents.path -> allow-list. url_paths maps every document's path to its url_path;
    redirects maps a stub's path to its normalized target url_path. A stub takes its final
    non-stub target's allow-list; a cycle or a target missing from the corpus is an AclError."""
    by_url = {url: path for path, url in url_paths.items()}
    acls = {}
    for path in url_paths:
        seen = [path]
        while path in redirects:
            target = redirects[path]
            if target not in by_url:
                raise AclError(f"{seen[0]}: redirect target {target} is not in the corpus")
            path = by_url[target]
            if path in seen:
                raise AclError(f"redirect cycle: {' -> '.join([*seen, path])}")
            seen.append(path)
        acls[seen[0]] = resolve(policy, path.removeprefix(CORPUS_PREFIX))
    return acls


def read_redirects(paths: list[str], checkout: Path = CHECKOUT) -> dict[str, str]:
    """documents.path -> normalized `redirect_to:` target, read from the pinned files (the stored
    body has no front matter)."""
    redirects = {}
    for path in paths:
        front_matter, _ = split_front_matter((checkout / path).read_text(encoding="utf-8"))
        if target := derive_redirect(front_matter):
            redirects[path] = target
    return redirects


def _documents(conn) -> dict[str, str]:
    return dict(conn.execute("SELECT path, url_path FROM documents ORDER BY path").fetchall())


def load_policy(conn) -> Policy:
    """The policy, checked for stale rules against the ingested documents (AC-1)."""
    return load(p.removeprefix(CORPUS_PREFIX) for p in _documents(conn))


def expected_acls(conn, policy: Policy, checkout: Path = CHECKOUT) -> dict[str, tuple[str, ...]]:
    """documents.path -> allow-list recomputed from the policy file, redirect stubs resolved
    to their final target (AC-3). The ground truth for AC-5 and for leak (AC-12)."""
    url_paths = _documents(conn)
    return resolve_acls(policy, url_paths, read_redirects(list(url_paths), checkout))


def check_stale(conn, policy: Policy, checkout: Path = CHECKOUT) -> None:
    """AC-5: raises StaleACL, naming `make acl`, if documents.acl_tags or chunks.allowed_groups
    differ from expected_acls()."""
    expected = expected_acls(conn, policy, checkout)
    stored = dict(conn.execute("SELECT path, acl_tags FROM documents").fetchall())
    docs = sorted(p for p, acl in expected.items() if tuple(stored.get(p) or ()) != acl)
    (chunks,) = conn.execute(
        "SELECT count(*) FROM chunks c JOIN documents d USING (doc_id) "
        "WHERE c.allowed_groups IS DISTINCT FROM d.acl_tags"
    ).fetchone()
    if docs or chunks:
        sample = f" (e.g. {docs[0]})" if docs else ""
        raise StaleACL(
            f"stored ACLs differ from {policy.version}: {len(docs)} documents{sample}, "
            f"{chunks} chunks. Run `make acl`."
        )


def apply(conn, acls: Mapping[str, tuple[str, ...]]) -> tuple[int, int]:
    """Write documents.acl_tags, then copy each to its chunks.allowed_groups in every config.
    Idempotent: only differing rows are written. Returns (documents, chunks) changed."""
    with conn.transaction():
        conn.execute("CREATE TEMP TABLE acl_in (path text PRIMARY KEY, acl text[]) ON COMMIT DROP")
        with conn.cursor().copy("COPY acl_in (path, acl) FROM STDIN") as copy:
            for path, acl in acls.items():
                copy.write_row((path, list(acl)))
        docs = conn.execute(
            "UPDATE documents d SET acl_tags = a.acl FROM acl_in a "
            "WHERE d.path = a.path AND d.acl_tags IS DISTINCT FROM a.acl"
        ).rowcount
        chunks = conn.execute(
            "UPDATE chunks c SET allowed_groups = d.acl_tags FROM documents d "
            "WHERE c.doc_id = d.doc_id AND c.allowed_groups IS DISTINCT FROM d.acl_tags"
        ).rowcount
    return docs, chunks


def report(conn, policy: Policy, acls: Mapping[str, tuple[str, ...]]) -> str:
    """The dry run: per-group doc and chunk counts, the share restricted from staff, and each
    fixture persona's visible chunk share, all on the baseline config."""
    counts = dict(
        conn.execute(
            "SELECT d.path, count(*) FROM chunks c JOIN documents d USING (doc_id) "
            "WHERE c.config_id = %s GROUP BY d.path",
            (BASELINE_CONFIG,),
        ).fetchall()
    )
    total = sum(counts.values())
    out = [
        f"policy {policy.version} (sha256 {policy.sha256[:12]}), {len(acls)} documents, "
        f"{total} {BASELINE_CONFIG} chunks",
        "",
        f"{'group':<28} {'docs':>6} {'chunks':>7}",
    ]
    for group in sorted(policy.groups):
        paths = [p for p, acl in acls.items() if group in acl]
        out.append(f"{group:<28} {len(paths):>6} {sum(counts.get(p, 0) for p in paths):>7}")
    hidden = [p for p, acl in acls.items() if "staff" not in acl]
    hidden_chunks = sum(counts.get(p, 0) for p in hidden)
    out += [
        "",
        f"restricted from staff: {len(hidden)} docs / {hidden_chunks} chunks "
        f"({100 * hidden_chunks / total:.2f}%)",
        "",
        f"{'persona':<12} {'visible chunks':>14} {'share':>8}  groups",
    ]
    for user_id in identity.user_ids():
        principal = identity.load(user_id, policy)
        visible = sum(counts.get(p, 0) for p, acl in acls.items() if principal.groups & set(acl))
        out.append(
            f"{user_id:<12} {visible:>14} {100 * visible / total:>7.2f}%  "
            f"{', '.join(principal.group_list)}"
        )
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Resolve the ACL policy onto documents and chunks.")
    ap.add_argument("--confirm", action="store_true", help="write the ACLs (default: dry run)")
    args = ap.parse_args(argv)
    if error := verify(read_manifest()):
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    with connect() as conn:
        policy = load_policy(conn)
        acls = expected_acls(conn, policy)
        print(report(conn, policy, acls))
        if not args.confirm:
            print("\nDry run: nothing written. CONFIRM=1 to apply.")
            return 0
        docs, chunks = apply(conn, acls)
        check_stale(conn, policy)
    print(f"\napplied: {docs} documents and {chunks} chunks changed (all configs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
