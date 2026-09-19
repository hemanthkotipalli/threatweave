"""
apps/api/app/services/report_service.py
---------------------------------------
Service for assembling comprehensive investigation reports on demand.
Maintains an immutable audit log entry in the `investigation_reports` table
every time a report is requested.
"""
from __future__ import annotations

import html
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundError
from app.models.agent_run import AgentRun
from app.models.investigation import Investigation
from app.models.investigation_report import InvestigationReport

logger = logging.getLogger("threatweave-api.services.report")


def generate_report(
    investigation_id: str | uuid.UUID,
    db: Session,
    format_type: str = "html",
) -> dict[str, Any]:
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
        format=format_type,
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


def generate_pdf_report(report_data: dict[str, Any]) -> bytes:
    """
    Renders structured investigation report dictionary into a publication-grade,
    container-independent PDF document using ReportLab.

    Guarantees:
    - Pure Python / standard C extension with zero external OS font/library dependencies.
    - Deterministic, consistent styling across Windows and Linux Docker containers.
    - Full coverage of metadata, risk breakdown, evidence, findings, citations, and conflicts.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0E0C0B"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748B"),
    )
    section_h1 = ParagraphStyle(
        "SectionH1",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0E0C0B"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
    )
    body_bold = ParagraphStyle(
        "BodyDarkBold",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0E0C0B"),
    )
    meta_label = ParagraphStyle(
        "MetaLabel",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#475569"),
    )
    meta_val = ParagraphStyle(
        "MetaVal",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0F172A"),
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1E293B"),
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#0F172A"),
    )
    badge_style = ParagraphStyle(
        "BadgeText",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=colors.white,
    )

    def esc(text: Any) -> str:
        return html.escape(str(text)) if text is not None else ""

    sev_color_map = {
        "critical": colors.HexColor("#DC2626"),
        "high": colors.HexColor("#EA580C"),
        "medium": colors.HexColor("#D97706"),
        "low": colors.HexColor("#2563EB"),
        "info": colors.HexColor("#4B5563"),
    }

    inv = report_data.get("investigation", {})
    risk = report_data.get("risk") or {}
    evidence_inputs = report_data.get("evidence_inputs", [])
    findings = report_data.get("findings", [])
    rag_citations = report_data.get("rag_citations", [])
    conflict_logs = report_data.get("conflict_logs", [])

    final_sev = str(inv.get("final_severity") or "info").lower()
    sev_color = sev_color_map.get(final_sev, colors.HexColor("#4B5563"))

    story = []

    # 1. Header Banner
    story.append(Paragraph("THREATWEAVE INTELLIGENCE DOSSIER", title_style))
    story.append(Paragraph("Autonomous Agentic Multimodal Cyber Threat Intelligence &amp; Incident Response", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#FF6B35"), spaceBefore=6, spaceAfter=10))

    # 2. Metadata Grid Table
    inv_title = esc(inv.get("title") or "Untitled Investigation")
    inv_id = esc(inv.get("id") or "")
    inv_status = esc(inv.get("status") or "unknown").upper()
    created_at = esc(inv.get("created_at") or "N/A")
    completed_at = esc(inv.get("completed_at") or "N/A")
    report_gen_at = esc(report_data.get("generated_at") or "N/A")

    meta_table_data = [
        [
            Paragraph("<b>Investigation:</b>", meta_label), Paragraph(inv_title, meta_val),
            Paragraph("<b>Status:</b>", meta_label), Paragraph(inv_status, meta_val),
        ],
        [
            Paragraph("<b>Identifier:</b>", meta_label), Paragraph(inv_id, meta_val),
            Paragraph("<b>Created:</b>", meta_label), Paragraph(created_at, meta_val),
        ],
        [
            Paragraph("<b>Report Generated:</b>", meta_label), Paragraph(report_gen_at, meta_val),
            Paragraph("<b>Completed:</b>", meta_label), Paragraph(completed_at, meta_val),
        ],
    ]
    meta_table = Table(meta_table_data, colWidths=[90, 200, 70, 180])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # 3. Executive Threat Assessment
    story.append(Paragraph("1. Executive Threat Assessment", section_h1))

    score_val = risk.get("score")
    score_str = f"{score_val:.4f}" if score_val is not None else "N/A"
    conf_val = risk.get("confidence")
    conf_str = f"{(conf_val * 100):.1f}%" if conf_val is not None else "N/A"
    low_conf = risk.get("low_confidence", False)

    summary_banner_data = [
        [
            Paragraph("<b>COMPOSITE RISK SCORE</b>", meta_label),
            Paragraph("<b>SEVERITY LEVEL</b>", meta_label),
            Paragraph("<b>EPISTEMIC CONFIDENCE</b>", meta_label),
            Paragraph("<b>UNCERTAINTY FLAG</b>", meta_label),
        ],
        [
            Paragraph(f"<font size=14><b>{score_str}</b></font> / 1.0", body_bold),
            Paragraph(f"<b>{final_sev.upper()}</b>", ParagraphStyle("SevBadge", parent=badge_style, textColor=sev_color, fontSize=11, leading=13)),
            Paragraph(f"<font size=11><b>{conf_str}</b></font>", body_bold),
            Paragraph("FLAGGED (Low Conf)" if low_conf else "CONFIRMED", ParagraphStyle("ConfFlag", parent=body_style, textColor=colors.HexColor("#DC2626") if low_conf else colors.HexColor("#16A34A"), fontName="Helvetica-Bold")),
        ],
    ]
    summary_table = Table(summary_banner_data, colWidths=[140, 130, 140, 130])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FFFFFF")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94A3B8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 8))

    # Mathematical Formula Decomposition Table
    breakdown_list = risk.get("breakdown") or []
    if breakdown_list:
        decomp_rows = [
            [
                Paragraph("<b>Component Name</b>", table_cell_bold),
                Paragraph("<b>Engine Value</b>", table_cell_bold),
                Paragraph("<b>Mathematical Weight</b>", table_cell_bold),
                Paragraph("<b>Risk Contribution</b>", table_cell_bold),
            ]
        ]
        for item in breakdown_list:
            comp_name = esc(item.get("component", "")).replace("_", " ").title()
            val = item.get("value", 0.0)
            weight = item.get("weight", 1.0)
            contrib = item.get("contribution", 0.0)
            decomp_rows.append([
                Paragraph(comp_name, table_cell),
                Paragraph(f"{val:+.4f}", table_cell),
                Paragraph(f"{weight:+.2f}", table_cell),
                Paragraph(f"<b>{contrib:+.4f}</b>", table_cell_bold),
            ])
        decomp_table = Table(decomp_rows, colWidths=[180, 120, 120, 120])
        decomp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(decomp_table)
    story.append(Spacer(1, 12))

    # 4. Ingested Evidence Inputs
    story.append(Paragraph("2. Ingested Evidence Inputs", section_h1))
    if evidence_inputs:
        ev_rows = [
            [
                Paragraph("<b>Modality</b>", table_cell_bold),
                Paragraph("<b>Content Reference / Path</b>", table_cell_bold),
                Paragraph("<b>Ingested Timestamp</b>", table_cell_bold),
            ]
        ]
        for ev in evidence_inputs:
            mod = esc(ev.get("modality", "")).upper()
            ref = esc(ev.get("raw_content_ref") or ev.get("file_path") or "")
            ts = esc(ev.get("created_at") or "")
            ev_rows.append([
                Paragraph(f"<b>{mod}</b>", table_cell),
                Paragraph(ref, table_cell),
                Paragraph(ts, table_cell),
            ])
        ev_table = Table(ev_rows, colWidths=[80, 320, 140])
        ev_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(ev_table)
    else:
        story.append(Paragraph("No raw evidence items logged for this investigation.", body_style))
    story.append(Spacer(1, 12))

    # 5. Multi-Agent Swarm Findings
    story.append(Paragraph("3. Multi-Agent Swarm Evidence Findings", section_h1))
    if findings:
        for idx, f in enumerate(findings, 1):
            agent = esc(f.get("agent_name", "Unknown Agent")).replace("_", " ").title()
            f_sev = str(f.get("severity", "info")).lower()
            f_conf = f.get("confidence", 0.0)
            f_text = esc(f.get("finding", ""))
            reasoning = esc(f.get("reasoning", ""))
            indicators = f.get("indicators") or []
            ind_str = ", ".join(esc(i) for i in indicators) if indicators else "None extracted"

            finding_box = [
                [
                    Paragraph(f"<b>Finding #{idx}: {agent}</b>", table_cell_bold),
                    Paragraph(f"Severity: <b>{f_sev.upper()}</b> | Conf: <b>{f_conf:.2f}</b>", table_cell_bold),
                ],
                [
                    Paragraph(f"<b>Assessment:</b> {f_text}", table_cell),
                    Paragraph(f"<b>Indicators:</b> {ind_str}", table_cell),
                ],
            ]
            if reasoning:
                finding_box.append([
                    Paragraph(f"<b>Reasoning:</b> {reasoning}", table_cell),
                    Paragraph("", table_cell),
                ])

            f_table = Table(finding_box, colWidths=[360, 180])
            f_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#FFFFFF")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(KeepTogether([f_table, Spacer(1, 6)]))
    else:
        story.append(Paragraph("No specialist agent findings recorded.", body_style))
    story.append(Spacer(1, 8))

    # 6. RAG Grounding Citations
    story.append(Paragraph("4. Curated Threat Intelligence Grounding (RAG)", section_h1))
    if rag_citations:
        rag_rows = [
            [
                Paragraph("<b>Advisory Title &amp; Source</b>", table_cell_bold),
                Paragraph("<b>Similarity Score</b>", table_cell_bold),
                Paragraph("<b>Matched Intelligence Excerpt</b>", table_cell_bold),
            ]
        ]
        for cit in rag_citations:
            title_text = esc(cit.get("source_title", "Unknown Source"))
            src_type = esc(cit.get("source_type", ""))
            sim = cit.get("similarity_score", 0.0)
            chunk = esc(cit.get("chunk_text", ""))
            if len(chunk) > 200:
                chunk = chunk[:200] + "..."
            rag_rows.append([
                Paragraph(f"<b>{title_text}</b><br/><i>{src_type}</i>", table_cell),
                Paragraph(f"&sigma; = <b>{sim:.4f}</b>", table_cell),
                Paragraph(chunk, table_cell),
            ])
        rag_table = Table(rag_rows, colWidths=[180, 80, 280])
        rag_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(rag_table)
    else:
        story.append(Paragraph("No external advisories cleared the semantic similarity threshold (&sigma; &ge; 0.40).", body_style))
    story.append(Spacer(1, 12))

    # 7. Inter-Agent Conflicts & Resolution Telemetry
    story.append(Paragraph("5. Inter-Agent Conflict Resolution Log", section_h1))
    if conflict_logs:
        conf_rows = [
            [
                Paragraph("<b>Conflicting Agents</b>", table_cell_bold),
                Paragraph("<b>Conflict Type</b>", table_cell_bold),
                Paragraph("<b>Resolution Rule &amp; Outcome</b>", table_cell_bold),
            ]
        ]
        for c in conflict_logs:
            agents = f"{esc(c.get('agent_a', ''))} vs {esc(c.get('agent_b', ''))}"
            c_type = esc(c.get("conflict_type", ""))
            rule = esc(c.get("resolution_rule", ""))
            outcome = esc(c.get("resolution_outcome", ""))
            conf_rows.append([
                Paragraph(agents, table_cell),
                Paragraph(c_type, table_cell),
                Paragraph(f"<b>{rule}:</b> {outcome}", table_cell),
            ])
        conf_table = Table(conf_rows, colWidths=[140, 140, 260])
        conf_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(conf_table)
    else:
        story.append(Paragraph("Zero inter-modality contradictions detected across active specialist agents.", body_style))
    story.append(Spacer(1, 16))

    # 8. Footer Certification
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceBefore=8, spaceAfter=8))
    story.append(Paragraph(
        "Report compiled autonomously by ThreatWeave Swarm Orchestrator. "
        "Risk scores and corroboration heuristics are computed deterministically without external LLM stochasticity.",
        subtitle_style
    ))

    doc.build(story)
    return buffer.getvalue()
