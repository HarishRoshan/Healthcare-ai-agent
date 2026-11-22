
import sqlite3

import pytest
from pydantic import ValidationError

import healthcare_tools
from healthcare_validation import PatientInput
from healthcare_tools import (
    get_appointment_count,
    get_patient_status
)


# TOPIC 1: TEMPORARY TEST DATABASE
@pytest.fixture(autouse=True)
def test_database(tmp_path, monkeypatch):
    # Create a temporary database path
    database_path = tmp_path / "test_healthcare.db"

    # Redirect healthcare tools to the test database
    monkeypatch.setattr(
        healthcare_tools,
        "DB_PATH",
        database_path
    )

    # Create the patients table
    with sqlite3.connect(database_path) as connection:
        connection.execute("""
            CREATE TABLE patients (
                patient_id INTEGER PRIMARY KEY,
                appointment_count INTEGER,
                patient_status TEXT
            )
        """)

        # Insert predictable fictional test data
        connection.executemany(
            """
            INSERT INTO patients
            (patient_id, appointment_count, patient_status)
            VALUES (?, ?, ?)
            """,
            [
                (101, 2, "Active"),
                (102, 3, "Active"),
                (103, 1, "Inactive")
            ]
        )

        connection.commit()


# TOPIC 2: REUSABLE PATIENT FIXTURE
@pytest.fixture
def sample_patient():
    return {
        "patient_id": 102,
        "appointment_count": 3,
        "status": "Active"
    }


# TOPIC 3: PARAMETERIZED TESTING
@pytest.mark.parametrize(
    "patient_id, expected_count",
    [
        (101, 2),
        (102, 3),
        (103, 1)
    ]
)
def test_appointments(patient_id, expected_count):
    result = get_appointment_count(patient_id)

    assert result == {
        "appointment_count": expected_count
    }


def test_patient_103_status():
    result = get_patient_status(103)

    assert result == {
        "patient_status": "Inactive"
    }


def test_unknown_patient():
    result = get_appointment_count(999)

    assert result == {
        "error": "Patient not found"
    }


def test_unknown_patient_status():
    result = get_patient_status(999)

    assert result == {
        "error": "Patient not found"
    }


def test_fixture_appointments(sample_patient):
    result = get_appointment_count(
        sample_patient["patient_id"]
    )

    assert result == {
        "appointment_count": sample_patient["appointment_count"]
    }


def test_fixture_status(sample_patient):
    result = get_patient_status(
        sample_patient["patient_id"]
    )

    assert result == {
        "patient_status": sample_patient["status"]
    }


# TOPIC 4: PYDANTIC VALIDATION
def test_negative_patient_id():
    with pytest.raises(ValidationError):
        PatientInput(patient_id=-5)


def test_string_patient_id():
    with pytest.raises(ValidationError):
        PatientInput(patient_id="hello")


def test_valid_patient_id():
    patient = PatientInput(patient_id=102)

    assert patient.patient_id == 102
