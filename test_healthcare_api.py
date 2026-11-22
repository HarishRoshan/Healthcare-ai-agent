
import os
from unittest.mock import patch

os.environ.setdefault(
    "OPENAI_API_KEY",
    "test-key-not-for-real-requests"
)

from fastapi.testclient import TestClient
from healthcare_api import app


client = TestClient(app)


# TEST 1: Home endpoint.
def test_home_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    assert response.json() == {
        "message": "Healthcare API is running!"
    }


# TEST 2: Patient 102 appointments.
def test_patient_102_appointments(test_database):
    response = client.get(
        "/patients/102/appointments"
    )

    assert response.status_code == 200
    assert response.json()["appointment_count"] == 4


# TEST 3: Unknown patient.
def test_unknown_patient(test_database):
    response = client.get(
        "/patients/999999/appointments"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found"


# TEST 4: Invalid negative patient ID.
def test_invalid_patient_id(test_database):
    response = client.get(
        "/patients/-1/status"
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Patient ID must be positive"
    )


# TEST 5: Database-driven patient list.
def test_patient_list(test_database):
    response = client.get("/patients")

    assert response.status_code == 200

    patients = response.json()["patients"]

    assert isinstance(patients, list)

    patient_ids = [
        patient["id"]
        for patient in patients
    ]

    assert 101 in patient_ids
    assert 102 in patient_ids
    assert 103 in patient_ids
    assert 104 in patient_ids


# TEST 6: Patient 103 status.
def test_patient_103_status(test_database):
    response = client.get("/patients/103/status")

    assert response.status_code == 200
    assert response.json()["patient_status"] == "Inactive"


# TEST 7: Reject an empty AI question.
def test_empty_agent_question():
    response = client.post(
        "/agent/ask",
        json={"question": ""}
    )

    assert response.status_code == 422


# TEST 8: Mock the AI agent.
def test_agent_with_mock():

    with patch(
        "healthcare_api.ask_healthcare_agent",
        return_value="Mock AI response"
    ) as mock_agent:

        response = client.post(
            "/agent/ask",
            json={"question": "Hello"}
        )

        assert response.status_code == 200

        mock_agent.assert_called_once_with("Hello")

        assert "Mock AI response" in str(response.json())
