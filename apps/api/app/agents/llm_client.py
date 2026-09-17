from __future__ import annotations

import logging
import random
import time

from groq import APIError as GroqAPIError
from groq import APITimeoutError as GroqTimeoutError
from groq import Groq
from groq import RateLimitError as GroqRateLimitError

from app.core.config import settings
from app.core.errors import ExternalServiceError

logger = logging.getLogger("threatweave-api.agents.llm_client")

_GROQ_PLACEHOLDER = "your_groq_api_key_here"

# Retry configuration for HTTP 429 (Rate Limit) responses
_MAX_RETRIES: int = 3
_BASE_DELAY: float = 1.0
_BACKOFF_FACTOR: float = 2.0
_JITTER_RATIO: float = 0.25
_MAX_DELAY: float = 8.0
_MAX_TOTAL_WAIT: float = 15.0


def _is_rate_limit_error(exc: Exception) -> bool:
    """
    Checks whether an exception represents an HTTP 429 Rate Limit response from Groq.
    Handles both explicit GroqRateLimitError and GroqAPIError with status_code 429.
    """
    return isinstance(exc, GroqRateLimitError) or (
        isinstance(exc, GroqAPIError) and getattr(exc, "status_code", None) == 429
    )


def call_llm(system_prompt: str, user_content: str, timeout: int | None = None) -> str:
    """
    Calls the Groq inference API using the official Groq Python SDK.
    Uses JSON mode (response_format={"type": "json_object"}) to reduce
    the chance of markdown-fenced or malformed JSON responses.
    Masks credentials and translates all errors/timeouts into ExternalServiceError.

    Implements jittered exponential backoff retry logic specifically on HTTP 429
    (rate limit) responses. Other errors (timeouts, 500s, connection errors) fail
    fast without retrying to preserve analysis time budgets.

    :param system_prompt: Strict guidelines given to the model as system instructions.
    :param user_content: The text content to analyze.
    :param timeout: Optional override for the connection timeout in seconds.
    :return: Raw JSON string from the model (unwrapped from the chat completion envelope).
    :raises ExternalServiceError: On missing key, timeout, API error, rate limit, or unexpected failure.
    """
    api_key = settings.GROQ_API_KEY
    if not api_key or api_key == _GROQ_PLACEHOLDER:
        logger.error("Groq API key is not configured or is using the default placeholder.")
        raise ExternalServiceError(
            message="Threat intelligence service key is unconfigured.",
            code="missing_api_key",
        )

    resolved_timeout = timeout if timeout is not None else settings.TEXT_AGENT_TIMEOUT

    # Debug: log model, timeout, but never the API key
    logger.debug("Initializing Groq client: model=%s, timeout=%s", settings.TEXT_AGENT_MODEL, resolved_timeout)
    client = Groq(
        api_key=api_key,
        timeout=float(resolved_timeout),
    )

    total_waited = 0.0
    for attempt in range(1, _MAX_RETRIES + 2):
        try:
            completion = client.chat.completions.create(
                model=settings.TEXT_AGENT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=1024,
                temperature=0.1,                          # Low temperature for deterministic analysis
                response_format={"type": "json_object"},  # JSON mode: disables fences, forces valid JSON
            )
            # Debug: raw response content
            logger.debug("Groq completion raw response: %s", completion)

            choices = completion.choices
            if not choices or not choices[0].message.content:
                logger.error("Groq API returned a completion with empty content.")
                raise ExternalServiceError(
                    message="Threat intelligence service returned an empty response.",
                    code="empty_llm_response",
                )

            return choices[0].message.content

        except GroqTimeoutError as te:
            logger.error("Groq API connection timed out after %s seconds.", resolved_timeout)
            raise ExternalServiceError(
                message="Threat intelligence service request timed out.",
                code="external_service_timeout",
            ) from te

        except (GroqAPIError, GroqRateLimitError) as ae:
            status_code = getattr(ae, "status_code", "N/A")
            message = getattr(ae, "message", str(ae))

            # Only retry if HTTP 429 rate limit and retry budget remains
            if _is_rate_limit_error(ae) and attempt <= _MAX_RETRIES:
                raw_delay = min(_BASE_DELAY * (_BACKOFF_FACTOR ** (attempt - 1)), _MAX_DELAY)
                jitter = random.uniform(-_JITTER_RATIO * raw_delay, _JITTER_RATIO * raw_delay)
                sleep_time = max(0.1, raw_delay + jitter)

                if total_waited + sleep_time > _MAX_TOTAL_WAIT:
                    sleep_time = max(0.0, _MAX_TOTAL_WAIT - total_waited)

                if sleep_time > 0.0:
                    logger.warning(
                        "Groq API rate limit (429) encountered. Retrying in %.2fs (attempt %d/%d)...",
                        sleep_time,
                        attempt,
                        _MAX_RETRIES,
                    )
                    time.sleep(sleep_time)
                    total_waited += sleep_time
                    continue

            # Retries exhausted or non-429 API error
            logger.error("Groq API error: status=%s message=%s", status_code, message)
            logger.debug("GroqAPIError details", exc_info=True)
            if _is_rate_limit_error(ae):
                raise ExternalServiceError(
                    message="Threat intelligence service rate limit exceeded.",
                    code="rate_limit_exceeded",
                ) from ae
            raise ExternalServiceError(
                message="Threat intelligence external service returned an error.",
                code="external_service_error",
            ) from ae

        except ExternalServiceError:
            # Re-raise our own error (empty content check above) without wrapping
            raise

        except Exception as e:
            logger.error("Unexpected error during Groq API invocation: %s", e)
            logger.debug("Unexpected exception details", exc_info=True)
            raise ExternalServiceError(
                message="An unexpected connection error occurred during API communication.",
                code="external_service_error",
            ) from e

    raise ExternalServiceError(
        message="Threat intelligence service rate limit exceeded after retries.",
        code="rate_limit_exceeded",
    )
