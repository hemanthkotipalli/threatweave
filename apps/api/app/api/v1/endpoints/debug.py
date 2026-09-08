from __future__ import annotations

import logging

from fastapi import APIRouter, File, UploadFile, status
from pydantic import BaseModel, Field

from app.agents.image_agent import analyze_image
from app.agents.qr_agent import analyze_qr
from app.agents.text_agent import analyze_text
from app.agents.url_agent import analyze_url
from app.agents.voice_agent import analyze_voice
from app.core.config import settings
from app.core.errors import NotFoundError
from app.schemas.evidence import EvidenceItem

logger = logging.getLogger("threatweave-api.endpoints.debug")

router = APIRouter()


class DebugTextAgentRequest(BaseModel):
    """
    Request body schema for Text Agent debug testing.
    """
    content: str = Field(..., description="The raw text block to analyze.")


class DebugUrlAgentRequest(BaseModel):
    """
    Request body schema for URL Agent debug testing.
    """
    url: str = Field(..., description="The URL to analyze for structural threat indicators.")


@router.post(
    "/text-agent",
    response_model=EvidenceItem,
    status_code=status.HTTP_200_OK,
    summary="Directly invoke the Text Agent for debug and local auditing."
)
def debug_text_agent(payload: DebugTextAgentRequest) -> EvidenceItem:
    """
    Exposes the Text Agent directly for testing and auditing in development.
    Throws NotFoundError (HTTP 404) in non-development environments.
    """
    if settings.ENVIRONMENT != "development":
        logger.warning(f"Refused request to debug endpoint in environment: {settings.ENVIRONMENT}")
        raise NotFoundError(message="Resource not found in this environment")

    logger.info("Directly invoking Text Agent via debug endpoint")
    result = analyze_text(payload.content)
    return result


@router.post(
    "/url-agent",
    response_model=EvidenceItem,
    status_code=status.HTTP_200_OK,
    summary="Directly invoke the URL Agent for debug and local auditing."
)
def debug_url_agent(payload: DebugUrlAgentRequest) -> EvidenceItem:
    """
    Exposes the URL Agent directly for testing and auditing in development.
    Throws NotFoundError (HTTP 404) in non-development environments.
    """
    if settings.ENVIRONMENT != "development":
        logger.warning(
            "Refused request to URL Agent debug endpoint in environment: %s",
            settings.ENVIRONMENT,
        )
        raise NotFoundError(message="Resource not found in this environment")

    logger.info("Directly invoking URL Agent via debug endpoint")
    result = analyze_url(payload.url)
    return result


@router.post(
    "/qr-agent",
    response_model=EvidenceItem,
    status_code=status.HTTP_200_OK,
    summary="Directly invoke the QR Agent for debug and local auditing."
)
async def debug_qr_agent(
    image: UploadFile = File(..., description="QR code image file to analyze."),  # noqa: B008
) -> EvidenceItem:
    """
    Exposes the QR Agent directly for testing and auditing in development.
    Accepts multipart image upload.
    Throws NotFoundError (HTTP 404) in non-development environments.
    """
    if settings.ENVIRONMENT != "development":
        logger.warning(
            "Refused request to QR Agent debug endpoint in environment: %s",
            settings.ENVIRONMENT,
        )
        raise NotFoundError(message="Resource not found in this environment")

    logger.info("Directly invoking QR Agent via debug endpoint with filename=%r", image.filename)
    image_bytes = await image.read()
    result = analyze_qr(image_bytes)
    return result


@router.post(
    "/image-agent",
    response_model=EvidenceItem,
    status_code=status.HTTP_200_OK,
    summary="Directly invoke the Image Agent for debug and local auditing."
)
async def debug_image_agent(
    image: UploadFile = File(..., description="Image or screenshot file to analyze."),  # noqa: B008
) -> EvidenceItem:
    """
    Exposes the Image Agent directly for testing and auditing in development.
    Accepts multipart image upload.
    Throws NotFoundError (HTTP 404) in non-development environments.
    """
    if settings.ENVIRONMENT != "development":
        logger.warning(
            "Refused request to Image Agent debug endpoint in environment: %s",
            settings.ENVIRONMENT,
        )
        raise NotFoundError(message="Resource not found in this environment")

    logger.info("Directly invoking Image Agent via debug endpoint with filename=%r", image.filename)
    image_bytes = await image.read()
    result = analyze_image(image_bytes)
    return result


@router.post(
    "/voice-agent",
    response_model=EvidenceItem,
    status_code=status.HTTP_200_OK,
    summary="Directly invoke the Voice Agent for debug and local auditing."
)
async def debug_voice_agent(
    audio: UploadFile = File(..., description="Audio file to analyze for telephone fraud / vishing."),  # noqa: B008
) -> EvidenceItem:
    """
    Exposes the Voice Agent directly for testing and auditing in development.
    Accepts multipart audio upload.
    Throws NotFoundError (HTTP 404) in non-development environments.
    """
    if settings.ENVIRONMENT != "development":
        logger.warning(
            "Refused request to Voice Agent debug endpoint in environment: %s",
            settings.ENVIRONMENT,
        )
        raise NotFoundError(message="Resource not found in this environment")

    logger.info("Directly invoking Voice Agent via debug endpoint with filename=%r", audio.filename)
    audio_bytes = await audio.read()
    result = analyze_voice(audio_bytes)
    return result




