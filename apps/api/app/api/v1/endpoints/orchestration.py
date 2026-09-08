"""
app/api/v1/endpoints/orchestration.py
-------------------------------------
API route triggering the LangGraph swarm orchestration pipeline for an investigation (Phase 10).
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.investigation import InvestigationAnalyzeResponse
from app.services.orchestration_service import run_investigation_analysis

logger = logging.getLogger("threatweave-api.endpoints.orchestration")

router = APIRouter()


@router.post(
    "/{id}/analyze",
    response_model=InvestigationAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger LangGraph swarm orchestration for a threat investigation.",
)
async def analyze_investigation(
    id: uuid.UUID,
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> dict:

    """
    Executes dynamic agent routing and parallel execution across all required
    specialist agents based on the evidence inputs associated with the investigation.
    Returns 200 with summary of active agents, agent runs, and findings.
    Returns 404 if the investigation does not exist.
    """
    logger.info("Received request to run swarm analysis for investigation %s", id)
    result = run_investigation_analysis(investigation_id=id, db=db)
    return result
