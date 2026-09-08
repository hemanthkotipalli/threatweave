"""
tests/test_orchestrator_routing.py
----------------------------------
Integration tests verifying LangGraph dynamic agent routing (ThreatWeave Phase 10).

Coverage:
- Investigation with ONLY text evidence -> text_agent is done, 4 others are skipped.
- Investigation with url + image (no QR code) -> url_agent & image_agent are done, others skipped.
- Investigation with image containing QR code -> qr_agent is done.
- Cross-modal investigation (text + url + image + voice) -> all relevant agents ran,
  agent_findings rows exist with valid foreign keys in database.
"""
from __future__ import annotations

import io
import uuid

import qrcode
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.agent_finding import AgentFinding
from app.models.agent_run import AgentRun
from app.models.enums import AgentStatus
from tests.test_image_agent import _create_text_image_bytes
from tests.test_voice_agent import _create_synthetic_speech_wav

client = TestClient(app)


def _create_qr_image_bytes(data: str) -> bytes:
    """Helper to programmatically generate a PNG QR code in memory."""
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestOrchestratorRouting:
    def test_text_only_routing(self):
        """Text only -> text_agent runs, url/qr/image/voice are skipped."""
        resp = client.post(
            "/api/v1/investigations",
            data={"text": "URGENT: Your bank account will be suspended. Verify now.", "title": "Text Routing Test"},
        )
        assert resp.status_code == 201
        inv_id = resp.json()["investigation"]["id"]

        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert data["status"] == "completed"

        # Verify direct database state
        with SessionLocal() as db:
            runs = db.query(AgentRun).filter(AgentRun.investigation_id == uuid.UUID(inv_id)).all()
            run_map = {r.agent_name: r.status for r in runs}

            assert run_map.get("text_agent") == AgentStatus.DONE
            assert run_map.get("url_agent") == AgentStatus.SKIPPED
            assert run_map.get("qr_agent") == AgentStatus.SKIPPED
            assert run_map.get("image_agent") == AgentStatus.SKIPPED
            assert run_map.get("voice_agent") == AgentStatus.SKIPPED

    def test_url_and_image_no_qr_routing(self):
        """URL + Image (no QR code) -> url_agent & image_agent run, others skipped."""
        img_bytes = _create_text_image_bytes("Payment Successful! Rs. 49,999 received from Ramesh Kumar")
        resp = client.post(
            "/api/v1/investigations",
            data={"url": "http://192.168.1.1@paypal-verify.tk/login", "title": "URL Image Routing Test"},
            files={"image": ("payment_proof.png", io.BytesIO(img_bytes), "image/png")},
        )
        assert resp.status_code == 201
        inv_id = resp.json()["investigation"]["id"]

        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert data["status"] == "completed"

        with SessionLocal() as db:
            runs = db.query(AgentRun).filter(AgentRun.investigation_id == uuid.UUID(inv_id)).all()
            run_map = {r.agent_name: r.status for r in runs}

            assert run_map.get("url_agent") == AgentStatus.DONE
            assert run_map.get("image_agent") == AgentStatus.DONE
            assert run_map.get("text_agent") == AgentStatus.SKIPPED
            assert run_map.get("qr_agent") == AgentStatus.SKIPPED
            assert run_map.get("voice_agent") == AgentStatus.SKIPPED

    def test_image_with_qr_code_routing(self):
        """Image containing standalone QR code -> qr_agent runs."""
        qr_bytes = _create_qr_image_bytes("https://malicious-qr-verify.com/login")
        resp = client.post(
            "/api/v1/investigations",
            data={"title": "QR Routing Test"},
            files={"image": ("qr_code.png", io.BytesIO(qr_bytes), "image/png")},
        )
        assert resp.status_code == 201
        inv_id = resp.json()["investigation"]["id"]

        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert data["status"] == "completed"

        with SessionLocal() as db:
            runs = db.query(AgentRun).filter(AgentRun.investigation_id == uuid.UUID(inv_id)).all()
            run_map = {r.agent_name: r.status for r in runs}

            assert run_map.get("qr_agent") == AgentStatus.DONE
            assert run_map.get("text_agent") == AgentStatus.SKIPPED
            assert run_map.get("url_agent") == AgentStatus.SKIPPED
            assert run_map.get("voice_agent") == AgentStatus.SKIPPED

    def test_full_cross_modal_routing(self):
        """Full cross-modal investigation (text + url + image + voice) -> all relevant agents ran."""
        img_bytes = _create_text_image_bytes("Notice: Account suspension warning")
        voice_bytes = _create_synthetic_speech_wav("Automated bank call. Your account is compromised. Press 1 now.")

        resp = client.post(
            "/api/v1/investigations",
            data={
                "title": "Full Cross-Modal Swarm Test",
                "text": "Urgent security notification: suspicious login attempt detected.",
                "url": "http://secure-bank-login.xyz/verify",
            },
            files={
                "image": ("suspicious_notice.png", io.BytesIO(img_bytes), "image/png"),
                "voice": ("vishing_voicemail.wav", io.BytesIO(voice_bytes), "audio/wav"),
            },
        )
        assert resp.status_code == 201
        inv_id = resp.json()["investigation"]["id"]

        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200
        data = analyze_resp.json()
        assert data["status"] == "completed"

        # Verify in database directly
        with SessionLocal() as db:
            runs = db.query(AgentRun).filter(AgentRun.investigation_id == uuid.UUID(inv_id)).all()
            run_map = {r.agent_name: r for r in runs}

            # All 4 modalities had inputs, so their agents should be DONE
            for agent in ("text_agent", "url_agent", "image_agent", "voice_agent"):
                assert agent in run_map, f"Missing AgentRun row for {agent}"
                assert run_map[agent].status == AgentStatus.DONE
                assert run_map[agent].latency_ms is not None
                assert run_map[agent].latency_ms >= 0

                # Verify foreign key linkage of AgentFinding rows
                findings = db.query(AgentFinding).filter(AgentFinding.agent_run_id == run_map[agent].id).all()
                assert len(findings) >= 1, f"Expected AgentFinding rows for {agent}"
                for f in findings:
                    assert f.agent_run_id == run_map[agent].id
                    assert f.finding
                    assert 0.0 <= f.confidence <= 1.0
                    assert f.status
