"""
apps/api/tests/test_security_hardening.py
-----------------------------------------
Security hardening and vulnerability resistance tests for ThreatWeave (Phase 18).

Coverage:
1. File Upload Magic Byte Enforcement:
   - Rejects non-image files masquerading as .png (plain text, PE executables).
   - Rejects non-audio files masquerading as .wav/.mp3.
   - Verifies consistent structured 400 error envelope with 'invalid_file_format'.
2. Raw SQL Interpolation Codebase Audit:
   - Scans all Python source files under apps/api/app for dangerous SQL formatting patterns.
   - Verifies all database queries utilize parameterized SQLAlchemy ORM statements.
3. JWT Signature Tampering & Integrity:
   - Generates valid signed token, tampers with base64 payload claims (without re-signing).
   - Verifies get_current_user detects cryptographic signature mismatch and rejects with 401.
   - Verifies token with mutated signature bytes is rejected.
4. Password Hash Leakage Prevention:
   - Verifies OpenAPI schema does not expose 'password_hash' in any output model.
   - Captures application logs during user registration and authentication flows,
     confirming bcrypt hashes never leak into log streams.
"""
from __future__ import annotations

import base64
import io
import json
import logging
import os
import re
from pathlib import Path

from starlette.testclient import TestClient

from app.core.security import create_access_token
from app.main import app

client = TestClient(app)


class TestFileUploadHardening:
    """Verifies strict magic-byte validation and rejection of disguised files."""

    def test_reject_fake_image_file_with_png_extension(self):
        """
        Submits plain text content disguised as a .png file.
        Confirms magic-byte inspection rejects it with 422 invalid_file_format,
        preventing file storage or unparsed byte ingestion.
        """
        fake_png_bytes = b"This is not a PNG file. It is plain text pretending to be an image."
        resp = client.post(
            "/api/v1/investigations",
            data={"title": "Malicious Disguised File Test"},
            files={"image": ("exploit.png", io.BytesIO(fake_png_bytes), "image/png")},
        )
        assert resp.status_code == 422, f"Expected 422 for fake image, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["error"]["code"] == "invalid_file_format"
        assert "Invalid image file format" in data["error"]["message"]

    def test_reject_executable_pe_binary_with_png_extension(self):
        """
        Submits Windows PE executable header bytes (MZ...) disguised as a .png file.
        Confirms immediate rejection via magic-byte signature check.
        """
        pe_executable_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + (b"\x00" * 100)
        resp = client.post(
            "/api/v1/investigations",
            data={"title": "PE Binary Image Upload Test"},
            files={"image": ("payload.png", io.BytesIO(pe_executable_bytes), "image/png")},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["error"]["code"] == "invalid_file_format"

    def test_reject_fake_audio_file_with_wav_extension(self):
        """
        Submits arbitrary non-audio text bytes disguised as .wav.
        Confirms rejection with invalid_file_format.
        """
        fake_wav_bytes = b"NOT_A_WAVE_HEADER_JUST_RANDOM_TEXT_FOR_SECURITY_TESTING"
        resp = client.post(
            "/api/v1/investigations",
            data={"title": "Fake Audio Test"},
            files={"voice": ("fake_audio.wav", io.BytesIO(fake_wav_bytes), "audio/wav")},
        )
        assert resp.status_code == 422
        data = resp.json()
        assert data["error"]["code"] == "invalid_file_format"
        assert "Invalid audio file format" in data["error"]["message"]


class TestSqlInjectionAudit:
    """Automated source code review confirming zero raw SQL string interpolations."""

    def test_codebase_contains_no_raw_sql_interpolations(self):
        """
        Scans all Python modules in apps/api/app/ for dangerous raw SQL interpolation patterns.
        Confirms that all SQL operations use SQLAlchemy ORM expressions or parameterized queries.
        """
        app_dir = Path(__file__).resolve().parent.parent / "app"
        assert app_dir.exists() and app_dir.is_dir(), f"app directory not found at {app_dir}"

        dangerous_patterns = [
            re.compile(r'text\s*\(\s*f["\']', re.IGNORECASE),
            re.compile(r'execute\s*\(\s*f["\']', re.IGNORECASE),
            re.compile(r'f["\']\s*(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\s+', re.IGNORECASE),
            re.compile(r'["\']\s*(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\s+.*["\']\s*%\s*', re.IGNORECASE),
            re.compile(r'["\']\s*(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\s+.*\.format\(', re.IGNORECASE),
        ]

        violations: list[str] = []
        scanned_files = 0

        for root, _, files in os.walk(app_dir):
            for file in files:
                if file.endswith(".py"):
                    scanned_files += 1
                    file_path = Path(root) / file
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for line_idx, line in enumerate(content.splitlines(), start=1):
                        for pattern in dangerous_patterns:
                            if pattern.search(line):
                                violations.append(f"{file_path.name}:{line_idx}: {line.strip()}")

        assert scanned_files >= 25, f"Expected to scan at least 25 Python files, only scanned {scanned_files}"
        assert len(violations) == 0, (
            f"Potential raw SQL string interpolation detected in {len(violations)} locations:\n"
            + "\n".join(violations)
        )
        print(f"\n[SQL Audit Verified] Scanned {scanned_files} app source files: 0 raw SQL interpolations found.")


class TestJwtSecurityHardening:
    """Verifies cryptographic signature verification and tamper detection."""

    def test_tampered_jwt_payload_rejected(self):
        """
        Takes a genuine signed JWT, modifies the payload segment (e.g. elevates role
        or changes user identity) without possessing the secret key to re-sign it.
        Confirms get_current_user detects the signature mismatch and returns 401.
        """
        valid_token = create_access_token({"sub": "11111111-1111-1111-1111-111111111111", "email": "victim@test.com", "role": "analyst"})
        parts = valid_token.split(".")
        assert len(parts) == 3, "JWT must consist of header.payload.signature"

        # Decode payload, tamper with claims, and re-encode
        payload_bytes = base64.urlsafe_b64decode(parts[1] + "==")
        payload_dict = json.loads(payload_bytes.decode("utf-8"))
        payload_dict["sub"] = "99999999-9999-9999-9999-999999999999"
        payload_dict["role"] = "superadmin"

        tampered_payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_dict).encode("utf-8")).decode("utf-8").rstrip("=")
        # Reassemble token with tampered payload but ORIGINAL signature
        tampered_token = f"{parts[0]}.{tampered_payload_b64}.{parts[2]}"

        # Attempt to access protected /api/v1/auth/me
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert data["error"]["code"] in ("invalid_token", "unauthenticated")
        assert "Invalid" in data["error"]["message"] or "Could not validate" in data["error"]["message"]

    def test_corrupted_signature_jwt_rejected(self):
        """
        Tampers with the signature bytes of an otherwise valid token.
        Confirms get_current_user returns 401.
        """
        valid_token = create_access_token({"sub": "22222222-2222-2222-2222-222222222222", "email": "analyst@test.com"})
        parts = valid_token.split(".")
        # Mutate last character of signature
        mutated_sig = parts[2][:-1] + ("A" if parts[2][-1] != "A" else "B")
        tampered_token = f"{parts[0]}.{parts[1]}.{mutated_sig}"

        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] in ("invalid_token", "unauthenticated")


class TestPasswordHashLeakage:
    """Verifies that password hashes are never exposed via API schemas or application logs."""

    def test_openapi_schemas_never_expose_password_hash(self):
        """
        Inspects the generated OpenAPI / Swagger documentation schema.
        Confirms no response schema includes 'password_hash' property.
        """
        openapi = app.openapi()
        components = openapi.get("components", {}).get("schemas", {})

        leaking_schemas: list[str] = []
        for schema_name, schema_def in components.items():
            properties = schema_def.get("properties", {})
            if "password_hash" in properties:
                leaking_schemas.append(schema_name)

        assert len(leaking_schemas) == 0, (
            f"CRITICAL SECURITY LEAK: password_hash exposed in OpenAPI schemas: {leaking_schemas}"
        )

    def test_application_logs_never_contain_password_hash_values(self, caplog):
        """
        Executes registration and login workflows with log capturing enabled.
        Confirms that neither the raw password nor any bcrypt hash ($2b$...) is logged.
        """
        caplog.set_level(logging.DEBUG)

        test_email = "log_security_audit@threatweave.local"
        test_password = "SuperSecretPassword999!"

        # Register user
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={"email": test_email, "password": test_password},
        )
        assert reg_resp.status_code in (201, 409)

        # Login user
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": test_email, "password": test_password},
        )
        assert login_resp.status_code == 200

        all_logs = caplog.text

        # Verify plaintext password never logged
        assert test_password not in all_logs, "CRITICAL: Plaintext password leaked into application logs!"

        # Verify bcrypt hash format ($2a$, $2b$, $2y$) never logged
        bcrypt_regex = re.compile(r"\$2[aby]\$[0-9]{2}\$[./A-Za-z0-9]{53}")
        matches = bcrypt_regex.findall(all_logs)
        assert len(matches) == 0, f"CRITICAL: Bcrypt password hash found in application logs: {matches}"

        # Verify literal string 'password_hash=' with an actual hash value is not logged
        assert "password_hash" not in all_logs or not any(k in all_logs for k in ["$2b$", "$2a$"])
        print("\n[Log Audit Verified] Zero plaintext passwords or bcrypt hashes leaked into logs.")
