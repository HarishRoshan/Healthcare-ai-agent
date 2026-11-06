
from healthcare_tools import (
    get_appointment_count,
    get_patient_status
)


# Test 1: Existing patient's appointments
def test_patient_102_appointments():
    result = get_appointment_count(102)
    assert result == {"appointment_count": 3}


# Test 2: Another patient's appointments
def test_patient_101_appointments():
    result = get_appointment_count(101)
    assert result == {"appointment_count": 2}


# Test 3: Patient status
def test_patient_103_status():
    result = get_patient_status(103)
    assert result == {"patient_status": "Inactive"}


# Test 4: Unknown patient
def test_unknown_patient():
    result = get_appointment_count(999)
    assert result == {"error": "Patient not found"}


# Test 5: Unknown patient's status
def test_unknown_patient_status():
    result = get_patient_status(999)
    assert result == {"error": "Patient not found"}
