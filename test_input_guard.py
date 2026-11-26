
import pytest

from aura_input_guard import (
    count_tokens,
    validate_question,
    validate_llm_input,
    InputTokenLimitExceeded,
)


def test_token_count():
    assert count_tokens("Hello") == 1


def test_valid_question():
    assert validate_question(
        "What is the patient status?"
    ) > 0


def test_empty_question():
    with pytest.raises(ValueError):
        validate_question("")


def test_oversized_question():
    with pytest.raises(InputTokenLimitExceeded):
        validate_question("hello " * 2000)


def test_valid_llm_payload():
    payload = {
        "instructions": "You are AURA AI",
        "input": "Hello",
    }

    assert validate_llm_input(payload) > 0


def test_oversized_llm_payload():
    payload = {
        "instructions": "You are AURA AI",
        "input": "hello " * 10000,
    }

    with pytest.raises(InputTokenLimitExceeded):
        validate_llm_input(payload)


def test_special_token_text():
    assert count_tokens("<|endoftext|>") > 0


def test_invalid_input_type():
    with pytest.raises(TypeError):
        count_tokens(123)
