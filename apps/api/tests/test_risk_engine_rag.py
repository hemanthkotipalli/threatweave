"""
tests/test_risk_engine_rag.py
-----------------------------
Unit tests verifying the Phase 12 surgical update to compute_risk().
Validates that retrieved citations clearing threshold grant the +0.15 intel_bonus,
while empty or below-threshold citations preserve 0.0 bonus with zero regression.
"""
from __future__ import annotations

from app.agents.risk_engine import compute_risk
from app.core.config import settings


class TestRiskEngineRagBonus:
    def test_rag_citation_clearing_threshold_grants_intel_bonus(self):
        """
        When rag_citations contains at least one citation with similarity_score >= threshold:
        - intel_bonus must equal 0.15.
        - final_risk must reflect base_score + corroboration_bonus + 0.15 - contradiction_penalty.
        - breakdown list must contain component 'intel_bonus' with value 0.15 and contribution 0.15.
        """
        findings = [
            {
                "agent": "text_agent",
                "severity": "high",  # weight = 0.75
                "confidence": 0.80,   # score = 0.60
                "indicators": ["credential_request"],
                "status": "ok",
            }
        ]
        # Single finding: base_score = 0.60, corroboration = 0.0, penalty = 0.0
        # Without intel_bonus: final_risk = 0.60
        # With intel_bonus: final_risk = 0.60 + 0.15 = 0.75

        citations = [
            {
                "source_title": "CERT-In Advisory: Phishing Campaigns",
                "source_type": "CERT-In",
                "similarity_score": settings.RAG_SIMILARITY_THRESHOLD + 0.05,
                "chunk_text": "Phishing campaign sample advisory text...",
            }
        ]

        result = compute_risk(findings, rag_citations=citations)

        assert result["intel_bonus"] == 0.15
        assert result["base_score"] == 0.60
        assert result["final_risk"] == 0.75
        assert result["severity"] == "high"

        intel_item = next((item for item in result["breakdown"] if item["component"] == "intel_bonus"), None)
        assert intel_item is not None
        assert intel_item["value"] == 0.15
        assert intel_item["weight"] == 1.0
        assert intel_item["contribution"] == 0.15

    def test_empty_rag_citations_preserves_zero_intel_bonus_regression_proof(self):
        """
        Regression proof for Phase 11:
        Calling compute_risk() with empty rag_citations list (or None) must produce
        intel_bonus == 0.0, identically matching Phase 11's behavior.
        """
        findings = [
            {
                "agent": "text_agent",
                "severity": "high",
                "confidence": 0.80,
                "indicators": ["credential_request"],
                "status": "ok",
            }
        ]

        # Call with None (default parameter)
        result_none = compute_risk(findings)
        assert result_none["intel_bonus"] == 0.0
        assert result_none["final_risk"] == 0.60

        # Call with explicit empty list
        result_empty = compute_risk(findings, rag_citations=[])
        assert result_empty["intel_bonus"] == 0.0
        assert result_empty["final_risk"] == 0.60

        # Output must be identical between None and empty list
        assert result_none == result_empty

    def test_below_threshold_citations_grant_zero_intel_bonus(self):
        """
        If citations exist but all are strictly below settings.RAG_SIMILARITY_THRESHOLD,
        intel_bonus must remain 0.0.
        """
        findings = [
            {
                "agent": "text_agent",
                "severity": "medium",  # weight = 0.50
                "confidence": 0.80,    # score = 0.40
                "indicators": ["generic_alert"],
                "status": "ok",
            }
        ]

        sub_threshold_citations = [
            {
                "source_title": "Marginal Advisory",
                "source_type": "Scam-Intel",
                "similarity_score": settings.RAG_SIMILARITY_THRESHOLD - 0.10,
                "chunk_text": "Vaguely related text...",
            }
        ]

        result = compute_risk(findings, rag_citations=sub_threshold_citations)
        assert result["intel_bonus"] == 0.0
        assert result["final_risk"] == 0.40

    def test_clamping_with_intel_bonus_does_not_exceed_one(self):
        """
        A critical finding with high confidence and corroboration + intel bonus
        must clamp cleanly at 1.0 without overflow.
        """
        findings = [
            {"agent": "text_agent", "severity": "critical", "confidence": 1.0, "indicators": ["otp_theft"], "status": "ok"},
            {"agent": "url_agent", "severity": "critical", "confidence": 1.0, "indicators": ["otp_theft"], "status": "ok"},
        ]
        # base_score = 1.0, corroboration = +0.10, intel = +0.15 -> raw = 1.25 -> clamped = 1.0
        citations = [{"similarity_score": 0.85}]

        result = compute_risk(findings, rag_citations=citations)
        assert result["intel_bonus"] == 0.15
        assert result["final_risk"] == 1.0
        assert result["severity"] == "critical"
