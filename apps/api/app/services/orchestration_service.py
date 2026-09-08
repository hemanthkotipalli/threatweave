"""
app/services/orchestration_service.py
-------------------------------------
Service layer executing the LangGraph swarm orchestration pipeline for investigations (Phase 10).
Manages top-level state transitions (pending -> running -> completed/failed) and
dispatches execution to the compiled LangGraph state machine.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.agents.graph import investigation_graph
from app.agents.orchestrator_state import InvestigationState
from app.core.config import settings
from app.core.errors import NotFoundError
from app.models.agent_run import AgentRun
from app.models.investigation import Investigation
from app.services import webhook_service

logger = logging.getLogger("threatweave-api.services.orchestration")

SEVERITY_RANKS: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def _should_notify_n8n(severity: str | None) -> bool:
    """Evaluates whether the investigation severity meets or exceeds the alert threshold."""
    if not severity:
        return False
    sev_clean = severity.lower().strip()
    threshold = (settings.N8N_ALERT_SEVERITY_THRESHOLD or "high").lower().strip()
    return SEVERITY_RANKS.get(sev_clean, 0) >= SEVERITY_RANKS.get(threshold, 3)


def _extract_top_indicators(findings: list[dict[str, Any]], limit: int = 5) -> list[str]:
    """Aggregates and returns the top 3-5 most common indicators across all findings."""
    from collections import Counter
    counts: Counter[str] = Counter()
    for f in findings:
        for ind in f.get("indicators", []):
            if isinstance(ind, str) and ind.strip():
                counts[ind.strip()] += 1
    return [item[0] for item in counts.most_common(limit)]


def run_investigation_analysis(
    investigation_id: str | uuid.UUID,
    db: Session,
) -> dict[str, Any]:
    """
    Orchestrates swarm analysis for a specified investigation:
    1. Loads the investigation and its associated evidence inputs.
    2. Transitions investigation.status to 'running'.
    3. Executes the LangGraph state machine across specialist agents.
    4. On completion, transitions investigation.status to 'completed'.
    5. Dispatches high-severity alert webhook to n8n if threshold is met (Phase 16).
    6. Returns an execution summary detailing active/skipped agents and findings.

    Raises:
        NotFoundError: If the investigation ID does not exist.
    """
    if isinstance(investigation_id, str):
        try:
            inv_uuid = uuid.UUID(investigation_id)
        except ValueError as exc:
            raise NotFoundError(message=f"Invalid investigation ID format: {investigation_id}") from exc
    else:
        inv_uuid = investigation_id

    investigation = db.query(Investigation).filter(Investigation.id == inv_uuid).first()
    if not investigation:
        logger.warning("Investigation %s not found for analysis", inv_uuid)
        raise NotFoundError(message=f"Investigation with ID {inv_uuid} was not found on this server")

    logger.info("Starting swarm analysis for investigation %s", inv_uuid)

    # 1. Update status to running
    investigation.status = "running"
    db.commit()
    db.refresh(investigation)

    # 2. Construct initial state for LangGraph
    serialized_inputs: list[dict[str, Any]] = []
    for ev in investigation.evidence_inputs:
        mod_val = ev.modality.value if hasattr(ev.modality, "value") else str(ev.modality)
        serialized_inputs.append({
            "id": str(ev.id),
            "modality": mod_val,
            "raw_content_ref": ev.raw_content_ref,
            "file_path": ev.file_path,
        })

    initial_state: InvestigationState = {
        "investigation_id": str(investigation.id),
        "evidence_inputs": serialized_inputs,
        "present_modalities": [],
        "required_agents": [],
        "active_agent_names": [],
        "findings": [],
        "corroborations": [],
        "conflicts": [],
        "rag_citations": [],
        "risk_result": None,
    }

    # 3. Invoke compiled graph
    try:
        final_state = investigation_graph.invoke(initial_state)
        investigation.status = "completed"
        db.commit()
        logger.info("Swarm analysis successfully completed for investigation %s", inv_uuid)
    except Exception:
        logger.exception("Swarm analysis failed unexpectedly for investigation %s", inv_uuid)
        investigation.status = "failed"
        db.commit()
        raise

    # 4. Refresh investigation row to get final risk metrics
    db.refresh(investigation)

    # 5. Optional webhook notification for high/critical severity (Phase 16)
    webhook_dispatched = False
    try:
        sev_val = (
            investigation.final_severity.value
            if hasattr(investigation.final_severity, "value")
            else str(investigation.final_severity)
            if investigation.final_severity
            else None
        )
        if _should_notify_n8n(sev_val):
            top_indicators = _extract_top_indicators(final_state.get("findings", []), limit=5)
            summary_payload = {
                "investigation_id": str(investigation.id),
                "title": investigation.title,
                "final_risk_score": investigation.final_risk_score,
                "final_severity": sev_val,
                "top_indicators": top_indicators,
                "created_at": investigation.created_at.isoformat() if investigation.created_at else None,
            }
            webhook_service.notify_high_severity(summary_payload)
            webhook_dispatched = True
    except Exception as exc:  # noqa: BLE001
        # External notifications must NEVER cause investigation failure
        logger.warning(
            "Non-fatal error dispatching webhook alert for investigation %s: %s",
            inv_uuid,
            exc,
        )

    # 6. Gather DB-persisted agent runs
    runs = db.query(AgentRun).filter(AgentRun.investigation_id == investigation.id).all()

    agent_runs_summary = [
        {
            "id": str(r.id),
            "agent_name": r.agent_name,
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "latency_ms": r.latency_ms,
        }
        for r in runs
    ]

    return {
        "investigation_id": str(investigation.id),
        "status": investigation.status,
        "active_agents": final_state.get("active_agent_names", []),
        "agent_runs": agent_runs_summary,
        "findings_count": len(final_state.get("findings", [])),
        "findings": final_state.get("findings", []),
        "rag_citations": final_state.get("rag_citations", []),
        "risk": final_state.get("risk_result"),
        "webhook_dispatched": webhook_dispatched,
    }

