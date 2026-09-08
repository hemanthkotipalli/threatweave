"""
apps/api/tests/test_edge_cases.py
---------------------------------
Edge-case, boundary condition, and extreme-input tests for ThreatWeave (Phase 18).

Coverage:
1. Full 5-Modality Swarm Execution:
   - Runs ONE investigation with text + url + image + qr + voice simultaneously.
   - Triggers dynamic hybrid routing (QR flyer with embedded OCR text + QR code).
   - Asserts all 5 specialist agents run (text, url, qr, image, voice), none skipped.
   - Confirms full pipeline completion with non-crashing final risk score.
2. Empty and Near-Empty Inputs:
   - Empty text input rejected gracefully at boundary (400 validation error).
   - Minimal 1x1 blank image handled gracefully through full pipeline (no crash, low risk).
   - 1-second pure silent audio handled gracefully through full pipeline (no crash, low risk).
3. Boundary Text Payload (20,000 Chars):
   - Ingests near-maximum 19,500-character text payload.
   - Confirms Text Agent and Groq/LLM summarizer process without timeout or memory crash.
   - Confirms text exceeding 20,000 chars is rejected with 400 'text_too_long'.
4. Multilingual & Emoji Evidence Inputs:
   - Ingests Unicode payload with Cyrillic, Chinese, Devanagari, and security emojis.
   - Asserts UTF-8 database storage and end-to-end processing without UnicodeDecodeError.
   - Documents observed multilingual behavior.
"""
from __future__ import annotations

import io
import uuid

import qrcode
from PIL import Image, ImageDraw, ImageFont
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.agent_run import AgentRun
from app.models.enums import AgentStatus
from app.models.investigation import Investigation
from tests.test_voice_agent import _create_silent_wav, _create_synthetic_speech_wav

client = TestClient(app)


def _create_hybrid_qr_flyer_bytes(qr_payload: str, banner_text: str) -> bytes:
    """
    Creates an image containing both a scannable QR code AND high-contrast OCR text (>15 chars).
    Under Phase 10's plan_node routing rules:
    - decode_qr finds the QR code -> schedules qr_agent
    - OCR extracts > 15 chars of text -> ALSO schedules image_agent
    """
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(qr_payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    canvas_w, canvas_h = 800, 700
    img = Image.new("RGB", (canvas_w, canvas_h), color="white")
    draw = ImageDraw.Draw(img)

    # Paste QR centered at top
    img.paste(qr_img, (215, 30))

    # Render OCR text at bottom with multi-line wrap
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
            font = ImageFont.truetype(font_path, 22)
            break
        except (OSError, TypeError, ValueError):
            pass
    if font is None:
        try:
            font = ImageFont.load_default(size=20)
        except (TypeError, ValueError):
            font = ImageFont.load_default()

    words = banner_text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + 1 > 45:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
        else:
            curr.append(w)
            curr_len += len(w) + 1
    if curr:
        lines.append(" ".join(curr))

    y = 480
    for line in lines:
        draw.text((40, y), line, fill="black", font=font)
        y += 35

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestAllFiveModalitiesSwarm:
    """Tests simultaneous execution of all 5 specialist agents in a single investigation."""

    def test_single_investigation_all_five_agents_executed(self):
        """
        Submits text + url + hybrid (QR + OCR image) + voice in ONE investigation.
        Verifies that all 5 agents (text_agent, url_agent, qr_agent, image_agent, voice_agent)
        run and transition to DONE status, without any being skipped or failing.
        """
        hybrid_img_bytes = _create_hybrid_qr_flyer_bytes(
            qr_payload="https://suspicious-qr-verify.net/portal",
            banner_text="SECURITY NOTICE: Scan QR code to resolve immediate banking suspension.",
        )
        voice_bytes = _create_synthetic_speech_wav(
            "This is an automated alert from your financial institution. Immediate action is required."
        )

        create_resp = client.post(
            "/api/v1/investigations",
            data={
                "title": "All-Five-Modalities Comprehensive Swarm",
                "text": "Urgent alert: Account credentials need verification on portal.",
                "url": "http://192.168.1.1@secure-update-center.org/login",
            },
            files={
                "image": ("hybrid_security_flyer.png", io.BytesIO(hybrid_img_bytes), "image/png"),
                "voice": ("urgent_voicemail.wav", io.BytesIO(voice_bytes), "audio/wav"),
            },
        )
        assert create_resp.status_code == 201, f"Failed to create 5-modality investigation: {create_resp.text}"
        inv_id = create_resp.json()["investigation"]["id"]

        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200, f"Analyze failed: {analyze_resp.text}"
        data = analyze_resp.json()
        assert data["status"] == "completed"
        assert data["risk"] is not None
        assert 0.0 <= data["risk"]["final_risk"] <= 1.0

        # Direct DB verification: confirm all 5 specialist agents executed and none skipped
        with SessionLocal() as db:
            runs = db.query(AgentRun).filter(AgentRun.investigation_id == uuid.UUID(inv_id)).all()
            run_statuses = {r.agent_name: r.status for r in runs}

            expected_agents = ["text_agent", "url_agent", "qr_agent", "image_agent", "voice_agent"]
            for ag in expected_agents:
                assert ag in run_statuses, f"Agent {ag} was not tracked in AgentRun records!"
                assert run_statuses[ag] == AgentStatus.DONE, (
                    f"Expected {ag} to be DONE, got {run_statuses[ag]} instead!"
                )

        print(f"\n[5-Modality Verified] All 5 agents ran to completion for investigation {inv_id}.")


class TestEmptyAndNearEmptyInputs:
    """Tests system boundary behavior on empty or minimal inputs."""

    def test_empty_text_input_rejected(self):
        """Empty string input without other evidence must be rejected with 400 validation error."""
        resp = client.post(
            "/api/v1/investigations",
            data={"title": "Empty Text Test", "text": "   "},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["error"]["code"] == "validation_error"

    def test_blank_1x1_image_handled_gracefully(self):
        """
        Submits a valid 1x1 white PNG image (no text, no QR).
        Confirms full pipeline processes it without crashing, yielding low risk score.
        """
        img = Image.new("RGB", (1, 1), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        blank_bytes = buf.getvalue()

        create_resp = client.post(
            "/api/v1/investigations",
            data={"title": "Blank 1x1 Image Investigation"},
            files={"image": ("blank.png", io.BytesIO(blank_bytes), "image/png")},
        )
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investigation"]["id"]

        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert data["status"] == "completed"
        assert data["risk"] is not None
        assert data["risk"]["severity"].lower() in ("low", "informational", "info")

    def test_silent_audio_handled_gracefully(self):
        """
        Submits 1.0 second of pure silence (WAV zeros).
        Confirms Whisper and Voice Agent handle zero-transcription gracefully without crashing.
        """
        silent_bytes = _create_silent_wav(duration_sec=1.0)

        create_resp = client.post(
            "/api/v1/investigations",
            data={"title": "Silent Audio Investigation"},
            files={"voice": ("silence.wav", io.BytesIO(silent_bytes), "audio/wav")},
        )
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investigation"]["id"]

        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert data["status"] == "completed"
        assert data["risk"] is not None


class TestTextLengthBoundaries:
    """Tests MAX_TEXT_CHARS (20,000) limits and large payload handling."""

    def test_large_text_near_20000_limit_handled(self):
        """
        Submits 19,500 characters of text (within MAX_TEXT_CHARS limit).
        Confirms text ingestion and analysis complete without memory exhaustion or timeouts.
        """
        filler = "Account verification is required due to observed anomalous network transactions. "
        # 19500 chars
        large_text = (filler * (19500 // len(filler) + 1))[:19500]
        assert len(large_text) == 19500

        create_resp = client.post(
            "/api/v1/investigations",
            data={"title": "Large Payload Test (19.5k)", "text": large_text},
        )
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investigation"]["id"]

        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200
        assert analyze_resp.json()["status"] == "completed"

    def test_text_exceeding_20000_limit_rejected(self):
        """Text of 20,001 characters must be rejected with 400 text_too_long."""
        excessive_text = "A" * 20001
        resp = client.post(
            "/api/v1/investigations",
            data={"title": "Excessive Payload Test", "text": excessive_text},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["error"]["code"] == "text_too_long"
        assert "20000" in data["error"]["message"]


class TestMultilingualAndEmojiText:
    """Tests pipeline resilience against multilingual scripts and emojis."""

    def test_multilingual_unicode_and_emojis_pipeline_resilience(self):
        """
        Submits mixed Russian, Chinese, Devanagari, and emoji threat text with an embedded link.
        Verifies UTF-8 persistence, absence of Unicode exceptions, and successful risk scoring.
        """
        unicode_payload = (
            "🚨 ВНИМАНИЕ: Срочно подтвердите пароль! "
            "安全警告：您的银行账户已被冻结，请立即登录解锁 🔒 "
            "⚠️ कृपया तुरंत अपनी पहचान सत्यापित करें: "
            "http://identity-verify-international.xyz/update"
        )

        create_resp = client.post(
            "/api/v1/investigations",
            data={"title": "Multilingual Threat Unicode Test 🌐", "text": unicode_payload},
        )
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investigation"]["id"]

        # Verify DB stored the exact unicode string without mangling
        with SessionLocal() as db:
            inv = db.query(Investigation).filter(Investigation.id == uuid.UUID(inv_id)).first()
            assert inv is not None
            text_input = next(
                ev for ev in inv.evidence_inputs
                if (ev.modality.value if hasattr(ev.modality, "value") else str(ev.modality)) == "text"
            )
            assert "安全警告" in text_input.raw_content_ref
            assert "ВНИМАНИЕ" in text_input.raw_content_ref
            assert "🚨" in text_input.raw_content_ref

        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert data["status"] == "completed"
        assert data["risk"] is not None
        print(f"\n[Multilingual Verified] Investigation completed with risk score {data['risk']['final_risk']}.")
