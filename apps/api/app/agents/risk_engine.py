"""
app/agents/risk_engine.py
-------------------------
Deterministic, defensible multi-agent risk scoring engine for ThreatWeave (Phase 11).

Implements the exact mathematical formula:
    base_score = mean(severity_weight * confidence across non-failed findings)
    corroboration_bonus = +0.10 per additional corroborating agent beyond the first per group, capped at +0.25
    intel_bonus = 0.0 (Phase 12 placeholder)
    contradiction_penalty = 0.10 * len(conflicts), capped at 0.30
    final_risk = clamp(base_score + corroboration_bonus + intel_bonus - contradiction_penalty, 0.0, 1.0)

This is a PURE mathematical function with zero database or LLM calls.
"""
from __future__ import annotations

import logging
from typing import Any

from app.agents.correlation import find_conflicts, find_corroboration
from app.core.config import settings

logger = logging.getLogger("threatweave-api.agents.risk_engine")

# Strict architectural severity weights
SEVERITY_WEIGHTS: dict[str, float] = {
    "info": 0.0,
    "low": 0.25,
    "medium": 0.50,
    "high": 0.75,
    "critical": 1.00,
}


def _determine_severity_band(score: float) -> str:
    """
    Maps continuous numeric score [0.0, 1.0] to discrete severity bands:
    0.00-0.19 info, 0.20-0.39 low, 0.40-0.59 medium, 0.60-0.79 high, 0.80-1.00 critical.
    """
    if score < 0.20:
        return "info"
    if score < 0.40:
        return "low"
    if score < 0.60:
        return "medium"
    if score < 0.80:
        return "high"
    return "critical"


def compute_risk(
    findings: list[dict[str, Any]],
    rag_citations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Computes a deterministic risk score across consolidated agent findings.
    
    This is a pure mathematical function:
    - Same input findings list always produces byte-identical output.
    - Zero randomness, zero database queries, zero external network or LLM calls.

    :param findings: List of EvidenceItem dictionaries from specialist agents.
    :param rag_citations: Optional list of retrieved external threat advisory citations.
    :return: Dictionary containing:
        - final_risk: float [0.0, 1.0]
        - severity: str ('info', 'low', 'medium', 'high', 'critical')
        - confidence: float [0.0, 1.0] (average confidence of included findings)
        - low_confidence: bool (True if < 2 findings or avg_confidence < 0.4)
        - base_score: float
        - corroboration_bonus: float
        - intel_bonus: float
        - contradiction_penalty: float
        - breakdown: list of component breakdown dictionaries
        - corroborations: list of corroboration groups
        - conflicts: list of detected conflicts
    """
    # 1. Filter out failed findings entirely
    # Findings with status == 'degraded_fallback' ARE included, same as 'ok'
    included_findings = [
        f for f in findings if f.get("status") != "failed"
    ]

    # 2. Base Score Calculation
    if not included_findings:
        base_score = 0.0
        avg_confidence = 0.0
    else:
        per_finding_scores = []
        confidences = []
        for f in included_findings:
            sev = str(f.get("severity", "info")).lower()
            weight = SEVERITY_WEIGHTS.get(sev, 0.0)
            conf = float(f.get("confidence", 0.0))
            # Clamp confidence defensibly between 0.0 and 1.0
            conf = max(0.0, min(1.0, conf))
            confidences.append(conf)
            per_finding_scores.append(weight * conf)

        base_score = sum(per_finding_scores) / len(per_finding_scores)
        avg_confidence = sum(confidences) / len(confidences)

    # 3. Corroboration Bonus
    # Group findings by shared indicator strings across DIFFERENT agents
    # For each group of 2+ agents, +0.10 per additional agent beyond first, capped at +0.25 total
    corroboration_groups = find_corroboration(included_findings)
    raw_corroboration_bonus = sum(
        0.10 * (len(group["agents"]) - 1) for group in corroboration_groups
    )
    corroboration_bonus = min(0.25, raw_corroboration_bonus)

    # 4. Intel Bonus (Phase 12 live RAG-derived logic)
    citations = rag_citations or []
    intel_bonus = (
        0.15
        if any(
            float(c.get("similarity_score", 0.0)) >= settings.RAG_SIMILARITY_THRESHOLD
            for c in citations
        )
        else 0.0
    )

    # 5. Contradiction Penalty
    # -0.10 per detected conflict, capped at 0.30
    conflicts = find_conflicts(included_findings)
    raw_contradiction_penalty = 0.10 * len(conflicts)
    contradiction_penalty = min(0.30, raw_contradiction_penalty)

    # 6. Final Risk Calculation
    raw_final_risk = base_score + corroboration_bonus + intel_bonus - contradiction_penalty
    final_risk = max(0.0, min(1.0, raw_final_risk))

    # 7. Severity Banding
    severity = _determine_severity_band(final_risk)

    # 8. Uncertainty Rule:
    # If fewer than 2 findings were included in base_score calculation,
    # OR average confidence across included findings is < 0.4, set low_confidence=True
    low_confidence = (len(included_findings) < 2) or (avg_confidence < 0.4)

    # 9. Format Detailed Formula Breakdown
    breakdown = [
        {
            "component": "base_score",
            "value": round(base_score, 4),
            "weight": 1.0,
            "contribution": round(base_score, 4),
        },
        {
            "component": "corroboration_bonus",
            "value": round(corroboration_bonus, 4),
            "weight": 1.0,
            "contribution": round(corroboration_bonus, 4),
        },
        {
            "component": "intel_bonus",
            "value": round(intel_bonus, 4),
            "weight": 1.0,
            "contribution": round(intel_bonus, 4),
        },
        {
            "component": "contradiction_penalty",
            "value": round(contradiction_penalty, 4),
            "weight": -1.0,
            "contribution": round(-contradiction_penalty, 4),
        },
    ]

    return {
        "final_risk": round(final_risk, 4),
        "severity": severity,
        "confidence": round(avg_confidence, 4),
        "low_confidence": low_confidence,
        "base_score": round(base_score, 4),
        "corroboration_bonus": round(corroboration_bonus, 4),
        "intel_bonus": round(intel_bonus, 4),
        "contradiction_penalty": round(contradiction_penalty, 4),
        "breakdown": breakdown,
        "corroborations": corroboration_groups,
        "conflicts": conflicts,
    }
