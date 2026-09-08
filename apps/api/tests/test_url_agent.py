"""
tests/test_url_agent.py
-----------------------
Unit tests for ThreatWeave Phase 6 — URL Agent.

Coverage:
- Malicious structural URL → high/critical severity + expected indicators.
- Clean HTTPS URL → info/low severity.
- lookalike_score discriminates the real brand domain (no false self-flag).
- Malformed / empty / None-like input → safe result, never raises.
- Mock reputation failure → graceful degraded_fallback.
- Mock LLM failure → graceful degraded_fallback with heuristic result.
- No-env-vars path: URL_REPUTATION_API_KEY unset → no HTTP call attempted.
- Single weak flag (suspicious_tld only) → must NOT reach high/critical.
"""
from __future__ import annotations

from unittest.mock import patch

from app.agents.url_agent import analyze_url
from app.core.errors import ExternalServiceError
from app.core.url_heuristics import (
    count_subdomains,
    has_https,
    has_suspicious_tld,
    is_ip_address_host,
    is_known_shortener,
    lookalike_score,
    run_heuristics,
)

# ---------------------------------------------------------------------------
# Heuristic unit tests (network-free, no mocking required)
# ---------------------------------------------------------------------------

class TestHasHttps:
    def test_https_url_returns_true(self):
        assert has_https("https://www.example.com/path") is True

    def test_http_url_returns_false(self):
        assert has_https("http://www.example.com/path") is False

    def test_malformed_url_returns_false(self):
        assert has_https("not a url at all") is False

    def test_empty_string_returns_false(self):
        assert has_https("") is False


class TestIsIpAddressHost:
    def test_ipv4_host_returns_true(self):
        assert is_ip_address_host("http://192.168.1.1/login") is True

    def test_ipv4_with_path_returns_true(self):
        assert is_ip_address_host("http://10.0.0.1/paypal-verify") is True

    def test_domain_host_returns_false(self):
        assert is_ip_address_host("https://www.paypal.com/signin") is False

    def test_malformed_url_returns_false(self):
        assert is_ip_address_host("garbage input") is False

    def test_empty_string_returns_false(self):
        assert is_ip_address_host("") is False


class TestCountSubdomains:
    def test_no_subdomains(self):
        assert count_subdomains("https://paypal.com/login") == 0

    def test_www_counts_as_one(self):
        assert count_subdomains("https://www.paypal.com/login") == 1

    def test_multiple_subdomains(self):
        # login.secure.banking.example.com → "example.com" = 2 parts
        # host has 5 parts → 3 subdomains
        assert count_subdomains("http://login.secure.banking.example.com") == 3

    def test_malformed_returns_zero(self):
        assert count_subdomains("not a url") == 0


class TestIsKnownShortener:
    def test_bitly_returns_true(self):
        assert is_known_shortener("https://bit.ly/3xYzAbC") is True

    def test_tinyurl_returns_true(self):
        assert is_known_shortener("http://tinyurl.com/abcde") is True

    def test_twitter_tco_returns_true(self):
        assert is_known_shortener("https://t.co/xyz123") is True

    def test_legitimate_domain_returns_false(self):
        assert is_known_shortener("https://www.wikipedia.org") is False

    def test_malformed_returns_false(self):
        assert is_known_shortener("not a url") is False


class TestHasSuspiciousTld:
    def test_dot_tk_returns_true(self):
        assert has_suspicious_tld("http://evil-site.tk/login") is True

    def test_dot_xyz_returns_true(self):
        assert has_suspicious_tld("http://free-money.xyz") is True

    def test_dot_ml_returns_true(self):
        assert has_suspicious_tld("http://phish.ml") is True

    def test_legitimate_tld_returns_false(self):
        assert has_suspicious_tld("https://www.google.com") is False

    def test_dot_in_returns_false(self):
        assert has_suspicious_tld("https://sbi.co.in") is False

    def test_malformed_returns_false(self):
        assert has_suspicious_tld("garbage") is False


class TestLookalikScore:
    def test_obvious_typosquat_paypal(self):
        score, brand = lookalike_score("http://paypa1.com/login")
        assert score >= 0.75, f"Expected high similarity, got {score}"
        assert brand == "paypal.com"

    def test_real_paypal_not_self_flagged(self):
        """The real paypal.com domain must score 1.0 (exact match) — NOT flagged."""
        score, brand = lookalike_score("https://www.paypal.com/signin")
        # Exact match: score == 1.0 → url_agent deliberately does NOT flag these
        assert score == 1.0
        assert brand == "paypal.com"

    def test_real_sbi_not_self_flagged(self):
        score, _brand = lookalike_score("https://onlinesbi.com/login")
        assert score == 1.0

    def test_sbi_lookalike_detected(self):
        score, _brand = lookalike_score("http://onlinesbi-secure.com/verify")
        # The registered domain "onlinesbi-secure.com" is similar to "onlinesbi.com"
        assert score >= 0.6, f"Expected moderate similarity, got {score}"

    def test_unrelated_domain_low_score(self):
        score, _ = lookalike_score("https://www.wikipedia.org")
        assert score < 0.6, f"Unrelated domain should have low score, got {score}"

    def test_malformed_input_returns_zero(self):
        score, brand = lookalike_score("not a url at all")
        assert score == 0.0
        assert brand == ""

    def test_empty_string_returns_zero(self):
        score, _brand = lookalike_score("")
        assert score == 0.0


class TestRunHeuristics:
    def test_malicious_ip_url_high_severity(self):
        """IP address + no HTTPS + login path → should be high/critical."""
        result = run_heuristics("http://192.168.1.1/paypal-login")
        assert "ip_address_url" in result["indicators"]
        assert "no_https" in result["indicators"]
        assert result["suggested_severity"] in ("high", "critical")

    def test_clean_https_url_info_severity(self):
        result = run_heuristics("https://www.wikipedia.org")
        assert result["suggested_severity"] in ("info", "low")
        assert "no_https" not in result["indicators"]
        assert "ip_address_url" not in result["indicators"]

    def test_single_suspicious_tld_stays_below_high(self):
        """A lone .tk TLD must NOT reach high or critical — weak signal rule."""
        result = run_heuristics("https://my-project.tk")
        assert "suspicious_tld" in result["indicators"]
        severity = result["suggested_severity"]
        assert severity not in ("high", "critical"), (
            f"Single weak signal should not reach '{severity}'"
        )

    def test_lookalike_domain_flagged(self):
        result = run_heuristics("http://paypa1.com/login")
        assert "lookalike_domain" in result["indicators"]

    def test_lookalike_domain_flagged_for_combosquat_and_userinfo(self):
        result = run_heuristics("http://192.168.1.1@paypa1-verify.tk/login")
        assert "lookalike_domain" in result["indicators"]
        assert "no_https" in result["indicators"]
        assert "suspicious_url_structure" in result["indicators"]
        assert "suspicious_tld" in result["indicators"]
        assert result["suggested_severity"] in ("high", "critical")

    def test_combosquat_paypa1_verify_score(self):
        score, brand = lookalike_score("http://192.168.1.1@paypa1-verify.tk/login")
        assert score >= 0.75, f"Expected high similarity for paypa1-verify, got {score}"
        assert brand == "paypal.com"

    def test_homoglyph_leetspeak_score(self):
        score, brand = lookalike_score("http://p4yp4l-security.xyz/login")
        assert score >= 0.75, f"Expected homoglyph lookalike match, got {score}"
        assert brand == "paypal.com"

    def test_malformed_url_returns_safe_defaults(self):
        result = run_heuristics("not a url at all")
        assert isinstance(result["indicators"], list)
        assert isinstance(result["suggested_severity"], str)
        assert isinstance(result["details"], dict)

    def test_empty_string_returns_safe_defaults(self):
        result = run_heuristics("")
        assert isinstance(result["indicators"], list)


# ---------------------------------------------------------------------------
# URL Agent integration tests (with mocking)
# ---------------------------------------------------------------------------

class TestAnalyzeUrl:

    def test_malicious_ip_url_returns_high_or_critical(self):
        """
        'http://192.168.1.1/paypa1-login' has: no_https + ip_address_url +
        lookalike_domain (paypa1 ≈ paypal) → must be high or critical.
        """
        result = analyze_url("http://192.168.1.1/paypa1-login")
        assert result.agent == "url_agent"
        assert result.modality == "url"
        assert result.severity in ("high", "critical")
        assert "ip_address_url" in result.indicators
        assert result.status in ("ok", "degraded_fallback")
        assert result.confidence > 0.5

    def test_clean_wikipedia_returns_low_or_info(self):
        """A clean, well-known HTTPS URL should score info or low."""
        result = analyze_url("https://www.wikipedia.org")
        assert result.agent == "url_agent"
        assert result.severity in ("info", "low")
        assert result.status in ("ok", "degraded_fallback")

    def test_malformed_input_returns_failed_or_safe(self):
        """Malformed input must never raise — returns failed or safe status."""
        result = analyze_url("not a url at all")
        assert result.agent == "url_agent"
        # Should be safe (info or low) or failed — never raise
        assert result.severity in ("info", "low", "medium", "high", "critical")
        assert result.status in ("ok", "degraded_fallback", "failed")

    def test_empty_string_never_raises(self):
        result = analyze_url("")
        assert result.agent == "url_agent"
        # Any valid status is acceptable — no exception must escape
        assert result.status in ("ok", "degraded_fallback", "failed")

    def test_reputation_failure_still_returns_valid_result(self):
        """
        When reputation_client raises ExternalServiceError, the agent must
        still return a valid EvidenceItem using heuristics only.
        """
        with patch(
            "app.agents.url_agent.check_reputation",
            side_effect=ExternalServiceError(
                message="Reputation API is down", code="reputation_api_error"
            ),
        ):
            result = analyze_url("http://bit.ly/3xPhish")
        assert result.agent == "url_agent"
        assert result.status in ("ok", "degraded_fallback")
        # url_shortener should still be detected via heuristics
        assert "url_shortener" in result.indicators

    def test_llm_failure_produces_degraded_fallback(self):
        """
        When call_llm raises ExternalServiceError, status must be
        'degraded_fallback' and the result must still contain heuristic indicators.
        """
        with patch(
            "app.agents.url_agent.call_llm",
            side_effect=ExternalServiceError(
                message="LLM unavailable", code="external_service_error"
            ),
        ):
            result = analyze_url("http://192.168.1.1/verify-account")
        assert result.agent == "url_agent"
        assert result.status == "degraded_fallback"
        assert "ip_address_url" in result.indicators
        assert "no_https" in result.indicators

    def test_both_reputation_and_llm_fail_still_returns_result(self):
        """
        Belt-and-suspenders: both optional layers fail → heuristic-only result.
        """
        with (
            patch(
                "app.agents.url_agent.check_reputation",
                side_effect=ExternalServiceError("down", "reputation_api_error"),
            ),
            patch(
                "app.agents.url_agent.call_llm",
                side_effect=ExternalServiceError("down", "external_service_error"),
            ),
        ):
            result = analyze_url("http://fake-icicibank.tk/login")
        assert result.agent == "url_agent"
        assert result.status == "degraded_fallback"
        assert isinstance(result.indicators, list)
        assert result.severity in ("info", "low", "medium", "high", "critical")

    def test_no_reputation_api_key_no_network_call(self):
        """
        Critical: when URL_REPUTATION_API_KEY is empty, check_reputation()
        must return None immediately — assert_not_called() on the internal
        HTTP client verifies no network call is attempted.
        """
        # Patch settings to ensure key is empty
        with (
            patch("app.agents.reputation_client.settings") as mock_settings,
            patch("app.agents.reputation_client.httpx") as mock_httpx,
        ):
            mock_settings.URL_REPUTATION_API_KEY = ""
            mock_settings.URL_REPUTATION_API_TIMEOUT_SECONDS = 8

            from app.agents.reputation_client import check_reputation
            result = check_reputation("http://192.168.1.1/phish")

        assert result is None
        mock_httpx.get.assert_not_called()
        mock_httpx.post.assert_not_called()

    def test_single_tld_flag_never_reaches_high(self):
        """
        A URL with ONLY a suspicious TLD (no other flags) must stay below high.
        This is the corroboration-required rule.
        """
        # https + no IP + no shortener + no lookalike + only bad TLD
        result = analyze_url("https://my-project.tk")
        assert result.severity not in ("high", "critical"), (
            f"Single weak signal (suspicious_tld) reached '{result.severity}' — violation"
        )

    def test_real_brand_domain_not_flagged_as_lookalike(self):
        """
        The real paypal.com must not be flagged with lookalike_domain.
        lookalike_score returns 1.0 for exact match → agent deliberately skips.
        """
        result = analyze_url("https://www.paypal.com/signin")
        assert "lookalike_domain" not in result.indicators, (
            "Real brand domain incorrectly flagged as lookalike"
        )
