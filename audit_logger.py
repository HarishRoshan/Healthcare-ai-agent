
import os
import sqlite3
import psycopg

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from aura_database import (
    using_postgresql,
    postgres_connection,
)


AUDIT_DB = Path(
    os.environ.get(
        "AURA_AUDIT_DB_PATH",
        str(Path(__file__).resolve().parent / "aura_audit.db")
    )
)


def initialize_audit_database():

    if using_postgresql():
        return

    with closing(sqlite3.connect(AUDIT_DB, timeout=5)) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                username TEXT NOT NULL,
                patient_id INTEGER,
                action TEXT NOT NULL,
                outcome TEXT NOT NULL,
                source TEXT NOT NULL
            )
        """)
        connection.commit()


def log_audit_event(
    username,
    patient_id,
    action,
    outcome,
    source,
):
    if outcome not in {"allowed", "denied"}:
        raise ValueError("Invalid audit outcome")

    if source not in {"api", "agent"}:
        raise ValueError("Invalid audit source")

    timestamp = datetime.now(timezone.utc).isoformat()

    values = (
        timestamp,
        username,
        patient_id,
        action,
        outcome,
        source,
    )

    if using_postgresql():
        try:
            with postgres_connection() as connection:
                connection.execute("""
                    INSERT INTO public.audit_events (
                        timestamp,
                        username,
                        patient_id,
                        action,
                        outcome,
                        source
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, values)

        except psycopg.Error as error:
            raise RuntimeError(
                "Audit database unavailable"
            ) from error

        return

    initialize_audit_database()

    with closing(sqlite3.connect(AUDIT_DB, timeout=5)) as connection:
        connection.execute("""
            INSERT INTO audit_events (
                timestamp,
                username,
                patient_id,
                action,
                outcome,
                source
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, values)

        connection.commit()
