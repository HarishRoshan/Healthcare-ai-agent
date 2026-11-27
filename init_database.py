
import os
import sqlite3
from pathlib import Path


DATABASE_PATH = Path(
    os.environ.get(
        "AURA_DATABASE_PATH",
        str(Path(__file__).with_name("healthcare.db"))
    )
)


def initialize_database():
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id INTEGER PRIMARY KEY,
                appointment_count INTEGER,
                patient_status TEXT
            )
        """)

        patients = [
            (101, 2, "Active"),
            (102, 4, "Active"),
            (103, 1, "Inactive")
        ]

        connection.executemany("""
            INSERT OR IGNORE INTO patients
            (patient_id, appointment_count, patient_status)
            VALUES (?, ?, ?)
        """, patients)

    print("AURA database initialized successfully.")


if __name__ == "__main__":
    initialize_database()
