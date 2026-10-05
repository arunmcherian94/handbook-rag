import os

import psycopg
import pytest

pytestmark = pytest.mark.integration

HINT = "Database unreachable. Run `cp .env.example .env && make up` first."


@pytest.fixture(scope="module")
def conn():
    try:
        c = psycopg.connect(
            host="localhost",
            port=os.environ["POSTGRES_PORT"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            dbname=os.environ["POSTGRES_DB"],
            connect_timeout=3,
        )
    except (KeyError, psycopg.OperationalError) as e:
        pytest.fail(f"{HINT} ({type(e).__name__}: {e})")
    with c:
        yield c


def test_vector_extension_installed(conn):
    row = conn.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'").fetchone()
    assert row is not None


def test_cosine_distance(conn):
    (dist,) = conn.execute("SELECT '[1,0,0]'::vector <=> '[0,1,0]'::vector").fetchone()
    assert dist == pytest.approx(1.0)
