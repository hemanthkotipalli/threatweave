from __future__ import annotations

import logging

from groq import APIError as GroqAPIError
from groq import APITimeoutError as GroqTimeoutError
from groq import Groq

from app.core.config import settings
from app.core.errors import ExternalServiceError

logger = logging.getLogger("threatweave-api.agents.llm_client")

_GROQ_PLACEHOLDER = "your_groq_api_key_here"


def call_llm(system_prompt: str, user_content: str, timeout: int | None = None) -> str:
    """
    Calls the Groq inference API using the official Groq Python SDK.
    Uses JSON mode (response_format={"type": "json_object"}) to reduce
    the chance of markdown-fenced or malformed JSON responses.
    Masks credentials and translates all errors/timeouts into ExternalServiceError.

    :param system_prompt: Strict guidelines given to the model as system instructions.
    :param user_content: The text content to analyze.
    :param timeout: Optional override for the connection timeout in seconds.
    :return: Raw JSON string from the model (unwrapped from the chat completion envelope).
    :raises ExternalServiceError: On missing key, timeout, API error, or any unexpected failure.
    """
    api_key = settings.GROQ_API_KEY
    if not api_key or api_key == _GROQ_PLACEHOLDER:
        logger.error("Groq API key is not configured or is using the default placeholder.")
        raise ExternalServiceError(
            message="Threat intelligence service key is unconfigured.",
            code="missing_api_key",
        )

    resolved_timeout = timeout if timeout is not None else settings.TEXT_AGENT_TIMEOUT

    try:
        # Debug: log model, timeout, but never the API key
        logger.debug("Initializing Groq client: model=%s, timeout=%s", settings.TEXT_AGENT_MODEL, resolved_timeout)
        client = Groq(
            api_key=api_key,
            timeout=float(resolved_timeout),
        )

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
        logger.error(f"Groq API connection timed out after {resolved_timeout} seconds.")
        raise ExternalServiceError(
            message="Threat intelligence service request timed out.",
            code="external_service_timeout",
        ) from te

    except GroqAPIError as ae:
        # Mask credentials — log status and message only, never the key
        status_code = getattr(ae, "status_code", "N/A")
        message = getattr(ae, "message", str(ae))
        logger.error(f"Groq API error: status={status_code} message={message}")
        # Log full exception details for debugging
        logger.debug("GroqAPIError details", exc_info=True)
        raise ExternalServiceError(
            message="Threat intelligence external service returned an error.",
            code="external_service_error",
        ) from ae

    except ExternalServiceError:
        # Re-raise our own error (empty content check above) without wrapping
        raise

    except Exception as e:
        logger.error(f"Unexpected error during Groq API invocation: {e!s}")
        logger.debug("Unexpected exception details", exc_info=True)
        raise ExternalServiceError(
            message="An unexpected connection error occurred during API communication.",
            code="external_service_error",
        ) from e
