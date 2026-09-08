"""
app/services/webhook_service.py
---------------------------------
Dispatches external webhook notifications to n8n for high/critical severity investigations (Phase 16).
Guaranteed graceful degradation: network failures, timeouts, or unconfigured webhooks
NEVER raise exceptions or disrupt investigation analysis.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger("threatweave-api.services.webhook")

WEBHOOK_TIMEOUT_SECONDS: float = 5.0


def notify_high_severity(investigation_summary: dict[str, Any]) -> None:
    """
    Dispatches a structured investigation summary payload to the configured n8n webhook.

    Reliability Guarantee:
    - If settings.N8N_WEBHOOK_URL is unset/empty, returns immediately with ZERO network calls.
    - If configured, sends an HTTP POST with a 5.0-second timeout.
    - Any network error, timeout, or non-2xx response is logged without raising an exception,
      ensuring that webhook side-effects never fail or block the calling investigation.

    Args:
        investigation_summary: Dictionary containing investigation metadata,
            risk metrics, severity, and top extracted indicators.
    """
    webhook_url = (settings.N8N_WEBHOOK_URL or "").strip()
    if not webhook_url:
        logger.debug("n8n webhook not configured, skipping")
        return

    logger.info(
        "Dispatching high-severity alert webhook to n8n for investigation %s",
        investigation_summary.get("investigation_id"),
    )

    try:
        with httpx.Client(timeout=WEBHOOK_TIMEOUT_SECONDS) as client:
            response = client.post(
                webhook_url,
                json=investigation_summary,
                headers={"Content-Type": "application/json", "User-Agent": "ThreatWeave-Alert-Dispatcher/1.0"},
            )
            if response.is_success:
                logger.info(
                    "n8n webhook delivered successfully (status=%d) for investigation %s",
                    response.status_code,
                    investigation_summary.get("investigation_id"),
                )
            else:
                logger.warning(
                    "n8n webhook responded with non-success status %d for investigation %s: %s",
                    response.status_code,
                    investigation_summary.get("investigation_id"),
                    response.text[:200],
                )
    except httpx.TimeoutException as exc:
        logger.warning(
            "n8n webhook timed out after %.1fs for investigation %s: %s",
            WEBHOOK_TIMEOUT_SECONDS,
            investigation_summary.get("investigation_id"),
            exc,
        )
    except httpx.RequestError as exc:
        logger.warning(
            "n8n webhook connection error for investigation %s: %s",
            investigation_summary.get("investigation_id"),
            exc,
        )
    except Exception:
        logger.exception(
            "Unexpected error while notifying n8n webhook for investigation %s",
            investigation_summary.get("investigation_id"),
        )
