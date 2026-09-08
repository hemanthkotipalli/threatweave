"""
tests/test_risk_integration.py
------------------------------
Cross-modal integration test for Phase 11: Evidence Correlation & Risk Engine.
Validates that multimodal evidence correlation genuinely increases the overall risk signal
beyond what any single agent detects in isolation.
"""
from __future__ import annotations

import io
import uuid

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.agents.risk_engine import compute_risk
from app.db.session import SessionLocal
from app.main import app
from app.models.conflict_log import ConflictLog
from app.models.investigation import Investigation
from app.models.risk_breakdown import RiskBreakdown

client = TestClient(app)


def _generate_phishing_image_bytes(headline: str, body: str) -> bytes:
    """Generates synthetic image containing phishing lure text."""
    img = Image.new("RGB", (600, 250), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), headline, fill=(200, 0, 0))
    draw.text((20, 80), body, fill=(0, 0, 0))
    draw.text((20, 130), "Visit http://192.168.1.50/sbi-verify/login.php immediately", fill=(0, 0, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestCrossModalRiskIntegration:
    """Tests full orchestrator pipeline with correlation, conflict detection, and risk scoring."""

    def test_cross_modal_correlation_elevates_risk_score(self):
        """
        Thesis proof test:
        Submitting cross-modal evidence (Text + URL + Image describing the same scam):
        1. All three specialist agents run.
        2. Shared indicators across agents trigger corroboration_bonus.
        3. The combined final_risk_score is strictly higher than compute_risk()
           evaluated on any single agent's finding alone.
        4. Verifies database persistence of RiskBreakdown and ConflictLog rows.
        """
        phishing_url = "http://192.168.1.50/sbi-verify/login.php"
        image_bytes = _generate_phishing_image_bytes(
            "URGENT SBI SECURITY ALERT",
            "Your banking credentials require immediate password verification.",
        )

        create_resp = client.post(
            "/api/v1/investigations",
            data={
                "title": "Cross-Modal Correlation Test",
                "text": f"URGENT: Your SBI bank account credentials have expired. Verify your password now at {phishing_url}",
                "url": phishing_url,
            },
            files={
                "image": ("scam_flyer.png", io.BytesIO(image_bytes), "image/png"),
            },
        )
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investigation"]["id"]

        # Run Swarm Orchestration with Phase 11 Risk Engine
        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200
        analyze_data = analyze_resp.json()

        assert analyze_data["status"] == "completed"
        assert "risk" in analyze_data
        risk_result = analyze_data["risk"]
        assert risk_result is not None

        combined_final_risk = risk_result["final_risk"]
        findings = analyze_data["findings"]
        assert len(findings) >= 2, "Expected at least 2 specialist findings in cross-modal run"

        # Corroboration bonus must be strictly positive due to cross-modal indicator overlap
        assert risk_result["corroboration_bonus"] > 0.0, (
            f"Expected positive corroboration bonus, got {risk_result['corroboration_bonus']}"
        )

        # Core Thesis Assertion:
        # Combined final_risk_score must be GREATER than calling compute_risk on any single finding alone
        for f in findings:
            single_eval = compute_risk([f])
            assert combined_final_risk > single_eval["final_risk"], (
                f"Combined risk ({combined_final_risk}) was not higher than single agent "
                f"{f.get('agent')} risk ({single_eval['final_risk']})"
            )

        # Direct Database Verification:
        # Check that risk_breakdown and investigation columns were committed
        with SessionLocal() as db:
            inv_uuid = uuid.UUID(inv_id)
            inv_row = db.query(Investigation).filter(Investigation.id == inv_uuid).first()
            assert inv_row is not None
            assert inv_row.final_risk_score == combined_final_risk
            assert inv_row.final_severity is not None

            # Verify risk_breakdown rows in DB
            rb_rows = db.query(RiskBreakdown).filter(RiskBreakdown.investigation_id == inv_uuid).all()
            assert len(rb_rows) == 4
            component_names = {r.component for r in rb_rows}
            assert component_names == {"base_score", "corroboration_bonus", "intel_bonus", "contradiction_penalty"}

            # Verify conflict_logs queryable (can be 0 or more depending on heuristic severity match)
            conflict_rows = db.query(ConflictLog).filter(ConflictLog.investigation_id == inv_uuid).all()
            assert isinstance(conflict_rows, list)

        # GET /investigations/{id} API verification
        detail_resp = client.get(f"/api/v1/investigations/{inv_id}")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()

        assert "risk" in detail_data
        detail_risk = detail_data["risk"]
        assert detail_risk is not None
        assert detail_risk["score"] == combined_final_risk
        assert len(detail_risk["breakdown"]) == 4
