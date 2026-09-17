from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from groq import APIError as GroqAPIError
from groq import APITimeoutError as GroqTimeoutError
from groq import RateLimitError as GroqRateLimitError

from app.agents.llm_client import call_llm
from app.agents.text_agent import analyze_text
from app.core.errors import ExternalServiceError
from app.schemas.evidence import EvidenceItem


def _make_mock_completion(content: str = '{"finding": "test"}') -> MagicMock:
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    return mock_completion


class TestGroqRateLimitRetry:
    """Regression tests for HTTP 429 jittered exponential backoff retry in call_llm."""

    def test_429_retries_with_increasing_delays_and_succeeds(self):
        """
        Groq API fails twice with 429 RateLimitError, then succeeds on 3rd attempt.
        Asserts retry logic attempts multiple times and sleeps with backoff.
        """
        mock_response = MagicMock(status_code=429, headers={})
        rate_limit_err = GroqRateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": {"message": "Rate limit exceeded"}},
        )
        success_completion = _make_mock_completion('{"status": "recovered"}')

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            rate_limit_err,
            rate_limit_err,
            success_completion,
        ]

        with (
            patch("app.agents.llm_client.Groq", return_value=mock_client),
            patch("app.agents.llm_client.time.sleep") as mock_sleep,
            patch("app.agents.llm_client.settings.GROQ_API_KEY", "test_key_valid"),
        ):
            result = call_llm(system_prompt="sys", user_content="user")

        assert result == '{"status": "recovered"}'
        assert mock_client.chat.completions.create.call_count == 3
        assert mock_sleep.call_count == 2

        # Delays should increase (attempt 1 base 1.0s, attempt 2 base 2.0s with +-25% jitter)
        first_delay = mock_sleep.call_args_list[0][0][0]
        second_delay = mock_sleep.call_args_list[1][0][0]
        assert 0.75 <= first_delay <= 1.25
        assert 1.50 <= second_delay <= 2.50
        assert second_delay > first_delay

    def test_429_exhausts_retries_and_raises_rate_limit_exceeded(self):
        """
        Groq API continuously returns 429.
        Asserts max retries (3) are attempted, sleep called 3 times, then ExternalServiceError raised.
        """
        mock_response = MagicMock(status_code=429, headers={})
        rate_limit_err = GroqRateLimitError(
            message="Rate limit exceeded",
            response=mock_response,
            body={"error": {"message": "Rate limit exceeded"}},
        )

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = rate_limit_err

        with (
            patch("app.agents.llm_client.Groq", return_value=mock_client),
            patch("app.agents.llm_client.time.sleep") as mock_sleep,
            patch("app.agents.llm_client.settings.GROQ_API_KEY", "test_key_valid"),
            pytest.raises(ExternalServiceError) as exc_info,
        ):
            call_llm(system_prompt="sys", user_content="user")

        assert exc_info.value.code == "rate_limit_exceeded"
        # 1 initial + 3 retries = 4 create calls
        assert mock_client.chat.completions.create.call_count == 4
        assert mock_sleep.call_count == 3

    def test_non_429_timeout_does_not_retry(self):
        """
        Groq API raises GroqTimeoutError.
        Asserts zero retry attempts and sleep is never called.
        """
        timeout_err = GroqTimeoutError(request=MagicMock())
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = timeout_err

        with (
            patch("app.agents.llm_client.Groq", return_value=mock_client),
            patch("app.agents.llm_client.time.sleep") as mock_sleep,
            patch("app.agents.llm_client.settings.GROQ_API_KEY", "test_key_valid"),
            pytest.raises(ExternalServiceError) as exc_info,
        ):
            call_llm(system_prompt="sys", user_content="user")

        assert exc_info.value.code == "external_service_timeout"
        assert mock_client.chat.completions.create.call_count == 1
        assert mock_sleep.call_count == 0

    def test_non_429_api_error_does_not_retry(self):
        """
        Groq API raises GroqAPIError with status 500.
        Asserts zero retry attempts and sleep is never called.
        """
        api_err = GroqAPIError(
            message="Internal server error",
            request=MagicMock(),
            body={"error": {"message": "Server error"}},
        )
        api_err.status_code = 500

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = api_err

        with (
            patch("app.agents.llm_client.Groq", return_value=mock_client),
            patch("app.agents.llm_client.time.sleep") as mock_sleep,
            patch("app.agents.llm_client.settings.GROQ_API_KEY", "test_key_valid"),
            pytest.raises(ExternalServiceError) as exc_info,
        ):
            call_llm(system_prompt="sys", user_content="user")

        assert exc_info.value.code == "external_service_error"
        assert mock_client.chat.completions.create.call_count == 1
        assert mock_sleep.call_count == 0

    def test_text_agent_falls_through_to_degraded_fallback_on_exhausted_429(self):
        """
        End-to-end caller verification:
        When Groq rate limits are exhausted, analyze_text smoothly falls through to
        degraded_fallback with an identical EvidenceItem shape.
        """
        rate_limit_exc = ExternalServiceError(
            message="Threat intelligence service rate limit exceeded.",
            code="rate_limit_exceeded",
        )

        with patch("app.agents.text_agent.call_llm", side_effect=rate_limit_exc):
            item = analyze_text("URGENT: Your bank account is locked! Click http://phish.top to verify OTP.")

        assert isinstance(item, EvidenceItem)
        assert item.status == "degraded_fallback"
        assert item.agent == "text_agent"
        assert item.modality == "text"
        assert item.severity in ("medium", "high", "critical")
        assert "urgency_language" in item.indicators
        assert "Heuristic analysis detected" in item.finding
