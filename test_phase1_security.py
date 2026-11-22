
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# The tests never call OpenAI.
# A placeholder permits importing the agent module.
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")

from fastapi.testclient import TestClient

import audit_logger
import healthcare_api
import healthcare_agent


class Phase1SecurityTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.audit_patch = patch.object(
            audit_logger,
            "AUDIT_DB",
            Path(self.temp_dir.name) / "test_audit.db",
        )
        self.audit_patch.start()

        self.env_patch = patch.dict(
            os.environ,
            {
                "AURA_DEMO_USERNAME": "aura_demo",
                "AURA_DEMO_PASSWORD": "test-password-12345",
                "AURA_SESSION_SECRET": "a" * 40,
            },
        )
        self.env_patch.start()

        self.client = TestClient(
            healthcare_api.app,
            raise_server_exceptions=False,
        )

    def tearDown(self):
        self.client.close()
        self.env_patch.stop()
        self.audit_patch.stop()
        self.temp_dir.cleanup()

    def login(self):
        response = self.client.post(
            "/auth/login",
            json={
                "username": "aura_demo",
                "password": "test-password-12345",
            },
        )
        self.assertEqual(response.status_code, 200)


    def audit_rows(self):
        db_path = audit_logger.AUDIT_DB

        if not db_path.exists():
            return []

        connection = sqlite3.connect(db_path)

        try:
            return connection.execute(
                """
                SELECT username, patient_id, action,
                       outcome, source
                FROM audit_events
                ORDER BY id
                """
            ).fetchall()
        finally:
            connection.close()


    def test_01_unauthenticated_access_denied(self):
        response = self.client.get(
            "/patients/101/appointments"
        )
        self.assertEqual(response.status_code, 401)

    def test_02_invalid_login_denied(self):
        response = self.client.post(
            "/auth/login",
            json={
                "username": "aura_demo",
                "password": "incorrect-password",
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_03_api_patient_102_denied_and_logged(self):
        self.login()

        response = self.client.get(
            "/patients/102/appointments"
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn(
            (
                "aura_demo",
                102,
                "view_appointments",
                "denied",
                "api",
            ),
            self.audit_rows(),
        )

    def test_04_api_patient_101_allowed_and_logged(self):
        self.login()

        with patch.object(
            healthcare_api,
            "get_appointment_count",
            return_value={
                "patient_id": 101,
                "appointments": 2,
            },
        ):
            response = self.client.get(
                "/patients/101/appointments"
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            (
                "aura_demo",
                101,
                "view_appointments",
                "allowed",
                "api",
            ),
            self.audit_rows(),
        )

    def test_05_agent_patient_102_denied_and_logged(self):
        with patch.object(
            healthcare_agent,
            "get_appointment_count",
        ) as database_tool:
            result = healthcare_agent.execute_tool(
                "get_appointment_count",
                '{"patient_id": 102}',
                allowed_patient_ids={101},
                username="aura_demo",
            )

            database_tool.assert_not_called()

        self.assertEqual(result["error"], "Access denied")
        self.assertIn(
            (
                "aura_demo",
                102,
                "get_appointment_count",
                "denied",
                "agent",
            ),
            self.audit_rows(),
        )

    def test_06_agent_patient_101_allowed_and_logged(self):
        with patch.object(
            healthcare_agent,
            "get_appointment_count",
            return_value={
                "patient_id": 101,
                "appointments": 2,
            },
        ) as database_tool:
            result = healthcare_agent.execute_tool(
                "get_appointment_count",
                '{"patient_id": 101}',
                allowed_patient_ids={101},
                username="aura_demo",
            )

            database_tool.assert_called_once_with(101)

        self.assertEqual(result["appointments"], 2)
        self.assertIn(
            (
                "aura_demo",
                101,
                "get_appointment_count",
                "allowed",
                "agent",
            ),
            self.audit_rows(),
        )

    def test_07_agent_without_username_denied(self):
        result = healthcare_agent.execute_tool(
            "get_patient_status",
            '{"patient_id": 101}',
            allowed_patient_ids={101},
        )
        self.assertEqual(result["error"], "Access denied")

    def test_08_invalid_session_denied(self):
        self.client.cookies.set(
            healthcare_api.COOKIE_NAME,
            "invalid.token",
        )
        response = self.client.get("/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_09_unexpected_error_is_safe(self):
        self.login()

        with patch.object(
            healthcare_api,
            "get_all_patients",
            side_effect=Exception("SECRET_INTERNAL_DETAIL"),
        ):
            response = self.client.get("/patients")

        self.assertEqual(response.status_code, 500)
        self.assertNotIn(
            "SECRET_INTERNAL_DETAIL",
            response.text,
        )

    def test_10_audit_failure_blocks_patient_access(self):
        self.login()

        with patch.object(
            healthcare_api,
            "log_audit_event",
            side_effect=OSError("Audit storage unavailable"),
        ):
            with patch.object(
                healthcare_api,
                "get_appointment_count",
            ) as database_tool:
                response = self.client.get(
                    "/patients/101/appointments"
                )
                database_tool.assert_not_called()

        self.assertEqual(response.status_code, 500)


if __name__ == "__main__":
    unittest.main(verbosity=2)
