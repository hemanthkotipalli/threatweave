"""
apps/api/app/api/v1/endpoints/reports.py
----------------------------------------
Endpoint for generating and retrieving comprehensive investigation reports.
Reports are generated on demand to ensure fresh data and logged to the
investigation_reports audit table.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.report_service import generate_report

logger = logging.getLogger("threatweave-api.endpoints.reports")

router = APIRouter()


@router.get(
    "/{id}/report",
    summary="Generate and retrieve a complete threat investigation report.",
    response_description="Structured JSON report payload with investigation findings, risk, and citations."
)
async def get_investigation_report(
    id: uuid.UUID,
    db: Session = Depends(get_db)  # noqa: B008
) -> dict[str, Any]:
    """
    Generates a complete, structured investigation report payload on demand,
    including evidence inputs, swarm findings, deterministic risk breakdown,
    RAG threat intelligence citations, and conflict resolution logs.

    Each request writes an audit log entry in the investigation_reports table.
    Server-side PDF generation is deferred; the frontend utilizes this structured
    payload along with browser print-to-PDF (@media print) for crisp, lightweight exports.
    """
    logger.info("Report requested for investigation %s", id)
    return generate_report(investigation_id=id, db=db)
