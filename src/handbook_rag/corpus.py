"""Reproduce the pinned handbook checkout described in CORPUS.md (spec 0001)."""

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

CHECKOUT = Path("data/handbook")


@dataclass(frozen=True)
class Manifest:
    repo: str
    sha: str
    paths: list[str]
    file_count: int


def read_manifest(path: Path = Path("CORPUS.md")) -> Manifest:
    text = path.read_text()

    def field(name: str) -> str:
        m = re.search(rf"^- {name}: *(\S+)", text, re.MULTILINE)
        if not m:
            raise ValueError(f"{path}: missing '- {name}:' line")
        return m.group(1)

    block = re.search(r"^```sparse\n(.*?)^```", text, re.MULTILINE | re.DOTALL)
    if not block:
        raise ValueError(f"{path}: missing ```sparse block")
    return Manifest(
        repo=field("Source repo"),
        sha=field("Snapshot commit SHA"),
        paths=block.group(1).split(),
        file_count=int(field("File count")),
    )


def count_md(checkout: Path, paths: list[str]) -> int:
    return sum(1 for p in paths for _ in (checkout / p).rglob("*.md"))


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(CHECKOUT), *args], check=True, text=True)


def git_out(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(CHECKOUT), *args], check=True, capture_output=True, text=True
    ).stdout


def main() -> int:
    m = read_manifest()
    if not (CHECKOUT / ".git").exists():
        CHECKOUT.parent.mkdir(exist_ok=True)
        subprocess.run(
            ["git", "clone", "--filter=blob:none", "--no-checkout", m.repo, str(CHECKOUT)],
            check=True,
        )
    has_sha = subprocess.run(
        ["git", "-C", str(CHECKOUT), "cat-file", "-e", f"{m.sha}^{{commit}}"],
        capture_output=True,
    )
    if has_sha.returncode != 0:
        git("fetch", "origin", m.sha)
    git("sparse-checkout", "set", "--cone", *m.paths)
    git("checkout", "--quiet", "--detach", m.sha)

    error = verify(m)
    if error:
        print(error, file=sys.stderr)
        return 1
    print(f"corpus ok: {CHECKOUT} at {m.sha}, {m.file_count} .md files")
    return 0


def verify(m: Manifest) -> str | None:
    """Return why the checkout doesn't match the pin, or None if it does."""
    head = git_out("rev-parse", "HEAD").strip()
    if head != m.sha:
        return f"HEAD {head} != pinned {m.sha}"
    dirty = git_out("status", "--porcelain")
    if dirty:
        return f"{CHECKOUT} has local changes; corpus must match the pin:\n{dirty}"
    n = count_md(CHECKOUT, m.paths)
    if n != m.file_count:
        return f"found {n} .md files, CORPUS.md expects {m.file_count}"
    return None


if __name__ == "__main__":
    sys.exit(main())
