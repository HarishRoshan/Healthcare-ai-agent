
import os

os.environ.setdefault(
    "OPENAI_API_KEY",
    "test-key-not-for-real-requests"
)

from fastapi.testclient import TestClient
from healthcare_api import app


client = TestClient(app)


# TEST 9: Verify isolated database access.
def test_isolated_patient_appointments(test_database):

    response = client.get(
        "/patients/501/appointments"
    )

    assert response.status_code == 200

    assert response.json()["appointment_count"] == 6
