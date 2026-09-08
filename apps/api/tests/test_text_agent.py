from __future__ import annotations

from unittest.mock import patch

from app.agents.text_agent import analyze_text
from app.core.errors import ExternalServiceError
from app.schemas.evidence import EvidenceItem

PHISHING_TEXT = (
    "URGENT: Your account has been suspended due to suspicious activity. "
    "Dear Customer, click this link immediately and enter your password to verify "
    "your identity and avoid permanent account termination: http://bit.ly/fake-bank-login"
)

BENIGN_TEXT = "Hey, are we still on for lunch tomorrow? Let me know!"

GARBAGE_TEXT = ""

VERY_LONG_TEXT = "a" * 500_000


class TestTextAgentLLMPath:
    """Tests using the LLM path (mocked to avoid real API calls)."""

    def test_phishing_text_returns_medium_or_higher(self) -> None:
        """
        LLM mocked to return a high-confidence phishing analysis.
        Asserts severity is 'medium' or higher and at least one expected indicator present.
        """
        mock_response = (
            '{"finding": "Text contains multiple phishing indicators including urgency and credential request.", '
            '"confidence": 0.92, "severity": "high", '
            '"indicators": ["urgency_language", "credential_request", "suspicious_link_mention", "generic_greeting"], '
            '"reasoning": "The message uses urgent account suspension threats and requests credentials via an external link."}'
        )
        with patch("app.agents.text_agent.call_llm", return_value=mock_response):
            result = analyze_text(PHISHING_TEXT)

        assert isinstance(result, EvidenceItem)
        assert result.status == "ok"
        assert result.severity in ("medium", "high", "critical")
        assert any(
            ind in result.indicators
            for ind in ("urgency_language", "credential_request", "suspicious_link_mention")
        )

    def test_benign_text_returns_low_severity(self) -> None:
        """
        LLM mocked to return benign analysis.
        Asserts severity is 'info' or 'low'.
        """
        mock_response = (
            '{"finding": "No threat indicators detected in this message.", '
            '"confidence": 0.1, "severity": "info", '
            '"indicators": [], '
            '"reasoning": "The text is a casual social invitation with no suspicious patterns."}'
        )
        with patch("app.agents.text_agent.call_llm", return_value=mock_response):
            result = analyze_text(BENIGN_TEXT)

        assert isinstance(result, EvidenceItem)
        assert result.status == "ok"
        assert result.severity in ("info", "low")

    def test_llm_unknown_indicators_are_filtered(self) -> None:
        """
        LLM response includes unknown indicator strings.
        Asserts that invalid indicators are dropped silently.
        """
        mock_response = (
            '{"finding": "Suspicious patterns detected.", '
            '"confidence": 0.7, "severity": "medium", '
            '"indicators": ["urgency_language", "INVALID_INDICATOR", "ANOTHER_BAD_ONE"], '
            '"reasoning": "The text references urgency and suspicious indicators."}'
        )
        with patch("app.agents.text_agent.call_llm", return_value=mock_response):
            result = analyze_text(PHISHING_TEXT)

        assert isinstance(result, EvidenceItem)
        assert "INVALID_INDICATOR" not in result.indicators
        assert "ANOTHER_BAD_ONE" not in result.indicators
        assert "urgency_language" in result.indicators

    def test_confidence_is_clamped(self) -> None:
        """LLM returns out-of-range confidence — must be clamped to [0.0, 1.0]."""
        mock_response = (
            '{"finding": "Very suspicious.", "confidence": 1.9, "severity": "critical", '
            '"indicators": ["urgency_language"], "reasoning": "Very suspicious."}'
        )
        with patch("app.agents.text_agent.call_llm", return_value=mock_response):
            result = analyze_text(PHISHING_TEXT)

        assert result.confidence <= 1.0

    def test_llm_returns_markdown_fenced_json(self) -> None:
        """
        LLM returns a code-fenced JSON block.
        Asserts the fences are stripped and the response parses correctly.
        """
        mock_response = (
            "```json\n"
            '{"finding": "Fenced response.", "confidence": 0.5, "severity": "medium", '
            '"indicators": ["urgency_language"], "reasoning": "Contains urgency patterns."}\n'
            "```"
        )
        with patch("app.agents.text_agent.call_llm", return_value=mock_response):
            result = analyze_text(PHISHING_TEXT)

        assert isinstance(result, EvidenceItem)
        assert result.status == "ok"
        assert result.finding == "Fenced response."


class TestTextAgentFallbackPath:
    """Tests forcing the heuristic fallback path."""

    def test_fallback_on_external_service_error(self) -> None:
        """
        Mocks call_llm to raise ExternalServiceError.
        Asserts the function returns a valid EvidenceItem with status='degraded_fallback'.
        """
        with patch(
            "app.agents.text_agent.call_llm",
            side_effect=ExternalServiceError(message="API unavailable", code="timeout")
        ):
            result = analyze_text(PHISHING_TEXT)

        assert isinstance(result, EvidenceItem)
        assert result.status == "degraded_fallback"
        assert result.confidence <= 0.6
        # Phishing text should still trigger heuristic indicators
        assert len(result.indicators) > 0

    def test_fallback_on_invalid_json(self) -> None:
        """
        Mocks call_llm to return malformed JSON.
        Asserts fallback path is triggered.
        """
        with patch("app.agents.text_agent.call_llm", return_value="NOT VALID JSON !!@#$"):
            result = analyze_text(PHISHING_TEXT)

        assert isinstance(result, EvidenceItem)
        assert result.status == "degraded_fallback"

    def test_fallback_benign_text_has_no_indicators(self) -> None:
        """
        Benign text on the fallback path should return zero indicators and low severity.
        """
        with patch(
            "app.agents.text_agent.call_llm",
            side_effect=ExternalServiceError(message="API unavailable", code="timeout")
        ):
            result = analyze_text(BENIGN_TEXT)

        assert isinstance(result, EvidenceItem)
        assert result.status == "degraded_fallback"
        assert result.severity in ("info", "low")


class TestTextAgentSafetyNet:
    """Tests the absolute safety net: analyze_text must never raise."""

    def test_empty_string_never_raises(self) -> None:
        """Empty string input must not raise any exception."""
        with patch(
            "app.agents.text_agent.call_llm",
            side_effect=ExternalServiceError(message="API unavailable", code="timeout")
        ):
            result = analyze_text(GARBAGE_TEXT)

        assert isinstance(result, EvidenceItem)

    def test_very_long_string_never_raises(self) -> None:
        """Extremely large text input must not raise any exception."""
        with patch(
            "app.agents.text_agent.call_llm",
            side_effect=ExternalServiceError(message="API unavailable", code="timeout")
        ):
            result = analyze_text(VERY_LONG_TEXT)

        assert isinstance(result, EvidenceItem)

    def test_none_like_exception_is_caught(self) -> None:
        """
        Forces both LLM and fallback paths to fail completely.
        Asserts the absolute safety net returns status='failed'.
        """
        with (
            patch("app.agents.text_agent.call_llm", side_effect=RuntimeError("hard crash")),
            patch("app.agents.text_agent.re.search", side_effect=RuntimeError("broken re")),
        ):
            result = analyze_text(PHISHING_TEXT)

        assert isinstance(result, EvidenceItem)
        assert result.status == "failed"
        assert result.confidence == 0.0
        assert result.severity == "info"
        assert result.indicators == []
