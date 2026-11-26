
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import healthcare_agent as agent

from aura_execution_budget import ExecutionBudgetExceeded


def make_response(tool_count=0):
    return SimpleNamespace(
        id="mock_response",
        output_text="Test answer",
        output=[
            SimpleNamespace(
                type="function_call",
                name="get_patient_status",
                arguments='{"patient_id": 101}',
                call_id=f"call_{i}",
            )
            for i in range(tool_count)
        ],
    )


@pytest.fixture
def mocked_agent(monkeypatch):
    llm = Mock()
    tool = Mock(return_value={"status": "active"})

    monkeypatch.setattr(
        agent.client.responses, "create", llm
    )

    monkeypatch.setattr(agent, "execute_tool", tool)

    return llm, tool


def test_normal_agent_response(mocked_agent):
    llm, tool = mocked_agent
    llm.return_value = make_response()

    answer, _ = agent.run_agent("Hello")

    assert answer == "Test answer"
    assert llm.call_count == 1
    assert tool.call_count == 0


def test_llm_call_limit(mocked_agent):
    llm, tool = mocked_agent
    llm.return_value = make_response(tool_count=1)

    with pytest.raises(ExecutionBudgetExceeded):
        agent.run_agent("Check patient 101")

    assert llm.call_count == 5
    assert tool.call_count == 4


def test_tool_call_limit(mocked_agent):
    llm, tool = mocked_agent
    llm.return_value = make_response(tool_count=6)

    with pytest.raises(ExecutionBudgetExceeded):
        agent.run_agent("Check patient 101")

    assert tool.call_count == 5
    assert llm.call_count == 1


def test_final_allowed_llm_response(mocked_agent):
    llm, tool = mocked_agent

    llm.side_effect = [
        make_response(tool_count=1)
        for _ in range(4)
    ] + [make_response()]

    answer, _ = agent.run_agent("Check patient 101")

    assert answer == "Test answer"
    assert llm.call_count == 5
    assert tool.call_count == 4


def test_independent_request_budgets(mocked_agent):
    llm, tool = mocked_agent

    llm.return_value = make_response(tool_count=1)

    with pytest.raises(ExecutionBudgetExceeded):
        agent.run_agent("Check patient 101")

    llm.reset_mock()
    llm.return_value = make_response()

    answer, _ = agent.run_agent("Hello")

    assert answer == "Test answer"
    assert llm.call_count == 1


def test_output_token_limit(mocked_agent):
    llm, tool = mocked_agent
    llm.return_value = make_response()

    agent.run_agent("Hello")

    assert llm.call_args.kwargs["max_output_tokens"] == 500


def test_unauthorized_patient_access(monkeypatch):
    database_tool = Mock()
    audit = Mock()

    monkeypatch.setattr(
        agent, "get_patient_status", database_tool
    )
    monkeypatch.setattr(
        agent, "log_audit_event", audit
    )

    result = agent.execute_tool(
        "get_patient_status",
        json.dumps({"patient_id": 102}),
        allowed_patient_ids={101},
        username="aura_demo",
    )

    assert result["error"] == "Access denied"
    database_tool.assert_not_called()
    audit.assert_called_once()
