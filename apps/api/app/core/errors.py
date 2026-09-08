import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("threatweave-api.errors")

class ThreatWeaveError(Exception):
    """
    Base exception class for all customized ThreatWeave application errors.
    """
    def __init__(self, code: str, message: str, status_code: int = 500, details: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class NotFoundError(ThreatWeaveError):
    """
    Exception raised when a requested resource is not found (HTTP 404).
    """
    def __init__(self, message: str = "Resource not found", code: str = "not_found", details: Any = None) -> None:
        super().__init__(code=code, message=message, status_code=404, details=details)


class ValidationError(ThreatWeaveError):
    """
    Exception raised during request parameter or payload validation failure (HTTP 422).
    """
    def __init__(self, message: str = "Validation failed", code: str = "validation_error", details: Any = None) -> None:
        super().__init__(code=code, message=message, status_code=422, details=details)


class ExternalServiceError(ThreatWeaveError):
    """
    Exception raised when an external API, LLM, or utility fails to degrade gracefully (HTTP 502).
    """
    def __init__(self, message: str = "External service integration failed", code: str = "external_service_error", details: Any = None) -> None:
        super().__init__(code=code, message=message, status_code=502, details=details)


class AuthenticationError(ThreatWeaveError):
    """
    Exception raised when authentication fails or valid credentials are missing (HTTP 401).
    """
    def __init__(self, message: str = "Authentication failed", code: str = "authentication_error", details: Any = None) -> None:
        super().__init__(code=code, message=message, status_code=401, details=details)


class ConflictError(ThreatWeaveError):
    """
    Exception raised when an entity already exists or conflicts with the current state (HTTP 409).
    """
    def __init__(self, message: str = "Resource conflict", code: str = "conflict_error", details: Any = None) -> None:
        super().__init__(code=code, message=message, status_code=409, details=details)



async def threatweave_exception_handler(request: Request, exc: ThreatWeaveError) -> JSONResponse:
    """
    FastAPI handler for catching custom ThreatWeaveErrors and formatting them as standard JSON.
    """
    logger.warning(f"Handled application error: {exc.message} (code: {exc.code}, status: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    FastAPI handler mapping default request validation errors (Pydantic models) to the standard JSON structure.
    """
    details = exc.errors()
    logger.warning(f"Request validation failed: {details}")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed.",
                "details": details,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    FastAPI handler catching any unhandled standard exception, logging the full traceback server-side,
    and returning a clean generic internal error mapping to the client (leaks no tracebacks).
    """
    logger.exception("An unhandled server exception occurred")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred on the server.",
                "details": None,
            }
        },
    )
