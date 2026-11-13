import pytest

from pydantic import ValidationError
from healthcare_validation import PatientInput

from healthcare_tools import (
    get_appointment_count,
    get_patient_status
)
# TOPIC 2: FIXTURES
# Prepare reusable fictional patient data
@pytest.fixture
def sample_patient():
    return {
        "patient_id": 102,
        "appointment_count": 3,
        "status": "Active"
    }


# TOPIC 1: PARAMETERIZATION
# Test multiple patients using one function
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


# Test patient status
def test_patient_103_status():
    result = get_patient_status(103)

    assert result == {
        "patient_status": "Inactive"
    }


# Test unknown patient appointments
def test_unknown_patient():
    result = get_appointment_count(999)

    assert result == {
        "error": "Patient not found"
    }


# Test unknown patient status
def test_unknown_patient_status():
    result = get_patient_status(999)

    assert result == {
        "error": "Patient not found"
    }


# TOPIC 2: USING FIXTURES
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


# TOPIC 3: TESTING INVALID INPUTS
# Negative patient ID must be rejected
def test_negative_patient_id():
    with pytest.raises(ValidationError):
        PatientInput(patient_id=-5)


# String patient ID must be rejected
def test_string_patient_id():
    with pytest.raises(ValidationError):
        PatientInput(patient_id="hello")


# Valid patient ID must be accepted
def test_valid_patient_id():
    patient = PatientInput(patient_id=102)

    assert patient.patient_id == 102
