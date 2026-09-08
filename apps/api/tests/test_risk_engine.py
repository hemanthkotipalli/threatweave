"""
tests/test_risk_engine.py
-------------------------
Unit tests for the pure deterministic risk scoring engine (Phase 11).
Tests compute_risk() directly without graph or database dependencies.
"""
from __future__ import annotations

import json

from app.agents.risk_engine import compute_risk


class TestRiskEngineDirect:
    """Direct mathematical unit tests for compute_risk()."""

    def test_single_critical_finding_hand_calculated(self):
        """
        Single finding: severity='critical', confidence=0.9.
        Hand calculation:
            severity_weight = 1.0
            per_finding_score = 1.0 * 0.9 = 0.90
            base_score = 0.90
            corroboration_bonus = 0.0
            intel_bonus = 0.0
            contradiction_penalty = 0.0
            final_risk = 0.90
            severity = 'critical' (0.80 - 1.00)
            low_confidence = True (< 2 findings included)
        """
        findings = [
            {
                "agent": "text_agent",
                "modality": "text",
                "finding": "Phishing lure detected.",
                "confidence": 0.9,
                "severity": "critical",
                "indicators": ["credential_request"],
                "status": "ok",
            }
        ]

        result = compute_risk(findings)

        assert result["final_risk"] == 0.90
        assert result["severity"] == "critical"
        assert result["confidence"] == 0.90
        assert result["low_confidence"] is True
        assert result["base_score"] == 0.90
        assert result["corroboration_bonus"] == 0.0
        assert result["intel_bonus"] == 0.0
        assert result["contradiction_penalty"] == 0.0

        # Check breakdown components
        breakdown_map = {item["component"]: item for item in result["breakdown"]}
        assert breakdown_map["base_score"]["contribution"] == 0.90
        assert breakdown_map["corroboration_bonus"]["contribution"] == 0.0
        assert breakdown_map["intel_bonus"]["contribution"] == 0.0
        assert breakdown_map["contradiction_penalty"]["contribution"] == 0.0

    def test_corroboration_bonus_applied_two_agents(self):
        """
        Two findings from DIFFERENT agents sharing an indicator -> corroboration_bonus = 0.10.
        Finding A: text_agent, severity='medium' (0.5), conf=0.8 -> score = 0.4
        Finding B: url_agent, severity='medium' (0.5), conf=0.8 -> score = 0.4
        base_score = 0.40
        corroboration_bonus = 0.10 (2 agents share 'credential_request')
        final_risk = 0.40 + 0.10 = 0.50
        severity = 'medium' (0.40 - 0.59)
        low_confidence = False
        """
        findings = [
            {
                "agent": "text_agent",
                "modality": "text",
                "severity": "medium",
                "confidence": 0.8,
                "indicators": ["credential_request"],
                "status": "ok",
            },
            {
                "agent": "url_agent",
                "modality": "url",
                "severity": "medium",
                "confidence": 0.8,
                "indicators": ["credential_request"],
                "status": "ok",
            },
        ]

        result = compute_risk(findings)

        assert result["base_score"] == 0.40
        assert result["corroboration_bonus"] == 0.10
        assert result["final_risk"] == 0.50
        assert result["severity"] == "medium"
        assert result["low_confidence"] is False
        assert len(result["corroborations"]) == 1
        assert result["corroborations"][0]["indicator"] == "credential_request"
        assert result["corroborations"][0]["agents"] == ["text_agent", "url_agent"]

    def test_corroboration_bonus_caps_at_0_25(self):
        """
        Four findings from four distinct agents all sharing an indicator:
        Raw bonus = 0.10 * (4 - 1) = 0.30 -> capped at +0.25.
        """
        findings = [
            {"agent": "text_agent", "severity": "medium", "confidence": 0.6, "indicators": ["credential_request"], "status": "ok"},
            {"agent": "url_agent", "severity": "medium", "confidence": 0.6, "indicators": ["credential_request"], "status": "ok"},
            {"agent": "qr_agent", "severity": "medium", "confidence": 0.6, "indicators": ["credential_request"], "status": "ok"},
            {"agent": "image_agent", "severity": "medium", "confidence": 0.6, "indicators": ["credential_request"], "status": "ok"},
        ]

        result = compute_risk(findings)

        # 0.30 raw bonus must be capped at 0.25
        assert result["corroboration_bonus"] == 0.25

    def test_direct_conflict_contradiction_penalty_applied(self):
        """
        Two findings in direct conflict on related indicator:
        Finding A: text_agent, severity='critical' (1.0), conf=0.8 -> score = 0.8
        Finding B: url_agent, severity='info' (0.0), conf=0.8 -> score = 0.0
        Shared category: credential_request and impersonation_claim both in 'social_engineering'.
        base_score = (0.8 + 0.0) / 2 = 0.40
        contradiction_penalty = 0.10
        final_risk = 0.40 - 0.10 = 0.30
        severity = 'low' (0.20 - 0.39)
        """
        findings = [
            {
                "agent": "text_agent",
                "severity": "critical",
                "confidence": 0.8,
                "indicators": ["credential_request"],
                "status": "ok",
            },
            {
                "agent": "url_agent",
                "severity": "info",
                "confidence": 0.8,
                "indicators": ["impersonation_claim"],
                "status": "ok",
            },
        ]

        result = compute_risk(findings)

        assert len(result["conflicts"]) == 1
        assert result["contradiction_penalty"] == 0.10
        assert result["base_score"] == 0.40
        assert result["final_risk"] == 0.30
        assert result["severity"] == "low"

    def test_contradiction_penalty_caps_at_0_30(self):
        """
        Multiple conflicts (4+ detected) -> contradiction_penalty caps at 0.30, not 0.40.
        """
        findings = [
            {"agent": "text_agent", "severity": "critical", "confidence": 0.9, "indicators": ["urgency_language"], "status": "ok"},
            {"agent": "voice_agent", "severity": "critical", "confidence": 0.9, "indicators": ["vishing_script_pattern"], "status": "ok"},
            {"agent": "image_agent", "severity": "info", "confidence": 0.9, "indicators": ["impersonation_banner"], "status": "ok"},
            {"agent": "url_agent", "severity": "low", "confidence": 0.9, "indicators": ["credential_request"], "status": "ok"},
        ]
        # (text vs image), (text vs url), (voice vs image), (voice vs url) -> 4 conflicts in social_engineering
        result = compute_risk(findings)

        assert len(result["conflicts"]) >= 4
        assert result["contradiction_penalty"] == 0.30

    def test_low_confidence_flagged_when_fewer_than_two_findings(self):
        """Only 1 finding included -> low_confidence = True."""
        findings = [
            {"agent": "text_agent", "severity": "high", "confidence": 0.95, "indicators": ["urgency_language"], "status": "ok"}
        ]
        result = compute_risk(findings)
        assert result["low_confidence"] is True

    def test_low_confidence_flagged_when_average_confidence_below_point_four(self):
        """2 findings with avg confidence < 0.4 -> low_confidence = True."""
        findings = [
            {"agent": "text_agent", "severity": "high", "confidence": 0.30, "indicators": ["urgency_language"], "status": "ok"},
            {"agent": "url_agent", "severity": "high", "confidence": 0.30, "indicators": ["no_https"], "status": "ok"},
        ]
        result = compute_risk(findings)
        assert result["confidence"] == 0.30
        assert result["low_confidence"] is True

    def test_failed_findings_excluded_from_base_score(self):
        """Findings with status='failed' must be excluded from base_score calculation."""
        findings = [
            {"agent": "text_agent", "severity": "high", "confidence": 0.8, "indicators": ["urgency_language"], "status": "ok"},
            {"agent": "url_agent", "severity": "critical", "confidence": 1.0, "indicators": ["known_malicious_domain"], "status": "failed"},
        ]
        result = compute_risk(findings)

        # Only text_agent finding is included (severity='high' weight 0.75 * 0.8 = 0.60)
        assert result["base_score"] == 0.60
        assert result["confidence"] == 0.80
        assert result["low_confidence"] is True  # only 1 non-failed finding

    def test_pure_function_determinism_byte_identical_output(self):
        """Determinism check: Calling compute_risk twice on same input produces identical output."""
        findings = [
            {"agent": "text_agent", "severity": "high", "confidence": 0.75, "indicators": ["urgency_language", "credential_request"], "status": "ok"},
            {"agent": "url_agent", "severity": "medium", "confidence": 0.60, "indicators": ["no_https", "url_shortener"], "status": "degraded_fallback"},
            {"agent": "image_agent", "severity": "low", "confidence": 0.50, "indicators": ["embedded_contact_info"], "status": "ok"},
        ]

        res1 = compute_risk(findings)
        res2 = compute_risk(findings)

        assert res1 == res2
        assert json.dumps(res1, sort_keys=True) == json.dumps(res2, sort_keys=True)
