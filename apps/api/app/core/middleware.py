import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logging import request_id_context

logger = logging.getLogger("threatweave-api.middleware")

class RequestTelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware responsible for request telemetry:
    - Generates or propagates a unique Request ID (X-Request-ID).
    - Sets the Request ID in the async context variable for logger formatting.
    - Tracks and logs request timing in milliseconds.
    - Injects X-Request-ID into response headers.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract X-Request-ID from request headers, or generate a fresh UUID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Set the Request ID context variable so the JSON formatter catches it
        token = request_id_context.set(request_id)
        
        start_time = time.perf_counter()
        response: Response
        
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"Request failed: {request.method} {request.url.path} in {duration_ms:.2f}ms"
            )
            # Re-raise the exception to be captured by the error handlers
            raise
        finally:
            # Calculate execution duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log successful completion with duration (if response exists)
            if 'response' in locals():
                logger.info(
                    f"Request completed: {request.method} {request.url.path} -> {response.status_code} in {duration_ms:.2f}ms"
                )
            
            # Reset Request ID context
            request_id_context.reset(token)

        # Add Request ID header to response
        response.headers["X-Request-ID"] = request_id
        return response
