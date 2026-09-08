from __future__ import annotations

import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

# Import all models to ensure complete declarative schema registry
from app.db.base import Base  # noqa: F401
from app.main import app

# Instantiate the TestClient with raise_server_exceptions=False to test standard error response envelopes
client = TestClient(app, raise_server_exceptions=False)

# Valid 1x1 PNG bytes for testing file signature verification
VALID_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

# Text disguised as PNG to test binary signature verification failure
INVALID_PNG = b"Plain text file renamed as image.png to bypass basic type validation."


def test_multi_input_upload_success() -> None:
    """
    Asserts that text, URL, and image upload creates a single investigation
    with 3 evidence inputs and correct status mappings.
    """
    files = {
        "image": ("sample.png", io.BytesIO(VALID_PNG), "image/png")
    }
    data = {
        "title": "Multi-Input Test Task",
        "text": "Threat indicators identified inside external feed.",
        "url": "https://threatfeeds.local/intel/123"
    }

    response = client.post("/api/v1/investigations", data=data, files=files)
    
    assert response.status_code == 201
    res_data = response.json()
    
    assert "investigation" in res_data
    investigation = res_data["investigation"]
    assert investigation["title"] == "Multi-Input Test Task"
    assert investigation["status"] == "pending"
    assert "id" in investigation

    assert "evidence_inputs" in res_data
    evidence_inputs = res_data["evidence_inputs"]
    assert len(evidence_inputs) == 3

    # Check modalities are created and mapped correctly
    modalities = {item["modality"] for item in evidence_inputs}
    assert modalities == {"text", "url", "image"}


def test_single_input_text_only_success() -> None:
    """
    Asserts that sending only text input executes successfully.
    """
    data = {
        "text": "Single input warning description."
    }

    response = client.post("/api/v1/investigations", data=data)
    
    assert response.status_code == 201
    res_data = response.json()
    
    investigation = res_data["investigation"]
    assert investigation["title"] == "Untitled investigation"  # default title
    
    evidence_inputs = res_data["evidence_inputs"]
    assert len(evidence_inputs) == 1
    assert evidence_inputs[0]["modality"] == "text"


def test_no_input_provided_failure() -> None:
    """
    Asserts that sending empty inputs returns HTTP 422 standard validation error.
    """
    response = client.post("/api/v1/investigations", data={})
    
    assert response.status_code == 422
    res_data = response.json()
    
    assert "error" in res_data
    error = res_data["error"]
    assert error["code"] == "validation_error"
    assert "At least one evidence input" in error["message"]


def test_oversized_file_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Asserts that an oversized file raises an HTTP 422 validation error.
    Patches settings.MAX_IMAGE_SIZE_MB to 0 to simulate file size limit violations.
    """
    monkeypatch.setattr(settings, "MAX_IMAGE_SIZE_MB", 0)

    files = {
        "image": ("large.png", io.BytesIO(VALID_PNG), "image/png")
    }
    data = {
        "title": "Oversized File Test"
    }

    response = client.post("/api/v1/investigations", data=data, files=files)
    
    assert response.status_code == 422
    res_data = response.json()
    
    assert "error" in res_data
    error = res_data["error"]
    assert error["code"] == "file_too_large"
    assert "exceeds maximum limit" in error["message"]


def test_invalid_file_signature_failure() -> None:
    """
    Asserts that uploading a file with an invalid signature (e.g. text disguised as PNG)
    triggers HTTP 422 validation error.
    """
    files = {
        "image": ("fake.png", io.BytesIO(INVALID_PNG), "image/png")
    }
    data = {
        "title": "Spoofed Signature Test"
    }

    response = client.post("/api/v1/investigations", data=data, files=files)
    
    assert response.status_code == 422
    res_data = response.json()
    
    assert "error" in res_data
    error = res_data["error"]
    assert error["code"] == "invalid_file_format"
    assert "Invalid image file format" in error["message"]


def test_get_investigation_roundtrip() -> None:
    """
    Asserts that an investigation can be created and retrieved successfully.
    """
    # 1. Create the task first
    data = {"text": "Roundtrip test feed metadata."}
    create_res = client.post("/api/v1/investigations", data=data)
    assert create_res.status_code == 201
    
    created_id = create_res.json()["investigation"]["id"]

    # 2. Query the detail endpoint
    get_res = client.get(f"/api/v1/investigations/{created_id}")
    assert get_res.status_code == 200
    detail_data = get_res.json()
    
    assert detail_data["id"] == created_id
    assert detail_data["title"] == "Untitled investigation"
    assert detail_data["status"] == "pending"
    
    # Assert full evidence inputs detail is included
    assert "evidence_inputs" in detail_data
    evidence_inputs = detail_data["evidence_inputs"]
    assert len(evidence_inputs) == 1
    assert evidence_inputs[0]["modality"] == "text"
    assert evidence_inputs[0]["raw_content_ref"] == "Roundtrip test feed metadata."
    assert evidence_inputs[0]["file_path"] is None


def test_get_nonexistent_investigation_not_found() -> None:
    """
    Asserts that fetching a nonexistent UUID returns HTTP 404 standard NotFound error.
    """
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/api/v1/investigations/{random_uuid}")
    
    assert response.status_code == 404
    res_data = response.json()
    
    assert "error" in res_data
    error = res_data["error"]
    assert error["code"] == "not_found"
    assert "was not found" in error["message"]
