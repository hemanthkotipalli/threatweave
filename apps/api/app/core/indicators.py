from __future__ import annotations

from enum import Enum


class Indicator(str, Enum):
    """
    Enum representing standardized security Indicators of Compromise (IoCs)
    and social engineering features shared across ThreatWeave multimodal agents.

    Text-Agent Indicators (Phase 5)
    --------------------------------
    These cover social-engineering signals found in free-form text content.

    URL-Agent Indicators (Phase 6)
    --------------------------------
    These cover structural and reputation signals found in URLs.
    """
    # --- Text-Agent Indicators ---
    URGENCY_LANGUAGE = "urgency_language"
    CREDENTIAL_REQUEST = "credential_request"
    IMPERSONATION_CLAIM = "impersonation_claim"
    FINANCIAL_MANIPULATION = "financial_manipulation"
    SUSPICIOUS_LINK_MENTION = "suspicious_link_mention"
    GENERIC_GREETING = "generic_greeting"
    SPELLING_GRAMMAR_ANOMALY = "spelling_grammar_anomaly"
    PAYMENT_REQUEST = "payment_request"
    UNUSUAL_SENDER_PATTERN = "unusual_sender_pattern"

    # --- URL-Agent Indicators ---
    LOOKALIKE_DOMAIN = "lookalike_domain"
    SUSPICIOUS_TLD = "suspicious_tld"
    NO_HTTPS = "no_https"
    IP_ADDRESS_URL = "ip_address_url"
    EXCESSIVE_SUBDOMAINS = "excessive_subdomains"
    URL_SHORTENER = "url_shortener"
    KNOWN_MALICIOUS_DOMAIN = "known_malicious_domain"
    SUSPICIOUS_URL_STRUCTURE = "suspicious_url_structure"
    REDIRECT_CHAIN_DETECTED = "redirect_chain_detected"

    # --- QR-Agent Indicators (Phase 7) ---
    QR_PAYMENT_REQUEST = "qr_payment_request"
    QR_NON_URL_PAYLOAD = "qr_non_url_payload"
    QR_DECODE_FAILED = "qr_decode_failed"
    QR_UPI_DEEPLINK_SUSPICIOUS = "qr_upi_deeplink_suspicious"

    # --- Image-Agent Indicators (Phase 8) ---
    FAKE_PAYMENT_CONFIRMATION = "fake_payment_confirmation"
    IMPERSONATION_BANNER = "impersonation_banner"
    EMBEDDED_CONTACT_INFO = "embedded_contact_info"
    OCR_LOW_CONFIDENCE = "ocr_low_confidence"
    OCR_FAILED = "ocr_failed"

    # --- Voice-Agent Indicators (Phase 9) ---
    VISHING_SCRIPT_PATTERN = "vishing_script_pattern"
    ROBOTIC_SPEECH_PATTERN = "robotic_speech_pattern"
    STT_LOW_CONFIDENCE = "stt_low_confidence"
    STT_FAILED = "stt_failed"
    AI_VOICE_INDICATOR_WEAK = "ai_voice_indicator_weak"


# Shared source-of-truth vocabulary set for verification
VALID_INDICATORS: set[str] = {item.value for item in Indicator}

