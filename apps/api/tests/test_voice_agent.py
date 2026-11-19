"""
tests/test_voice_agent.py
-------------------------
Unit and integration tests for ThreatWeave Phase 9 — Voice Agent.

Coverage:
- Programmatic audio fixture generation (pyttsx3 local TTS & pure WAV synthesis).
- Vishing script pattern detection and genuine Text Agent delegation.
- Benign audio clip handling and low-risk classification.
- Corrupted / non-audio bytes safety-net (status="failed", never raises).
- Silent audio handling (stt_failed / stt_low_confidence, never raises).
- Acoustic heuristic test asserting ai_voice_indicator_weak confidence cap <= 0.40.
- Automated Anti-Proof check: asserting finding/reasoning output contains no claims
  of proven/detected synthetic or deepfake voice.
- Debug endpoint POST /api/v1/debug/voice-agent multipart upload.
"""
from __future__ import annotations

import io
import os
import re
import tempfile
import wave
from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.agents.text_agent import analyze_text
from app.agents.voice_agent import analyze_voice
from app.core.stt_engine import transcribe_audio
from app.core.voice_heuristics import (
    analyze_acoustic_features,
    has_vishing_script_pattern,
)
from app.main import app


def _create_synthetic_speech_wav(text: str) -> bytes:
    """Helper to synthesize audio speech via pyttsx3 into in-memory WAV bytes."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        temp_path = tf.name

    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.save_to_file(text, temp_path)
        engine.runAndWait()

        with open(temp_path, "rb") as f:
            return f.read()
    except Exception:  # noqa: BLE001
        # Fallback to modulated tone WAV if SAPI5/espeak unavailable or fails
        return _create_synthetic_tone_wav(duration_sec=2.0)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _create_synthetic_tone_wav(duration_sec: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generates synthetic modulated tone WAV bytes."""
    b = io.BytesIO()
    with wave.open(b, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        t = np.linspace(0, duration_sec, int(sample_rate * duration_sec))
        signal = (np.sin(2 * np.pi * 440 * t) * 8000).astype(np.int16)
        wf.writeframes(signal.tobytes())
    return b.getvalue()


def _create_silent_wav(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    """Generates pure silent WAV bytes."""
    b = io.BytesIO()
    with wave.open(b, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        silence = np.zeros(int(sample_rate * duration_sec), dtype=np.int16)
        wf.writeframes(silence.tobytes())
    return b.getvalue()


class TestVoiceHeuristics:
    def test_vishing_script_pattern_positive(self):
        script = "This is an automated call from your bank. Your account has been compromised. Press 1 now to verify your PIN. Do not hang up."
        assert has_vishing_script_pattern(script) is True

    def test_vishing_script_pattern_scare_tactics(self):
        script = "This call is being recorded for security purposes. A warrant has been issued by the customs department. Do not hang up."
        assert has_vishing_script_pattern(script) is True

    def test_vishing_script_pattern_negative_benign(self):
        benign = "Hey John, are we still meeting for lunch tomorrow at the cafeteria? Let me know."
        assert has_vishing_script_pattern(benign) is False

    def test_vishing_script_empty_or_short(self):
        assert has_vishing_script_pattern("") is False
        assert has_vishing_script_pattern("Hello") is False

    def test_acoustic_features_on_flat_tone_bounded_confidence(self):
        """Acoustic feature confidence contribution must trigger on flat audio and be hard-capped at 0.40."""
        # Flat unmodulated tone creates near-zero energy variance (robotic/monotone)
        tone_bytes = _create_synthetic_tone_wav(duration_sec=2.0)
        acoustic = analyze_acoustic_features(tone_bytes)

        assert acoustic["is_monotone_cadence"] is True
        assert acoustic["indicator"] == "ai_voice_indicator_weak"
        assert 0.0 < acoustic["confidence_contribution"] <= 0.40

    def test_acoustic_features_empty_audio_never_raises(self):
        res = analyze_acoustic_features(b"")
        assert res["confidence_contribution"] == 0.0
        assert res["is_monotone_cadence"] is False

    def test_acoustic_features_on_non_wav_container(self):
        """Acoustic feature analysis must decode non-WAV formats (FLAC/OGG/MP3) via PyAV."""
        import av

        bio = io.BytesIO()
        container = av.open(bio, mode="w", format="flac")
        stream = container.add_stream("flac", rate=16000)
        t = np.linspace(0, 2.0, 32000)
        samples = (np.sin(2 * np.pi * 440 * t) * 8000).astype(np.int16)
        frame = av.AudioFrame.from_ndarray(samples.reshape(1, -1), format="s16", layout="mono")
        frame.rate = 16000
        for packet in stream.encode(frame):
            container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)
        container.close()

        flac_bytes = bio.getvalue()
        acoustic = analyze_acoustic_features(flac_bytes)
        assert acoustic["is_monotone_cadence"] is True
        assert acoustic["indicator"] == "ai_voice_indicator_weak"


class TestSttEngine:
    def test_stt_transcribes_valid_audio(self):
        phrase = "Threat intelligence automated test."
        audio_bytes = _create_synthetic_speech_wav(phrase)
        transcript, conf = transcribe_audio(audio_bytes)
        assert isinstance(transcript, str)
        assert isinstance(conf, float)
        assert conf >= 0.0

    def test_stt_handles_silent_audio(self):
        silent_bytes = _create_silent_wav(1.0)
        transcript, conf = transcribe_audio(silent_bytes)
        assert transcript == ""
        assert conf == 0.0

    def test_stt_handles_corrupted_bytes(self):
        transcript, conf = transcribe_audio(b"not an audio stream \x00\xff")
        assert transcript == ""
        assert conf == 0.0


class TestVoiceAgent:
    @patch("app.agents.voice_agent.transcribe_audio")
    def test_vishing_audio_fires_indicator_and_delegates_to_text_agent(self, mock_transcribe):
        """
        Vishing script audio -> vishing_script_pattern fires, genuine text_agent
        delegation occurs, text_analysis is populated, severity is high/critical.
        """
        phrase = "This is an automated call from your bank. Your account has been compromised. Press 1 now to verify your PIN. Do not hang up."
        mock_transcribe.return_value = (phrase, 0.95)
        audio_bytes = _create_synthetic_speech_wav(phrase)

        direct_text = analyze_text(phrase)
        result = analyze_voice(audio_bytes)

        assert result.agent == "voice_agent"
        assert result.modality == "voice"
        assert "vishing_script_pattern" in result.indicators
        assert result.severity in ("high", "critical")

        # Verify genuine delegation and populated text_analysis
        assert "text_analysis" in result.evidence
        assert result.evidence["text_analysis"].get("agent") == "text_agent"
        assert result.evidence["text_analysis"].get("severity") == direct_text.severity

        # Indicators from text agent are merged
        assert any(ind in result.indicators for ind in direct_text.indicators)

    @patch("app.agents.voice_agent.transcribe_audio")
    def test_benign_audio_returns_low_severity(self, mock_transcribe):
        """Benign conversation audio -> low severity, text_analysis populated."""
        phrase = "Hey, are we still meeting for lunch tomorrow at twelve? Let me know."
        mock_transcribe.return_value = (phrase, 0.95)
        audio_bytes = _create_synthetic_speech_wav(phrase)

        result = analyze_voice(audio_bytes)
        assert result.agent == "voice_agent"
        assert result.modality == "voice"
        assert result.severity in ("info", "low")
        assert "vishing_script_pattern" not in result.indicators
        assert "text_analysis" in result.evidence

    def test_silent_audio_returns_stt_failed_safely(self):
        """Silent audio -> stt_failed indicator, low severity, status='ok'."""
        silent_bytes = _create_silent_wav(1.0)
        result = analyze_voice(silent_bytes)

        assert result.agent == "voice_agent"
        assert result.modality == "voice"
        assert result.severity in ("info", "low")
        assert "stt_failed" in result.indicators
        assert result.status == "ok"

    def test_corrupted_audio_bytes_returns_failed_never_raises(self):
        """Corrupted/non-audio bytes -> status='failed', no exception."""
        corrupted = b"garbage data \x00\x01\x02 not audio"
        result = analyze_voice(corrupted)

        assert result.agent == "voice_agent"
        assert result.modality == "voice"
        assert result.status == "failed"
        assert result.confidence == 0.0

    def test_acoustic_confidence_contribution_capped_at_0_40(self):
        """Acoustic heuristic indicator confidence contribution never exceeds 0.40."""
        tone_bytes = _create_synthetic_tone_wav(duration_sec=2.0)
        result = analyze_voice(tone_bytes)

        assert result.agent == "voice_agent"
        if "ai_voice_indicator_weak" in result.indicators and "vishing_script_pattern" not in result.indicators:
            assert result.confidence <= 0.40

    @patch("app.agents.voice_agent.transcribe_audio")
    def test_never_claims_proof_of_ai_or_deepfake_voice(self, mock_transcribe):
        """
        AUTOMATED ANTI-PROOF SAFETY CHECK:
        The Voice Agent must NEVER claim to have proven or definitively detected
        AI-generated or deepfake voice in its findings or reasoning.
        """
        phrase = "This is an automated call from your bank. Your account has been compromised. Press 1 now to verify your PIN. Do not hang up."
        mock_transcribe.return_value = (phrase, 0.95)
        audio_bytes = _create_synthetic_speech_wav(phrase)
        result = analyze_voice(audio_bytes)

        combined_text = f"{result.finding} {result.reasoning}".lower()

        forbidden_proof_patterns = [
            r"\bdetected\s+ai\s+voice\b",
            r"\bproven\s+deepfake\b",
            r"\bconfirmed\s+synthetic\b",
            r"\bverified\s+artificial\s+audio\b",
            r"\bproven\s+ai\s+voice\b",
            r"\bdetected\s+deepfake\b",
            r"\bconfirmed\s+deepfake\b",
        ]

        for pattern in forbidden_proof_patterns:
            assert not re.search(pattern, combined_text), (
                f"Forbidden proof-claim pattern '{pattern}' found in Voice Agent output: {combined_text}"
            )


class TestDebugVoiceEndpoint:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_debug_voice_agent_endpoint(self, client):
        audio_bytes = _create_synthetic_speech_wav("Meeting reminder for tomorrow morning.")
        response = client.post(
            "/api/v1/debug/voice-agent",
            files={"audio": ("sample.wav", audio_bytes, "audio/wav")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "voice_agent"
        assert data["modality"] == "voice"
        assert "status" in data
        assert "text_analysis" in data["evidence"]


class TestVoiceAgentTempfileCleanup:
    """Regression tests verifying temporary file cleanup under normal and exception flows."""

    def test_temp_audio_file_cleaned_up_on_exception(self):
        """
        Simulates an unhandled exception during audio processing (transcribe_audio).
        Asserts that the temporary file created on disk is guaranteed to be deleted
        by the try/finally cleanup block, and voice_agent safely returns failed status.
        """
        tone_bytes = _create_synthetic_tone_wav(duration_sec=1.0)
        temp_dir = tempfile.gettempdir()
        existing_wavs = set(os.listdir(temp_dir))
        captured_temp_files: list[str] = []

        def crashing_stt(audio_bytes: bytes):
            # Inspect the temp directory for any new .wav files created by temporary_audio_file
            for fname in os.listdir(temp_dir):
                if fname.endswith(".wav") and fname not in existing_wavs:
                    full_path = os.path.join(temp_dir, fname)
                    if full_path not in captured_temp_files:
                        captured_temp_files.append(full_path)
            raise RuntimeError("Simulated STT worker crash mid-processing")

        with patch("app.agents.voice_agent.transcribe_audio", side_effect=crashing_stt):
            result = analyze_voice(tone_bytes)

        assert result.status == "failed"
        assert result.evidence.get("error") == "unhandled_internal_error"

        # Assert that all captured temporary files have been deleted from disk
        for temp_file in captured_temp_files:
            assert not os.path.exists(temp_file), f"Temp file {temp_file} was leaked on disk!"

    def test_temp_audio_file_context_manager_cleanup_direct(self):
        """
        Directly exercises temporary_audio_file context manager under exception
        to guarantee try/finally unlink execution.
        """
        from app.agents.voice_agent import temporary_audio_file

        test_bytes = b"RIFF" + b"\x00" * 60
        leaked_path: str | None = None

        with (
            pytest.raises(ValueError, match="mid-stream failure"),
            temporary_audio_file(test_bytes) as temp_path,
        ):
            leaked_path = temp_path
            assert os.path.exists(temp_path)
            raise ValueError("mid-stream failure")

        assert leaked_path is not None
        assert not os.path.exists(leaked_path), f"Temp file {leaked_path} was not cleaned up on exception!"
