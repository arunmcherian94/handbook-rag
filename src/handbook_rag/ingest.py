"""Load the pinned handbook checkout into the documents table (spec 0002)."""

import re
import sys
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from handbook_rag.corpus import CHECKOUT, git_out, read_manifest, verify
from handbook_rag.db import connect

SCHEMA = Path("db/init/002_documents.sql")
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n?", re.DOTALL)


@dataclass(frozen=True)
class Doc:
    doc_id: uuid.UUID
    path: str
    url_path: str
    title: str
    body: str


@dataclass
class Scan:
    found: int = 0
    docs: list[Doc] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)  # (reason, path)


def split_front_matter(text: str) -> tuple[str, str]:
    m = FRONT_MATTER.match(text)
    return (m.group(1), text[m.end() :]) if m else ("", text)


def derive_title(front_matter: str, body: str, path: str) -> str:
    m = re.search(r"^title:[ \t]*(.+?)[ \t]*$", front_matter, re.MULTILINE | re.IGNORECASE)
    if m and m.group(1).strip("\"'"):
        return m.group(1).strip("\"'")
    m = re.search(r"^# +(.+?)[ \t]*$", body, re.MULTILINE)
    if m:
        return m.group(1)
    p = Path(path)
    return p.parent.name if p.name in ("_index.md", "index.md") else p.stem


def derive_url_path(path: str) -> str:
    """content/handbook/a/b.md -> /handbook/a/b/; _index.md and index.md map to the directory.

    Lowercased, as Hugo does by default (the mixed-case URL 302-redirects on the live site).
    """
    p = Path(path).relative_to("content")
    parts = p.parent.parts if p.name in ("_index.md", "index.md") else (*p.parent.parts, p.stem)
    return "/" + "".join(f"{part}/" for part in parts).lower()


def skip_reason(front_matter: str, body: str) -> str | None:
    if re.search(r"^draft:[ \t]*true\b", front_matter, re.MULTILINE | re.IGNORECASE):
        return "draft"
    if not body.strip():
        return "empty_body"
    return None


def scan(checkout: Path, paths: list[str]) -> Scan:
    result = Scan()
    for file in sorted(f for p in paths for f in (checkout / p).rglob("*.md")):
        result.found += 1
        rel = file.relative_to(checkout).as_posix()
        try:
            text = file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            result.skipped.append(("decode_error", rel))
            continue
        front_matter, body = split_front_matter(text)
        reason = skip_reason(front_matter, body)
        if reason:
            result.skipped.append((reason, rel))
            continue
        result.docs.append(
            Doc(
                doc_id=uuid.uuid5(uuid.NAMESPACE_URL, rel),
                path=rel,
                url_path=derive_url_path(rel),
                title=derive_title(front_matter, body, rel),
                body=body,
            )
        )
    return result


UPSERT = """
INSERT INTO documents (doc_id, path, url_path, title, body, commit_sha, commit_date)
VALUES (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (doc_id) DO UPDATE SET
    path = EXCLUDED.path, url_path = EXCLUDED.url_path, title = EXCLUDED.title,
    body = EXCLUDED.body, commit_sha = EXCLUDED.commit_sha,
    commit_date = EXCLUDED.commit_date, ingested_at = now()
"""


def run(conn) -> Scan:
    m = read_manifest()
    error = verify(m)
    if error:
        raise SystemExit(f"{error}\nRun `make corpus` to restore the pinned checkout.")
    commit_date = git_out("show", "-s", "--format=%cI", m.sha).strip()

    result = scan(CHECKOUT, m.paths)
    with conn.transaction():
        conn.execute(SCHEMA.read_text())
        with conn.cursor() as cur:
            cur.executemany(
                UPSERT,
                [
                    (d.doc_id, d.path, d.url_path, d.title, d.body, m.sha, commit_date)
                    for d in result.docs
                ],
            )
        # Mirror the snapshot: drop rows for files no longer present or now skipped.
        conn.execute(
            "DELETE FROM documents WHERE doc_id <> ALL(%s)", ([d.doc_id for d in result.docs],)
        )
    return result


def main() -> int:
    with connect() as conn:
        result = run(conn)
    for reason, path in result.skipped:
        print(f"skip {reason} {path}")
    reasons = ", ".join(f"{r} {n}" for r, n in Counter(r for r, _ in result.skipped).items())
    print(
        f"found {result.found}, ingested {len(result.docs)}, "
        f"skipped {len(result.skipped)} ({reasons or 'none'})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
