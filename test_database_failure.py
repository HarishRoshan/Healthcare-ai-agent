
from unittest.mock import patch

from fastapi.testclient import TestClient

from healthcare_api import app, verify_session
from healthcare_tools import DatabaseUnavailableError


def test_database_failure_returns_503():
    # Override authentication only for this test
    app.dependency_overrides[verify_session] = lambda: "test_user"

    try:
        with TestClient(app) as client:
            # Simulate the database tool failing
            with patch(
                "healthcare_api.get_appointment_count",
                side_effect=DatabaseUnavailableError(
                    "Database temporarily unavailable"
                )
            ):
                response = client.get(
                    "/patients/101/appointments"
                )

        # Verify the API responds safely
        assert response.status_code == 503

        assert response.json() == {
            "detail": "Patient information temporarily unavailable"
        }

    finally:
        # Restore normal authentication behaviour
        app.dependency_overrides.pop(verify_session, None)

def test_agent_database_failure_returns_503():
    app.dependency_overrides[verify_session] = lambda: "test_user"

    try:
        with TestClient(app) as client:
            with patch(
                "healthcare_api.ask_healthcare_agent",
                side_effect=DatabaseUnavailableError(
                    "Database temporarily unavailable"
                ),
            ):
                response = client.post(
                    "/agent/ask",
                    json={
                        "question": "How many appointments does patient 101 have?"
                    },
                )

        assert response.status_code == 503

        assert response.json() == {
            "detail": "Patient information temporarily unavailable"
        }

    finally:
        app.dependency_overrides.pop(verify_session, None)
