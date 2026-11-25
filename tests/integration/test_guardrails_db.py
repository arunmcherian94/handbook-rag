"""Corpus checks for the guardrails (spec 0014 AC-4, AC-14). Read-only SELECTs."""

from collections import Counter

import psycopg
import pytest

from handbook_rag.agent import guardrails
from handbook_rag.constants import BASELINE_CONFIG
from handbook_rag.db import connect

pytestmark = pytest.mark.integration


@pytest.fixture
def conn():
    try:
        c = connect()
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"Database unreachable. Run `make up` first. ({type(e).__name__}: {e})")
    with c:
        yield c


def test_fixture_marker_is_not_in_the_corpus(conn):
    """AC-14: GR-FIXTURE- (the injection fixtures' marker) matches no chunk."""
    (n,) = conn.execute("SELECT count(*) FROM chunks WHERE content LIKE '%GR-FIXTURE-%'").fetchone()
    assert n == 0


def test_injection_patterns_false_positive_rate(conn):
    """AC-4: each pattern matches at most 0.1% of the fixed-512-64 chunks."""
    rows = conn.execute(
        "SELECT content, heading FROM chunks WHERE config_id = %s", (BASELINE_CONFIG,)
    ).fetchall()
    if not rows:
        pytest.skip(f"no chunks for config {BASELINE_CONFIG}")
    counts: Counter[str] = Counter()
    for content, heading in rows:
        reasons = set(guardrails.scan_injection(content))
        if heading:
            reasons |= set(guardrails.scan_injection(heading))
        counts.update(reasons)
    total = len(rows)
    limit = total // 1000
    print(f"\nchunks ({BASELINE_CONFIG}): {total}; limit per reason: {limit}")
    for reason in guardrails.PATTERN_REASONS:
        print(f"{reason}: {counts[reason]}")
    assert total > 0
    assert BASELINE_CONFIG == "fixed-512-64"
    assert {r: n for r, n in counts.items() if n > limit} == {}
