"""
tests/test_image_agent.py
-------------------------
Unit and integration tests for ThreatWeave Phase 8 — Image Agent.

Coverage:
- Programmatic PIL test fixture generation.
- Fake payment confirmation heuristic detection.
- Phishing URL detection in screenshot and genuine URL Agent delegation.
- Phishing text detection in screenshot and genuine Text Agent delegation.
- Institutional impersonation banner detection.
- Clean blank image handling (ocr_failed / ocr_low_confidence, never raises).
- Corrupted / non-image bytes (status="failed", never raises).
- Debug endpoint POST /api/v1/debug/image-agent multipart upload.
"""
from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from app.agents.image_agent import analyze_image
from app.agents.text_agent import analyze_text
from app.agents.url_agent import analyze_url
from app.core.image_heuristics import (
    extract_embedded_contact_info,
    extract_embedded_urls,
    has_impersonation_claim,
    has_payment_confirmation_pattern,
)
from app.core.ocr_engine import extract_text
from app.main import app


def _create_text_image_bytes(text: str, width: int = 1400, height: int = 200) -> bytes:
    """Helper to programmatically render high-contrast black text on white canvas with clear monospace font."""
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)
    font = None
    for font_path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "consola.ttf",
        "arial.ttf",
    ):
        try:
            font = ImageFont.truetype(font_path, 30)
            break
        except (OSError, TypeError, ValueError):
            pass
    if font is None:
        try:
            font = ImageFont.load_default(size=28)
        except (TypeError, ValueError):
            font = ImageFont.load_default()

    draw.text((30, 60), text, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_solid_image_bytes(width: int = 200, height: int = 200, color: str = "white") -> bytes:
    """Helper to generate a clean image with zero text."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestImageHeuristics:
    def test_payment_confirmation_positive(self):
        text = "Payment Successful! Rs. 49,999 received from Ramesh Kumar"
        assert has_payment_confirmation_pattern(text) is True

    def test_payment_confirmation_negative(self):
        text = "Meeting scheduled tomorrow with Ramesh Kumar at office."
        assert has_payment_confirmation_pattern(text) is False

    def test_impersonation_positive(self):
        text = "SBI Warning: Your account is suspended immediately. Update KYC."
        assert has_impersonation_claim(text) is True

    def test_impersonation_negative(self):
        text = "Welcome to the community event hosted in Mumbai."
        assert has_impersonation_claim(text) is False

    def test_extract_urls(self):
        text = "Please log in to http://192.168.1.1@paypa1-verify.tk/login to proceed."
        urls = extract_embedded_urls(text)
        assert len(urls) == 1
        assert "paypa1-verify.tk" in urls[0]

    def test_extract_contact_info(self):
        text = "Contact support at +91-9876543210 or send to merchant@icici"
        contacts = extract_embedded_contact_info(text)
        assert any("9876543210" in c for c in contacts)
        assert any("merchant@icici" in c for c in contacts)

    def test_extract_contact_info_excludes_url_userinfo(self):
        text = "Visit http://192.168.1.1@paypal-verify.tk/login now"
        contacts = extract_embedded_contact_info(text)
        assert contacts == []


class TestOcrEngine:
    def test_ocr_extracts_text_from_clean_fixture(self):
        sample = "ThreatWeave Security Audit"
        img_bytes = _create_text_image_bytes(sample)
        extracted, conf = extract_text(img_bytes)
        assert "ThreatWeave" in extracted or "Security" in extracted
        assert conf > 0.0

    def test_ocr_blank_image_returns_empty(self):
        blank_bytes = _create_solid_image_bytes()
        extracted, conf = extract_text(blank_bytes)
        assert extracted == ""
        assert conf == 0.0

    def test_ocr_corrupted_bytes_never_raises(self):
        extracted, conf = extract_text(b"not an image \x00\xff")
        assert extracted == ""
        assert conf == 0.0


class TestImageAgent:
    def test_fake_payment_confirmation_fires_indicator(self):
        """Image rendering fake payment confirmation -> fake_payment_confirmation fires."""
        img_bytes = _create_text_image_bytes("Payment Successful! Rs. 49,999 received from Ramesh Kumar")
        result = analyze_image(img_bytes)

        assert result.agent == "image_agent"
        assert result.modality == "image"
        assert "fake_payment_confirmation" in result.indicators
        assert result.severity in ("high", "critical")

    def test_embedded_phishing_url_delegation_matches_url_agent(self):
        """
        Image rendering phishing URL -> proves genuine delegation to url_agent.
        Asserts severity and indicators match url_agent.analyze_url() directly.
        """
        target_url = "http://192.168.1.1@paypa1-verify.tk/login"
        img_bytes = _create_text_image_bytes(f"Visit {target_url} now")

        img_result = analyze_image(img_bytes)

        assert img_result.agent == "image_agent"
        assert img_result.modality == "image"
        assert "url_analyses" in img_result.evidence
        assert len(img_result.evidence["url_analyses"]) >= 1

        delegated_url = img_result.evidence["heuristics"]["embedded_urls"][0]
        direct_url_result = analyze_url(delegated_url)

        assert img_result.severity == direct_url_result.severity
        for ind in direct_url_result.indicators:
            assert ind in img_result.indicators

    def test_phishing_text_delegation_matches_text_agent(self):
        """
        Image rendering phishing text -> proves genuine delegation to text_agent.
        """
        phish_phrase = "URGENT: Your bank account will be suspended immediately. Verify credentials now."
        img_bytes = _create_text_image_bytes(phish_phrase)

        direct_text_result = analyze_text(phish_phrase)
        img_result = analyze_image(img_bytes)

        assert img_result.agent == "image_agent"
        assert img_result.modality == "image"
        # Core social engineering flags should be present in merged indicators
        assert any(ind in img_result.indicators for ind in direct_text_result.indicators)

    def test_impersonation_banner_fires_indicator(self):
        """Image rendering bank impersonation with urgency language -> impersonation_banner fires."""
        banner_text = "State Bank of India Warning: Your account is suspended immediately. Update KYC."
        img_bytes = _create_text_image_bytes(banner_text)

        result = analyze_image(img_bytes)
        assert result.agent == "image_agent"
        assert "impersonation_banner" in result.indicators
        assert result.severity in ("high", "critical")

    def test_blank_image_returns_low_severity_safe_result(self):
        """Blank image -> ocr_failed indicator, severity info, no exception."""
        blank_bytes = _create_solid_image_bytes()
        result = analyze_image(blank_bytes)

        assert result.agent == "image_agent"
        assert result.modality == "image"
        assert result.severity in ("info", "low")
        assert "ocr_failed" in result.indicators
        assert result.status == "ok"

    def test_corrupted_bytes_returns_failed_never_raises(self):
        """Corrupted/random bytes -> status='failed', no exception."""
        corrupted = b"garbage data \x00\x01\x02 not image"
        result = analyze_image(corrupted)

        assert result.agent == "image_agent"
        assert result.modality == "image"
        assert result.status == "failed"
        assert result.confidence == 0.0


class TestDebugImageEndpoint:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_debug_image_agent_endpoint(self, client):
        img_bytes = _create_text_image_bytes("Notice: System maintenance completed.")
        response = client.post(
            "/api/v1/debug/image-agent",
            files={"image": ("screenshot.png", img_bytes, "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent"] == "image_agent"
        assert data["modality"] == "image"
        assert "status" in data
        assert "text_analysis" in data["evidence"]
        assert data["evidence"]["text_analysis"].get("agent") == "text_agent"
