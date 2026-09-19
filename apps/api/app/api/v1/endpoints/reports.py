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

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.report_service import generate_pdf_report, generate_report

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
    """
    logger.info("Report requested for investigation %s", id)
    return generate_report(investigation_id=id, db=db)


@router.get(
    "/{id}/report/pdf",
    summary="Generate and download an official PDF threat investigation report.",
    response_description="Binary PDF file stream."
)
async def get_investigation_report_pdf(
    id: uuid.UUID,
    db: Session = Depends(get_db)  # noqa: B008
) -> Response:
    """
    Generates and returns an official PDF investigation report rendered server-side
    via ReportLab.

    Reuses generate_report() data-assembly logic, records an audit log row with format='pdf',
    and streams the resulting binary PDF with appropriate Content-Disposition headers.
    """
    logger.info("PDF report requested for investigation %s", id)
    report_data = generate_report(investigation_id=id, db=db, format_type="pdf")
    pdf_bytes = generate_pdf_report(report_data)
    filename = f"threatweave-investigation-{id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "application/pdf",
        },
    )
