"""
app/api/v1/endpoints/auth.py
----------------------------
Authentication endpoints for user registration, login (JWT issue), and current profile lookup.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_user_token,
    register_user,
)

logger = logging.getLogger("threatweave-api.endpoints.auth")

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account with hashed password",
)
async def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> User:
    """
    Registers a new user account.
    Hashes the password with bcrypt and stores the record in PostgreSQL.
    Returns the created user's public profile (never returning the password hash).
    """
    logger.info("Register request received for email: %s", payload.email)
    user = register_user(db=db, req=payload)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue a JWT access token",
)
async def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> TokenResponse:
    """
    Verifies user credentials (email & bcrypt password hash) and returns a signed JWT access token.
    """
    logger.info("Login request received for email: %s", payload.email)
    user = authenticate_user(db=db, req=payload)
    token_response = create_user_token(user=user)
    return token_response


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get profile of currently authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_user),  # noqa: B008
) -> User:
    """
    Returns the public profile details of the user associated with the provided Bearer token.
    """
    return current_user
