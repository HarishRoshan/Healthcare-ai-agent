
import pytest
from fastapi.testclient import TestClient

import healthcare_api
from aura_rate_limiter import SlidingWindowRateLimiter


@pytest.fixture
def client(monkeypatch):

    monkeypatch.setattr(
        healthcare_api, "RATE_LIMIT_ENABLED", True
    )

    monkeypatch.setattr(
        healthcare_api,
        "rate_limiter",
        SlidingWindowRateLimiter(),
    )

    monkeypatch.setenv(
        "AURA_DEMO_USERNAME", "aura_demo"
    )
    monkeypatch.setenv(
        "AURA_DEMO_PASSWORD", "test-password-12345"
    )
    monkeypatch.setenv(
        "AURA_SESSION_SECRET", "a" * 40
    )

    with TestClient(healthcare_api.app) as client:
        yield client


def invalid_login(client):
    return client.post(
        "/auth/login",
        json={
            "username": "invalid-user",
            "password": "invalid-password",
        },
    )


def test_login_rate_limit(client):

    for _ in range(5):
        assert invalid_login(client).status_code == 401

    response = invalid_login(client)

    assert response.status_code == 429
    assert 1 <= int(response.headers["Retry-After"]) <= 60


def test_agent_rate_limit(client):

    for _ in range(10):
        response = client.post(
            "/agent/ask",
            json={"question": "Test question"},
        )
        assert response.status_code == 401

    response = client.post(
        "/agent/ask",
        json={"question": "Test question"},
    )

    assert response.status_code == 429


def test_patient_rate_limit(client):

    for _ in range(30):
        assert client.get("/patients").status_code == 401

    assert client.get("/patients").status_code == 429


def test_endpoint_limits_are_independent(client):

    for _ in range(5):
        invalid_login(client)

    assert invalid_login(client).status_code == 429

    assert client.get("/patients").status_code == 401


def test_rate_limited_response_has_trace_id(client):

    for _ in range(5):
        invalid_login(client)

    response = invalid_login(client)

    assert response.status_code == 429
    assert response.headers.get("X-Trace-ID")


def test_rate_limiter_feature_flag(client, monkeypatch):

    monkeypatch.setattr(
        healthcare_api, "RATE_LIMIT_ENABLED", False
    )

    for _ in range(7):
        assert invalid_login(client).status_code == 401
