"""
app/agents/qr_agent.py
-----------------------
ThreatWeave Phase 7 — QR Agent.

Public API
----------
    analyze_qr(image_bytes: bytes) -> EvidenceItem

Architecture & Delegation
-------------------------
1. QR Decoder Layer:
   - Uses app.core.qr_decoder.decode_qr() to extract text from image bytes.
   - If decode fails or image is empty/corrupt -> returns failed EvidenceItem
     with indicator "qr_decode_failed". Never raises.

2. True Delegation Paths:
   - URL Payloads:
     Directly imports and calls app.agents.url_agent.analyze_url(payload).
     Preserves severity, confidence, indicators, and nests URL evidence under
     "url_analysis".
   - Text / Unrecognized Payloads:
     Directly imports and calls app.agents.text_agent.analyze_text(payload).
     Adds indicator "qr_non_url_payload" and adjusts findings to reflect QR origin.

3. UPI Payment Deep-Link Analysis:
   - Native parsing of upi://pay deep-links.
   - Computes VPA vs Payee Name resemblance and flags "qr_upi_deeplink_suspicious"
     on impersonation or incongruous amounts. Always flags "qr_payment_request".
   - Synthesizes findings via LLM (with template fallback).

4. Safety Net:
   - Catches any unexpected exception and returns safe failed EvidenceItem.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from app.agents.llm_client import call_llm
from app.agents.prompts.qr_agent_prompt import QR_UPI_SYSTEM_PROMPT
from app.agents.text_agent import analyze_text
from app.agents.url_agent import analyze_url
from app.core.errors import ExternalServiceError
from app.core.indicators import VALID_INDICATORS
from app.core.qr_decoder import decode_qr
from app.core.url_heuristics import _levenshtein
from app.schemas.evidence import EvidenceItem

logger = logging.getLogger("threatweave-api.agents.qr_agent")

_URL_PATTERN = re.compile(
    r"^(?:https?://|www\.)[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+$",
    re.IGNORECASE,
)

_DECEPTIVE_TERMS: tuple[str, ...] = (
    "support",
    "official",
    "refund",
    "cashback",
    "lottery",
    "reward",
    "customercare",
    "customer_care",
    "billdesk",
    "electricity",
    "telecom",
    "bank",
    "helpline",
)


def _is_url_payload(text: str) -> bool:
    """Returns True if the string is structurally a web URL."""
    lowered = text.strip().lower()
    if lowered.startswith(("http://", "https://")):
        return True
    if lowered.startswith("www.") and "." in lowered:
        return True
    return bool(_URL_PATTERN.match(text.strip()))


def _is_upi_payload(text: str) -> bool:
    """Returns True if the payload is a UPI payment URI."""
    return text.strip().lower().startswith("upi://")


def _compute_vpa_similarity(payee_name: str, vpa: str) -> float:
    """
    Computes a 0–1 similarity score between the payee name and VPA local-part.
    Reuses normalized Levenshtein distance.
    """
    vpa_local = vpa.split("@")[0] if "@" in vpa else vpa
    clean_name = re.sub(r"[^a-zA-Z0-9]", "", payee_name).lower()
    clean_vpa = re.sub(r"[^a-zA-Z0-9]", "", vpa_local).lower()

    if not clean_name or not clean_vpa:
        return 0.0

    if clean_name in clean_vpa or clean_vpa in clean_name:
        return 0.95

    max_len = max(len(clean_name), len(clean_vpa))
    dist = _levenshtein(clean_name, clean_vpa)
    return max(0.0, 1.0 - (dist / max_len))


def _analyze_upi_payload(payload: str, timestamp: datetime) -> EvidenceItem:
    """
    Analyzes a UPI deep-link for payment manipulation, deceptive payee names,
    and VPA mismatches.
    """
    parsed = urlparse(payload)
    params = parse_qs(parsed.query)

    pa = params.get("pa", [""])[0].strip()
    pn = params.get("pn", [""])[0].strip()
    am = params.get("am", [""])[0].strip()
    tn = params.get("tn", [""])[0].strip()

    indicators: list[str] = ["qr_payment_request"]

    # Compute similarity between claimed payee name and actual VPA handle
    vpa_sim = _compute_vpa_similarity(pn, pa)
    vpa_local = pa.split("@")[0].lower() if "@" in pa else pa.lower()
    pn_lower = pn.lower()

    # Check for deceptive corporate / authority terms in payee name
    claimed_official = any(term in pn_lower for term in _DECEPTIVE_TERMS)
    vpa_has_official = any(term in vpa_local for term in _DECEPTIVE_TERMS)
    has_authority_impersonation = claimed_official and not vpa_has_official

    # Amount heuristic: flag high prefilled amounts or suspicious amounts
    suspicious_amount = False
    try:
        if am:
            val = float(am)
            if val >= 10000.0 or (val >= 2000.0 and vpa_sim < 0.4):
                suspicious_amount = True
    except ValueError:
        pass

    # Flag suspicious if payee name has low resemblance or authority impersonation
    if pn and pa and (vpa_sim < 0.4 or has_authority_impersonation or (suspicious_amount and vpa_sim < 0.6)):
        indicators.append("qr_upi_deeplink_suspicious")

    # Severity evaluation
    if "qr_upi_deeplink_suspicious" in indicators:
        severity = "critical" if (has_authority_impersonation and suspicious_amount) else "high"
        confidence = 0.88
    else:
        severity = "low"
        confidence = 0.70

    details = {
        "pa": pa,
        "pn": pn,
        "am": am,
        "tn": tn,
        "vpa_payee_similarity": round(vpa_sim, 4),
        "claimed_official_role": claimed_official,
        "suspicious_amount": suspicious_amount,
    }

    finding: str
    reasoning: str
    status: str

    # LLM Synthesis Path
    try:
        user_content = json.dumps({
            "upi_parameters": details,
            "indicators": indicators,
            "suggested_severity": severity,
        })
        raw_response = call_llm(system_prompt=QR_UPI_SYSTEM_PROMPT, user_content=user_content)
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
            if m:
                cleaned = m.group(1).strip()
        parsed_json = json.loads(cleaned)
        finding = str(parsed_json.get("finding", f"UPI payment request to '{pa}'."))
        reasoning = str(parsed_json.get("reasoning", "UPI deep-link analysis completed."))
        llm_conf = parsed_json.get("confidence")
        if llm_conf is not None:
            confidence = round(0.7 * confidence + 0.3 * float(llm_conf), 4)
        status = "ok"
    except (ExternalServiceError, json.JSONDecodeError, TypeError, KeyError, ValueError) as llm_err:
        logger.warning("LLM synthesis failed for UPI QR payload (%s) — using fallback template", llm_err)
        if "qr_upi_deeplink_suspicious" in indicators:
            finding = f"Suspicious UPI payment request: payee '{pn}' does not match VPA handle '{pa}'."
            reasoning = (
                f"The QR encodes a payment deep-link to VPA '{pa}' but advertises payee name '{pn}'. "
                f"Similarity score is {round(vpa_sim, 2)}, indicating possible impersonation or fraud."
            )
        else:
            finding = f"Valid UPI payment request to '{pn}' ({pa})."
            reasoning = f"The QR encodes a payment deep-link to VPA '{pa}' with consistent payee identity."
        status = "degraded_fallback"

    return EvidenceItem(
        agent="qr_agent",
        modality="qr",
        finding=finding,
        confidence=confidence,
        severity=severity,
        indicators=[ind for ind in indicators if ind in VALID_INDICATORS],
        evidence={"decoded_payload": payload, "upi_details": details},
        reasoning=reasoning,
        status=status,
        timestamp=timestamp,
    )


def analyze_qr(image_bytes: bytes) -> EvidenceItem:
    """
    Decodes and analyzes a QR code image for phishing, fraud, and security threats.

    Delegation model:
    - URL payload: Delegates directly to url_agent.analyze_url().
    - UPI deep-link: Performs native deep-link analysis for VPA fraud.
    - Plain text / Other: Delegates directly to text_agent.analyze_text().

    Guaranteed never to raise an unhandled exception under any input.

    :param image_bytes: Raw binary image bytes.
    :return: EvidenceItem representing audit conclusion.
    """
    timestamp = datetime.now(timezone.utc)

    try:
        # Step 1: Decode QR code
        decoded_payload = decode_qr(image_bytes)

        if decoded_payload is None:
            return EvidenceItem(
                agent="qr_agent",
                modality="qr",
                finding="No QR code could be decoded from the provided image.",
                confidence=0.0,
                severity="info",
                indicators=["qr_decode_failed"],
                evidence={"error": "decode_failed"},
                reasoning="The provided image was either corrupted, empty, or contained no decodable QR code pattern.",
                status="failed",
                timestamp=timestamp,
            )

        # Step 2: URL Payload -> Genuine delegation to URL Agent
        if _is_url_payload(decoded_payload):
            url_to_analyze = decoded_payload
            if url_to_analyze.lower().startswith("www."):
                url_to_analyze = "https://" + url_to_analyze

            logger.info("QR Agent delegating URL payload to url_agent.analyze_url()")
            url_item = analyze_url(url_to_analyze)

            qr_finding = (
                f"QR code decodes to a URL with security concerns: {url_item.finding}"
                if url_item.severity in ("high", "critical", "medium")
                else f"QR code decodes to URL: {url_item.finding}"
            )
            qr_reasoning = f"Decoded QR URL '{decoded_payload}'. {url_item.reasoning}"

            return EvidenceItem(
                agent="qr_agent",
                modality="qr",
                finding=qr_finding,
                confidence=url_item.confidence,
                severity=url_item.severity,
                indicators=list(url_item.indicators),
                evidence={
                    "decoded_payload": decoded_payload,
                    "url_analysis": url_item.evidence,
                },
                reasoning=qr_reasoning,
                external_refs=url_item.external_refs,
                status=url_item.status,
                timestamp=timestamp,
            )

        # Step 3: UPI Deep-Link Payload -> Native UPI payment analysis
        if _is_upi_payload(decoded_payload):
            logger.info("QR Agent processing UPI deep-link payload")
            return _analyze_upi_payload(decoded_payload, timestamp)

        # Step 4: Text / Non-URL Payload -> Genuine delegation to Text Agent
        logger.info("QR Agent delegating plain-text payload to text_agent.analyze_text()")
        text_item = analyze_text(decoded_payload)

        # Append qr_non_url_payload
        indicators = list(text_item.indicators)
        if "qr_non_url_payload" not in indicators:
            indicators.append("qr_non_url_payload")

        qr_finding = f"QR code decodes to non-URL text payload: {text_item.finding}"
        qr_reasoning = f"Decoded plain text from QR code: {text_item.reasoning}"

        return EvidenceItem(
            agent="qr_agent",
            modality="qr",
            finding=qr_finding,
            confidence=text_item.confidence,
            severity=text_item.severity,
            indicators=indicators,
            evidence={
                "decoded_payload": decoded_payload,
                "text_analysis": text_item.evidence if hasattr(text_item, "evidence") else {},
            },
            reasoning=qr_reasoning,
            external_refs=text_item.external_refs,
            status=text_item.status,
            timestamp=timestamp,
        )

    except Exception:
        logger.exception("Unexpected error inside QR Agent")

    # Safety Net: Nothing ever escapes
    return EvidenceItem(
        agent="qr_agent",
        modality="qr",
        finding="QR code analysis could not be completed.",
        confidence=0.0,
        severity="info",
        indicators=[],
        evidence={},
        reasoning="QR Agent encountered an unrecoverable internal error.",
        status="failed",
        timestamp=timestamp,
    )
