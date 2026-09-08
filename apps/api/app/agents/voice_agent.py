"""
app/agents/voice_agent.py
-------------------------
Voice Agent implementation for ThreatWeave (Phase 9).
Performs offline speech-to-text (STT) transcription via faster-whisper,
scripted vishing-pattern detection, non-conclusive acoustic variance analysis,
and genuine delegation to the Text Agent (app.agents.text_agent.analyze_text).

CRITICAL FRAMING AND SAFETY REQUIREMENT:
This agent NEVER claims to have detected or proven AI-generated, synthetic,
or deepfake voice. Any acoustic signal is labeled as 'ai_voice_indicator_weak',
capped at 0.40 confidence contribution, and accompanied by hedged language.

Public API:
    analyze_voice(audio_bytes: bytes) -> EvidenceItem
"""
from __future__ import annotations

import io
import json
import logging
import re
from datetime import datetime, timezone

import av

from app.agents.llm_client import ExternalServiceError, call_llm
from app.agents.prompts.voice_agent_prompt import VOICE_AGENT_SYSTEM_PROMPT
from app.agents.text_agent import analyze_text
from app.core.indicators import VALID_INDICATORS
from app.core.stt_engine import transcribe_audio
from app.core.voice_heuristics import (
    analyze_acoustic_features,
    has_vishing_script_pattern,
)
from app.schemas.evidence import EvidenceItem

logger = logging.getLogger("threatweave-api.agents.voice_agent")

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
    transcript: str,
) -> tuple[str, str]:
    """
    Builds template-based finding and reasoning when LLM synthesis is unavailable.
    Guarantees that no claims of proven synthetic/AI voice are made.
    """
    if "vishing_script_pattern" in indicators:
        finding = "Audio recording matches characteristic call-center social engineering (vishing) script patterns."
        reasoning = (
            "The caller uses scripted pressure tactics, claims of account compromise, or urgency prompts "
            "typical of fraudulent telephone operations attempting credential or payment harvesting."
        )
    elif "ai_voice_indicator_weak" in indicators:
        finding = "Voice recording exhibits an acoustic pattern of low pitch and energy variance."
        reasoning = (
            "Acoustic analysis identified an unusually uniform audio cadence. This is a weak, non-conclusive "
            "signal that may be consistent with automated telephony playback, not proof of synthetic audio."
        )
    elif indicators:
        indicators_str = ", ".join(indicators)
        finding = f"Voice sample flagged for threat indicators: {indicators_str}."
        reasoning = (
            f"Transcript evaluation and delegated text analysis identified concerns: {indicators_str}. "
            f"Severity evaluated as '{severity}'."
        )
    else:
        sample_preview = transcript[:80] + "..." if len(transcript) > 80 else transcript
        finding = "Voice recording analyzed; no malicious indicators detected."
        reasoning = f"Transcription ('{sample_preview}') shows benign communication without recognized threat patterns."

    return finding, reasoning


def analyze_voice(audio_bytes: bytes) -> EvidenceItem:
    """
    Analyzes an audio file for telephone fraud (vishing) scripts, automated robotic
    coercion signals, and social engineering lures.

    Delegates the full transcript to `text_agent.analyze_text()` and merges findings
    with voice-specific indicators and maximum constituent severity.

    Guarantees:
    - Never raises an unhandled exception on any input.
    - Never claims proof of AI-generated or deepfake voice.

    :param audio_bytes: Raw binary bytes of the audio file.
    :return: EvidenceItem representing the unified forensic conclusion.
    """
    timestamp = datetime.now(timezone.utc)

    try:
        # Step 1: Validate audio byte integrity
        if not audio_bytes or not isinstance(audio_bytes, bytes) or len(audio_bytes) < 64:
            return EvidenceItem(
                agent="voice_agent",
                modality="voice",
                finding="Audio input is empty or invalid.",
                confidence=0.0,
                severity="info",
                indicators=[],
                evidence={"error": "empty_input"},
                reasoning="No valid binary audio data was provided for analysis.",
                status="failed",
                timestamp=timestamp,
            )

        # Inspect format integrity via PyAV container verification
        try:
            container = av.open(io.BytesIO(audio_bytes))
            audio_streams = [s for s in container.streams if s.type == "audio"]
            if not audio_streams:
                logger.warning("Uploaded file contains no audio streams")
                return EvidenceItem(
                    agent="voice_agent",
                    modality="voice",
                    finding="Provided file does not contain valid audio data.",
                    confidence=0.0,
                    severity="info",
                    indicators=[],
                    evidence={"error": "no_audio_streams"},
                    reasoning="The container could not identify any readable audio tracks.",
                    status="failed",
                    timestamp=timestamp,
                )
        except Exception as probe_err:  # noqa: BLE001 - corrupted bytes return failed EvidenceItem
            logger.warning("Corrupted or unreadable audio bytes: %s", probe_err)
            return EvidenceItem(
                agent="voice_agent",
                modality="voice",
                finding="Corrupted or unreadable audio file.",
                confidence=0.0,
                severity="info",
                indicators=[],
                evidence={"error": "corrupted_audio_bytes", "details": str(probe_err)},
                reasoning="File format could not be decoded by the audio parser.",
                status="failed",
                timestamp=timestamp,
            )

        # Step 2: Speech-to-Text Transcription
        transcript, stt_conf = transcribe_audio(audio_bytes)

        # Step 3: Handle empty or silent audio
        if not transcript:
            return EvidenceItem(
                agent="voice_agent",
                modality="voice",
                finding="No intelligible speech detected in audio recording.",
                confidence=0.0,
                severity="info",
                indicators=["stt_failed"],
                evidence={
                    "transcript": "",
                    "stt_confidence": 0.0,
                    "heuristics": {
                        "has_vishing_script": False,
                        "acoustic_features": {},
                    },
                    "text_analysis": {},
                },
                reasoning="Transcription processing yielded no recognizable speech or audible words.",
                status="ok",
                timestamp=timestamp,
            )

        # Step 4: Voice-Specific Heuristic Checks
        has_vishing = has_vishing_script_pattern(transcript)
        acoustic_data = analyze_acoustic_features(audio_bytes)

        indicators: list[str] = []
        candidate_severities: list[str] = []

        if has_vishing:
            indicators.append("vishing_script_pattern")
            candidate_severities.append("high")

        if stt_conf < 0.40:
            indicators.append("stt_low_confidence")

        if acoustic_data.get("indicator") == "ai_voice_indicator_weak":
            indicators.append("ai_voice_indicator_weak")

        # Step 5: Delegate transcript to Text Agent
        logger.info("Voice Agent delegating transcript to text_agent")
        text_item = analyze_text(transcript)
        candidate_severities.append(text_item.severity)

        for ind in text_item.indicators:
            if ind in VALID_INDICATORS and ind not in indicators:
                indicators.append(ind)

        # Step 6: Severity Reconciliation
        final_severity = _max_severity(candidate_severities)

        # Blend confidence: taking highest confidence among components
        confidence = max(stt_conf, text_item.confidence)
        if acoustic_data.get("confidence_contribution"):
            # Acoustic confidence contribution is strictly capped at 0.40
            acoustic_conf = min(0.40, float(acoustic_data["confidence_contribution"]))
            if not candidate_severities or final_severity in ("info", "low"):
                confidence = min(0.40, max(confidence, acoustic_conf))
        confidence = round(max(0.0, min(1.0, confidence)), 4)

        evidence = {
            "transcript": transcript,
            "stt_confidence": stt_conf,
            "heuristics": {
                "has_vishing_script": has_vishing,
                "acoustic_features": acoustic_data,
            },
            "text_analysis": text_item.model_dump(mode="json") if hasattr(text_item, "model_dump") else {},
        }

        # Step 7: LLM Synthesis
        finding: str
        reasoning: str
        status: str

        try:
            user_content = json.dumps({
                "transcript": transcript,
                "stt_confidence": stt_conf,
                "indicators": indicators,
                "suggested_severity": final_severity,
                "has_vishing_script": has_vishing,
                "acoustic_signal_present": bool(acoustic_data.get("indicator")),
                "delegated_text_summary": {
                    "severity": text_item.severity,
                    "indicators": text_item.indicators,
                    "finding": text_item.finding,
                },
            })

            logger.info("Invoking LLM synthesis for Voice Agent")
            raw_response = call_llm(
                system_prompt=VOICE_AGENT_SYSTEM_PROMPT,
                user_content=user_content,
            )
            cleaned = _clean_json(raw_response)
            parsed = json.loads(cleaned)

            finding = str(parsed.get("finding", "Voice threat intelligence assessment completed."))
            reasoning = str(parsed.get("reasoning", "Analysis synthesized by LLM."))
            llm_conf = parsed.get("confidence")
            if llm_conf is not None:
                confidence = round(0.7 * confidence + 0.3 * float(llm_conf), 4)
            confidence = max(0.0, min(1.0, confidence))
            status = "ok"

        except (ExternalServiceError, json.JSONDecodeError, TypeError, KeyError, ValueError, RuntimeError) as llm_err:
            logger.warning("LLM synthesis failed for Voice Agent (%s) — using fallback template", llm_err)
            finding, reasoning = _build_fallback_finding(indicators, final_severity, transcript)
            status = "degraded_fallback"

        # Step 8: Return unified EvidenceItem
        return EvidenceItem(
            agent="voice_agent",
            modality="voice",
            finding=finding,
            confidence=confidence,
            severity=final_severity,
            indicators=indicators,
            evidence=evidence,
            reasoning=reasoning,
            status=status,
            timestamp=timestamp,
        )

    except Exception:
        logger.exception("Unexpected unhandled error inside Voice Agent")
        return EvidenceItem(
            agent="voice_agent",
            modality="voice",
            finding="Voice analysis could not be completed.",
            confidence=0.0,
            severity="info",
            indicators=[],
            evidence={"error": "unhandled_internal_error"},
            reasoning="Voice Agent encountered an unrecoverable internal exception.",
            status="failed",
            timestamp=timestamp,
        )
