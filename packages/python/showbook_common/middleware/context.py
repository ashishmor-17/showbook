from typing import Optional
import structlog

def get_correlation_id() -> Optional[str]:
    return structlog.contextvars.get_contextvars().get("trace_id")

def set_correlation_id(correlation_id: Optional[str]) -> None:
    structlog.contextvars.bind_contextvars(trace_id=correlation_id)

def reset_correlation_id() -> None:
    structlog.contextvars.unbind_contextvars("trace_id")
