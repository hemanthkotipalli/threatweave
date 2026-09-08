import logging

from fastapi import APIRouter

logger = logging.getLogger("threatweave-api.health")

router = APIRouter()

@router.get("/health")
def get_health() -> dict[str, str]:
    """
    Version 1 health check endpoint.
    Returns status, service name, and API version.
    """
    logger.info("v1 health check endpoint accessed")
    return {
        "status": "ok",
        "service": "threatweave-api",
        "version": "v1"
    }
