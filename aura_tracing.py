
"""Request-scoped trace ID for AURA."""

from contextvars import ContextVar

trace_id_context = ContextVar(
    "aura_trace_id",
    default=None,
)


def get_trace_id():
    return trace_id_context.get()
