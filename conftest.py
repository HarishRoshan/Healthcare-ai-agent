
import os
import sqlite3

import pytest

# Set a dummy key only if no key exists.
# The tests do not make real OpenAI requests.
os.environ.setdefault(
    "OPENAI_API_KEY",
    "test-key-not-for-real-requests"
)

import healthcare_tools


@pytest.fixture
def test_database(tmp_path, monkeypatch):

    # Create a temporary SQLite database path.
    test_db_path = tmp_path / "test_healthcare.db"

    # Create the database and patients table.
    with sqlite3.connect(test_db_path) as connection:

        connection.execute("""
            CREATE TABLE patients (
                patient_id INTEGER PRIMARY KEY,
                appointment_count INTEGER,
                patient_status TEXT
            )
        """)

        # Insert predictable fictional records.
        connection.executemany(
            """
            INSERT INTO patients (
                patient_id,
                appointment_count,
                patient_status
            )
            VALUES (?, ?, ?)
            """,
            [
                (101, 2, "Active"),
                (102, 4, "Active"),
                (103, 1, "Inactive"),
                (104, 3, "Active"),
                (501, 6, "Active")
            ]
        )

        connection.commit()

    # Redirect the database tools to this temporary file.
    monkeypatch.setattr(
        healthcare_tools,
        "DB_PATH",
        test_db_path
    )

    return test_db_path
