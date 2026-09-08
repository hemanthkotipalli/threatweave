"""
app/services/auth_service.py
----------------------------
Authentication business logic: user registration, credential verification, and JWT generation.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError, ConflictError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest

logger = logging.getLogger("threatweave-api.auth")


def register_user(db: Session, req: UserRegisterRequest) -> User:
    """
    Registers a new user account with bcrypt-hashed password.
    Raises ConflictError (HTTP 409) if the email address is already taken.
    """
    email_clean = str(req.email).strip().lower()
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        logger.warning("Registration rejected: email %s is already registered", email_clean)
        raise ConflictError(
            message=f"User with email '{email_clean}' is already registered.",
            code="user_already_exists",
        )

    hashed_pw = hash_password(req.password)
    user = User(
        email=email_clean,
        password_hash=hashed_pw,
        role="analyst",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("User registered successfully: id=%s, email=%s", user.id, user.email)
    return user


def authenticate_user(db: Session, req: UserLoginRequest) -> User:
    """
    Authenticates user credentials against the database.
    Raises AuthenticationError (HTTP 401) on non-existent email or invalid password.
    """
    email_clean = str(req.email).strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user:
        logger.warning("Authentication failed: user with email %s not found", email_clean)
        raise AuthenticationError(
            message="Invalid email or password.",
            code="invalid_credentials",
        )

    if not verify_password(req.password, user.password_hash):
        logger.warning("Authentication failed: incorrect password for email %s", email_clean)
        raise AuthenticationError(
            message="Invalid email or password.",
            code="invalid_credentials",
        )

    logger.info("User authenticated successfully: id=%s, email=%s", user.id, user.email)
    return user


def create_user_token(user: User) -> TokenResponse:
    """
    Issues a signed JWT access token for an authenticated user.
    """
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    }
    access_token = create_access_token(data=payload)
    return TokenResponse(access_token=access_token, token_type="bearer")
