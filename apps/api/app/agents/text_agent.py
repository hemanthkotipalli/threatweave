from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone

from app.agents.llm_client import call_llm
from app.agents.prompts.text_agent_prompt import SYSTEM_PROMPT
from app.core.errors import ExternalServiceError
from app.core.indicators import VALID_INDICATORS
from app.schemas.evidence import EvidenceItem

logger = logging.getLogger("threatweave-api.agents.text_agent")


def clean_json_response(raw_text: str) -> str:
    """
    Strips markdown code fences (e.g. ```json ... ```) or conversational commentary
    from the raw response string to prepare it for JSON parsing.
    """
    cleaned = raw_text.strip()
    
    # Check for markdown code blocks
    if cleaned.startswith("```"):
        # Match ```json or ``` and strip
        match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
            
    # Handle single quotes replaced or trailing commas
    return cleaned


def analyze_text(content: str) -> EvidenceItem:
    """
    Analyzes input text for phishing, scams, and social engineering indicators.
    
    1. Primary Path: Sends prompt + content to the Groq LLM API (JSON mode).
    2. Fallback Path: Scans content using keyword/regex heuristics (caps confidence at 0.6).
    3. Safety Net: Catches all exceptions and returns a failed status EvidenceItem.
    """
    timestamp = datetime.now(timezone.utc)
    
    try:
        # Primary LLM Path
        logger.info("Executing primary LLM path for text agent analysis")
        raw_response = call_llm(system_prompt=SYSTEM_PROMPT, user_content=content)
        cleaned_response = clean_json_response(raw_response)
        
        parsed = json.loads(cleaned_response)
        
        # Extract fields defensively
        finding = parsed.get("finding", "No specific threat identified.")
        confidence = float(parsed.get("confidence", 0.5))
        severity = parsed.get("severity", "info")
        raw_indicators = parsed.get("indicators", [])
        reasoning = parsed.get("reasoning", "Analysis completed by LLM.")

        # Filter indicators against shared vocabulary
        filtered_indicators = []
        for ind in raw_indicators:
            if ind in VALID_INDICATORS:
                filtered_indicators.append(ind)
            else:
                logger.warning(f"Dropped unknown indicator returned by LLM: {ind}")

        # Clamp confidence to [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))

        # Assure severity literal type
        if severity not in ("info", "low", "medium", "high", "critical"):
            severity = "info"

        return EvidenceItem(
            agent="text_agent",
            modality="text",
            finding=finding,
            confidence=confidence,
            severity=severity,
            indicators=filtered_indicators,
            reasoning=reasoning,
            status="ok",
            timestamp=timestamp
        )

    except Exception as exc:
        logger.warning(f"Primary LLM path failed ({exc!s}). Initiating heuristic fallback path.")
        
        # Fallback heuristic path
        try:
            matched_indicators = []
            
            # Formulate keyword dictionary for regex matches
            heuristics = {
                "urgency_language": [
                    r"\bact now\b", r"\bverify immediately\b", r"\baction required\b", 
                    r"\burgent\b", r"\bsuspended\b", r"\bterminate\b", r"\bexpire\b",
                    r"\bcritical warning\b", r"power cut", r"power will be disconnected",
                    r"disconnected tonight", r"immediate disconnection",
                    r"within \d+ (?:hours?|mins?|minutes?)", r"last notice", r"final notice",
                    r"electricity.*disconnected",
                ],
                "credential_request": [
                    r"enter your password", r"enter your pin", r"enter your login",
                    r"verify your password", r"verify your pin", r"verify your login",
                    r"confirm your password", r"confirm your pin", r"confirm your login",
                    r"verify your identity", r"verify your account",
                    r"\bcredentials\b", r"login details", r"password reset",
                    r"security code", r"one.time.code", r"authentication code",
                    r"provide your password", r"submit your password",
                    r"\bkyc\b", r"\bpan card\b", r"\baadhaar\b", r"\botp\b",
                    r"share.*(?:otp|pin|password)", r"update.*kyc", r"link.*aadhaar",
                    r"submit.*(?:documents?|details?)",
                ],
                "impersonation_claim": [
                    r"support team", r"security department", r"\bhelpdesk\b", 
                    r"\badministrator\b", r"\bsystem admin\b", r"customer service", 
                    r"microsoft support", r"bank representative",
                    r"\bbescom\b", r"\byono\b", r"electricity board", r"power corporation",
                    r"\bcibil\b", r"\bnarcotics\b", r"\btrai\b", r"\bmha\b",
                    r"police department", r"digital arrest", r"customs officer",
                    r"fedex parcel", r"income tax", r"telecom department",
                ],
                "financial_manipulation": [
                    r"transfer fund", r"bank details", r"wire transfer", 
                    r"cash prize", r"million dollars", r"\blottery\b", r"unclaimed money",
                    r"\bkbc\b", r"part.?time job", r"youtube like", r"daily earnings",
                    r"task earnings", r"work from home.*earn", r"investment return",
                    r"bonus credit", r"cashback reward", r"crypto profit",
                ],
                "suspicious_link_mention": [
                    r"click this link", r"visit URL", r"login here", 
                    r"click below", r"link below", r"https?://",
                    r"download apk", r"install app", r"update your app", r"visit link",
                ],
                "generic_greeting": [
                    r"dear customer", r"valued client", r"dear user", 
                    r"dear member", r"dear account holder",
                ],
                "spelling_grammar_anomaly": [
                    r"\bcongratulatons\b", r"\bbeneficary\b", r"\binvalide\b",
                ],
                "payment_request": [
                    r"pay immediately", r"overdue invoice", r"make payment", 
                    r"outstanding balance", r"wire the money",
                    r"pay bill", r"unpaid electricity", r"bill pending",
                    r"penalty fee", r"clear your dues",
                ],
                "unusual_sender_pattern": [
                    r"do-not-reply", r"\bnoreply\b", r"alert-security", r"system-mailer",
                ]
            }

            content_lower = content.lower()
            for indicator, patterns in heuristics.items():
                for pattern in patterns:
                    if re.search(pattern, content_lower):
                        matched_indicators.append(indicator)
                        break  # Match found for this category, proceed to next indicator

            # Calculate confidence and severity based on matches
            num_matches = len(matched_indicators)
            confidence = min(0.6, 0.2 + (0.1 * num_matches))
            
            # Determine severity with contextual combination requirements:
            # Prevents isolated single words from prematurely escalating to high severity.
            has_credential = "credential_request" in matched_indicators
            has_financial = "financial_manipulation" in matched_indicators
            has_urgency = "urgency_language" in matched_indicators
            has_impersonation = "impersonation_claim" in matched_indicators
            has_payment = "payment_request" in matched_indicators
            has_link = "suspicious_link_mention" in matched_indicators

            severity = "info"
            if num_matches >= 4:
                severity = "critical"
            elif num_matches >= 2:
                if has_credential and (has_urgency or has_impersonation or has_link):
                    severity = "high"
                elif has_financial and (has_urgency or has_impersonation or has_payment or has_link):
                    severity = "high"
                elif has_impersonation and (has_urgency or has_payment):
                    severity = "high"
                elif has_urgency or has_payment or has_credential or has_financial:
                    severity = "medium"
                else:
                    severity = "low"
            elif num_matches == 1:
                if has_credential or has_financial or has_urgency or has_payment:
                    severity = "medium"
                else:
                    severity = "low"

            finding = f"Heuristic analysis detected {num_matches} social engineering indicators." if num_matches > 0 else "No threat indicators detected via heuristics."
            reasoning = f"Primary service was offline or failed to respond. Fallback matches: {', '.join(matched_indicators)}."
            
            return EvidenceItem(
                agent="text_agent",
                modality="text",
                finding=finding,
                confidence=confidence,
                severity=severity,
                indicators=matched_indicators,
                reasoning=reasoning,
                status="degraded_fallback",
                timestamp=timestamp
            )
            
        except Exception:
            logger.exception("Heuristic fallback check failed")
            # Proceed to safety net below

    except Exception:
        logger.exception("Unexpected anomaly inside Text Agent")
        # Proceed to safety net below

    # Safety Net: absolute assurance against escaping errors
    return EvidenceItem(
        agent="text_agent",
        modality="text",
        finding="Analysis could not be completed",
        confidence=0.0,
        severity="info",
        indicators=[],
        reasoning="Text agent encountered an unrecoverable error.",
        status="failed",
        timestamp=timestamp
    )
