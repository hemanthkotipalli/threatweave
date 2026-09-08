"""
apps/api/app/api/v1/endpoints/demo.py
-------------------------------------
Endpoints for ThreatWeave Demo Mode.
Provides curated scenarios and triggers real, synchronous pipeline execution
using live database persistence and swarm orchestration.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.demo.scenarios import (
    get_all_scenarios_metadata,
    prepare_scenario_inputs,
)
from app.services.ingestion_service import ingest_investigation
from app.services.orchestration_service import run_investigation_analysis

logger = logging.getLogger("threatweave-api.endpoints.demo")

router = APIRouter()


@router.get(
    "/scenarios",
    summary="List all curated Demo Mode threat scenarios",
    response_description="Array of available demo scenarios with metadata and modality flags.",
)
async def list_demo_scenarios() -> list[dict[str, Any]]:
    """
    Returns metadata for all 6 curated demonstration scenarios:
    - phishing_email (text)
    - malicious_url (url)
    - fake_payment_qr (qr)
    - fraudulent_screenshot (image)
    - scam_voice (voice)
    - cross_modal (multimodal combined)
    """
    logger.info("Listing all curated demo scenarios")
    return get_all_scenarios_metadata()


@router.post(
    "/scenarios/{key}/run",
    summary="Execute a curated demo scenario through the genuine pipeline",
    response_description="Created and analyzed investigation outcome with final risk score.",
)
async def run_demo_scenario(
    key: str,
    mode: str = Query(
        "combined",
        description="Execution mode for cross_modal: 'combined', 'text_only', 'url_only', 'image_only'",
    ),
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Runs a curated demo scenario end-to-end through the REAL pipeline:
    1. Prepares genuine scenario evidence inputs.
    2. Calls ingestion_service.ingest_investigation().
    3. Calls orchestration_service.run_investigation_analysis().
    4. Returns the completed investigation result with deterministic risk scores.
    """
    logger.info("Executing demo scenario '%s' (mode=%s)", key, mode)

    title, text, url, img_file, voice_file = prepare_scenario_inputs(scenario_key=key, mode=mode)

    # 1. Genuine ingestion call (is_demo=True attributes to placeholder system_analyst with no auth requirement)
    investigation = ingest_investigation(
        db=db,
        title=title,
        text=text,
        url=url,
        image_file=img_file,
        voice_file=voice_file,
        is_demo=True,
    )


    # 2. Genuine swarm orchestration call
    analysis_result = run_investigation_analysis(
        investigation_id=investigation.id,
        db=db,
    )

    # Refresh investigation to get updated risk scores
    db.refresh(investigation)

    sev_val = (
        investigation.final_severity.value
        if hasattr(investigation.final_severity, "value")
        else str(investigation.final_severity)
        if investigation.final_severity
        else None
    )

    return {
        "investigation_id": str(investigation.id),
        "scenario_key": key,
        "mode": mode,
        "status": investigation.status,
        "final_risk_score": investigation.final_risk_score,
        "final_severity": sev_val,
        "final_confidence": investigation.final_confidence,
        "risk": analysis_result.get("risk"),
    }
