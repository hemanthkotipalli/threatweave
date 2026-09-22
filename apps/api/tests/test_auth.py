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


class TestIdorAndOwnershipIsolation:
    """
    Comprehensive regression test suite for IDOR vulnerability prevention
    and multi-tenant ownership isolation across all investigation endpoints.
    """

    @pytest.fixture
    def two_users(self):
        """Creates two distinct authenticated users with valid JWT tokens."""
        uid_a = uuid.uuid4().hex[:6]
        uid_b = uuid.uuid4().hex[:6]
        email_a = f"owner_a_{uid_a}@threatweave.test"
        email_b = f"intruder_b_{uid_b}@threatweave.test"
        pwd = "SecurePassword123!"

        client.post("/api/v1/auth/register", json={"email": email_a, "password": pwd})
        client.post("/api/v1/auth/register", json={"email": email_b, "password": pwd})

        login_a = client.post("/api/v1/auth/login", json={"email": email_a, "password": pwd})
        login_b = client.post("/api/v1/auth/login", json={"email": email_b, "password": pwd})

        token_a = login_a.json()["access_token"]
        token_b = login_b.json()["access_token"]

        return {
            "token_a": token_a,
            "headers_a": {"Authorization": f"Bearer {token_a}"},
            "token_b": token_b,
            "headers_b": {"Authorization": f"Bearer {token_b}"},
        }

    def test_owner_can_access_own_investigation(self, two_users):
        """
        Proof (a): The owner (User A) can access their own investigation normally:
        - GET /api/v1/investigations/{id} -> 200 OK
        - GET /api/v1/investigations/{id}/report -> 200 OK
        - GET /api/v1/investigations/{id}/report/pdf -> 200 OK
        - POST /api/v1/investigations/{id}/analyze -> 200 OK
        """
        create_res = client.post(
            "/api/v1/investigations",
            data={"title": "User A Private Case", "text": "Confidential internal investigation"},
            headers=two_users["headers_a"],
        )
        assert create_res.status_code == 201
        inv_id = create_res.json()["investigation"]["id"]

        # 1. Detail endpoint
        res_get = client.get(f"/api/v1/investigations/{inv_id}", headers=two_users["headers_a"])
        assert res_get.status_code == 200
        assert res_get.json()["title"] == "User A Private Case"

        # 2. JSON Report endpoint
        res_rep = client.get(f"/api/v1/investigations/{inv_id}/report", headers=two_users["headers_a"])
        assert res_rep.status_code == 200
        assert res_rep.json()["investigation"]["title"] == "User A Private Case"

        # 3. PDF Report endpoint (header)
        res_pdf = client.get(f"/api/v1/investigations/{inv_id}/report/pdf", headers=two_users["headers_a"])
        assert res_pdf.status_code == 200
        assert res_pdf.headers["content-type"] == "application/pdf"

        # 3b. PDF Report endpoint via ?token= query param
        res_pdf_param = client.get(f"/api/v1/investigations/{inv_id}/report/pdf?token={two_users['token_a']}")
        assert res_pdf_param.status_code == 200
        assert res_pdf_param.headers["content-type"] == "application/pdf"

        # 4. Swarm analyze endpoint
        with patch("app.api.v1.endpoints.orchestration.run_investigation_analysis") as mock_run:
            mock_run.return_value = {
                "investigation_id": inv_id,
                "status": "completed",
                "active_agents": [],
                "agent_runs": [],
                "findings_count": 0,
            }
            res_analyze = client.post(f"/api/v1/investigations/{inv_id}/analyze", headers=two_users["headers_a"])
            assert res_analyze.status_code == 200

    def test_different_authenticated_user_gets_404_idor_rejection(self, two_users):
        """
        Proof (b): A different authenticated user (User B) attempting to access
        User A's investigation is rejected with HTTP 404 (not 403) across all endpoints:
        - GET /api/v1/investigations/{id} -> 404 Not Found
        - GET /api/v1/investigations/{id}/report -> 404 Not Found
        - GET /api/v1/investigations/{id}/report/pdf -> 404 Not Found
        - POST /api/v1/investigations/{id}/analyze -> 404 Not Found
        """
        create_res = client.post(
            "/api/v1/investigations",
            data={"title": "User A Private Case 2", "text": "Secret confidential payload"},
            headers=two_users["headers_a"],
        )
        assert create_res.status_code == 201
        inv_id = create_res.json()["investigation"]["id"]

        # 1. Detail endpoint - User B gets 404
        res_get = client.get(f"/api/v1/investigations/{inv_id}", headers=two_users["headers_b"])
        assert res_get.status_code == 404, f"Expected 404, got {res_get.status_code}: {res_get.text}"
        assert "not found" in res_get.json()["error"]["message"].lower()

        # 2. JSON Report endpoint - User B gets 404
        res_rep = client.get(f"/api/v1/investigations/{inv_id}/report", headers=two_users["headers_b"])
        assert res_rep.status_code == 404, f"Expected 404, got {res_rep.status_code}: {res_rep.text}"
        assert "not found" in res_rep.json()["error"]["message"].lower()

        # 3. PDF Report endpoint - User B gets 404
        res_pdf = client.get(f"/api/v1/investigations/{inv_id}/report/pdf", headers=two_users["headers_b"])
        assert res_pdf.status_code == 404, f"Expected 404, got {res_pdf.status_code}: {res_pdf.text}"

        # 4. Swarm analyze endpoint - User B gets 404
        res_analyze = client.post(f"/api/v1/investigations/{inv_id}/analyze", headers=two_users["headers_b"])
        assert res_analyze.status_code == 404, f"Expected 404, got {res_analyze.status_code}: {res_analyze.text}"

    def test_unauthenticated_request_gets_401_on_private_investigation(self, two_users):
        """
        Proof (c): An unauthenticated request attempting to access a private investigation
        is rejected with HTTP 401 across all endpoints:
        - GET /api/v1/investigations/{id} -> 401 Unauthorized
        - GET /api/v1/investigations/{id}/report -> 401 Unauthorized
        - GET /api/v1/investigations/{id}/report/pdf -> 401 Unauthorized
        - POST /api/v1/investigations/{id}/analyze -> 401 Unauthorized
        """
        create_res = client.post(
            "/api/v1/investigations",
            data={"title": "User A Private Case 3", "text": "Secret confidential payload"},
            headers=two_users["headers_a"],
        )
        assert create_res.status_code == 201
        inv_id = create_res.json()["investigation"]["id"]

        # 1. Detail endpoint - unauthenticated gets 401
        res_get = client.get(f"/api/v1/investigations/{inv_id}")
        assert res_get.status_code == 401, f"Expected 401, got {res_get.status_code}: {res_get.text}"

        # 2. JSON Report endpoint - unauthenticated gets 401
        res_rep = client.get(f"/api/v1/investigations/{inv_id}/report")
        assert res_rep.status_code == 401, f"Expected 401, got {res_rep.status_code}: {res_rep.text}"

        # 3. PDF Report endpoint - unauthenticated gets 401
        res_pdf = client.get(f"/api/v1/investigations/{inv_id}/report/pdf")
        assert res_pdf.status_code == 401, f"Expected 401, got {res_pdf.status_code}: {res_pdf.text}"

        # 4. Swarm analyze endpoint - unauthenticated gets 401
        res_analyze = client.post(f"/api/v1/investigations/{inv_id}/analyze")
        assert res_analyze.status_code == 401, f"Expected 401, got {res_analyze.status_code}: {res_analyze.text}"

    def test_list_investigations_filters_to_own_investigations_only(self, two_users):
        """
        Proof that GET /api/v1/investigations filters strictly to the current user's
        own investigations, preventing cross-tenant list exposure.
        """
        title_a = f"User A Specific Inv - {uuid.uuid4().hex[:6]}"
        title_b = f"User B Specific Inv - {uuid.uuid4().hex[:6]}"

        client.post(
            "/api/v1/investigations",
            data={"title": title_a, "text": "Evidence for A"},
            headers=two_users["headers_a"],
        )
        client.post(
            "/api/v1/investigations",
            data={"title": title_b, "text": "Evidence for B"},
            headers=two_users["headers_b"],
        )

        # User A lists investigations: sees title_a, does NOT see title_b
        res_a = client.get("/api/v1/investigations", headers=two_users["headers_a"])
        assert res_a.status_code == 200
        titles_a = [item["title"] for item in res_a.json()["items"]]
        assert title_a in titles_a
        assert title_b not in titles_a

        # User B lists investigations: sees title_b, does NOT see title_a
        res_b = client.get("/api/v1/investigations", headers=two_users["headers_b"])
        assert res_b.status_code == 200
        titles_b = [item["title"] for item in res_b.json()["items"]]
        assert title_b in titles_b
        assert title_a not in titles_b

        # Unauthenticated request lists investigations: does NOT see either private title
        res_anon = client.get("/api/v1/investigations")
        assert res_anon.status_code == 200
        titles_anon = [item["title"] for item in res_anon.json()["items"]]
        assert title_a not in titles_anon
        assert title_b not in titles_anon

    def test_demo_investigations_remain_publicly_viewable_without_auth(self, two_users):
        """
        Proof that Demo Mode investigations (attributed to system_analyst)
        remain viewable without authentication across detail and report endpoints.
        """
        from app.services.ingestion_service import ingest_investigation
        with SessionLocal() as db:
            demo_inv = ingest_investigation(
                db=db,
                title="Demo Public Phishing Lure",
                text="Demo sample phishing email",
                is_demo=True,
            )
            demo_id = str(demo_inv.id)

        # Unauthenticated can view demo investigation detail
        res_get = client.get(f"/api/v1/investigations/{demo_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == demo_id

        # Unauthenticated can view demo investigation report
        res_rep = client.get(f"/api/v1/investigations/{demo_id}/report")
        assert res_rep.status_code == 200

        # Unauthenticated can download demo investigation PDF
        res_pdf = client.get(f"/api/v1/investigations/{demo_id}/report/pdf")
        assert res_pdf.status_code == 200
        assert res_pdf.headers["content-type"] == "application/pdf"

        # Authenticated User B can also view demo investigation
        res_user_b = client.get(f"/api/v1/investigations/{demo_id}", headers=two_users["headers_b"])
        assert res_user_b.status_code == 200

