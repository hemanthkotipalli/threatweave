"""
app/agents/reputation_client.py
--------------------------------
Optional URL/domain reputation API client for ThreatWeave Phase 6.

Behaviour contract
------------------
- If ``settings.URL_REPUTATION_API_KEY`` is unset or empty → return ``None``
  immediately.  No network call is ever attempted.  Log at DEBUG level only
  (not an error).
- If configured but the API call fails or times out → raise
  ``ExternalServiceError`` so the caller (url_agent) can gracefully continue
  without reputation data.  The agent is never broken by a reputation failure.

The actual API integration is left as a stub (``_call_api``) that raises
``NotImplementedError`` — the key "not configured" / "configured but failed"
flow is fully exercisable in tests without a live API.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import ExternalServiceError

logger = logging.getLogger("threatweave-api.agents.reputation_client")

_PLACEHOLDER = ""  # empty string = "not configured"


def check_reputation(url: str, timeout: int | None = None) -> dict[str, Any] | None:
    """
    Queries an external URL reputation API for the given URL.

    Returns ``None`` (not an error) if the API key is not configured.
    Raises ``ExternalServiceError`` if the API is configured but the call fails.

    :param url:     The URL to look up.
    :param timeout: Override for the HTTP timeout in seconds.
                    Defaults to ``settings.URL_REPUTATION_API_TIMEOUT_SECONDS``.
    :return: Parsed reputation dict from the API, or ``None`` if unconfigured.
    :raises ExternalServiceError: On network failure, timeout, or API error.
    """
    api_key = settings.URL_REPUTATION_API_KEY

    # --- Not-configured path: skip network entirely ---
    if not api_key or api_key == _PLACEHOLDER:
        logger.debug(
            "URL reputation API key is not configured — skipping reputation check "
            "(set URL_REPUTATION_API_KEY in .env to enable)."
        )
        return None

    resolved_timeout = (
        timeout if timeout is not None else settings.URL_REPUTATION_API_TIMEOUT_SECONDS
    )

    try:
        return _call_api(url=url, api_key=api_key, timeout=resolved_timeout)
    except ExternalServiceError:
        raise
    except httpx.TimeoutException as te:
        logger.error(
            "URL reputation API timed out after %s seconds for url=%r",
            resolved_timeout,
            url,
        )
        raise ExternalServiceError(
            message="URL reputation service request timed out.",
            code="reputation_timeout",
        ) from te
    except httpx.HTTPStatusError as he:
        logger.error(
            "URL reputation API returned HTTP %s for url=%r",
            he.response.status_code,
            url,
        )
        raise ExternalServiceError(
            message="URL reputation service returned an error response.",
            code="reputation_api_error",
        ) from he
    except Exception as exc:
        logger.error(
            "Unexpected error during URL reputation lookup for url=%r: %s",
            url,
            exc,
        )
        raise ExternalServiceError(
            message="URL reputation lookup encountered an unexpected error.",
            code="reputation_api_error",
        ) from exc


def _call_api(url: str, api_key: str, timeout: int) -> dict[str, Any]:
    """
    Internal stub: performs the actual HTTP request to the reputation API.

    Replace this function body when integrating a concrete provider
    (e.g. VirusTotal, URLScan.io, Google Safe Browsing).

    :raises NotImplementedError: Always — integration not yet wired.
    """
    # TODO (Phase 6+): Wire to a live reputation API such as:
    #   - VirusTotal v3 URL lookup  (https://developers.virustotal.com)
    #   - URLScan.io  (https://urlscan.io/docs/api/)
    #   - Google Safe Browsing  (https://developers.google.com/safe-browsing)
    #
    # Stub example using httpx (already in requirements):
    #
    #   response = httpx.get(
    #       "https://www.virustotal.com/api/v3/urls",
    #       headers={"x-apikey": api_key},
    #       params={"url": url},
    #       timeout=timeout,
    #   )
    #   response.raise_for_status()
    #   return response.json()
    #
    raise NotImplementedError(
        "Reputation API integration is not yet configured. "
        "Implement _call_api() with a concrete provider."
    )
