import os

import psycopg


def connect() -> psycopg.Connection:
    """Connect to the docker DB using the POSTGRES_* variables from .env."""
    return psycopg.connect(
        host="localhost",
        port=os.environ["POSTGRES_PORT"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        dbname=os.environ["POSTGRES_DB"],
        connect_timeout=3,
    )


def vector_literal(v: list[float]) -> str:
    """pgvector text input, sent as a parameter and cast with ::vector (no numpy adapter)."""
    return "[" + ",".join(repr(float(x)) for x in v) + "]"
