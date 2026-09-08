from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.errors import NotFoundError
from app.models.investigation import Investigation
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.investigation import (
    InvestigationCreateResponse,
    InvestigationDetailResponse,
    InvestigationListItemResponse,
)
from app.services.ingestion_service import ingest_investigation

logger = logging.getLogger("threatweave-api.endpoints.investigations")

router = APIRouter()


@router.post(
    "",
    response_model=InvestigationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new threat investigation task with multimodal evidence inputs."
)
async def create_investigation(
    title: str | None = Form(None),
    text: str | None = Form(None),
    url: str | None = Form(None),
    image: UploadFile | None = File(None),  # noqa: B008
    voice: UploadFile | None = File(None),  # noqa: B008
    db: Session = Depends(get_db),          # noqa: B008
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> dict:
    """
    Ingests and processes raw evidence inputs (text, URL, images, or audio files).
    Stores evidence files on disk and commits investigation metadata to the database.
    Requires authentication; associates the investigation with the authenticated user.
    """
    logger.info("Received request to create investigation by user %s", current_user.id)
    investigation = ingest_investigation(
        db=db,
        title=title,
        text=text,
        url=url,
        image_file=image,
        voice_file=voice,
        user_id=current_user.id,
        is_demo=False,
    )
    return {
        "investigation": investigation,
        "evidence_inputs": investigation.evidence_inputs
    }



from datetime import datetime, timezone

from sqlalchemy import false
from sqlalchemy.orm import selectinload

from app.models.enums import Severity


def _parse_datetime_param(val: str | datetime | None) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    val_clean = str(val).strip()
    if not val_clean:
        return None
    if " " in val_clean and ("+" not in val_clean):
        parts = val_clean.rsplit(" ", 1)
        if len(parts) == 2 and (":" in parts[1] or len(parts[1]) == 4):
            val_clean = f"{parts[0]}+{parts[1]}"
    if val_clean.endswith("Z"):
        val_clean = val_clean[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(val_clean)
    except (ValueError, TypeError):
        try:
            return datetime.strptime(val_clean, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None



@router.get(
    "",
    response_model=PaginatedResponse[InvestigationListItemResponse],
    summary="List investigations with pagination ordered by created_at desc."
)
async def list_investigations(
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size limit"),
    status: str | None = Query(None, description="Optional status filter"),
    severity: str | None = Query(None, description="Optional severity filter"),
    date_from: str | None = Query(None, description="Optional start datetime ISO filter"),
    date_to: str | None = Query(None, description="Optional end datetime ISO filter"),
    db: Session = Depends(get_db)  # noqa: B008
) -> PaginatedResponse[InvestigationListItemResponse]:
    """
    Retrieves a paginated list of investigations ordered by creation time descending,
    supporting real filtering by status, severity, and creation date range.
    Investigations with final_severity=None are gracefully excluded from severity filters.
    """
    logger.info(
        "Listing investigations: page=%d, page_size=%d, status=%s, severity=%s, date_from=%s, date_to=%s",
        page, page_size, status, severity, date_from, date_to,
    )
    query = db.query(Investigation)

    if status:
        query = query.filter(Investigation.status == status.strip().lower())

    if severity:
        sev_clean = severity.strip().lower()
        try:
            sev_enum = Severity(sev_clean)
            query = query.filter(Investigation.final_severity == sev_enum)
        except ValueError:
            query = query.filter(false())

    dt_from = _parse_datetime_param(date_from)
    if dt_from:
        query = query.filter(Investigation.created_at >= dt_from)

    dt_to = _parse_datetime_param(date_to)
    if dt_to:
        query = query.filter(Investigation.created_at <= dt_to)

    total = query.count()
    offset = (page - 1) * page_size
    items = (
        query.options(selectinload(Investigation.evidence_inputs))
        .order_by(Investigation.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    result_items: list[InvestigationListItemResponse] = []
    for inv in items:
        sev_val = (
            inv.final_severity.value
            if hasattr(inv.final_severity, "value")
            else str(inv.final_severity)
            if inv.final_severity
            else None
        )
        modality_list = (
            [inp.modality for inp in inv.evidence_inputs]
            if inv.evidence_inputs
            else []
        )
        result_items.append(
            InvestigationListItemResponse(
                id=inv.id,
                title=inv.title,
                status=inv.status,
                created_at=inv.created_at,
                final_risk_score=inv.final_risk_score,
                final_severity=sev_val,
                modalities=modality_list,
            )
        )

    return PaginatedResponse[InvestigationListItemResponse](
        items=result_items,
        total=total,
        page=page,
        page_size=page_size,
    )



@router.get(
    "/{id}",
    response_model=InvestigationDetailResponse,
    summary="Get complete investigation details and associated evidence sources."
)
async def get_investigation(
    id: uuid.UUID,
    db: Session = Depends(get_db)  # noqa: B008
) -> InvestigationDetailResponse:
    """
    Retrieves full details of a specific threat investigation task.
    Returns 404 NotFoundError if the requested ID does not exist.
    """
    logger.info("Retrieving investigation %s", id)
    from sqlalchemy.orm import selectinload

    from app.models.agent_run import AgentRun
    from app.schemas.investigation import (
        ConflictLogItemResponse,
        RiskBreakdownItemResponse,
        RiskDetailResponse,
    )

    investigation = (
        db.query(Investigation)
        .options(
            selectinload(Investigation.evidence_inputs),
            selectinload(Investigation.agent_runs).selectinload(AgentRun.findings),
            selectinload(Investigation.rag_citations),
            selectinload(Investigation.risk_breakdown),
            selectinload(Investigation.conflict_logs),
        )
        .filter(Investigation.id == id)
        .first()
    )

    if not investigation:
        logger.warning("Investigation %s not found", id)
        raise NotFoundError(message=f"Investigation with ID {id} was not found on this server")

    # Assemble risk field if scoring was executed
    risk_obj: RiskDetailResponse | None = None
    if investigation.final_risk_score is not None or investigation.risk_breakdown:
        active_findings_count = sum(
            1 for run in investigation.agent_runs for f in run.findings if f.status != "failed"
        )
        avg_conf = investigation.final_confidence or 0.0
        low_conf = (active_findings_count < 2) or (avg_conf < 0.4)

        risk_obj = RiskDetailResponse(
            score=investigation.final_risk_score,
            severity=(
                investigation.final_severity.value
                if hasattr(investigation.final_severity, "value")
                else str(investigation.final_severity)
                if investigation.final_severity
                else None
            ),
            confidence=investigation.final_confidence,
            low_confidence=low_conf,
            breakdown=[
                RiskBreakdownItemResponse(
                    component=rb.component,
                    value=rb.value,
                    weight=rb.weight,
                    contribution=rb.contribution,
                )
                for rb in investigation.risk_breakdown
            ],
            conflicts=[
                ConflictLogItemResponse(
                    id=c.id,
                    agent_a=c.agent_a,
                    agent_b=c.agent_b,
                    conflict_type=c.conflict_type,
                    resolution_rule=c.resolution_rule,
                    resolution_outcome=c.resolution_outcome,
                )
                for c in investigation.conflict_logs
            ],
        )

    resp = InvestigationDetailResponse.model_validate(investigation)
    resp.risk = risk_obj
    if investigation.final_severity:
        resp.final_severity = (
            investigation.final_severity.value
            if hasattr(investigation.final_severity, "value")
            else str(investigation.final_severity)
        )
    return resp

