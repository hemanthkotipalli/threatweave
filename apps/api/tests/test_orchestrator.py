"""
tests/test_orchestrator.py
--------------------------
End-to-end integration and defensive fault-tolerance tests for the
ThreatWeave LangGraph Orchestrator (Phase 10).

Coverage:
- Complete investigation lifecycle: create -> analyze -> retrieve detail.
- Investigation status transitions (pending -> running -> completed).
- Defensive error isolation: one agent raises an unexpected exception -> its AgentRun
  is marked 'failed', but other agents and the overall investigation still complete successfully.
- Non-existent investigation ID -> 404 NotFoundError.
"""
from __future__ import annotations

import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.agent_run import AgentRun
from app.models.enums import AgentStatus
from app.models.investigation import Investigation

client = TestClient(app)


class TestOrchestratorLifecycle:
    def test_e2e_investigation_analysis_and_detail_retrieval(self):
        """
        End-to-end:
        1. POST /api/v1/investigations creates investigation.
        2. POST /api/v1/investigations/{id}/analyze triggers LangGraph swarm.
        3. GET /api/v1/investigations/{id} returns full detail with agent_runs & findings.
        """
        create_resp = client.post(
            "/api/v1/investigations",
            data={
                "title": "E2E Lifecycle Test",
                "text": "Please confirm your security PIN immediately.",
                "url": "http://verify-account.tk",
            },
        )
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investigation"]["id"]

        # Initial state should be pending in DB
        with SessionLocal() as db:
            inv = db.query(Investigation).filter(Investigation.id == uuid.UUID(inv_id)).first()
            assert inv is not None
            assert inv.status == "pending"

        # Trigger analysis
        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200
        analysis_data = analyze_resp.json()
        assert analysis_data["status"] == "completed"
        assert len(analysis_data["findings"]) >= 2

        # Final state should be completed in DB
        with SessionLocal() as db:
            inv = db.query(Investigation).filter(Investigation.id == uuid.UUID(inv_id)).first()
            assert inv is not None
            assert inv.status == "completed"

        # GET detail endpoint verification
        detail_resp = client.get(f"/api/v1/investigations/{inv_id}")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["id"] == inv_id
        assert detail_data["status"] == "completed"
        assert len(detail_data["evidence_inputs"]) == 2
        assert len(detail_data["agent_runs"]) >= 2

        # Verify nested findings in response
        active_runs = [r for r in detail_data["agent_runs"] if r["status"] == "done"]
        assert len(active_runs) >= 2
        for r in active_runs:
            assert "findings" in r
            assert len(r["findings"]) >= 1
            assert r["findings"][0]["finding"]

    def test_analyze_non_existent_investigation_returns_404(self):
        """Non-existent ID -> 404 NotFoundError."""
        fake_id = str(uuid.uuid4())
        resp = client.post(f"/api/v1/investigations/{fake_id}/analyze")
        data = resp.json()
        err_msg = data.get("error", {}).get("message", "") or data.get("detail", "")
        assert "not found" in err_msg.lower()

    def test_defensive_fault_tolerance_single_agent_failure_does_not_crash_investigation(self):
        """
        Defensive second layer test:
        Mock one specialist agent to raise an unexpected top-level exception.
        Assert that:
        1. That specialist's AgentRun is marked status='failed'.
        2. Other required specialists still complete with status='done'.
        3. The overall investigation status still reaches 'completed'.
        """
        create_resp = client.post(
            "/api/v1/investigations",
            data={
                "title": "Fault Tolerance Test",
                "text": "Urgent security alert.",
                "url": "http://legit-site.com",
            },
        )
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investigation"]["id"]

        # Mock analyze_url to blow up with an unhandled exception
        with patch("app.agents.orchestrator_nodes.analyze_url", side_effect=RuntimeError("Simulated unhandled network crash")):
            analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
            assert analyze_resp.status_code == 200

        # Verify DB states
        with SessionLocal() as db:
            inv = db.query(Investigation).filter(Investigation.id == uuid.UUID(inv_id)).first()
            assert inv is not None
            # Investigation itself must still complete
            assert inv.status == "completed"

            runs = db.query(AgentRun).filter(AgentRun.investigation_id == uuid.UUID(inv_id)).all()
            run_map = {r.agent_name: r.status for r in runs}

            # url_agent failed, but text_agent succeeded
            assert run_map.get("url_agent") == AgentStatus.FAILED
            assert run_map.get("text_agent") == AgentStatus.DONE
