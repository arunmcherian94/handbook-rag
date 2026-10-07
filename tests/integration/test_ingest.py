import re
from datetime import datetime
from pathlib import Path

import psycopg
import pytest

from handbook_rag.corpus import CHECKOUT, read_manifest
from handbook_rag.db import connect
from handbook_rag.ingest import run, split_front_matter

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[2]
EXPENSES = "content/handbook/finance/expenses.md"


@pytest.fixture(scope="module")
def ingested():
    """Run ingestion twice against the real DB; yield (conn, first scan, second scan)."""
    mp = pytest.MonkeyPatch()
    mp.chdir(ROOT)
    if not (CHECKOUT / ".git").exists():
        pytest.fail("Corpus checkout missing. Run `make corpus` first.")
    try:
        conn = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    with conn:
        first = run(conn)
        first_rows = conn.execute("SELECT count(*) FROM documents").fetchone()[0]
        second = run(conn)
        yield conn, first, first_rows, second
    mp.undo()


def test_idempotent(ingested):
    """AC-3: rerun gives the same row count and no duplicates."""
    conn, first, first_rows, second = ingested
    rows, distinct = conn.execute("SELECT count(*), count(DISTINCT path) FROM documents").fetchone()
    assert rows == first_rows == distinct == len(second.docs) == len(first.docs)


def test_counts_match_corpus(ingested):
    """AC-6: files found equals CORPUS.md; every found file is ingested or skipped."""
    conn, _, _, scan = ingested
    rows = conn.execute("SELECT count(*) FROM documents").fetchone()[0]
    assert scan.found == read_manifest(ROOT / "CORPUS.md").file_count
    assert len(scan.docs) + len(scan.skipped) == scan.found
    assert rows + len(scan.skipped) == scan.found


def test_expenses_present_in_full(ingested):
    """AC-7: the Expenses doc is stored unabridged, including sections 3 and 4.1."""
    conn, _, _, _ = ingested
    body, url_path, sha, commit_date = conn.execute(
        "SELECT body, url_path, commit_sha, commit_date FROM documents WHERE path = %s",
        (EXPENSES,),
    ).fetchone()
    _, expected = split_front_matter((ROOT / CHECKOUT / EXPENSES).read_text())
    assert body == expected
    for heading in (
        "## 3. General Guidelines",
        "### 4.1 NON-TRAVEL RELATED EXPENSES",
        "#### Co-Working Space - Monthly",
        "### Internet",
    ):
        assert heading in body
    assert url_path == "/handbook/finance/expenses/"
    assert sha == read_manifest(ROOT / "CORPUS.md").sha
    snapshot = re.search(r"^- Snapshot date: *(\S+)", (ROOT / "CORPUS.md").read_text(), re.M)
    assert commit_date == datetime.fromisoformat(snapshot.group(1))
