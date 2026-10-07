import re
from pathlib import Path

from handbook_rag.corpus import read_manifest

ROOT = Path(__file__).resolve().parents[2]


def test_manifest_parses():
    """Spec 0001 AC-3: CORPUS.md is machine-readable."""
    m = read_manifest(ROOT / "CORPUS.md")
    assert m.repo.startswith("https://")
    assert re.fullmatch(r"[0-9a-f]{40}", m.sha)
    assert m.paths
    assert m.file_count > 0
