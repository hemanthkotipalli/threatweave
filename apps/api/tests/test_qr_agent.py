"""
tests/test_qr_agent.py
-----------------------
Unit and integration tests for ThreatWeave Phase 7 — QR Agent.

Coverage:
- Programmatic QR generation using qrcode library.
- URL-payload genuine delegation (asserts identical indicators and severity to url_agent.analyze_url).
- UPI deep-link analysis (mismatched VPA vs payee name flags qr_upi_deeplink_suspicious).
- UPI deep-link legitimate (payee matches VPA, no qr_upi_deeplink_suspicious).
- Plain-text payload delegation (matches text_agent.analyze_text result + qr_non_url_payload).
- Corrupted / non-image bytes (safe failed EvidenceItem, never raises).
- Clean valid image with no QR code (status="failed", qr_decode_failed indicator, never raises).
- Debug endpoint POST /api/v1/debug/qr-agent multipart upload verification.
"""
from __future__ import annotations

import io

import pytest
import qrcode
from fastapi.testclient import TestClient
from PIL import Image

from app.agents.qr_agent import analyze_qr
from app.agents.url_agent import analyze_url
from app.core.qr_decoder import decode_qr
from app.main import app


def _create_qr_image_bytes(data: str) -> bytes:
    """Helper to programmatically generate a PNG QR code in memory."""
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_solid_image_bytes(width: int = 200, height: int = 200, color: str = "white") -> bytes:
    """Helper to programmatically generate a plain solid color image without any QR code."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestQrDecoder:
    def test_decode_valid_qr(self):
        payload = "https://threatweave.local/test"
        img_bytes = _create_qr_image_bytes(payload)
        decoded = decode_qr(img_bytes)
        assert decoded == payload

    def test_decode_no_qr_image_returns_none(self):
        blank_bytes = _create_solid_image_bytes()
        decoded = decode_qr(blank_bytes)
        assert decoded is None

    def test_decode_corrupted_bytes_returns_none(self):
        corrupted = b"this is completely random corrupted data \x00\xff\xfe\x01\x02"
        decoded = decode_qr(corrupted)
        assert decoded is None

    def test_decode_empty_bytes_returns_none(self):
        assert decode_qr(b"") is None


class TestQrAgentUrlDelegation:
    def test_malicious_url_qr_delegation_matches_url_agent(self):
        """
        Encodes a malicious URL into a QR image.
        Asserts that qr_agent.analyze_qr() produces the EXACT SAME severity
        and indicators as calling url_agent.analyze_url() directly.
        Proves genuine delegation, not reimplemented logic.
        """
        test_url = "http://192.168.1.1@paypa1-verify.tk/login"
        qr_bytes = _create_qr_image_bytes(test_url)

        direct_url_result = analyze_url(test_url)
        qr_result = analyze_qr(qr_bytes)

        assert qr_result.agent == "qr_agent"
        assert qr_result.modality == "qr"
        assert qr_result.severity == direct_url_result.severity
        assert set(qr_result.indicators) == set(direct_url_result.indicators)
        assert "qr_non_url_payload" not in qr_result.indicators
        assert "url_analysis" in qr_result.evidence
        assert qr_result.confidence == pytest.approx(direct_url_result.confidence, abs=0.01)

    def test_clean_url_qr_delegation(self):
        clean_url = "https://www.wikipedia.org"
        qr_bytes = _create_qr_image_bytes(clean_url)

        direct_url_result = analyze_url(clean_url)
        qr_result = analyze_qr(qr_bytes)

        assert qr_result.agent == "qr_agent"
        assert qr_result.modality == "qr"
        assert qr_result.severity == direct_url_result.severity
        assert set(qr_result.indicators) == set(direct_url_result.indicators)
        assert "qr_non_url_payload" not in qr_result.indicators


class TestQrAgentUpiAnalysis:
    def test_suspicious_upi_deep_link_mismatched_payee(self):
        """
        A QR encoding a UPI payment where claimed payee name is 'Electricity Board Official'
        but actual VPA is 'scammer8831@fakebank'.
        Must flag qr_payment_request AND qr_upi_deeplink_suspicious.
        """
        upi_payload = "upi://pay?pa=scammer8831@fakebank&pn=Electricity+Board+Official&am=15000&cu=INR"
        qr_bytes = _create_qr_image_bytes(upi_payload)

        result = analyze_qr(qr_bytes)

        assert result.agent == "qr_agent"
        assert result.modality == "qr"
        assert "qr_payment_request" in result.indicators
        assert "qr_upi_deeplink_suspicious" in result.indicators
        assert result.severity in ("high", "critical")
        assert result.confidence >= 0.7
        assert "upi_details" in result.evidence
        assert result.evidence["upi_details"]["pa"] == "scammer8831@fakebank"

    def test_legitimate_upi_deep_link_consistent_identity(self):
        """
        A legitimate UPI QR code where payee name closely matches VPA username.
        qr_upi_deeplink_suspicious must NOT be present.
        """
        upi_payload = "upi://pay?pa=rameshkumar@okaxis&pn=Ramesh+Kumar&cu=INR"
        qr_bytes = _create_qr_image_bytes(upi_payload)

        result = analyze_qr(qr_bytes)

        assert result.agent == "qr_agent"
        assert result.modality == "qr"
        assert "qr_payment_request" in result.indicators
        assert "qr_upi_deeplink_suspicious" not in result.indicators
        assert result.severity in ("info", "low")


class TestQrAgentTextDelegation:
    def test_plain_text_qr_delegation_matches_text_agent(self):
        """
        A QR encoding a phishing-style plain text message.
        Asserts genuine delegation to text_agent.analyze_text(),
        with 'qr_non_url_payload' appended to the indicators.
        """
        from unittest.mock import patch

        from app.schemas.evidence import EvidenceItem

        phish_text = "URGENT: Your bank account will be suspended immediately. Verify credentials now."
        qr_bytes = _create_qr_image_bytes(phish_text)

        mock_item = EvidenceItem(
            agent="text_agent",
            modality="text",
            finding="Urgent phishing lure detected",
            confidence=0.92,
            severity="high",
            indicators=["urgency_language", "credential_request"],
            evidence={"raw_text": phish_text},
            reasoning="Suspicious urgent credential request",
            status="ok",
        )

        with patch("app.agents.qr_agent.analyze_text", return_value=mock_item) as mock_analyze:
            qr_result = analyze_qr(qr_bytes)

            mock_analyze.assert_called_once_with(phish_text)
            assert qr_result.agent == "qr_agent"
            assert qr_result.modality == "qr"
            assert qr_result.severity == "high"
            assert "qr_non_url_payload" in qr_result.indicators
            assert "urgency_language" in qr_result.indicators
            assert "credential_request" in qr_result.indicators


class TestQrAgentRobustness:
    def test_corrupted_image_bytes_never_raises(self):
        corrupted = b"not an image at all \x00\x01\x02 random bytes"
        result = analyze_qr(corrupted)

        assert result.agent == "qr_agent"
        assert result.modality == "qr"
        assert result.status == "failed"
        assert result.confidence == 0.0
        assert "qr_decode_failed" in result.indicators

    def test_empty_bytes_never_raises(self):
        result = analyze_qr(b"")

        assert result.agent == "qr_agent"
        assert result.status == "failed"
        assert "qr_decode_failed" in result.indicators

    def test_solid_image_without_qr_returns_failed(self):
        blank_bytes = _create_solid_image_bytes(300, 300, "white")
        result = analyze_qr(blank_bytes)

        assert result.agent == "qr_agent"
        assert result.status == "failed"
        assert "qr_decode_failed" in result.indicators


class TestDebugQrEndpoint:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_debug_qr_agent_endpoint_upload(self, client):
        qr_bytes = _create_qr_image_bytes("https://example.com/test-endpoint")
        response = client.post(
            "/api/v1/debug/qr-agent",
            files={"image": ("qr.png", qr_bytes, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "qr_agent"
        assert data["modality"] == "qr"
        assert "status" in data
