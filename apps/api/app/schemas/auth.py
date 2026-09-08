"""
app/schemas/auth.py
-------------------
Pydantic schemas for authentication and user account management.
Never includes sensitive data like password_hash in response models.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserRegisterRequest(BaseModel):
    """
    Schema for new user account registration.
    """
    email: str = Field(
        ...,
        pattern=EMAIL_REGEX,
        description="User's unique email address",
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Plaintext password for account creation (minimum 6 characters)",
    )


class UserLoginRequest(BaseModel):
    """
    Schema for user authentication and login.
    """
    email: str = Field(
        ...,
        pattern=EMAIL_REGEX,
        description="Registered user email address",
    )
    password: str = Field(..., min_length=1, description="Account password")



class TokenResponse(BaseModel):
    """
    Schema returned upon successful authentication containing JWT credentials.
    """
    access_token: str = Field(..., description="Signed JSON Web Token (JWT)")
    token_type: str = Field("bearer", description="Token authentication scheme")


class UserResponse(BaseModel):
    """
    Public representation of a User entity (excludes password hash).
    """
    id: uuid.UUID = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User's email address")
    role: str = Field(..., description="User access role (e.g. analyst, admin)")
    created_at: datetime = Field(..., description="Timestamp of account creation")

    model_config = ConfigDict(from_attributes=True)
