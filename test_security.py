
import os

os.environ.setdefault(
    "OPENAI_API_KEY",
    "test-key-not-for-real-requests"
)

from fastapi.testclient import TestClient
from healthcare_api import app


client = TestClient(app)


# TEST 10: Reject requests without an API key.
def test_missing_api_key(monkeypatch):
    monkeypatch.setenv("AURA_AUTH_ENABLED", "true")
    monkeypatch.setenv("AURA_API_KEY", "test-secret-key")

    response = client.get("/patients")

    assert response.status_code == 401


# TEST 11: Reject requests with an invalid API key.
def test_invalid_api_key(monkeypatch):
    monkeypatch.setenv("AURA_AUTH_ENABLED", "true")
    monkeypatch.setenv("AURA_API_KEY", "test-secret-key")

    response = client.get(
        "/patients",
        headers={"X-API-Key": "wrong-key"}
    )

    assert response.status_code == 401


# TEST 12: Accept a valid API key.
def test_valid_api_key(monkeypatch, test_database):
    monkeypatch.setenv("AURA_AUTH_ENABLED", "true")
    monkeypatch.setenv("AURA_API_KEY", "test-secret-key")

    response = client.get(
        "/patients",
        headers={"X-API-Key": "test-secret-key"}
    )

    assert response.status_code == 200

    patients = response.json()["patients"]

    assert isinstance(patients, list)
    assert len(patients) == 5
