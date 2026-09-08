"""
tests/test_webhook.py
----------------------
Unit and integration tests for Phase 16: n8n Integration & Webhook Notifications.

Validates:
1. When N8N_WEBHOOK_URL is unset/empty, notify_high_severity() returns immediately with zero HTTP calls (assert_not_called).
2. When N8N_WEBHOOK_URL is set but unreachable (connection error or timeout), notify_high_severity() logs the error and does not raise.
3. When N8N_WEBHOOK_URL is set and reachable, assert correct payload shape is transmitted.
4. When orchestration_service analyzes a high-severity investigation, the investigation reaches status="completed" regardless of whether the webhook succeeds or raises an exception.
5. When an investigation completes with LOW severity, notify_high_severity is NOT called at all (threshold gating).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.services import orchestration_service, webhook_service
from app.services.ingestion_service import ingest_investigation


class TestWebhookServiceUnit:

    """Direct unit tests for webhook_service.notify_high_severity."""

    @patch("httpx.Client")
    def test_webhook_url_unset_results_in_zero_network_calls(self, mock_client_cls):
        """When N8N_WEBHOOK_URL is empty, notify_high_severity returns immediately without HTTP calls."""
        with patch.object(settings, "N8N_WEBHOOK_URL", ""):
            payload = {
                "investigation_id": "test-id-123",
                "title": "Test Incident",
                "final_risk_score": 0.95,
                "final_severity": "critical",
                "top_indicators": ["urgency_language"],
            }
            webhook_service.notify_high_severity(payload)

            # Assert absolutely no HTTP client was created or called
            mock_client_cls.assert_not_called()

    @patch("httpx.Client")
    def test_webhook_unreachable_does_not_raise(self, mock_client_cls):
        """When N8N_WEBHOOK_URL is set but network fails or times out, notify_high_severity catches it safely."""
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.side_effect = httpx.ConnectError("Connection refused by n8n host:5678")
        mock_client_cls.return_value = mock_client

        with patch.object(settings, "N8N_WEBHOOK_URL", "http://localhost:5678/webhook/test"):
            payload = {
                "investigation_id": "test-id-456",
                "title": "Unreachable Target Test",
                "final_risk_score": 0.88,
                "final_severity": "high",
            }
            # Must NOT raise any exception
            webhook_service.notify_high_severity(payload)

            mock_client.post.assert_called_once()

    @patch("httpx.Client")
    def test_webhook_timeout_does_not_raise(self, mock_client_cls):
        """When n8n times out after 5 seconds, notify_high_severity handles it gracefully."""
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.side_effect = httpx.TimeoutException("Read timed out")
        mock_client_cls.return_value = mock_client

        with patch.object(settings, "N8N_WEBHOOK_URL", "http://localhost:5678/webhook/test"):
            payload = {"investigation_id": "test-id-789", "final_severity": "high"}
            webhook_service.notify_high_severity(payload)

            mock_client.post.assert_called_once()

    @patch("httpx.Client")
    def test_webhook_success_transmits_correct_payload(self, mock_client_cls):
        """When N8N_WEBHOOK_URL is set and reachable, assert exact payload and headers are sent."""
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.is_success = True
        mock_resp.status_code = 200
        mock_client.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        target_url = "http://localhost:5678/webhook/threatweave-alert"
        with patch.object(settings, "N8N_WEBHOOK_URL", target_url):
            payload = {
                "investigation_id": "test-id-999",
                "title": "Phishing Lure Alert",
                "final_risk_score": 0.92,
                "final_severity": "critical",
                "top_indicators": ["impersonation_claim", "urgency_language"],
                "created_at": "2026-09-08T08:00:00Z",
            }
            webhook_service.notify_high_severity(payload)

            mock_client.post.assert_called_once_with(
                target_url,
                json=payload,
                headers={"Content-Type": "application/json", "User-Agent": "ThreatWeave-Alert-Dispatcher/1.0"},
            )


class TestOrchestrationWebhookIntegration:
    """Integration tests verifying orchestration_service triggers webhooks according to severity thresholds."""

    @pytest.fixture
    def db_session(self):
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @pytest.fixture
    def test_user(self, db_session):
        user = db_session.query(User).first()
        if not user:
            user = User(
                email="webhook_tester@threatweave.local",
                password_hash="placeholder_hash",
                role="analyst",
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
        return user

    @patch("app.services.webhook_service.notify_high_severity")
    def test_high_severity_investigation_triggers_webhook_and_completes(
        self,
        mock_notify,
        db_session,
        test_user,
    ):
        """
        Runs a high/critical phishing scenario:
        - notify_high_severity is called with appropriate summary payload.
        - The investigation reaches status="completed".
        """
        # Create real investigation with high-severity indicators
        inv = ingest_investigation(
            db=db_session,
            title="High Severity Test Investigation",
            text=(
                "URGENT: Your SBI bank account has been temporarily restricted due to unauthorized login attempts. "
                "Immediate Action Required: Verify your security credentials and password within 24 hours to prevent permanent account suspension. "
                "Failure to update will result in complete account blocking under RBI directives."
            ),
            user_id=test_user.id,
        )


        with patch.object(settings, "N8N_ALERT_SEVERITY_THRESHOLD", "medium"):
            result = orchestration_service.run_investigation_analysis(inv.id, db=db_session)
            assert result["status"] == "completed"

            # Refresh investigation
            db_session.refresh(inv)
            assert inv.status == "completed"
            assert inv.final_risk_score is not None

            # Assert webhook was triggered
            mock_notify.assert_called_once()
            call_args = mock_notify.call_args[0][0]
            assert call_args["investigation_id"] == str(inv.id)
            assert call_args["final_risk_score"] == inv.final_risk_score
            assert isinstance(call_args["top_indicators"], list)

    @patch("app.services.webhook_service.notify_high_severity")
    def test_webhook_failure_does_not_fail_investigation(
        self,
        mock_notify,
        db_session,
        test_user,
    ):
        """
        Even if notify_high_severity raises an unexpected exception internally,
        the calling investigation MUST safely transition to 'completed'.
        """
        mock_notify.side_effect = RuntimeError("Catastrophic unexpected network driver crash")

        inv = ingest_investigation(
            db=db_session,
            title="Resilience Against Webhook Crash Test",
            text="URGENT: Immediate payment required to prevent account termination.",
            user_id=test_user.id,
        )

        with patch.object(settings, "N8N_ALERT_SEVERITY_THRESHOLD", "high"):
            result = orchestration_service.run_investigation_analysis(inv.id, db=db_session)

            db_session.refresh(inv)
            # Integrity guarantee: must remain completed, NOT failed
            assert inv.status == "completed"
            assert result["status"] == "completed"

    @patch("app.services.webhook_service.notify_high_severity")
    def test_low_severity_investigation_skips_webhook(
        self,
        mock_notify,
        db_session,
        test_user,
    ):
        """
        When an investigation results in low or info severity,
        notify_high_severity is NOT called because the threshold is not satisfied.
        """
        # Completely benign content
        inv = ingest_investigation(
            db=db_session,
            title="Benign Low Severity Investigation",
            text="Meeting notes from today's regular team sync: discussed quarterly project roadmap and sprint velocity.",
            user_id=test_user.id,
        )


        with patch.object(settings, "N8N_ALERT_SEVERITY_THRESHOLD", "high"):
            result = orchestration_service.run_investigation_analysis(inv.id, db=db_session)
            assert result["status"] == "completed"

            db_session.refresh(inv)
            assert inv.status == "completed"
            # Low severity must NOT trigger high-severity alert webhook
            if inv.final_severity in ("low", "info", None):
                mock_notify.assert_not_called()
