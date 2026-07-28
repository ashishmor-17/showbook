import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from .context import set_correlation_id, reset_correlation_id

class CorrelationIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("correlation-id")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Clear local structlog context first to ensure no trace leaks from previous tasks
        structlog.contextvars.clear_contextvars()
        set_correlation_id(correlation_id)
        
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            reset_correlation_id()
