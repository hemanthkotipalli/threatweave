"""
app/core/security.py
--------------------
Security utilities for password hashing (bcrypt) and JWT token generation/validation (PyJWT).
Includes fail-loud startup verification for non-development environments.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings
from app.core.errors import AuthenticationError

logger = logging.getLogger("threatweave-api.security")


def validate_security_configuration() -> None:
    """
    Validates that security-critical parameters are safely configured.
    Raises RuntimeError if JWT_SECRET_KEY is unset or set to the insecure default
    in any non-development environment.
    """
    env = (settings.ENVIRONMENT or "").strip().lower()
    secret = (settings.JWT_SECRET_KEY or "").strip()
    insecure_defaults = {"", "threatweave-dev-secret-key-change-in-prod", "secret", "changeme"}

    if env != "development" and secret in insecure_defaults:
        raise RuntimeError(
            f"CRITICAL SECURITY CONFIGURATION ERROR: JWT_SECRET_KEY cannot be empty or default "
            f"in environment '{env}'. You must provide a strong, random secret key."
        )
    logger.debug("Security configuration validated successfully for environment '%s'", env)


def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt with a securely generated salt.
    Never logs or stores the raw password.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt password hash.
    Returns False on hash mismatch or invalid format without leaking timing/tracebacks.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Password verification encountered an error: %s", exc)
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Encodes and signs a JSON Web Token (JWT) with user claims and expiration timestamp.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodes and validates the signature and expiration of a JWT access token.
    Raises AuthenticationError (HTTP 401) on expired, malformed, or invalid tokens.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.warning("Access token expired: %s", e)
        raise AuthenticationError(
            message="Authentication token has expired. Please log in again.",
            code="token_expired",
        ) from e
    except jwt.InvalidTokenError as e:
        logger.warning("Access token validation failed: %s", e)
        raise AuthenticationError(
            message="Invalid or malformed authentication token.",
            code="invalid_token",
        ) from e
