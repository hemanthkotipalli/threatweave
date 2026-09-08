from typing import Any, Generic, TypeVar

from pydantic import BaseModel

# Declare Type variable for generic responses
T = TypeVar("T")

class ErrorDetails(BaseModel):
    """
    Standard schema for error descriptions inside ResponseEnvelope.
    """
    code: str
    message: str
    details: Any | None = None


class ResponseEnvelope(BaseModel, Generic[T]):
    """
    Standard JSON response envelope layout wrapped around all REST API operations.
    """
    success: bool
    data: T | None = None
    error: ErrorDetails | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard envelope representing offset/limit paginated search query results.
    """
    items: list[T]
    total: int
    page: int
    page_size: int
