"""
app/agents/url_agent.py
-----------------------
ThreatWeave Phase 6 — URL Agent.

Public API
----------
    analyze_url(url: str) -> EvidenceItem

Layered fallback architecture
------------------------------
Layer 1 — Heuristics  (always runs, never fails):
    app.core.url_heuristics.run_heuristics()

Layer 2 — Reputation  (optional, skip-safe):
    app.agents.reputation_client.check_reputation()
    → None if unconfigured; ExternalServiceError if configured-but-failed.
    Either outcome is handled gracefully — analysis continues.

Layer 3 — LLM Synthesis  (optional, fallback-safe):
    app.agents.llm_client.call_llm()
    → On failure, a template string is built from heuristic output and
      status is set to "degraded_fallback".

Layer 4 — Safety net:
    Any unhandled exception at any layer returns a minimal EvidenceItem
    with status="failed" and confidence=0.0.  Nothing ever propagates out.

Severity authority
------------------
Final severity is driven by the heuristic layer's suggested_severity.
The LLM synthesis step produces "finding" and "reasoning" text ONLY —
it CANNOT override the severity computed from structural heuristics.
Reputation data CAN upgrade severity one step (medium → high) if the API
marks the URL as confirmed malicious.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from app.agents.llm_client import call_llm
from app.agents.prompts.url_agent_prompt import SYSTEM_PROMPT
from app.agents.reputation_client import check_reputation
from app.core.errors import ExternalServiceError
from app.core.indicators import VALID_INDICATORS
from app.core.url_heuristics import run_heuristics
from app.schemas.evidence import EvidenceItem

logger = logging.getLogger("threatweave-api.agents.url_agent")

# ---------------------------------------------------------------------------
# Severity helpers
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = ["info", "low", "medium", "high", "critical"]


def _upgrade_severity(current: str, steps: int = 1) -> str:
    """Bump severity up by `steps` levels, capped at 'critical'."""
    idx = _SEVERITY_ORDER.index(current) if current in _SEVERITY_ORDER else 0
    return _SEVERITY_ORDER[min(idx + steps, len(_SEVERITY_ORDER) - 1)]


def _severity_to_confidence(severity: str) -> float:
    """Map heuristic severity to a baseline confidence score."""
    return {
        "info": 0.1,
        "low": 0.35,
        "medium": 0.55,
        "high": 0.75,
        "critical": 0.92,
    }.get(severity, 0.1)


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def _clean_json(raw: str) -> str:
    """Strip markdown fences from an LLM response."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
    return cleaned


# ---------------------------------------------------------------------------
# Template fallback text builder
# ---------------------------------------------------------------------------

def _build_fallback_finding(indicators: list[str], severity: str) -> tuple[str, str]:
    """
    Constructs a plain-text finding and reasoning from heuristic output
    when the LLM path is unavailable.
    """
    if not indicators:
        finding = "No structural threat indicators detected in this URL."
        reasoning = "All heuristic checks passed without flagging suspicious patterns."
    else:
        indicator_phrase = ", ".join(indicators)
        finding = (
            f"URL flagged for structural indicators: {indicator_phrase}."
        )
        reasoning = (
            f"Heuristic analysis identified {len(indicators)} concern(s): "
            f"{indicator_phrase}. "
            f"Severity assessed as '{severity}' based on flag corroboration rules."
        )
    return finding, reasoning


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_url(url: str) -> EvidenceItem:
    """
    Analyses a URL for phishing, malware, and structural threat indicators.

    Execution layers:
    1. Structural heuristics (always — network-free).
    2. Optional reputation API (skipped if unconfigured; continues on failure).
    3. LLM synthesis of heuristic findings into plain language.
    4. Template-based text generation if LLM is unavailable.
    5. Safety-net return on any unhandled error.

    :param url: The URL string to analyse.
    :return: EvidenceItem with status "ok", "degraded_fallback", or "failed".
    """
    timestamp = datetime.now(timezone.utc)

    try:
        # ------------------------------------------------------------------
        # Layer 1: Heuristics — always runs, never raises
        # ------------------------------------------------------------------
        logger.info("Running URL heuristics for url=%r", url)
        heuristic_result = run_heuristics(url)

        raw_indicators: list[str] = heuristic_result.get("indicators", [])
        suggested_severity: str = heuristic_result.get("suggested_severity", "info")
        details: dict = heuristic_result.get("details", {})

        # Validate indicators against shared vocabulary
        indicators: list[str] = [
            ind for ind in raw_indicators if ind in VALID_INDICATORS
        ]
        dropped = set(raw_indicators) - set(indicators)
        if dropped:
            logger.warning("Dropped unknown heuristic indicators: %s", dropped)

        # ------------------------------------------------------------------
        # Layer 2: Reputation (optional — skip-safe)
        # ------------------------------------------------------------------
        reputation_data: dict | None = None
        try:
            reputation_data = check_reputation(url)
            if reputation_data is not None:
                logger.info("Reputation data received for url=%r", url)
                # If reputation confirms malicious → bump severity one step
                rep_malicious = reputation_data.get("malicious", False)
                if rep_malicious and suggested_severity not in ("high", "critical"):
                    suggested_severity = _upgrade_severity(suggested_severity)
                    logger.info(
                        "Severity upgraded to %s due to reputation confirmation.",
                        suggested_severity,
                    )
        except ExternalServiceError as rep_err:
            logger.warning(
                "Reputation check failed (%s) — continuing without reputation data.",
                rep_err,
            )
            reputation_data = None

        # ------------------------------------------------------------------
        # Layer 3: LLM synthesis
        # ------------------------------------------------------------------
        evidence: dict = {"heuristics": details}
        if reputation_data:
            evidence["reputation"] = reputation_data

        # Build user content for LLM: the pre-computed findings, not the raw URL
        user_content = json.dumps({
            "url_structure_summary": {
                "indicators_found": indicators,
                "suggested_severity": suggested_severity,
                "heuristic_details": details,
            }
        })

        finding: str
        reasoning: str
        status: str
        confidence: float = _severity_to_confidence(suggested_severity)

        try:
            logger.info("Invoking LLM synthesis for URL heuristic findings")
            raw_response = call_llm(
                system_prompt=SYSTEM_PROMPT,
                user_content=user_content,
            )
            cleaned = _clean_json(raw_response)
            parsed = json.loads(cleaned)

            finding = str(parsed.get("finding", "URL structural analysis completed."))
            reasoning = str(parsed.get("reasoning", "Analysis completed by LLM."))
            llm_confidence = parsed.get("confidence")
            if llm_confidence is not None:
                # Blend: 70% heuristic baseline, 30% LLM confidence
                confidence = round(
                    0.7 * confidence + 0.3 * float(llm_confidence), 4
                )
            confidence = max(0.0, min(1.0, confidence))
            status = "ok"

        except (ExternalServiceError, json.JSONDecodeError, TypeError, KeyError, ValueError, RuntimeError) as llm_err:
            logger.warning(
                "LLM synthesis failed (%s) — using template fallback.", llm_err
            )
            finding, reasoning = _build_fallback_finding(indicators, suggested_severity)
            status = "degraded_fallback"

        # ------------------------------------------------------------------
        # Assemble and return EvidenceItem
        # ------------------------------------------------------------------
        if suggested_severity not in ("info", "low", "medium", "high", "critical"):
            suggested_severity = "info"

        return EvidenceItem(
            agent="url_agent",
            modality="url",
            finding=finding,
            confidence=confidence,
            severity=suggested_severity,
            indicators=indicators,
            evidence=evidence,
            reasoning=reasoning,
            status=status,
            timestamp=timestamp,
        )

    except Exception:
        logger.exception("Unexpected error inside URL Agent for url=%r", url)

    # ------------------------------------------------------------------
    # Layer 4 — Safety net: nothing ever escapes
    # ------------------------------------------------------------------
    return EvidenceItem(
        agent="url_agent",
        modality="url",
        finding="URL analysis could not be completed.",
        confidence=0.0,
        severity="info",
        indicators=[],
        evidence={},
        reasoning="URL Agent encountered an unrecoverable error.",
        status="failed",
        timestamp=timestamp,
    )
