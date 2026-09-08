"""
apps/api/app/services/report_service.py
---------------------------------------
Service for assembling comprehensive investigation reports on demand.
Maintains an immutable audit log entry in the `investigation_reports` table
every time a report is requested.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundError
from app.models.agent_run import AgentRun
from app.models.investigation import Investigation
from app.models.investigation_report import InvestigationReport

logger = logging.getLogger("threatweave-api.services.report")


def generate_report(investigation_id: str | uuid.UUID, db: Session) -> dict[str, Any]:
    """
    Assembles a complete, structured investigation report payload containing:
    - Investigation metadata
    - Evidence inputs summary
    - All agent runs and findings
    - Deterministic risk breakdown and score
    - RAG threat intelligence citations
    - Swarm conflict logs

    Writes an immutable InvestigationReport audit record (format='html', file_path='on-demand:audit')
    to track when the report was requested.

    Raises:
        NotFoundError: If the investigation ID is not found.
    """
    try:
        inv_uuid = uuid.UUID(str(investigation_id))
    except (ValueError, TypeError) as err:
        logger.warning("Invalid investigation UUID for report generation: %s", investigation_id)
        raise NotFoundError(message=f"Investigation with ID '{investigation_id}' was not found.") from err

    logger.info("Generating on-demand report for investigation %s", inv_uuid)

    investigation = (
        db.query(Investigation)
        .options(
            selectinload(Investigation.evidence_inputs),
            selectinload(Investigation.agent_runs).selectinload(AgentRun.findings),
            selectinload(Investigation.rag_citations),
            selectinload(Investigation.risk_breakdown),
            selectinload(Investigation.conflict_logs),
        )
        .filter(Investigation.id == inv_uuid)
        .first()
    )

    if not investigation:
        logger.warning("Investigation %s not found for report generation", inv_uuid)
        raise NotFoundError(message=f"Investigation with ID '{investigation_id}' was not found.")

    # Record report generation audit log row
    report_audit = InvestigationReport(
        id=uuid.uuid4(),
        investigation_id=investigation.id,
        generated_at=datetime.now(timezone.utc),
        format="html",
        file_path="on-demand:audit",
    )
    db.add(report_audit)
    db.commit()
    db.refresh(report_audit)

    # Format final severity
    sev_val = (
        investigation.final_severity.value
        if hasattr(investigation.final_severity, "value")
        else str(investigation.final_severity)
        if investigation.final_severity
        else None
    )

    # Assemble flat and nested findings
    agent_runs_payload: list[dict[str, Any]] = []
    flat_findings: list[dict[str, Any]] = []
    active_findings_count = 0

    for run in investigation.agent_runs:
        run_findings_payload: list[dict[str, Any]] = []
        for f in run.findings:
            if f.status != "failed":
                active_findings_count += 1
            f_dict = {
                "id": str(f.id),
                "agent_name": run.agent_name,
                "finding": f.finding,
                "confidence": f.confidence,
                "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
                "indicators": f.indicators,
                "evidence": f.evidence,
                "reasoning": f.reasoning,
                "external_refs": f.external_refs,
                "status": f.status,
                "timestamp": f.timestamp.isoformat() if f.timestamp else None,
            }
            run_findings_payload.append(f_dict)
            flat_findings.append(f_dict)

        agent_runs_payload.append({
            "id": str(run.id),
            "agent_name": run.agent_name,
            "status": run.status,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "latency_ms": run.latency_ms,
            "findings": run_findings_payload,
        })

    # Assemble risk breakdown
    risk_payload: dict[str, Any] | None = None
    if investigation.final_risk_score is not None or investigation.risk_breakdown:
        avg_conf = investigation.final_confidence or 0.0
        low_conf = (active_findings_count < 2) or (avg_conf < 0.4)

        risk_payload = {
            "score": investigation.final_risk_score,
            "severity": sev_val,
            "confidence": investigation.final_confidence,
            "low_confidence": low_conf,
            "breakdown": [
                {
                    "component": rb.component,
                    "value": rb.value,
                    "weight": rb.weight,
                    "contribution": rb.contribution,
                }
                for rb in investigation.risk_breakdown
            ],
            "conflicts": [
                {
                    "id": str(c.id),
                    "agent_a": c.agent_a,
                    "agent_b": c.agent_b,
                    "conflict_type": c.conflict_type,
                    "resolution_rule": c.resolution_rule,
                    "resolution_outcome": c.resolution_outcome,
                }
                for c in investigation.conflict_logs
            ],
        }

    # Format conflict logs
    conflict_logs_payload = [
        {
            "id": str(c.id),
            "agent_a": c.agent_a,
            "agent_b": c.agent_b,
            "conflict_type": c.conflict_type,
            "resolution_rule": c.resolution_rule,
            "resolution_outcome": c.resolution_outcome,
        }
        for c in investigation.conflict_logs
    ]

    # Format evidence inputs
    evidence_inputs_payload = [
        {
            "id": str(inp.id),
            "modality": inp.modality,
            "raw_content_ref": inp.raw_content_ref,
            "file_path": inp.file_path,
            "created_at": inp.created_at.isoformat() if inp.created_at else None,
        }
        for inp in investigation.evidence_inputs
    ]

    # Format RAG citations
    rag_citations_payload = [
        {
            "id": str(cit.id),
            "source_title": cit.source_title,
            "source_type": cit.source_type,
            "chunk_text": cit.chunk_text,
            "similarity_score": cit.similarity_score,
            "url": cit.url,
        }
        for cit in investigation.rag_citations
    ]

    return {
        "report_id": str(report_audit.id),
        "generated_at": report_audit.generated_at.isoformat(),
        "format": report_audit.format,
        "investigation": {
            "id": str(investigation.id),
            "title": investigation.title,
            "status": investigation.status,
            "created_at": investigation.created_at.isoformat() if investigation.created_at else None,
            "completed_at": investigation.completed_at.isoformat() if investigation.completed_at else None,
            "final_risk_score": investigation.final_risk_score,
            "final_severity": sev_val,
            "final_confidence": investigation.final_confidence,
        },
        "evidence_inputs": evidence_inputs_payload,
        "agent_runs": agent_runs_payload,
        "findings": flat_findings,
        "risk": risk_payload,
        "rag_citations": rag_citations_payload,
        "conflict_logs": conflict_logs_payload,
    }
