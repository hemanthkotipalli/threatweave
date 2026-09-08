import logging
import uuid
from collections.abc import Generator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError
from app.core.security import decode_access_token
from app.db.session import get_db as _get_db
from app.models.user import User

logger = logging.getLogger("threatweave-api.deps")

security_bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a real SQLAlchemy database session.
    """
    yield from _get_db()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    """
    FastAPI dependency extracting, decoding, and validating the Bearer JWT token.
    Returns the authenticated User or raises AuthenticationError (HTTP 401).
    """
    if not credentials or not credentials.credentials:
        logger.warning("Authentication failed: no authorization header provided")
        raise AuthenticationError(
            message="Authentication credentials were not provided. Authorization Bearer token required.",
            code="authentication_required",
        )

    token = credentials.credentials.strip()
    payload = decode_access_token(token)

    user_id_str = payload.get("sub")
    if not user_id_str:
        logger.warning("Authentication failed: token missing 'sub' subject claim")
        raise AuthenticationError(
            message="Invalid token claims: subject identifier missing.",
            code="invalid_token",
        )

    try:
        user_id = uuid.UUID(str(user_id_str))
    except (ValueError, AttributeError):
        logger.warning("Authentication failed: invalid UUID in 'sub' claim: %s", user_id_str)
        raise AuthenticationError(
            message="Invalid token claims: subject is not a valid UUID.",
            code="invalid_token",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning("Authentication failed: user %s not found in database", user_id)
        raise AuthenticationError(
            message="User account associated with this token no longer exists.",
            code="user_not_found",
        )

    return user

