from fastapi.testclient import TestClient

from app.core.errors import NotFoundError
from app.main import app


# Add test endpoints dynamically to verify error handling without polluting production routes
@app.get("/test-not-found-error")
def trigger_not_found_error():
    raise NotFoundError(message="Test not found message", code="resource_missing")

@app.get("/test-unhandled-error")
def trigger_unhandled_error():
    raise ValueError("Triggering unhandled value error")

client = TestClient(app, raise_server_exceptions=False)

def test_health() -> None:
    """
    Assert that the unversioned health check endpoint is healthy and returns Phase 0 schema.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "threatweave-api"}

def test_v1_health() -> None:
    """
    Assert that the versioned v1 health check endpoint is healthy and returns v1 schema.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "threatweave-api",
        "version": "v1",
    }

def test_cors_headers() -> None:
    """
    Assert that request Origin matches the allowed CORS origins and returns correct headers.
    """
    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

def test_custom_error_handling() -> None:
    """
    Assert that raising custom ThreatWeaveErrors returns the standardized error JSON envelope.
    """
    response = client.get("/test-not-found-error")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "resource_missing"
    assert data["error"]["message"] == "Test not found message"
    assert data["error"]["details"] is None

def test_unhandled_error_handling() -> None:
    """
    Assert that generic exceptions are masked and return the generic "internal_error" code.
    """
    response = client.get("/test-unhandled-error")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "internal_error"
    assert data["error"]["message"] == "An unexpected error occurred on the server."
