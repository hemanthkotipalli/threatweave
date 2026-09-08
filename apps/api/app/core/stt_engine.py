"""
app/core/stt_engine.py
----------------------
Speech-to-text (STT) transcription engine using faster-whisper (ThreatWeave Phase 9).
Runs fully offline locally on CPU with int8 quantization.

Guarantees:
- Never raises exceptions: returns ("", 0.0) on failure or corrupted input.
- Model singleton caching: keeps the model in memory across invocations.
"""
from __future__ import annotations

import io
import logging
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

logger = logging.getLogger("threatweave-api.core.stt_engine")

_WHISPER_MODEL: WhisperModel | None = None
_MODEL_SIZE = "base"


def _get_whisper_model() -> WhisperModel:
    """
    Returns the cached WhisperModel singleton, initializing it if necessary.
    Uses CPU execution with int8 compute type for speed and low memory footprint.
    """
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        logger.info("Initializing faster-whisper model (size=%s, device=cpu, compute_type=int8)", _MODEL_SIZE)
        from faster_whisper import WhisperModel

        _WHISPER_MODEL = WhisperModel(_MODEL_SIZE, device="cpu", compute_type="int8")
        logger.info("faster-whisper model loaded successfully")
    return _WHISPER_MODEL


def transcribe_audio(audio_bytes: bytes) -> tuple[str, float]:
    """
    Transcribes raw audio bytes into text and returns an estimated confidence score.

    Args:
        audio_bytes: Raw bytes of the audio file (WAV, MP3, OGG, etc.)

    Returns:
        tuple[str, float]: (transcript_text, confidence_score_0_to_1)
        Returns ("", 0.0) on failure, corrupted bytes, or silent audio.
    """
    if not audio_bytes or len(audio_bytes) < 64:
        logger.debug("Audio bytes empty or too small (<64 bytes)")
        return ("", 0.0)

    try:
        model = _get_whisper_model()
        audio_stream = io.BytesIO(audio_bytes)

        # Transcribe audio stream
        segments, _info = model.transcribe(audio_stream, beam_size=5)

        segment_texts: list[str] = []
        confidences: list[float] = []

        for segment in segments:
            text = segment.text.strip()
            if text:
                segment_texts.append(text)
                # Map avg_logprob to estimated probability (0..1)
                logprob = getattr(segment, "avg_logprob", None)
                if logprob is not None:
                    prob = math.exp(max(logprob, -10.0))
                    confidences.append(max(0.0, min(1.0, prob)))

        transcript = " ".join(segment_texts).strip()
        if not transcript:
            logger.debug("Transcription resulted in empty text")
            return ("", 0.0)

        # Average confidence across non-empty segments
        if confidences:
            avg_conf = round(sum(confidences) / len(confidences), 4)
        else:
            avg_conf = 0.8

        logger.info("Transcription completed: %d chars, avg_conf=%.4f", len(transcript), avg_conf)
        return (transcript, avg_conf)

    except Exception as exc:  # noqa: BLE001 - contract specifies stt_engine must never raise
        logger.debug("transcribe_audio encountered error: %s", exc)
        return ("", 0.0)
