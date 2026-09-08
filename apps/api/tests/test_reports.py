"""
tests/test_reports.py
---------------------
Tests for Phase 14: Investigation History Filtering and Report Generation.
Verifies:
- Filtering by severity returns only matching investigations.
- Filtering by status returns only matching investigations.
- Graceful handling of investigations with final_severity=None when severity filter is applied.
- Date range filtering (date_from, date_to).
- Complete report payload assembly with all required sections (metadata, evidence, findings, risk, rag, conflicts).
- Insertion of InvestigationReport audit log row.
- Standard 404 error envelope on report request for non-existent investigation ID.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.agent_finding import AgentFinding
from app.models.agent_run import AgentRun
from app.models.conflict_log import ConflictLog
from app.models.enums import AgentStatus, FindingStatus, Severity
from app.models.evidence_input import EvidenceInput
from app.models.investigation import Investigation
from app.models.investigation_report import InvestigationReport
from app.models.rag_citation import RagCitation
from app.models.risk_breakdown import RiskBreakdown
from app.models.user import User

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def test_user_id() -> uuid.UUID:
    """Provides a valid user ID for test investigations."""
    with SessionLocal() as db:
        user = db.query(User).first()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email="phase14_test_analyst@threatweave.local",
                password_hash="test_hash_phase14",
                role="analyst",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user.id


class TestInvestigationFiltering:
    def test_filter_by_severity_and_null_handling(self, test_user_id: uuid.UUID):
        """
        Asserts that filtering by severity matches only the requested severity,
        and unanalyzed investigations (final_severity=None) do not trigger errors
        and are gracefully excluded.
        """
        with SessionLocal() as db:
            # 1. Create a high severity investigation
            inv_high = Investigation(
                id=uuid.uuid4(),
                user_id=test_user_id,
                title="Phase 14 High Severity Test",
                status="completed",
                final_risk_score=0.78,
                final_severity=Severity.HIGH,
                created_at=datetime.now(timezone.utc),
            )
            # 2. Create a critical severity investigation
            inv_crit = Investigation(
                id=uuid.uuid4(),
                user_id=test_user_id,
                title="Phase 14 Critical Severity Test",
                status="completed",
                final_risk_score=0.95,
                final_severity=Severity.CRITICAL,
                created_at=datetime.now(timezone.utc),
            )
            # 3. Create an unanalyzed investigation with final_severity=None
            inv_none = Investigation(
                id=uuid.uuid4(),
                user_id=test_user_id,
                title="Phase 14 Pending Severity Test",
                status="pending",
                final_risk_score=None,
                final_severity=None,
                created_at=datetime.now(timezone.utc),
            )
            db.add_all([inv_high, inv_crit, inv_none])
            db.commit()

            high_id = str(inv_high.id)
            crit_id = str(inv_crit.id)
            none_id = str(inv_none.id)

        try:
            # Query severity=high
            resp_high = client.get("/api/v1/investigations?severity=high")
            assert resp_high.status_code == 200
            data_high = resp_high.json()
            returned_ids_high = [item["id"] for item in data_high["items"]]

            assert high_id in returned_ids_high
            assert crit_id not in returned_ids_high
            assert none_id not in returned_ids_high
            # Verify all items in result have high severity
            for item in data_high["items"]:
                assert item["final_severity"] == "high"

            # Query severity=critical
            resp_crit = client.get("/api/v1/investigations?severity=critical")
            assert resp_crit.status_code == 200
            data_crit = resp_crit.json()
            returned_ids_crit = [item["id"] for item in data_crit["items"]]

            assert crit_id in returned_ids_crit
            assert high_id not in returned_ids_crit
            assert none_id not in returned_ids_crit

            # Query with an unknown / non-matching severity value
            resp_unknown = client.get("/api/v1/investigations?severity=nonexistent_severity")
            assert resp_unknown.status_code == 200
            assert resp_unknown.json()["total"] == 0
            assert len(resp_unknown.json()["items"]) == 0

        finally:
            with SessionLocal() as db:
                db.query(Investigation).filter(
                    Investigation.id.in_([uuid.UUID(high_id), uuid.UUID(crit_id), uuid.UUID(none_id)])
                ).delete(synchronize_session=False)
                db.commit()

    def test_filter_by_status(self, test_user_id: uuid.UUID):
        """
        Asserts that filtering by status returns only matching investigations.
        """
        with SessionLocal() as db:
            inv_pending = Investigation(
                id=uuid.uuid4(),
                user_id=test_user_id,
                title="Phase 14 Pending Status Filter",
                status="pending",
                created_at=datetime.now(timezone.utc),
            )
            inv_failed = Investigation(
                id=uuid.uuid4(),
                user_id=test_user_id,
                title="Phase 14 Failed Status Filter",
                status="failed",
                created_at=datetime.now(timezone.utc),
            )
            db.add_all([inv_pending, inv_failed])
            db.commit()

            pending_id = str(inv_pending.id)
            failed_id = str(inv_failed.id)

        try:
            resp_pending = client.get("/api/v1/investigations?status=pending")
            assert resp_pending.status_code == 200
            items_pending = resp_pending.json()["items"]
            pending_ids = [i["id"] for i in items_pending]

            assert pending_id in pending_ids
            assert failed_id not in pending_ids
            for i in items_pending:
                assert i["status"] == "pending"

            resp_failed = client.get("/api/v1/investigations?status=failed")
            assert resp_failed.status_code == 200
            items_failed = resp_failed.json()["items"]
            failed_ids = [i["id"] for i in items_failed]

            assert failed_id in failed_ids
            assert pending_id not in failed_ids
            for i in items_failed:
                assert i["status"] == "failed"

        finally:
            with SessionLocal() as db:
                db.query(Investigation).filter(
                    Investigation.id.in_([uuid.UUID(pending_id), uuid.UUID(failed_id)])
                ).delete(synchronize_session=False)
                db.commit()

    def test_filter_by_date_range(self, test_user_id: uuid.UUID):
        """
        Asserts that filtering by date_from and date_to restricts results to the timeframe.
        """
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        with SessionLocal() as db:
            inv_old = Investigation(
                id=uuid.uuid4(),
                user_id=test_user_id,
                title="Phase 14 Old Date Filter",
                status="completed",
                created_at=two_days_ago,
            )
            inv_recent = Investigation(
                id=uuid.uuid4(),
                user_id=test_user_id,
                title="Phase 14 Recent Date Filter",
                status="completed",
                created_at=now,
            )
            db.add_all([inv_old, inv_recent])
            db.commit()

            old_id = str(inv_old.id)
            recent_id = str(inv_recent.id)

        try:
            # Query date_from = yesterday (should only include inv_recent)
            from_iso = yesterday.isoformat()
            resp = client.get(f"/api/v1/investigations?date_from={from_iso}")
            assert resp.status_code == 200
            returned_ids = [item["id"] for item in resp.json()["items"]]

            assert recent_id in returned_ids
            assert old_id not in returned_ids

        finally:
            with SessionLocal() as db:
                db.query(Investigation).filter(
                    Investigation.id.in_([uuid.UUID(old_id), uuid.UUID(recent_id)])
                ).delete(synchronize_session=False)
                db.commit()


class TestReportGeneration:
    def test_generate_report_payload_and_audit_row(self, test_user_id: uuid.UUID):
        """
        Asserts that GET /api/v1/investigations/{id}/report returns all required
        report sections (metadata, evidence, agent findings, risk breakdown, rag citations, conflict logs)
        and inserts an InvestigationReport audit row.
        """
        inv_id = uuid.uuid4()
        run_id = uuid.uuid4()

        with SessionLocal() as db:
            # 1. Investigation
            inv = Investigation(
                id=inv_id,
                user_id=test_user_id,
                title="Phase 14 Comprehensive Report Audit Test",
                status="completed",
                final_risk_score=0.88,
                final_severity=Severity.HIGH,
                final_confidence=0.85,
                created_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            # 2. Evidence input
            evidence = EvidenceInput(
                id=uuid.uuid4(),
                investigation_id=inv_id,
                modality="text",
                raw_content_ref="Urgent notice: Update KYC at bit.ly/bank-fraud",
            )
            # 3. Agent run & finding
            agent_run = AgentRun(
                id=run_id,
                investigation_id=inv_id,
                agent_name="text_agent",
                status=AgentStatus.DONE,
                latency_ms=142,
            )
            finding = AgentFinding(
                id=uuid.uuid4(),
                agent_run_id=run_id,
                finding="High urgency credential phishing detected.",
                confidence=0.92,
                severity=Severity.HIGH,
                indicators=["urgency", "kyc_update", "suspicious_shortlink"],
                evidence={"matched_pattern": "Update KYC"},
                reasoning="Classic banking social engineering vector.",
                external_refs=[],
                status=FindingStatus.OK,
            )
            # 4. Risk breakdown
            rb1 = RiskBreakdown(
                id=uuid.uuid4(),
                investigation_id=inv_id,
                component="base_score",
                value=0.73,
                weight=0.5,
                contribution=0.365,
            )
            rb2 = RiskBreakdown(
                id=uuid.uuid4(),
                investigation_id=inv_id,
                component="corroboration_bonus",
                value=0.25,
                weight=1.0,
                contribution=0.25,
            )
            # 5. RAG Citation
            citation = RagCitation(
                id=uuid.uuid4(),
                investigation_id=inv_id,
                source_title="RBI Advisory on KYC Phishing",
                source_type="RBI",
                chunk_text="Never click on links asking to update KYC documents via SMS.",
                similarity_score=0.77,
                url="https://rbi.org.in/advisory/kyc",
            )
            # 6. Conflict log
            conflict = ConflictLog(
                id=uuid.uuid4(),
                investigation_id=inv_id,
                agent_a="text_agent",
                agent_b="url_agent",
                conflict_type="severity_discrepancy",
                resolution_rule="conservative_high",
                resolution_outcome="Adopted text_agent higher severity rating",
            )

            db.add_all([inv, evidence, agent_run, finding, rb1, rb2, citation, conflict])
            db.commit()

        try:
            # Request report
            resp = client.get(f"/api/v1/investigations/{inv_id}/report")
            assert resp.status_code == 200
            report = resp.json()

            # Verify top-level audit attributes
            assert "report_id" in report
            assert report["format"] == "html"
            assert "generated_at" in report

            # Verify investigation metadata
            inv_meta = report["investigation"]
            assert inv_meta["id"] == str(inv_id)
            assert inv_meta["title"] == "Phase 14 Comprehensive Report Audit Test"
            assert inv_meta["status"] == "completed"
            assert inv_meta["final_severity"] == "high"
            assert inv_meta["final_risk_score"] == 0.88

            # Verify evidence inputs
            assert len(report["evidence_inputs"]) == 1
            assert report["evidence_inputs"][0]["modality"] == "text"

            # Verify agent runs and findings
            assert len(report["agent_runs"]) == 1
            assert report["agent_runs"][0]["agent_name"] == "text_agent"
            assert len(report["findings"]) == 1
            assert "High urgency credential phishing" in report["findings"][0]["finding"]

            # Verify risk breakdown
            assert report["risk"] is not None
            assert report["risk"]["score"] == 0.88
            assert len(report["risk"]["breakdown"]) == 2
            components = [b["component"] for b in report["risk"]["breakdown"]]
            assert "base_score" in components
            assert "corroboration_bonus" in components

            # Verify RAG citations
            assert len(report["rag_citations"]) == 1
            assert report["rag_citations"][0]["source_title"] == "RBI Advisory on KYC Phishing"

            # Verify conflict logs
            assert len(report["conflict_logs"]) == 1
            assert report["conflict_logs"][0]["conflict_type"] == "severity_discrepancy"

            # Verify that an InvestigationReport audit row was written to DB
            with SessionLocal() as db:
                audit_records = (
                    db.query(InvestigationReport)
                    .filter(InvestigationReport.investigation_id == inv_id)
                    .all()
                )
                assert len(audit_records) >= 1
                matched_record = next(
                    (r for r in audit_records if str(r.id) == report["report_id"]), None
                )
                assert matched_record is not None
                assert matched_record.format == "html"
                assert matched_record.file_path == "on-demand:audit"

        finally:
            with SessionLocal() as db:
                # Cascade deletes associated runs, findings, citations, reports
                db.query(Investigation).filter(Investigation.id == inv_id).delete()
                db.commit()

    def test_nonexistent_investigation_report_returns_404(self):
        """
        Asserts that requesting a report for a non-existent UUID returns 404
        with the standard error envelope.
        """
        missing_id = uuid.uuid4()
        resp = client.get(f"/api/v1/investigations/{missing_id}/report")
        assert resp.status_code == 404

        data = resp.json()
        assert "error" in data or "detail" in data
        err_msg = data.get("error", {}).get("message", "") or data.get("detail", "")
        assert str(missing_id) in err_msg or "not found" in err_msg.lower()
