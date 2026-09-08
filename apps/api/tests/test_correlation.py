"""
tests/test_correlation.py
-------------------------
Unit tests for evidence corroboration and conflict detection (Phase 11).
"""
from __future__ import annotations

from app.agents.correlation import find_conflicts, find_corroboration


class TestCorrelationDirect:
    """Direct tests for find_corroboration() and find_conflicts()."""

    def test_shared_indicator_across_two_agents_detected_as_corroboration(self):
        """Two different agents sharing an indicator -> grouped in corroboration."""
        findings = [
            {"agent": "text_agent", "indicators": ["credential_request", "urgency_language"], "status": "ok"},
            {"agent": "image_agent", "indicators": ["credential_request"], "status": "ok"},
        ]

        groups = find_corroboration(findings)

        assert len(groups) == 1
        assert groups[0]["indicator"] == "credential_request"
        assert sorted(groups[0]["agents"]) == ["image_agent", "text_agent"]

    def test_intra_agent_duplicate_indicators_do_not_count_as_corroboration(self):
        """Single agent with duplicate indicators in its own list -> 0 corroboration."""
        findings = [
            {
                "agent": "text_agent",
                "indicators": ["credential_request", "credential_request", "urgency_language"],
                "status": "ok",
            }
        ]

        groups = find_corroboration(findings)
        assert len(groups) == 0

    def test_divergent_severity_on_related_signal_detected_as_conflict(self):
        """
        Both agents ran, severities diverge significantly on related signal:
        Agent A: text_agent, severity='critical', indicator='credential_request'
        Agent B: image_agent, severity='low', indicator='impersonation_banner'
        Both relate to 'social_engineering'.
        """
        findings = [
            {"agent": "text_agent", "severity": "critical", "indicators": ["credential_request"], "status": "ok"},
            {"agent": "image_agent", "severity": "low", "indicators": ["impersonation_banner"], "status": "ok"},
        ]

        conflicts = find_conflicts(findings)

        assert len(conflicts) == 1
        assert conflicts[0]["agent_a"] == "text_agent"
        assert conflicts[0]["agent_b"] == "image_agent"
        assert conflicts[0]["conflict_type"] == "severity_divergence"
        assert "social_engineering" in conflicts[0]["description"]

    def test_single_agent_running_other_skipped_does_not_trigger_conflict(self):
        """
        When only one agent ran (e.g. text_agent has a high severity finding, but no other agent ran),
        no conflict is triggered (both must have actually run and produced a finding).
        """
        findings = [
            {"agent": "text_agent", "severity": "critical", "indicators": ["credential_request"], "status": "ok"}
        ]

        conflicts = find_conflicts(findings)
        assert len(conflicts) == 0

    def test_failed_agent_does_not_trigger_conflict(self):
        """Agent with status='failed' must NOT be flagged as a conflict against an active agent."""
        findings = [
            {"agent": "text_agent", "severity": "critical", "indicators": ["credential_request"], "status": "ok"},
            {"agent": "url_agent", "severity": "info", "indicators": ["credential_request"], "status": "failed"},
        ]

        conflicts = find_conflicts(findings)
        assert len(conflicts) == 0

    def test_unrelated_signals_do_not_trigger_conflict_even_if_severities_differ(self):
        """
        Severities differ, but findings look at completely unrelated signals (no shared indicator or category).
        Text agent: 'urgency_language' (social_engineering)
        URL agent: 'no_https' (technical_infrastructure)
        -> Must NOT flag a conflict because they analyzed completely different domains.
        """
        findings = [
            {"agent": "text_agent", "severity": "critical", "indicators": ["urgency_language"], "status": "ok"},
            {"agent": "url_agent", "severity": "low", "indicators": ["no_https"], "status": "ok"},
        ]

        conflicts = find_conflicts(findings)
        assert len(conflicts) == 0
