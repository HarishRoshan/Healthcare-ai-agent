
import os
from contextlib import contextmanager

import psycopg
from dotenv import load_dotenv


load_dotenv()


def get_database_backend():
    backend = os.getenv(
        "AURA_DB_BACKEND", "sqlite"
    ).strip().lower()

    if backend not in {"sqlite", "postgresql"}:
        raise ValueError("Unsupported database backend")

    return backend


def using_postgresql():
    return get_database_backend() == "postgresql"


@contextmanager
def postgres_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    with psycopg.connect(
        database_url,
        sslmode="require",
        connect_timeout=10,
    ) as connection:
        yield connection
