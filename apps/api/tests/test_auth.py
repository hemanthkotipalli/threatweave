"""
tests/test_auth.py
------------------
Comprehensive tests for Phase 17: Authentication & Security.
Validates:
1. User registration with bcrypt-hashed password (assert hash != raw password and starts with $2b$ or $2a$).
2. Duplicate email registration fails with HTTP 409 Conflict.
3. Login with correct credentials returns valid JWT token.
4. Login with incorrect password returns HTTP 401 via standard error envelope.
5. POST /api/v1/investigations with NO Authorization header returns HTTP 401.
6. POST /api/v1/investigations with valid token returns HTTP 201 and correctly attributes user_id in DB.
7. POST /api/v1/demo/scenarios/{key}/run with NO Authorization header returns HTTP 200 (Demo Mode remains open).
8. Expired or malformed token returns HTTP 401, not a 500 or crash.
9. Startup security check raises RuntimeError when JWT_SECRET_KEY is unset/insecure in non-development.
10. GET /api/v1/auth/me returns current user profile and NEVER exposes password_hash.
"""
from __future__ import annotations

import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import (
    create_access_token,
    validate_security_configuration,
    verify_password,
)
from app.db.session import SessionLocal
from app.main import app
from app.models.investigation import Investigation
from app.models.user import User

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    """Ensure test_auth runs against real dependencies without test overrides."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


class TestAuthenticationAndSecurity:
    """Test suite for Phase 17 Authentication & Security."""

    def test_register_creates_user_with_bcrypt_hash(self):
        """
        Asserts that registering a user creates a DB row with a valid bcrypt hash
        (starts with $2b$ or $2a$) and NEVER stores the plaintext password.
        """
        unique_email = f"analyst_{uuid.uuid4().hex[:8]}@threatweave.local"
        raw_password = "SuperSecretPassword123!"

        resp = client.post(
            "/api/v1/auth/register",
            json={"email": unique_email, "password": raw_password},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()

        # Public response must contain id, email, role, created_at, and NEVER password_hash
        assert "id" in body
        assert body["email"] == unique_email
        assert body["role"] == "analyst"
        assert "created_at" in body
        assert "password_hash" not in body
        assert "password" not in body

        # Query database directly to assert raw password is NOT stored and hash is bcrypt
        with SessionLocal() as db:
            user = db.query(User).filter(User.email == unique_email).first()
            assert user is not None
            assert user.password_hash != raw_password
            assert user.password_hash.startswith(("$2b$", "$2a$"))
            assert verify_password(raw_password, user.password_hash) is True

    def test_register_duplicate_email_fails_with_conflict(self):
        """
        Asserts that registering with an already existing email returns HTTP 409 Conflict.
        """
        email = f"duplicate_{uuid.uuid4().hex[:8]}@threatweave.local"
        # First registration
        resp1 = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "password123"},
        )
        assert resp1.status_code == 201

        # Second registration with same email
        resp2 = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "different_password"},
        )
        assert resp2.status_code == 409
        body = resp2.json()
        assert "error" in body
        assert body["error"]["code"] == "user_already_exists"
        assert "already registered" in body["error"]["message"].lower()

    def test_login_success_and_failure(self):
        """
        Asserts that login with valid credentials returns a Bearer JWT,
        while login with wrong password returns HTTP 401 via standard envelope.
        """
        email = f"login_test_{uuid.uuid4().hex[:8]}@threatweave.local"
        password = "validPassword456!"

        # Register first
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        )
        assert reg_resp.status_code == 201

        # Correct login
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 200
        token_data = login_resp.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert len(token_data["access_token"]) > 20

        # Wrong password login
        bad_pw_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrong_password!"},
        )
        assert bad_pw_resp.status_code == 401
        bad_body = bad_pw_resp.json()
        assert "error" in bad_body
        assert bad_body["error"]["code"] == "invalid_credentials"

        # Non-existent user login
        missing_user_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@threatweave.local", "password": "any"},
        )
        assert missing_user_resp.status_code == 401

    def test_get_me_endpoint(self):
        """
        Asserts that GET /api/v1/auth/me returns the profile for a valid token,
        and returns 401 without a token.
        """
        # Unauthenticated
        resp_no_auth = client.get("/api/v1/auth/me")
        assert resp_no_auth.status_code == 401

        # Create user and get token
        email = f"me_test_{uuid.uuid4().hex[:8]}@threatweave.local"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "testPassword123"},
        )
        user_id = reg.json()["id"]

        login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "testPassword123"},
        )
        token = login.json()["access_token"]

        # Authenticated
        resp_auth = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp_auth.status_code == 200
        me = resp_auth.json()
        assert me["id"] == user_id
        assert me["email"] == email
        assert me["role"] == "analyst"
        assert "password_hash" not in me

    def test_investigation_creation_unauthenticated_fails_with_401(self):
        """
        Asserts that POST /api/v1/investigations with NO Authorization header returns 401.
        """
        resp = client.post(
            "/api/v1/investigations",
            data={"title": "Unauthenticated Attempt", "text": "Some threat intel text"},
        )
        assert resp.status_code == 401
        body = resp.json()
        assert "error" in body
        assert body["error"]["code"] in ("authentication_required", "authentication_error")

    def test_investigation_creation_authenticated_attributes_real_user(self):
        """
        Asserts that POST /api/v1/investigations with a valid Bearer token returns 201,
        and the created investigation's user_id in the DB matches the authenticated user,
        NOT system_analyst.
        """
        email = f"creator_{uuid.uuid4().hex[:8]}@threatweave.local"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "creatorPassword123!"},
        )
        assert reg.status_code == 201
        user_id_str = reg.json()["id"]
        expected_user_id = uuid.UUID(user_id_str)

        login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "creatorPassword123!"},
        )
        token = login.json()["access_token"]

        # Create investigation with auth header
        create_resp = client.post(
            "/api/v1/investigations",
            headers={"Authorization": f"Bearer {token}"},
            data={"title": "Real Authenticated Investigation", "text": "Suspicious login from IP 192.168.1.1"},
        )
        assert create_resp.status_code == 201
        inv_data = create_resp.json()["investigation"]
        created_inv_id = uuid.UUID(inv_data["id"])

        # Check DB directly to confirm attribution to the registered user
        with SessionLocal() as db:
            db_inv = db.query(Investigation).filter(Investigation.id == created_inv_id).first()
            assert db_inv is not None
            assert db_inv.user_id == expected_user_id

            # Verify it is NOT assigned to system_analyst
            sys_user = db.query(User).filter(User.email == "system_analyst@threatweave.local").first()
            if sys_user:
                assert db_inv.user_id != sys_user.id

    def test_demo_scenario_run_without_auth_header_succeeds(self):
        """
        CRITICAL REGRESSION TEST:
        Asserts that POST /api/v1/demo/scenarios/{key}/run with NO Authorization header at all
        still works and returns HTTP 200, proving Demo Mode remains completely open.
        """
        resp = client.post(
            "/api/v1/demo/scenarios/phishing_email/run",
            # Explicitly NO Authorization header
        )
        assert resp.status_code == 200, f"Demo scenario run failed: {resp.text}"
        data = resp.json()
        assert "investigation_id" in data
        assert "final_risk_score" in data
        assert data["final_risk_score"] is not None

        # Confirm the demo investigation is attributed to system_analyst in DB
        demo_inv_id = uuid.UUID(data["investigation_id"])
        with SessionLocal() as db:
            db_inv = db.query(Investigation).filter(Investigation.id == demo_inv_id).first()
            assert db_inv is not None
            sys_user = db.query(User).filter(User.email == "system_analyst@threatweave.local").first()
            assert sys_user is not None
            assert db_inv.user_id == sys_user.id

    def test_expired_or_malformed_token_returns_401(self):
        """
        Asserts that invalid, malformed, or expired tokens return HTTP 401, not a 500 or crash.
        """
        # Malformed token
        resp_malformed = client.post(
            "/api/v1/investigations",
            headers={"Authorization": "Bearer invalid.token.payload"},
            data={"text": "testing with garbage token"},
        )
        assert resp_malformed.status_code == 401
        assert resp_malformed.json()["error"]["code"] in ("invalid_token", "authentication_error")

        # Expired token
        expired_token = create_access_token(
            data={"sub": str(uuid.uuid4())},
            expires_delta=timedelta(seconds=-10),  # expired 10 seconds ago
        )
        resp_expired = client.post(
            "/api/v1/investigations",
            headers={"Authorization": f"Bearer {expired_token}"},
            data={"text": "testing with expired token"},
        )
        assert resp_expired.status_code == 401
        assert resp_expired.json()["error"]["code"] in ("token_expired", "authentication_error")

    def test_security_fail_loud_in_production(self):
        """
        Asserts that validate_security_configuration() raises a clear RuntimeError
        when ENVIRONMENT != 'development' and JWT_SECRET_KEY is empty or default.
        """
        with (
            patch.object(settings, "ENVIRONMENT", "production"),
            patch.object(settings, "JWT_SECRET_KEY", "threatweave-dev-secret-key-change-in-prod"),
            pytest.raises(RuntimeError, match="CRITICAL SECURITY CONFIGURATION ERROR"),
        ):
            validate_security_configuration()

        with (
            patch.object(settings, "ENVIRONMENT", "production"),
            patch.object(settings, "JWT_SECRET_KEY", ""),
            pytest.raises(RuntimeError, match="CRITICAL SECURITY CONFIGURATION ERROR"),
        ):
            validate_security_configuration()

        # In development mode, the default secret should be accepted without raising
        with (
            patch.object(settings, "ENVIRONMENT", "development"),
            patch.object(settings, "JWT_SECRET_KEY", "threatweave-dev-secret-key-change-in-prod"),
        ):
            validate_security_configuration()  # Should not raise
