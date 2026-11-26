
import sqlite3

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import healthcare_api as api

from aura_usage_quota import UsageQuota


@pytest.fixture
def setup_api(tmp_path, monkeypatch):

    quota = UsageQuota(
        db_path=tmp_path / "test_usage.db",
        daily_limit=2,
        monthly_limit=5,
    )

    mock_agent = Mock(return_value="Test AI response")

    monkeypatch.setattr(api, "usage_quota", quota)
    monkeypatch.setattr(api, "ask_healthcare_agent", mock_agent)
    monkeypatch.setattr(api, "RATE_LIMIT_ENABLED", False)

    api.app.dependency_overrides[api.verify_session] = (
        lambda: "aura_demo"
    )

    try:
        with TestClient(api.app) as client:
            yield client, quota, mock_agent

    finally:
        api.app.dependency_overrides.pop(
            api.verify_session, None
        )


def test_allowed_request(setup_api):

    client, quota, mock_agent = setup_api

    response = client.post(
        "/agent/ask",
        json={"question": "Hello"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Test AI response"
    assert mock_agent.call_count == 1


def test_daily_quota_exhausted(setup_api):

    client, quota, mock_agent = setup_api

    for _ in range(2):
        response = client.post(
            "/agent/ask",
            json={"question": "Hello"},
        )

        assert response.status_code == 200

    response = client.post(
        "/agent/ask",
        json={"question": "Hello"},
    )

    assert response.status_code == 429
    assert mock_agent.call_count == 2


def test_monthly_quota_exhausted(setup_api):

    client, quota, mock_agent = setup_api

    quota.daily_limit = 10
    quota.monthly_limit = 1

    first = client.post(
        "/agent/ask",
        json={"question": "Hello"},
    )

    second = client.post(
        "/agent/ask",
        json={"question": "Hello"},
    )

    assert first.status_code == 200
    assert second.status_code == 429
    assert mock_agent.call_count == 1


def test_unauthenticated_request(setup_api):

    client, quota, mock_agent = setup_api

    api.app.dependency_overrides.pop(
        api.verify_session, None
    )

    response = client.post(
        "/agent/ask",
        json={"question": "Hello"},
    )

    assert response.status_code == 401
    mock_agent.assert_not_called()

    result = quota.reserve_request()
    assert result["daily_used"] == 1


def test_invalid_question(setup_api):

    client, quota, mock_agent = setup_api

    response = client.post(
        "/agent/ask",
        json={"question": "   "},
    )

    assert response.status_code == 400
    mock_agent.assert_not_called()

    result = quota.reserve_request()
    assert result["daily_used"] == 1


def test_database_failure(setup_api, monkeypatch):

    client, quota, mock_agent = setup_api

    def unavailable():
        raise sqlite3.OperationalError(
            "Database unavailable"
        )

    monkeypatch.setattr(
        quota,
        "reserve_request",
        unavailable,
    )

    response = client.post(
        "/agent/ask",
        json={"question": "Hello"},
    )

    assert response.status_code == 503
    mock_agent.assert_not_called()


def test_exhausted_quota_blocks_ai(setup_api):

    client, quota, mock_agent = setup_api

    quota.reserve_request()
    quota.reserve_request()

    response = client.post(
        "/agent/ask",
        json={"question": "Hello"},
    )

    assert response.status_code == 429
    mock_agent.assert_not_called()


def test_failed_agent_consumes_quota(setup_api):

    client, quota, mock_agent = setup_api

    mock_agent.side_effect = RuntimeError(
        "Simulated agent failure"
    )

    response = client.post(
        "/agent/ask",
        json={"question": "Hello"},
    )

    assert response.status_code == 503

    result = quota.reserve_request()

    assert result["daily_used"] == 2
    assert result["monthly_used"] == 2
