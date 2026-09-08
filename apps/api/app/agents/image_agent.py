"""
app/agents/image_agent.py
--------------------------
ThreatWeave Phase 8 — Image Agent.

Public API
----------
    analyze_image(image_bytes: bytes) -> EvidenceItem

Architecture & Delegation
-------------------------
1. OCR Layer:
   - Uses app.core.ocr_engine.extract_text() to extract text & confidence.
   - If image bytes are invalid/corrupt -> returns failed EvidenceItem.
   - If image is valid but no text detected -> returns clean EvidenceItem with "ocr_failed".

2. Image Heuristics:
   - Evaluates fake_payment_confirmation, impersonation_banner, embedded_contact_info.

3. Genuine Delegation:
   - Discovered URLs: Each URL is delegated directly to app.agents.url_agent.analyze_url().
   - Extracted Text: Delegated directly to app.agents.text_agent.analyze_text().

4. Severity Reconciliation:
   - Final severity is the maximum across constituent findings (text_agent, all url_agents,
     and image heuristics). The LLM CANNOT override this severity.

5. LLM Synthesis & Fallback:
   - Groq synthesis for unified finding & reasoning (with template fallback).

6. Safety Net:
   - Catches any unexpected exception; never raises out of analyze_image().
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

import cv2
import numpy as np

from app.agents.llm_client import call_llm
from app.agents.prompts.image_agent_prompt import IMAGE_AGENT_SYSTEM_PROMPT
from app.agents.text_agent import analyze_text
from app.agents.url_agent import analyze_url
from app.core.errors import ExternalServiceError
from app.core.image_heuristics import (
    extract_embedded_contact_info,
    extract_embedded_urls,
    has_impersonation_claim,
    has_payment_confirmation_pattern,
)
from app.core.indicators import VALID_INDICATORS
from app.core.ocr_engine import extract_text
from app.schemas.evidence import EvidenceItem

logger = logging.getLogger("threatweave-api.agents.image_agent")

_SEVERITY_ORDER: list[str] = ["info", "low", "medium", "high", "critical"]


def _max_severity(severities: list[str]) -> str:
    """Returns highest severity among candidate tiers according to hierarchy."""
    if not severities:
        return "info"
    return max(
        severities,
        key=lambda s: _SEVERITY_ORDER.index(s) if s in _SEVERITY_ORDER else 0,
    )


def _clean_json(raw: str) -> str:
    """Strips markdown code fences from raw LLM output."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
    return cleaned


def _build_fallback_finding(
    indicators: list[str],
    severity: str,
    extracted_text: str,
) -> tuple[str, str]:
    """Builds template-based finding and reasoning when LLM synthesis is unavailable."""
    if "fake_payment_confirmation" in indicators:
        finding = "Screenshot appears to be a fraudulent payment confirmation or receipt."
        reasoning = (
            "Extracted text exhibits currency markers and transaction completion claims typical "
            "of fabricated payment screenshots used in financial deception."
        )
    elif "impersonation_banner" in indicators:
        finding = "Image contains an institutional impersonation banner with urgent coercion language."
        reasoning = (
            "The screenshot combines brand/institutional authority terms with urgency signals, "
            "indicating a coercive social engineering attempt."
        )
    elif indicators:
        indicators_str = ", ".join(indicators)
        finding = f"Image flagged for threat indicators: {indicators_str}."
        reasoning = (
            f"Image analysis and delegated component evaluation identified concerns: {indicators_str}. "
            f"Severity evaluated as '{severity}'."
        )
    else:
        sample_preview = extracted_text[:80] + "..." if len(extracted_text) > 80 else extracted_text
        finding = "Image analyzed; no malicious indicators detected."
        reasoning = f"OCR extracted text ('{sample_preview}') shows no actionable threat indicators."

    return finding, reasoning


def analyze_image(image_bytes: bytes) -> EvidenceItem:
    """
    Analyzes an image or screenshot for fake payment proofs, impersonation banners,
    embedded malicious links, and phishing text.

    :param image_bytes: Raw binary bytes of the image file.
    :return: EvidenceItem representing the unified forensic conclusion.
    """
    timestamp = datetime.now(timezone.utc)

    try:
        # Step 1: Validate image byte integrity
        if not image_bytes or not isinstance(image_bytes, bytes):
            return EvidenceItem(
                agent="image_agent",
                modality="image",
                finding="Image input is empty or invalid.",
                confidence=0.0,
                severity="info",
                indicators=[],
                evidence={"error": "empty_input"},
                reasoning="No binary image data was provided for analysis.",
                status="failed",
                timestamp=timestamp,
            )

        nparr = np.frombuffer(image_bytes, np.uint8)
        if nparr.size == 0:
            return EvidenceItem(
                agent="image_agent",
                modality="image",
                finding="Image byte buffer is empty.",
                confidence=0.0,
                severity="info",
                indicators=[],
                evidence={"error": "empty_buffer"},
                reasoning="The provided image bytes could not form a valid buffer.",
                status="failed",
                timestamp=timestamp,
            )

        cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if cv_img is None:
            return EvidenceItem(
                agent="image_agent",
                modality="image",
                finding="Image file is corrupted or could not be decoded.",
                confidence=0.0,
                severity="info",
                indicators=[],
                evidence={"error": "corrupted_image"},
                reasoning="The provided bytes do not constitute a valid or decodable image format.",
                status="failed",
                timestamp=timestamp,
            )

        # Step 2: OCR Text Extraction
        extracted_text, ocr_conf = extract_text(image_bytes)

        if not extracted_text.strip():
            logger.info("Image Agent: No readable text detected in image")
            return EvidenceItem(
                agent="image_agent",
                modality="image",
                finding="No readable text or threat indicators detected in the image.",
                confidence=0.0,
                severity="info",
                indicators=["ocr_failed"],
                evidence={"extracted_text": "", "ocr_confidence": 0.0},
                reasoning="OCR text recognition detected no readable textual segments in the provided screenshot.",
                status="ok",
                timestamp=timestamp,
            )

        # Step 3: Run image-specific pattern heuristics
        has_payment = has_payment_confirmation_pattern(extracted_text)
        has_impersonation = has_impersonation_claim(extracted_text)
        embedded_urls = extract_embedded_urls(extracted_text)
        embedded_contacts = extract_embedded_contact_info(extracted_text, exclude_urls=embedded_urls)

        indicators: list[str] = []
        if has_payment:
            indicators.append("fake_payment_confirmation")
        if has_impersonation:
            indicators.append("impersonation_banner")
        if embedded_contacts:
            indicators.append("embedded_contact_info")
        if ocr_conf < 0.4:
            indicators.append("ocr_low_confidence")

        # Step 4: URL Delegation for each discovered URL
        url_analyses: list[dict] = []
        candidate_severities: list[str] = []

        for url in embedded_urls:
            logger.info("Image Agent delegating embedded URL to url_agent: %s", url)
            url_item = analyze_url(url)
            url_analyses.append(url_item.model_dump(mode="json"))
            candidate_severities.append(url_item.severity)
            for ind in url_item.indicators:
                if ind in VALID_INDICATORS and ind not in indicators:
                    indicators.append(ind)

        # Step 5: Text Delegation for extracted OCR text
        logger.info("Image Agent delegating extracted text to text_agent")
        text_item = analyze_text(extracted_text)
        candidate_severities.append(text_item.severity)
        for ind in text_item.indicators:
            if ind in VALID_INDICATORS and ind not in indicators:
                indicators.append(ind)

        # Step 6: Severity Reconciliation
        if has_payment or has_impersonation:
            candidate_severities.append("high")

        final_severity = _max_severity(candidate_severities)

        # Blend confidence: taking highest confidence among components
        confidence = max(ocr_conf, text_item.confidence)
        if url_analyses:
            url_confs = [u.get("confidence", 0.0) for u in url_analyses]
            confidence = max(confidence, max(url_confs))
        confidence = max(0.0, min(1.0, confidence))

        evidence = {
            "extracted_text": extracted_text,
            "ocr_confidence": ocr_conf,
            "heuristics": {
                "has_payment_confirmation": has_payment,
                "has_impersonation_banner": has_impersonation,
                "embedded_contacts": embedded_contacts,
                "embedded_urls": embedded_urls,
            },
            "url_analyses": url_analyses,
            "text_analysis": text_item.model_dump(mode="json") if hasattr(text_item, "model_dump") else {},
        }

        # Step 7: LLM Synthesis
        finding: str
        reasoning: str
        status: str

        try:
            user_content = json.dumps({
                "extracted_text": extracted_text,
                "ocr_confidence": ocr_conf,
                "indicators": indicators,
                "suggested_severity": final_severity,
                "url_findings_count": len(url_analyses),
                "has_payment_confirmation": has_payment,
                "has_impersonation_banner": has_impersonation,
            })
            raw_response = call_llm(
                system_prompt=IMAGE_AGENT_SYSTEM_PROMPT,
                user_content=user_content,
            )
            cleaned = _clean_json(raw_response)
            parsed_json = json.loads(cleaned)

            finding = str(parsed_json.get("finding", "Image forensic analysis completed."))
            reasoning = str(parsed_json.get("reasoning", "Screenshot forensic analysis completed by LLM."))
            llm_conf = parsed_json.get("confidence")
            if llm_conf is not None:
                confidence = round(0.7 * confidence + 0.3 * float(llm_conf), 4)
            confidence = max(0.0, min(1.0, confidence))
            status = "ok"
        except (ExternalServiceError, json.JSONDecodeError, TypeError, KeyError, ValueError) as llm_err:
            logger.warning("LLM synthesis failed for Image Agent (%s) — using fallback template", llm_err)
            finding, reasoning = _build_fallback_finding(indicators, final_severity, extracted_text)
            status = "degraded_fallback"

        return EvidenceItem(
            agent="image_agent",
            modality="image",
            finding=finding,
            confidence=confidence,
            severity=final_severity,
            indicators=[ind for ind in indicators if ind in VALID_INDICATORS],
            evidence=evidence,
            reasoning=reasoning,
            status=status,
            timestamp=timestamp,
        )

    except Exception:
        logger.exception("Unexpected error inside Image Agent")

    # Safety Net: Nothing escapes
    return EvidenceItem(
        agent="image_agent",
        modality="image",
        finding="Image analysis could not be completed.",
        confidence=0.0,
        severity="info",
        indicators=[],
        evidence={},
        reasoning="Image Agent encountered an unrecoverable internal error.",
        status="failed",
        timestamp=timestamp,
    )
