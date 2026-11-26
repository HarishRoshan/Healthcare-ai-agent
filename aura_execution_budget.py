
class ExecutionBudgetExceeded(RuntimeError):
    """Raised when an agent exceeds its execution budget."""


class ExecutionBudget:

    def __init__(self, max_llm_calls=5, max_tool_calls=5):

        if max_llm_calls < 1 or max_tool_calls < 1:
            raise ValueError("Execution limits must be positive")

        self.max_llm_calls = max_llm_calls
        self.max_tool_calls = max_tool_calls

        self.llm_calls = 0
        self.tool_calls = 0

    def consume_llm_call(self):

        if self.llm_calls >= self.max_llm_calls:
            raise ExecutionBudgetExceeded(
                "Maximum LLM calls exceeded"
            )

        self.llm_calls += 1

    def consume_tool_call(self):

        if self.tool_calls >= self.max_tool_calls:
            raise ExecutionBudgetExceeded(
                "Maximum tool calls exceeded"
            )

        self.tool_calls += 1

    def summary(self):

        return {
            "llm_calls": self.llm_calls,
            "tool_calls": self.tool_calls,
            "max_llm_calls": self.max_llm_calls,
            "max_tool_calls": self.max_tool_calls,
            "remaining_llm_calls": (
                self.max_llm_calls - self.llm_calls
            ),
            "remaining_tool_calls": (
                self.max_tool_calls - self.tool_calls
            ),
        }
