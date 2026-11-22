
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("healthcare.db")


class DatabaseUnavailableError(Exception):
    """Raised when a SQLite database operation fails."""
    pass


def get_appointment_count(patient_id):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT appointment_count FROM patients WHERE patient_id = ?",
                (patient_id,)
            )

            result = cursor.fetchone()

    except sqlite3.Error as error:
        raise DatabaseUnavailableError(
            "Database temporarily unavailable"
        ) from error

    if result is None:
        return {"error": "Patient not found"}

    return {"appointment_count": result[0]}


def get_patient_status(patient_id):
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT patient_status FROM patients WHERE patient_id = ?",
                (patient_id,)
            )

            result = cursor.fetchone()

    except sqlite3.Error as error:
        raise DatabaseUnavailableError(
            "Database temporarily unavailable"
        ) from error

    if result is None:
        return {"error": "Patient not found"}

    return {"patient_status": result[0]}


def get_all_patients():
    try:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT patient_id, appointment_count, patient_status
                FROM patients
                ORDER BY patient_id
                """
            )

            rows = cursor.fetchall()

    except sqlite3.Error as error:
        raise DatabaseUnavailableError(
            "Database temporarily unavailable"
        ) from error

    patients = []

    for row in rows:
        patients.append({
            "id": row[0],
            "appointments": row[1],
            "status": row[2]
        })

    return {"patients": patients}
