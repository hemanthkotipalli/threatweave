"""
app/core/image_heuristics.py
----------------------------
Pure, network-free heuristic analysis functions operating on OCR-extracted text
from images and screenshots (ThreatWeave Phase 8).

Functions:
- has_payment_confirmation_pattern(text) -> bool
- has_impersonation_claim(text) -> bool
- extract_embedded_urls(text) -> list[str]
- extract_embedded_contact_info(text) -> list[str]

All functions handle empty/garbage text gracefully and never raise exceptions.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger("threatweave-api.core.image_heuristics")

# Currency symbols and indicators common in fraud screenshots (Indian & International)
_CURRENCY_PATTERN = re.compile(
    r"(?:₹|\$|€|£|Rs\.?|INR)\s*[\d,]+(?:\.\d{1,2})?|[\d,]+(?:\.\d{1,2})?\s*(?:₹|\$|€|£|Rs\.?|INR)",
    re.IGNORECASE,
)

# Receipt and transfer status terms (robust to OCR character slips)
_PAYMENT_STATUS_PATTERN = re.compile(
    r"(?:succes[a-z0-9]*|credit[a-z0-9]*|receiv[a-z0-9]*|paid|transfer[a-z0-9]*|complet[a-z0-9]*|payment|txn|utr|receipt)",
    re.IGNORECASE,
)

# Institutional and brand entities commonly impersonated in fraud banners
_AUTHORITY_ENTITIES = re.compile(
    r"(?:sbi|state\s*bank|hdfc|icici|axis(?:\s*bank)?|punjab\s*national(?:\s*bank)?|pnb|paytm|phonepe|gpay|google\s*pay|amazon|paypal|rbi|reserve\s*bank|income\s*tax|police|cyber\s*crime|customs|court|uidai|aadhaar|epfo|electricity\s*board)",
    re.IGNORECASE,
)

# Urgency and coercion signals (resilient to fused OCR words and stemming)
_URGENCY_SIGNALS = re.compile(
    r"(?:urgent|immediat[a-z]*|suspend[a-z]*|block[a-z]*|action\s*required|kyc|verif[a-z]*|penalt[a-z]*|legal\s*notice|warrant|account\s*frozen|deactivat[a-z]*|expir[a-z]*|compromis[a-z]*)",
    re.IGNORECASE,
)

# Regex for extracting raw URLs from OCR text (handles http/https/www/tld)
_URL_REGEX = re.compile(
    r"(?:https?://|www\.)[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+",
    re.IGNORECASE,
)

# Regex for Indian and standard phone numbers
_PHONE_REGEX = re.compile(
    r"(?:\+91[\-\s]?)?[6-9]\d{9}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b",
)

# Regex for UPI VPAs (username@bank)
_VPA_REGEX = re.compile(
    r"\b[a-zA-Z0-9.\-_]{2,50}@(?!gmail|yahoo|outlook|hotmail|icloud)[a-zA-Z]{2,30}\b",
    re.IGNORECASE,
)


def has_payment_confirmation_pattern(text: str) -> bool:
    """
    Detects whether the OCR text resembles a payment receipt, transfer confirmation,
    or credited funds screenshot (e.g. fake Paytm / GPay / banking payment proofs).

    Requires BOTH a currency/amount pattern AND a completion status keyword.
    """
    if not text or not isinstance(text, str):
        return False

    try:
        has_currency = bool(_CURRENCY_PATTERN.search(text))
        has_status = bool(_PAYMENT_STATUS_PATTERN.search(text))

        # Check for co-occurrence or strong receipts
        if has_currency and has_status:
            return True

        # Also flag strong composite phrases like "Payment Successful" even if amount format varies
        return bool(re.search(r"\b(?:payment\s+successful|money\s+received|funds\s+credited)\b", text, re.IGNORECASE))
    except Exception as exc:  # noqa: BLE001 - heuristics contract mandates never raising
        logger.debug("has_payment_confirmation_pattern error: %s", exc)
        return False


def has_impersonation_claim(text: str) -> bool:
    """
    Detects institutional/brand impersonation banners where a financial, government,
    or corporate entity name is combined with urgency, threats, or coercion language.
    """
    if not text or not isinstance(text, str):
        return False

    try:
        has_entity = bool(_AUTHORITY_ENTITIES.search(text))
        has_urgency = bool(_URGENCY_SIGNALS.search(text))
        return has_entity and has_urgency
    except Exception as exc:  # noqa: BLE001 - heuristics contract mandates never raising
        logger.debug("has_impersonation_claim error: %s", exc)
        return False


def extract_embedded_urls(text: str) -> list[str]:
    """
    Extracts all distinct HTTP/HTTPS/WWW URLs embedded within the OCR text.
    Normalizes common OCR artifacts (e.g. http"/ or spaces in protocol).
    Strips trailing punctuation common to OCR boundaries.
    """
    if not text or not isinstance(text, str):
        return []

    try:
        # Pre-normalize common OCR protocol artifacts: http"// -> http://, http: // -> http://, etc.
        normalized = re.sub(r"\bhttp[\"':;|\s]{1,3}[/\\|\"']{1,2}\s*", "http://", text, flags=re.IGNORECASE)
        normalized = re.sub(r"\bhttps[\"':;|\s]{1,3}[/\\|\"']{1,2}\s*", "https://", normalized, flags=re.IGNORECASE)
        raw_matches = _URL_REGEX.findall(normalized)
        cleaned_urls: list[str] = []
        for raw in raw_matches:
            # Strip trailing punctuation often caught by regex from sentences
            url = re.sub(r"[.,;:!?'\")\]]+$", "", raw).strip()
            if url and len(url) > 4:
                if url.lower().startswith("www."):
                    url = "https://" + url
                if url not in cleaned_urls:
                    cleaned_urls.append(url)
        return cleaned_urls
    except Exception as exc:  # noqa: BLE001 - heuristics contract mandates never raising
        logger.debug("extract_embedded_urls error: %s", exc)
        return []


def extract_embedded_contact_info(text: str, exclude_urls: list[str] | None = None) -> list[str]:
    """
    Extracts phone numbers and UPI VPA identifiers embedded in the screenshot text.
    Excludes any substrings that are part of extracted URLs to prevent userinfo
    segments (e.g. 192.168.1.1@paypal) from falsely matching as contact info.
    """
    if not text or not isinstance(text, str):
        return []

    try:
        search_text = text
        # Remove explicitly passed URLs or automatically discover and strip them
        urls_to_remove = exclude_urls if exclude_urls is not None else extract_embedded_urls(text)
        for url in urls_to_remove:
            search_text = search_text.replace(url, " ")

        # Strip remaining generic URL strings
        search_text = re.sub(r"https?://[^\s]+", " ", search_text)

        contacts: list[str] = []
        # Phones
        for match in _PHONE_REGEX.findall(search_text):
            cleaned = match.strip()
            if cleaned and cleaned not in contacts:
                contacts.append(cleaned)
        # VPAs
        for match in _VPA_REGEX.findall(search_text):
            cleaned = match.strip()
            if cleaned and cleaned not in contacts:
                contacts.append(cleaned)
        return contacts
    except Exception as exc:  # noqa: BLE001 - heuristics contract mandates never raising
        logger.debug("extract_embedded_contact_info error: %s", exc)
        return []
