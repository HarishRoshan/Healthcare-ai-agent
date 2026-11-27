
import os
import sqlite3
import psycopg

from pathlib import Path
from contextlib import closing

from aura_database import (
    using_postgresql,
    postgres_connection,
)


DB_PATH = Path(
    os.environ.get(
        "AURA_DATABASE_PATH",
        str(Path(__file__).with_name("healthcare.db"))
    )
)


class DatabaseUnavailableError(Exception):
    """Raised when a database operation fails."""
    pass


def _fetch_patient_data(sql, params=(), fetch_all=False):

    try:
        if using_postgresql():
            with postgres_connection() as connection:
                cursor = connection.execute(
                    sql.replace("?", "%s"),
                    params,
                )

                return (
                    cursor.fetchall()
                    if fetch_all
                    else cursor.fetchone()
                )

        with closing(sqlite3.connect(DB_PATH)) as connection:
            cursor = connection.execute(sql, params)

            return (
                cursor.fetchall()
                if fetch_all
                else cursor.fetchone()
            )

    except (sqlite3.Error, psycopg.Error, RuntimeError) as error:
        raise DatabaseUnavailableError(
            "Database temporarily unavailable"
        ) from error


def get_appointment_count(patient_id):

    result = _fetch_patient_data(
        "SELECT appointment_count FROM patients WHERE patient_id = ?",
        (patient_id,),
    )

    if result is None:
        return {"error": "Patient not found"}

    return {"appointment_count": result[0]}


def get_patient_status(patient_id):

    result = _fetch_patient_data(
        "SELECT patient_status FROM patients WHERE patient_id = ?",
        (patient_id,),
    )

    if result is None:
        return {"error": "Patient not found"}

    return {"patient_status": result[0]}


def get_all_patients():

    rows = _fetch_patient_data(
        """
        SELECT patient_id, appointment_count, patient_status
        FROM patients
        ORDER BY patient_id
        """,
        fetch_all=True,
    )

    patients = []

    for row in rows:
        patients.append({
            "id": row[0],
            "appointments": row[1],
            "status": row[2],
        })

    return {"patients": patients}
