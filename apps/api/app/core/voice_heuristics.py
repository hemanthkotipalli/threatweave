"""
app/core/voice_heuristics.py
----------------------------
Heuristic pattern detection and non-conclusive acoustic feature analysis
for audio recordings and voice call transcripts (ThreatWeave Phase 9).

CRITICAL FRAMING AND SAFETY REQUIREMENT:
This module NEVER claims to have detected or proven synthetic, deepfake, or
AI-generated voice. Any acoustic anomaly is strictly a WEAK, non-conclusive
indicator (capped at 0.40 maximum confidence contribution) and must always
be described in hedged, probabilistic terminology.
"""
from __future__ import annotations

import io
import logging
import re
import wave
from typing import Any

import numpy as np

logger = logging.getLogger("threatweave-api.core.voice_heuristics")

# Scripted telephone scam phrases common in vishing operations
_VISHING_PATTERNS = [
    # Bank & Financial Impersonation
    re.compile(r"(?:automated\s+call\s+from\s+your\s+bank|calling\s+from\s+(?:your\s+)?bank|reserve\s+bank|fraud\s+prevention\s+department)", re.IGNORECASE),
    re.compile(r"(?:account\s+(?:has\s+been\s+)?compromised|unauthorized\s+transaction|suspicious\s+activity\s+detected)", re.IGNORECASE),
    re.compile(r"(?:press\s+[0-9]\s+(?:to\s+)?(?:verify|connect|speak|cancel|confirm))", re.IGNORECASE),
    re.compile(r"(?:confirm\s+(?:your\s+)?(?:otp|pin|password|cvv|account\s+number|social\s+security))", re.IGNORECASE),
    # Coercion and Scaretactics
    re.compile(r"(?:do\s+not\s+hang\s+up|stay\s+on\s+the\s+line|immediate\s+action\s+is\s+required)", re.IGNORECASE),
    re.compile(r"(?:this\s+call\s+is\s+(?:being\s+)?recorded\s+for\s+(?:security|verification|quality)\s+purposes)", re.IGNORECASE),
    re.compile(r"(?:warrant\s+(?:has\s+been\s+)?issued|legal\s+action|digital\s+arrest|police\s+department|customs\s+department)", re.IGNORECASE),
    re.compile(r"(?:tech(?:nical)?\s+support|refund\s+(?:will\s+be\s+)?cancelled|install\s+(?:anydesk|teamviewer|quicksupport))", re.IGNORECASE),
]


def has_vishing_script_pattern(transcript: str) -> bool:
    """
    Determines whether a transcript matches characteristic scripted vishing / call center fraud.

    Args:
        transcript: Speech-to-text transcript string.

    Returns:
        bool: True if any prominent vishing script pattern is detected, False otherwise.
        Never raises.
    """
    if not transcript or not isinstance(transcript, str):
        return False

    try:
        normalized = transcript.strip().lower()
        if len(normalized) < 10:
            return False

        for pattern in _VISHING_PATTERNS:
            if pattern.search(normalized):
                logger.info("Vishing script pattern matched: %s", pattern.pattern[:40])
                return True

        return False
    except Exception as exc:  # noqa: BLE001 - heuristics contract mandates never raising
        logger.debug("has_vishing_script_pattern error: %s", exc)
        return False


def analyze_acoustic_features(audio_bytes: bytes) -> dict[str, Any]:
    """
    Computes lightweight, non-conclusive acoustic variance metrics across the audio clip.

    Checks for abnormally low pitch/energy modulation (monotone robotic cadence)
    often found in automated IVR spoofers or basic synthetic voices.

    CRITICAL: This is a WEAK, non-conclusive indicator only.
    The confidence contribution is strictly capped at 0.40.
    It does NOT prove synthetic or deepfake audio.

    Args:
        audio_bytes: Raw bytes of the audio file.

    Returns:
        dict: Numeric acoustic features and weak indicator if applicable.
        Never raises.
    """
    default_result: dict[str, Any] = {
        "energy_variance": 0.0,
        "zero_crossing_variance": 0.0,
        "is_monotone_cadence": False,
        "confidence_contribution": 0.0,
        "indicator": None,
    }

    if not audio_bytes or len(audio_bytes) < 512:
        return default_result

    try:
        samples: np.ndarray | None = None
        framerate: int = 16000

        # Attempt universal audio decoding (MP3, AAC, OGG, FLAC, WAV) via PyAV
        try:
            import av

            container = av.open(io.BytesIO(audio_bytes))
            audio_stream = next((s for s in container.streams if s.type == "audio"), None)
            if audio_stream is not None:
                resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
                chunks: list[np.ndarray] = []
                for frame in container.decode(audio_stream):
                    frame.pts = None
                    resampled = resampler.resample(frame)
                    if resampled:
                        for rf in resampled:
                            chunks.append(rf.to_ndarray().flatten())
                if chunks:
                    samples = np.concatenate(chunks).astype(np.float32)
                    framerate = 16000
        except Exception as av_exc:
            logger.debug("PyAV decode failed or unavailable (%s), trying wave fallback", av_exc)

        # Standard WAV fallback if PyAV was not used or failed
        if samples is None:
            stream = io.BytesIO(audio_bytes)
            with wave.open(stream, "rb") as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()

                if n_frames < framerate * 0.5:  # Less than 0.5 seconds
                    return default_result

                raw_frames = wf.readframes(n_frames)

            dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
            dtype = dtype_map.get(sampwidth, np.int16)
            samples = np.frombuffer(raw_frames, dtype=dtype)

            if n_channels > 1:
                samples = samples[::n_channels]  # Take first channel

            samples = samples.astype(np.float32)

        if samples is None or len(samples) < framerate * 0.5:
            return default_result

        # Compute energy across 100ms frames
        frame_size = int(framerate * 0.1)
        if frame_size <= 0 or len(samples) < frame_size * 2:
            return default_result

        num_chunks = len(samples) // frame_size
        chunks = samples[: num_chunks * frame_size].reshape(num_chunks, frame_size)

        # RMS energy per chunk
        rms_energies = np.sqrt(np.mean(chunks**2, axis=1) + 1e-9)

        # Zero-crossing rate per chunk (proxy for frequency fluctuation)
        zcrs = np.mean(np.abs(np.diff(np.sign(chunks), axis=1)) > 0, axis=1)

        # Variance metrics
        energy_mean = np.mean(rms_energies) + 1e-6
        energy_std = np.std(rms_energies)
        energy_cov = float(energy_std / energy_mean)  # Coefficient of variation

        zcr_std = float(np.std(zcrs))

        # Human natural speech typically has dynamic energy modulation (cov > 0.45).
        # Unnaturally flat, monotone TTS or scripted robotic tones have low variance.
        is_monotone = bool(energy_cov < 0.28 and zcr_std < 0.05 and energy_mean > 100)

        # Confidence contribution strictly capped at 0.40
        conf_contribution = 0.35 if is_monotone else 0.0
        conf_contribution = min(0.40, conf_contribution)

        indicator = "ai_voice_indicator_weak" if is_monotone else None

        return {
            "energy_variance": round(energy_cov, 4),
            "zero_crossing_variance": round(zcr_std, 4),
            "is_monotone_cadence": is_monotone,
            "confidence_contribution": conf_contribution,
            "indicator": indicator,
        }

    except Exception as exc:  # noqa: BLE001 - heuristics contract mandates never raising
        logger.debug("analyze_acoustic_features error: %s", exc)
        return default_result
