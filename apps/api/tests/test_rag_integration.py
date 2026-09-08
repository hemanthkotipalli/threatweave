"""
tests/test_rag_integration.py
-----------------------------
End-to-end integration test for Phase 12: RAG Pipeline + ChromaDB.
Validates that:
1. Running an investigation through LangGraph retrieves matching threat advisories from ChromaDB.
2. RagCitation records are persisted to PostgreSQL.
3. The intel_bonus (+0.15) is visibly applied to the final_risk_score and formula breakdown.
4. GET /api/v1/investigations/{id} returns the populated rag_citations array.
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.investigation import Investigation
from app.models.rag_citation import RagCitation
from app.models.risk_breakdown import RiskBreakdown

client = TestClient(app)


class TestRagPipelineIntegration:
    def test_e2e_investigation_triggers_rag_retrieval_and_intel_bonus(self):
        """
        Submitting an investigation with realistic phishing / credential harvesting evidence:
        1. Specialist agents run and emit indicators.
        2. rag_node queries ChromaDB with indicators and finding text.
        3. Relevant advisory citations (CERT-In / RBI) clear the 0.55 similarity threshold.
        4. RagCitation rows are committed to Postgres.
        5. risk_engine_node adds +0.15 intel_bonus to the final risk score.
        6. GET /api/v1/investigations/{id} returns the citations and updated score.
        """
        phishing_url = "http://192.168.1.100/sbi-verify/login.php"
        text_content = (
            f"URGENT: Your SBI bank account credentials have expired. "
            f"Immediate action required to avoid account deactivation. Verify password at {phishing_url}"
        )

        create_resp = client.post(
            "/api/v1/investigations",
            data={
                "title": "Phase 12 E2E RAG Phishing Test",
                "text": text_content,
                "url": phishing_url,
            },
        )
        assert create_resp.status_code == 201
        inv_id = create_resp.json()["investigation"]["id"]
        inv_uuid = uuid.UUID(inv_id)

        # Trigger Swarm Orchestration with RAG Pipeline
        analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert analyze_resp.status_code == 200
        analyze_data = analyze_resp.json()

        assert analyze_data["status"] == "completed"
        assert "rag_citations" in analyze_data
        citations = analyze_data["rag_citations"]

        # 1. Verify RAG retrieval populated citations clearing threshold
        assert len(citations) >= 1, f"Expected at least 1 RAG citation, got {len(citations)}"
        for c in citations:
            assert c["similarity_score"] >= settings.RAG_SIMILARITY_THRESHOLD
            assert c["source_type"] in ["CERT-In", "RBI", "Scam-Intel"]
            assert c["source_title"]

        # 2. Verify intel_bonus is active in risk breakdown
        risk_obj = analyze_data["risk"]
        assert risk_obj is not None
        assert risk_obj["intel_bonus"] == 0.15

        intel_breakdown = next(
            (b for b in risk_obj["breakdown"] if b["component"] == "intel_bonus"), None
        )
        assert intel_breakdown is not None
        assert intel_breakdown["value"] == 0.15
        assert intel_breakdown["contribution"] == 0.15

        # 3. Verify PostgreSQL persistence of RagCitation rows
        with SessionLocal() as db:
            db_citations = db.query(RagCitation).filter(RagCitation.investigation_id == inv_uuid).all()
            assert len(db_citations) >= 1
            for db_c in db_citations:
                st_val = db_c.source_type.value if hasattr(db_c.source_type, "value") else str(db_c.source_type)
                assert st_val in ["CERT-In", "RBI", "Scam-Intel"]
                assert db_c.chunk_text

            # Verify risk_breakdown rows in DB
            rb_intel = (
                db.query(RiskBreakdown)
                .filter(RiskBreakdown.investigation_id == inv_uuid, RiskBreakdown.component == "intel_bonus")
                .first()
            )
            assert rb_intel is not None
            assert rb_intel.value == 0.15
            assert rb_intel.contribution == 0.15

            # Verify Investigation record updated
            inv_row = db.query(Investigation).filter(Investigation.id == inv_uuid).first()
            assert inv_row is not None
            assert inv_row.final_risk_score == risk_obj["final_risk"]

        # 4. Verify GET /api/v1/investigations/{id} response
        detail_resp = client.get(f"/api/v1/investigations/{inv_id}")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()

        assert "rag_citations" in detail_data
        assert len(detail_data["rag_citations"]) == len(citations)
        assert detail_data["risk"]["score"] == risk_obj["final_risk"]
