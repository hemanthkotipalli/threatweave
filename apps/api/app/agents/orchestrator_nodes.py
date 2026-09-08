"""
app/agents/orchestrator_nodes.py
--------------------------------
Node execution functions for the ThreatWeave LangGraph Orchestrator (Phase 10).
Handles modal classification, dynamic QR-vs-image routing, database persistence
of AgentRun and AgentFinding records with independent session scoping, and
defensive execution of specialist agents.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import app.db.base  # noqa: F401 - ensure all models are registered on Base
from app.agents.correlation import find_conflicts, find_corroboration
from app.agents.image_agent import analyze_image
from app.agents.orchestrator_state import InvestigationState, RoutingTarget
from app.agents.qr_agent import analyze_qr
from app.agents.risk_engine import compute_risk
from app.agents.text_agent import analyze_text
from app.agents.url_agent import analyze_url
from app.agents.voice_agent import analyze_voice
from app.core.config import settings
from app.core.ocr_engine import extract_text
from app.core.qr_decoder import decode_qr
from app.db.session import SessionLocal
from app.models.agent_finding import AgentFinding
from app.models.agent_run import AgentRun
from app.models.conflict_log import ConflictLog
from app.models.enums import AgentStatus, FindingStatus, Severity, SourceType
from app.models.investigation import Investigation
from app.models.rag_citation import RagCitation
from app.models.risk_breakdown import RiskBreakdown
from app.rag.retriever import retrieve_relevant_advisories

logger = logging.getLogger("threatweave-api.agents.orchestrator_nodes")

ALL_SPECIALIST_AGENTS: list[str] = [
    "text_agent",
    "url_agent",
    "qr_agent",
    "image_agent",
    "voice_agent",
]


def _read_file_bytes(file_path: str | None) -> bytes:
    """Reads raw bytes from local disk, resolving relative storage paths, or returns empty bytes."""
    if not file_path:
        return b""
    resolved_path = file_path
    if not os.path.isabs(resolved_path):
        resolved_path = os.path.join(settings.STORAGE_PATH, file_path)
    if not os.path.isfile(resolved_path):
        logger.warning("File path does not exist on disk: %s (resolved: %s)", file_path, resolved_path)
        return b""
    try:
        with open(resolved_path, "rb") as f:
            return f.read()
    except Exception as exc:  # noqa: BLE001
        logger.error("Error reading file bytes at %s: %s", resolved_path, exc)
        return b""


def classify_node(state: InvestigationState) -> dict[str, Any]:
    """
    Reads evidence_inputs already loaded into state and identifies all present modalities.
    """
    logger.info("Orchestrator classify_node: evaluating present modalities")
    present_modalities: list[str] = []
    for ev in state.get("evidence_inputs", []):
        mod = str(ev.get("modality", "")).lower()
        if mod and mod not in present_modalities:
            present_modalities.append(mod)

    logger.info("Discovered modalities: %s", present_modalities)
    return {"present_modalities": present_modalities}


def plan_node(state: InvestigationState) -> dict[str, Any]:
    """
    Plans execution targets for each evidence input based on modality and content.

    CRITICAL QR-VS-IMAGE ROUTING RULE:
    1. Every 'image' evidence input is always tested with qr_decoder.decode_qr() first.
    2. If a QR code is decoded, qr_agent is scheduled.
    3. Surrounding text is checked via OCR: if text length > 15 chars, image_agent is ALSO
       scheduled (hybrid banner/flyer); if <= 15 chars, image_agent is skipped for this input
       (standalone QR code).
    4. If no QR code is found, image_agent is scheduled.

    SKIPPED AGENTS PERSISTENCE:
    For any of the 5 specialist agents not scheduled for this investigation, an AgentRun row
    with status='skipped' and latency_ms=0 is immediately created in the database.
    """
    logger.info("Orchestrator plan_node: determining required specialist agents")
    required_agents: list[RoutingTarget] = []
    evidence_inputs = state.get("evidence_inputs", [])

    for ev in evidence_inputs:
        ev_id = str(ev.get("id", ""))
        modality = str(ev.get("modality", "")).lower()
        raw_content = ev.get("raw_content_ref")
        file_path = ev.get("file_path")

        if modality == "text":
            required_agents.append({
                "agent_name": "text_agent",
                "evidence_input_id": ev_id,
                "modality": "text",
                "content_ref": raw_content,
                "file_path": None,
            })
        elif modality == "url":
            required_agents.append({
                "agent_name": "url_agent",
                "evidence_input_id": ev_id,
                "modality": "url",
                "content_ref": raw_content,
                "file_path": None,
            })
        elif modality == "voice":
            required_agents.append({
                "agent_name": "voice_agent",
                "evidence_input_id": ev_id,
                "modality": "voice",
                "content_ref": None,
                "file_path": file_path,
            })
        elif modality == "image":
            image_bytes = _read_file_bytes(file_path)
            qr_text = decode_qr(image_bytes) if image_bytes else None

            if qr_text:
                logger.info("QR code detected in image input %s -> scheduling qr_agent", ev_id)
                required_agents.append({
                    "agent_name": "qr_agent",
                    "evidence_input_id": ev_id,
                    "modality": "image",
                    "content_ref": None,
                    "file_path": file_path,
                })

                # Check surrounding context
                ocr_text, _ = extract_text(image_bytes) if image_bytes else ("", 0.0)
                if len(ocr_text.strip()) > 15:
                    logger.info("Surrounding OCR text detected in QR image %s (%d chars) -> also scheduling image_agent", ev_id, len(ocr_text))
                    required_agents.append({
                        "agent_name": "image_agent",
                        "evidence_input_id": ev_id,
                        "modality": "image",
                        "content_ref": None,
                        "file_path": file_path,
                    })
                else:
                    logger.info("Image %s contains solely QR code with no surrounding text -> skipping image_agent", ev_id)
            else:
                logger.info("No QR code detected in image input %s -> scheduling image_agent", ev_id)
                required_agents.append({
                    "agent_name": "image_agent",
                    "evidence_input_id": ev_id,
                    "modality": "image",
                    "content_ref": None,
                    "file_path": file_path,
                })

    active_agent_names = list({t["agent_name"] for t in required_agents})
    logger.info("Active agents scheduled to run: %s", active_agent_names)

    # Persist "skipped" status for unrequired specialists in DB
    investigation_uuid = uuid.UUID(state["investigation_id"])
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        existing_runs = db.query(AgentRun).filter(AgentRun.investigation_id == investigation_uuid).all()
        existing_agent_names = {r.agent_name for r in existing_runs}

        for agent in ALL_SPECIALIST_AGENTS:
            if agent not in active_agent_names and agent not in existing_agent_names:
                skipped_run = AgentRun(
                    investigation_id=investigation_uuid,
                    agent_name=agent,
                    status=AgentStatus.SKIPPED,
                    started_at=now,
                    finished_at=now,
                    latency_ms=0,
                )
                db.add(skipped_run)
        db.commit()

    return {
        "required_agents": required_agents,
        "active_agent_names": active_agent_names,
    }


def _execute_specialist_node(agent_name: str, state: InvestigationState) -> dict[str, Any]:
    """
    Generic execution harness for an individual specialist agent.
    Opens an independent database session, manages AgentRun lifecycle,
    persists AgentFinding records, and returns findings via reducer.
    """
    targets = [t for t in state.get("required_agents", []) if t["agent_name"] == agent_name]
    if not targets:
        return {"findings": []}

    investigation_uuid = uuid.UUID(state["investigation_id"])
    findings_to_return: list[dict[str, Any]] = []

    for target in targets:
        now = datetime.now(timezone.utc)
        # Open independent database session per execution branch
        with SessionLocal() as db:
            run = AgentRun(
                investigation_id=investigation_uuid,
                agent_name=agent_name,
                status=AgentStatus.RUNNING,
                started_at=now,
            )
            db.add(run)
            db.commit()
            db.refresh(run)

            t0 = time.time()
            try:
                # Dispatch to corresponding specialist function
                if agent_name == "text_agent":
                    item = analyze_text(target.get("content_ref") or "")
                elif agent_name == "url_agent":
                    item = analyze_url(target.get("content_ref") or "")
                elif agent_name == "qr_agent":
                    img_bytes = _read_file_bytes(target.get("file_path"))
                    item = analyze_qr(img_bytes)
                elif agent_name == "image_agent":
                    img_bytes = _read_file_bytes(target.get("file_path"))
                    item = analyze_image(img_bytes)
                elif agent_name == "voice_agent":
                    audio_bytes = _read_file_bytes(target.get("file_path"))
                    item = analyze_voice(audio_bytes)
                else:
                    raise ValueError(f"Unknown specialist agent: {agent_name}")

                elapsed_ms = int((time.time() - t0) * 1000)

                # Persist AgentFinding row
                sev_val = item.severity.lower() if item.severity else "info"
                status_val = item.status.lower() if item.status else "ok"

                finding_row = AgentFinding(
                    agent_run_id=run.id,
                    finding=item.finding,
                    confidence=item.confidence,
                    severity=Severity(sev_val) if sev_val in [s.value for s in Severity] else Severity.INFO,
                    indicators=item.indicators,
                    evidence=item.evidence,
                    reasoning=item.reasoning,
                    external_refs=item.external_refs,
                    status=FindingStatus(status_val) if status_val in [f.value for f in FindingStatus] else FindingStatus.OK,
                )
                db.add(finding_row)

                run.status = AgentStatus.DONE
                run.finished_at = datetime.now(timezone.utc)
                run.latency_ms = elapsed_ms
                db.commit()

                findings_to_return.append(item.model_dump(mode="json"))

            except Exception:
                elapsed_ms = int((time.time() - t0) * 1000)
                logger.exception("Agent %s failed during execution", agent_name)
                run.status = AgentStatus.FAILED
                run.finished_at = datetime.now(timezone.utc)
                run.latency_ms = elapsed_ms
                db.commit()

    return {"findings": findings_to_return}


def text_agent_node(state: InvestigationState) -> dict[str, Any]:
    """Node wrapper executing Text Agent analysis."""
    logger.info("Executing text_agent_node")
    return _execute_specialist_node("text_agent", state)


def url_agent_node(state: InvestigationState) -> dict[str, Any]:
    """Node wrapper executing URL Agent analysis."""
    logger.info("Executing url_agent_node")
    return _execute_specialist_node("url_agent", state)


def qr_agent_node(state: InvestigationState) -> dict[str, Any]:
    """Node wrapper executing QR Agent analysis."""
    logger.info("Executing qr_agent_node")
    return _execute_specialist_node("qr_agent", state)


def image_agent_node(state: InvestigationState) -> dict[str, Any]:
    """Node wrapper executing Image Agent analysis."""
    logger.info("Executing image_agent_node")
    return _execute_specialist_node("image_agent", state)


def voice_agent_node(state: InvestigationState) -> dict[str, Any]:
    """Node wrapper executing Voice Agent analysis."""
    logger.info("Executing voice_agent_node")
    return _execute_specialist_node("voice_agent", state)


def collect_node(state: InvestigationState) -> dict[str, Any]:
    """
    Convergence node gathering all findings from parallel branches.
    Hands off merged findings directly to downstream correlation and risk engine nodes.
    """
    total_findings = len(state.get("findings", []))
    logger.info("Orchestrator collect_node: gathered %d findings across swarm agents", total_findings)
    return {}


def correlate_node(state: InvestigationState) -> dict[str, Any]:
    """
    Performs cross-agent evidence correlation and conflict detection (Phase 11).
    Groups shared indicators across agents and detects significant severity divergences.
    """
    findings = state.get("findings", [])
    logger.info("Orchestrator correlate_node: running correlation across %d findings", len(findings))

    corroborations = find_corroboration(findings)
    conflicts = find_conflicts(findings)

    logger.info(
        "Correlation complete: %d corroboration groups found, %d conflicts detected",
        len(corroborations),
        len(conflicts),
    )
    return {
        "corroborations": corroborations,
        "conflicts": conflicts,
    }


def conflict_resolution_node(state: InvestigationState) -> dict[str, Any]:
    """
    Logs detected conflicts between active agents to the database (Phase 11).
    Conflicts are NEVER silently averaged away — every discrepancy is written to
    the conflict_logs table with resolution rule 'contradiction_penalty_applied'.
    """
    conflicts = state.get("conflicts", [])
    inv_id_str = state.get("investigation_id")
    if not conflicts or not inv_id_str:
        logger.info("Orchestrator conflict_resolution_node: no conflicts to log")
        return {}

    logger.info("Logging %d conflicts for investigation %s", len(conflicts), inv_id_str)
    inv_uuid = uuid.UUID(inv_id_str)

    with SessionLocal() as db:
        for c in conflicts:
            conflict_row = ConflictLog(
                investigation_id=inv_uuid,
                agent_a=c.get("agent_a", "unknown"),
                agent_b=c.get("agent_b", "unknown"),
                conflict_type=c.get("conflict_type", "severity_divergence"),
                resolution_rule="contradiction_penalty_applied",
                resolution_outcome=(
                    f"Contradiction penalty of -0.10 applied to final risk score ({c.get('description', '')})"
                ),
            )
            db.add(conflict_row)
        db.commit()

    return {}


def rag_node(state: InvestigationState) -> dict[str, Any]:
    """
    RAG threat intelligence retrieval node (Phase 12).
    Aggregates indicators and finding descriptions across specialist findings,
    retrieves similarity-clearing advisory citations from ChromaDB,
    and persists RagCitation records to the database.
    """
    findings = state.get("findings", [])
    inv_id_str = state.get("investigation_id")
    valid_findings = [f for f in findings if f.get("status") != "failed"]

    all_indicators: list[str] = []
    finding_texts: list[str] = []

    for f in valid_findings:
        inds = f.get("indicators", [])
        if isinstance(inds, list):
            all_indicators.extend(inds)
        text = f.get("finding", "")
        if text and len(text.strip()) > 5:
            finding_texts.append(text.strip())

    # Deduplicate indicators preserving order
    deduped_indicators = list(dict.fromkeys(all_indicators))

    logger.info(
        "Orchestrator rag_node: querying threat intelligence for %d indicators and %d finding texts",
        len(deduped_indicators),
        len(finding_texts),
    )

    citations = retrieve_relevant_advisories(
        indicators=deduped_indicators,
        finding_texts=finding_texts,
        top_k=settings.RAG_TOP_K,
        threshold=settings.RAG_SIMILARITY_THRESHOLD,
    )

    logger.info(
        "RAG retrieval complete: %d relevant advisory citations cleared threshold (>= %.2f)",
        len(citations),
        settings.RAG_SIMILARITY_THRESHOLD,
    )

    if inv_id_str:
        inv_uuid = uuid.UUID(inv_id_str)
        with SessionLocal() as db:
            # Idempotently delete previous rag citations if re-running
            db.query(RagCitation).filter(RagCitation.investigation_id == inv_uuid).delete()

            for c in citations:
                st_raw = c.get("source_type", "Scam-Intel")
                matched_source = SourceType.SCAM_INTEL
                for st in SourceType:
                    if st.value == st_raw or st.name.lower() == st_raw.lower().replace("-", "_"):
                        matched_source = st
                        break

                rc = RagCitation(
                    investigation_id=inv_uuid,
                    source_title=c.get("source_title", "Unknown Advisory"),
                    source_type=matched_source,
                    chunk_text=c.get("chunk_text", ""),
                    similarity_score=float(c.get("similarity_score", 0.0)),
                    url=c.get("url"),
                )
                db.add(rc)
                c["id"] = str(rc.id)
            db.commit()

    return {"rag_citations": citations}


def risk_engine_node(state: InvestigationState) -> dict[str, Any]:
    """
    Computes deterministic risk score and formula breakdown (Phases 11 & 12).
    Persists RiskBreakdown component records to the database and updates the
    Investigation record's final_risk_score, final_severity, and final_confidence.
    """
    findings = state.get("findings", [])
    rag_citations = state.get("rag_citations", [])
    inv_id_str = state.get("investigation_id")
    logger.info(
        "Orchestrator risk_engine_node: computing risk for investigation %s (with %d RAG citations)",
        inv_id_str,
        len(rag_citations),
    )

    risk_result = compute_risk(findings, rag_citations=rag_citations)
    logger.info(
        "Risk calculation result: final_risk=%.4f, severity=%s, confidence=%.4f, intel_bonus=%.2f, low_confidence=%s",
        risk_result["final_risk"],
        risk_result["severity"],
        risk_result["confidence"],
        risk_result["intel_bonus"],
        risk_result["low_confidence"],
    )

    if inv_id_str:
        inv_uuid = uuid.UUID(inv_id_str)
        with SessionLocal() as db:
            investigation = db.query(Investigation).filter(Investigation.id == inv_uuid).first()
            if investigation:
                # Idempotently delete previous breakdown rows if any
                db.query(RiskBreakdown).filter(RiskBreakdown.investigation_id == inv_uuid).delete()

                for item in risk_result.get("breakdown", []):
                    rb = RiskBreakdown(
                        investigation_id=inv_uuid,
                        component=item["component"],
                        value=float(item["value"]),
                        weight=float(item["weight"]),
                        contribution=float(item["contribution"]),
                    )
                    db.add(rb)

                investigation.final_risk_score = risk_result["final_risk"]
                investigation.final_severity = Severity(risk_result["severity"])
                investigation.final_confidence = risk_result["confidence"]
                db.commit()

    return {"risk_result": risk_result}


