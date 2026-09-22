import logging
import uuid
from collections.abc import Generator

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError, NotFoundError
from app.core.security import decode_access_token
from app.db.session import get_db as _get_db
from app.models.investigation import Investigation
from app.models.user import User

logger = logging.getLogger("threatweave-api.deps")

security_bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a real SQLAlchemy database session.
    """
    yield from _get_db()


def _resolve_user_from_token(token: str, db: Session) -> User:
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


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),  # noqa: B008
    token_query: str | None = Query(None, alias="token"),
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    """
    FastAPI dependency extracting, decoding, and validating the Bearer JWT token.
    Returns the authenticated User or raises AuthenticationError (HTTP 401).
    """
    token: str | None = None
    if credentials and credentials.credentials:
        token = credentials.credentials.strip()
    elif token_query and token_query.strip():
        token = token_query.strip()

    if not token:
        logger.warning("Authentication failed: no authorization header provided")
        raise AuthenticationError(
            message="Authentication credentials were not provided. Authorization Bearer token required.",
            code="authentication_required",
        )

    return _resolve_user_from_token(token=token, db=db)


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_bearer),  # noqa: B008
    token_query: str | None = Query(None, alias="token"),
    db: Session = Depends(get_db),  # noqa: B008
) -> User | None:
    """
    FastAPI dependency extracting, decoding, and validating optional Bearer JWT token.
    Accepts token via Authorization Bearer header or ?token= query parameter.
    Returns User if valid token is provided; returns None if no authorization credentials provided.
    Raises AuthenticationError (HTTP 401) if an invalid or expired token is provided.
    """
    token: str | None = None
    if credentials and credentials.credentials:
        token = credentials.credentials.strip()
    elif token_query and token_query.strip():
        token = token_query.strip()

    if not token:
        return None

    return _resolve_user_from_token(token=token, db=db)


def check_investigation_ownership(
    investigation: Investigation,
    current_user: User | None,
    db: Session,
) -> None:
    """
    Enforces multi-tenant ownership isolation:
    - Investigations attributed to system_analyst@threatweave.local (Demo Mode) are public.
    - Non-demo investigations require an authenticated user. If unauthenticated, raises 401.
    - Non-demo investigations require investigation.user_id == current_user.id.
      If mismatched, raises 404 (NotFoundError) to prevent ID enumeration.
    """
    demo_user = db.query(User).filter(User.email == "system_analyst@threatweave.local").first()
    is_demo = bool(demo_user and investigation.user_id == demo_user.id)
    if is_demo:
        return

    if not current_user:
        logger.warning("Access denied: unauthenticated request to private investigation %s", investigation.id)
        raise AuthenticationError(
            message="Authentication credentials were not provided. Authorization Bearer token required.",
            code="authentication_required",
        )

    if investigation.user_id != current_user.id:
        logger.warning(
            "Access denied (IDOR): User %s attempted to access investigation %s owned by user %s",
            current_user.id,
            investigation.id,
            investigation.user_id,
        )
        raise NotFoundError(message=f"Investigation with ID {investigation.id} was not found on this server")

