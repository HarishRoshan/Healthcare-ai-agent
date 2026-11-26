
import json
import tiktoken


MAX_QUESTION_TOKENS = 1000
MAX_INPUT_TOKENS = 8000

ENCODER = tiktoken.get_encoding("o200k_base")


class InputTokenLimitExceeded(RuntimeError):
    """Raised when input exceeds the configured token limit."""


def count_tokens(text: str) -> int:

    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    return len(
        ENCODER.encode(
            text,
            disallowed_special=(),
        )
    )


def validate_question(question: str) -> int:

    if not isinstance(question, str) or not question.strip():
        raise ValueError("A question is required")

    token_count = count_tokens(question)

    if token_count > MAX_QUESTION_TOKENS:
        raise InputTokenLimitExceeded(
            "Question exceeds the maximum token limit"
        )

    return token_count


def validate_llm_input(payload: dict) -> int:

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    token_count = count_tokens(serialized)

    if token_count > MAX_INPUT_TOKENS:
        raise InputTokenLimitExceeded(
            "LLM input exceeds the maximum token limit"
        )

    return token_count
