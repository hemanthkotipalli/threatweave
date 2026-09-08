from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import setup_logging

# Initialize JSON logging format first
setup_logging()

import logging

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import (
    ThreatWeaveError,
    request_validation_exception_handler,
    threatweave_exception_handler,
    unhandled_exception_handler,
)
from app.core.middleware import RequestTelemetryMiddleware
from app.core.security import validate_security_configuration

# Import database models to ensure ORM metadata registry is fully loaded
from app.db.base import Base  # noqa: F401

logger = logging.getLogger("threatweave-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup checks and graceful shutdown.
    """
    logger.info("ThreatWeave API starting up. Validating security configuration...")
    validate_security_configuration()
    yield
    logger.info("ThreatWeave API shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Agentic Multimodal Cyber Threat Intelligence & Response API Engine",
    version="0.2.0",
    lifespan=lifespan,
)


# Exception Handlers Registration
app.add_exception_handler(ThreatWeaveError, threatweave_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Middleware Registration
# Note: CORSMiddleware is added first, and then RequestTelemetryMiddleware.
# This wraps CORSMiddleware inside RequestTelemetryMiddleware so that CORS requests
# are tracked and timed with Request IDs as well.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestTelemetryMiddleware)

# Versioned Routes Registration
app.include_router(api_router, prefix="/api/v1")

# Legacy/Unversioned Routes Registration
@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Legacy unversioned health check endpoint.
    Kept for backwards compatibility with Phase 0 tooling.
    """
    logger.info("Legacy health check endpoint accessed")
    return {"status": "ok", "service": "threatweave-api"}




