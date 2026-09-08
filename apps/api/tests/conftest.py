"""
apps/api/tests/conftest.py
--------------------------
Pytest fixtures and configuration for ThreatWeave API test suite.
Injects a REAL, cryptographically valid JWT Bearer token into TestClient requests
for legacy pre-existing test suites so that the genuine `get_current_user` dependency,
JWT signature decoding, and database user lookup are exercised on every call.
Allows `test_auth.py` to test unauthenticated and malformed token requests without injection.
"""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.models.user import User


@pytest.fixture(scope="session", autouse=True)
def ensure_legacy_test_user():
    """Ensure a persistent test analyst exists in DB and issue a real signed JWT."""
    with SessionLocal() as db:
        test_user = db.query(User).filter(User.email == "legacy_test_analyst@threatweave.local").first()
        if not test_user:
            test_user = User(
                email="legacy_test_analyst@threatweave.local",
                password_hash=hash_password("LegacyTestPass123!"),
                role="analyst",
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)

        token = create_access_token({
            "sub": str(test_user.id),
            "email": test_user.email,
            "role": test_user.role,
        })

    return token


@pytest.fixture(autouse=True)
def inject_real_jwt_for_legacy_tests(request, ensure_legacy_test_user):
    """
    For non-auth tests, injects the real valid JWT into TestClient.request headers
    if no Authorization header was explicitly specified.
    This guarantees that the genuine `get_current_user` dependency, PyJWT decoding,
    and DB user resolution run on every single legacy test request.
    """
    if "test_auth" in request.node.nodeid:
        # test_auth controls its own headers to test 401s and custom tokens
        yield
        return

    real_token = ensure_legacy_test_user
    orig_request = TestClient.request

    def _request_with_real_jwt(self, method, url, **kwargs):
        headers = dict(kwargs.get("headers") or {})
        if "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {real_token}"
            kwargs["headers"] = headers
        return orig_request(self, method, url, **kwargs)

    TestClient.request = _request_with_real_jwt
    try:
        yield
    finally:
        TestClient.request = orig_request
