"""
tests/test_demo.py
------------------
Comprehensive tests for Phase 15: Demo Mode.
Validates:
- GET /api/v1/demo/scenarios returns exactly 6 scenarios with required keys.
- Running each of the 6 scenarios produces a completed investigation with a valid risk score.
- Numerical thesis proof: cross_modal combined final_risk_score is strictly higher
  than each of its individual-modality runs run separately (text_only, url_only, image_only).
- Scenarios complete cleanly even with GROQ_API_KEY unset (proving graceful heuristic fallback).
- Non-existent scenario key returns 404.
"""
from __future__ import annotations

import os
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.investigation import Investigation

client = TestClient(app, raise_server_exceptions=False)


class TestDemoScenarios:
    def test_list_demo_scenarios(self):
        """Asserts that GET /api/v1/demo/scenarios returns the 6 expected curated scenarios."""
        resp = client.get("/api/v1/demo/scenarios")
        assert resp.status_code == 200
        scenarios = resp.json()

        assert isinstance(scenarios, list)
        assert len(scenarios) == 6

        scenario_keys = {s["key"] for s in scenarios}
        expected_keys = {
            "phishing_email",
            "malicious_url",
            "fake_payment_qr",
            "fraudulent_screenshot",
            "scam_voice",
            "cross_modal",
        }
        assert scenario_keys == expected_keys

        for s in scenarios:
            assert s.get("title")
            assert s.get("description")
            assert s.get("modalities") and len(s["modalities"]) >= 1

    def test_run_single_modality_scenarios(self):
        """
        Runs each of the 5 single/focused modality scenarios through the live pipeline,
        asserting status='completed' and non-null final_risk_score.
        """
        scenarios_to_test = [
            "phishing_email",
            "malicious_url",
            "fake_payment_qr",
            "fraudulent_screenshot",
            "scam_voice",
        ]
        created_inv_ids = []

        try:
            for key in scenarios_to_test:
                resp = client.post(f"/api/v1/demo/scenarios/{key}/run")
                assert resp.status_code == 200, f"Scenario '{key}' failed with: {resp.text}"

                data = resp.json()
                assert "investigation_id" in data
                assert data["status"] == "completed"
                assert data["final_risk_score"] is not None
                assert 0.0 <= data["final_risk_score"] <= 1.0
                assert data["final_severity"] in ("info", "low", "medium", "high", "critical")

                created_inv_ids.append(data["investigation_id"])

        finally:
            with SessionLocal() as db:
                for inv_id in created_inv_ids:
                    db.query(Investigation).filter(Investigation.id == uuid.UUID(inv_id)).delete()
                db.commit()

    def test_cross_modal_combined_higher_than_individual_modalities(self):
        """
        Core Thesis Proof for Phase 15:
        Asserts that the cross_modal scenario's COMBINED run produces a final_risk_score
        strictly higher than each of its individual-modality runs (text_only, url_only, image_only).
        """
        created_inv_ids = []

        try:
            # 1. Run text_only
            resp_text = client.post("/api/v1/demo/scenarios/cross_modal/run?mode=text_only")
            assert resp_text.status_code == 200
            data_text = resp_text.json()
            score_text = data_text["final_risk_score"]
            created_inv_ids.append(data_text["investigation_id"])

            # 2. Run url_only
            resp_url = client.post("/api/v1/demo/scenarios/cross_modal/run?mode=url_only")
            assert resp_url.status_code == 200
            data_url = resp_url.json()
            score_url = data_url["final_risk_score"]
            created_inv_ids.append(data_url["investigation_id"])

            # 3. Run image_only
            resp_img = client.post("/api/v1/demo/scenarios/cross_modal/run?mode=image_only")
            assert resp_img.status_code == 200
            data_img = resp_img.json()
            score_img = data_img["final_risk_score"]
            created_inv_ids.append(data_img["investigation_id"])

            # 4. Run combined (all 3 modalities)
            resp_combined = client.post("/api/v1/demo/scenarios/cross_modal/run?mode=combined")
            assert resp_combined.status_code == 200
            data_combined = resp_combined.json()
            score_combined = data_combined["final_risk_score"]
            created_inv_ids.append(data_combined["investigation_id"])

            assert score_combined is not None
            assert score_text is not None
            assert score_url is not None
            assert score_img is not None

            # Numeric thesis verification
            assert score_combined > score_text, (
                f"Combined score ({score_combined}) must be strictly higher than text_only ({score_text})"
            )
            assert score_combined > score_url, (
                f"Combined score ({score_combined}) must be strictly higher than url_only ({score_url})"
            )
            assert score_combined > score_img, (
                f"Combined score ({score_combined}) must be strictly higher than image_only ({score_img})"
            )

            # Assert positive corroboration bonus in combined run
            assert data_combined.get("risk", {}).get("corroboration_bonus", 0.0) > 0.0, (
                "Combined run must produce a positive corroboration bonus"
            )

        finally:
            with SessionLocal() as db:
                for inv_id in created_inv_ids:
                    db.query(Investigation).filter(Investigation.id == uuid.UUID(inv_id)).delete()
                db.commit()

    def test_demo_execution_with_groq_api_key_unset(self):
        """
        Asserts that demo execution does not fail or crash if GROQ_API_KEY is not set.
        The system must gracefully use heuristic fallbacks.
        """
        with patch.dict(os.environ, {}, clear=True):
            resp = client.post("/api/v1/demo/scenarios/phishing_email/run")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "completed"
            assert data["final_risk_score"] is not None

            with SessionLocal() as db:
                db.query(Investigation).filter(Investigation.id == uuid.UUID(data["investigation_id"])).delete()
                db.commit()

    def test_run_unknown_scenario_returns_404(self):
        """Asserts that requesting a non-existent scenario returns 404."""
        resp = client.post("/api/v1/demo/scenarios/nonexistent_scenario_key/run")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data or "detail" in data
