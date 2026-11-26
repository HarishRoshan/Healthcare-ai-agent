
import os

os.environ.setdefault(
    "OPENAI_API_KEY",
    "test-key-not-for-real-requests"
)

from fastapi.testclient import TestClient

import healthcare_api
import audit_logger


# Verify authenticated access to an isolated database.
def test_isolated_patient_appointments(
    test_database,
    monkeypatch,
    tmp_path
):
    # Configure temporary test credentials.
    monkeypatch.setenv(
        "AURA_DEMO_USERNAME", "aura_demo"
    )
    monkeypatch.setenv(
        "AURA_DEMO_PASSWORD", "test-password-12345"
    )
    monkeypatch.setenv(
        "AURA_SESSION_SECRET", "a" * 40
    )

    # Isolate audit records.
    monkeypatch.setattr(
        audit_logger,
        "AUDIT_DB",
        tmp_path / "test_audit.db"
    )

    # Grant access to fictional patient 501
    # for this test only.
    monkeypatch.setitem(
        healthcare_api.DEMO_PATIENT_ACCESS,
        "aura_demo",
        {501}
    )

    with TestClient(
        healthcare_api.app,
        base_url="https://testserver"
    ) as client:

        # Authenticate the test user.
        login_response = client.post(
            "/auth/login",
            json={
                "username": "aura_demo",
                "password": "test-password-12345"
            }
        )

        assert login_response.status_code == 200

        # Retrieve data from the isolated database.
        response = client.get(
            "/patients/501/appointments"
        )

        assert response.status_code == 200
        assert response.json()["appointment_count"] == 6
