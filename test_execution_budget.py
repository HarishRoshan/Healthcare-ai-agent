
import pytest

from aura_execution_budget import (
    ExecutionBudget,
    ExecutionBudgetExceeded,
)


def test_llm_calls_within_limit():
    budget = ExecutionBudget()

    for _ in range(5):
        budget.consume_llm_call()

    assert budget.llm_calls == 5


def test_excessive_llm_calls_blocked():
    budget = ExecutionBudget()

    for _ in range(5):
        budget.consume_llm_call()

    with pytest.raises(ExecutionBudgetExceeded):
        budget.consume_llm_call()

    assert budget.llm_calls == 5


def test_tool_calls_within_limit():
    budget = ExecutionBudget()

    for _ in range(5):
        budget.consume_tool_call()

    assert budget.tool_calls == 5


def test_excessive_tool_calls_blocked():
    budget = ExecutionBudget()

    for _ in range(5):
        budget.consume_tool_call()

    with pytest.raises(ExecutionBudgetExceeded):
        budget.consume_tool_call()

    assert budget.tool_calls == 5


def test_independent_budgets():
    first = ExecutionBudget()
    second = ExecutionBudget()

    first.consume_llm_call()
    first.consume_tool_call()

    assert second.llm_calls == 0
    assert second.tool_calls == 0


def test_budget_summary():
    budget = ExecutionBudget()

    budget.consume_llm_call()
    budget.consume_tool_call()

    summary = budget.summary()

    assert summary["remaining_llm_calls"] == 4
    assert summary["remaining_tool_calls"] == 4


def test_invalid_limits():
    with pytest.raises(ValueError):
        ExecutionBudget(max_llm_calls=0)

    with pytest.raises(ValueError):
        ExecutionBudget(max_tool_calls=0)


def test_llm_and_tool_limits_are_independent():
    budget = ExecutionBudget()

    for _ in range(5):
        budget.consume_llm_call()

    budget.consume_tool_call()

    assert budget.llm_calls == 5
    assert budget.tool_calls == 1
