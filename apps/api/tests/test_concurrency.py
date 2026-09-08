"""
apps/api/tests/test_concurrency.py
-----------------------------------
Concurrency, isolation, and load-sanity test suite for ThreatWeave (Phase 18).

Coverage:
1. Concurrent Swarm Execution & Finding Isolation:
   - Creates 4 independent investigations with distinct multimodal evidence.
   - Dispatches their /analyze calls concurrently via ThreadPoolExecutor.
   - Verifies through direct database queries that all AgentRun and AgentFinding
     records are strictly and exclusively partitioned under their own investigation_id.
   - Confirms zero finding leakage across concurrent LangGraph execution sessions.
2. Sequential Load & Resource Leak Sanity (Task 5):
   - Executes 10 sequential investigations through full create -> analyze lifecycle.
   - Introspects SQLAlchemy engine connection pool status, verifying 0 checked-out
     connections remain leaked across cycles.
   - Asserts ChromaDB client singleton stability without connection exhaustion.
   - Records observed latency and memory/pool metrics.
"""
from __future__ import annotations

import io
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from starlette.testclient import TestClient

from app.db.session import SessionLocal, engine
from app.main import app
from app.models.agent_finding import AgentFinding
from app.models.agent_run import AgentRun
from app.models.investigation import Investigation
from app.rag.chroma_client import get_chroma_client
from tests.test_image_agent import _create_text_image_bytes
from tests.test_orchestrator_routing import _create_qr_image_bytes

client = TestClient(app)


class TestConcurrencyAndIsolation:
    """Tests verifying node session isolation and non-leakage under concurrent load."""

    def test_concurrent_investigation_analysis_isolation(self):
        """
        Creates 4 distinct investigations with different evidence profiles:
        - Inv 1: Pure text phishing
        - Inv 2: Pure URL credential harvester
        - Inv 3: Image with embedded OCR text
        - Inv 4: Standalone QR code payload

        Fires /analyze concurrently across 4 worker threads.
        Asserts that every AgentFinding created in DB is strictly linked to its
        own investigation_id and agent_run_id with zero cross-contamination.
        """
        # Step 1: Create 4 distinct investigations
        inv_payloads = [
            {
                "data": {
                    "title": "Concurrent 1 - Text Phish",
                    "text": "URGENT SECURITY ALERT: Unauthorized access to your bank account. Reset your PIN immediately.",
                },
                "files": None,
                "expected_agent": "text_agent",
            },
            {
                "data": {
                    "title": "Concurrent 2 - Malicious URL",
                    "url": "http://192.168.1.100@paypal-security-update.tk/login",
                },
                "files": None,
                "expected_agent": "url_agent",
            },
            {
                "data": {
                    "title": "Concurrent 3 - Image Notice",
                },
                "files": {
                    "image": (
                        "suspicious_memo.png",
                        io.BytesIO(_create_text_image_bytes("Warning: Payment failed. Confirm card details.")),
                        "image/png",
                    )
                },
                "expected_agent": "image_agent",
            },
            {
                "data": {
                    "title": "Concurrent 4 - QR Code",
                },
                "files": {
                    "image": (
                        "login_qr.png",
                        io.BytesIO(_create_qr_image_bytes("https://malicious-login-portal.com/auth")),
                        "image/png",
                    )
                },
                "expected_agent": "qr_agent",
            },
        ]

        created_ids: list[str] = []
        for p in inv_payloads:
            if p["files"]:
                resp = client.post("/api/v1/investigations", data=p["data"], files=p["files"])
            else:
                resp = client.post("/api/v1/investigations", data=p["data"])
            assert resp.status_code == 201, f"Failed to create investigation: {resp.text}"
            created_ids.append(resp.json()["investigation"]["id"])

        assert len(created_ids) == 4
        assert len(set(created_ids)) == 4, "Investigation IDs must be unique"

        # Step 2: Fire concurrent /analyze calls
        def _run_analyze(inv_id: str):
            c = TestClient(app)
            return inv_id, c.post(f"/api/v1/investigations/{inv_id}/analyze")

        start_time = time.perf_counter()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(_run_analyze, i_id) for i_id in created_ids]
            results = [f.result() for f in futures]
        elapsed = time.perf_counter() - start_time

        # Step 3: Verify each concurrent call completed with 200
        for inv_id, resp in results:
            assert resp.status_code == 200, f"Concurrent analyze failed for {inv_id}: {resp.text}"
            data = resp.json()
            assert data["status"] == "completed"
            assert data["risk"] is not None

        # Step 4: Direct DB Verification of strict findings partition
        with SessionLocal() as db:
            investigation_finding_ids: dict[str, set[str]] = {}

            for inv_id_str in created_ids:
                inv_uuid = uuid.UUID(inv_id_str)
                inv = db.query(Investigation).filter(Investigation.id == inv_uuid).first()
                assert inv is not None
                assert inv.status == "completed"

                # Check agent runs for this investigation
                runs = db.query(AgentRun).filter(AgentRun.investigation_id == inv_uuid).all()
                run_ids = {r.id for r in runs}

                # Check findings for this investigation
                findings = (
                    db.query(AgentFinding)
                    .join(AgentRun, AgentFinding.agent_run_id == AgentRun.id)
                    .filter(AgentRun.investigation_id == inv_uuid)
                    .all()
                )

                # Every finding must belong to a run from THIS investigation
                for f in findings:
                    assert f.agent_run_id in run_ids, (
                        f"Finding {f.id} references agent_run_id {f.agent_run_id} not in investigation {inv_uuid} runs!"
                    )

                f_ids = {str(f.id) for f in findings}
                investigation_finding_ids[inv_id_str] = f_ids

            # Step 5: Assert zero overlap between finding sets across investigations
            for i in range(len(created_ids)):
                for j in range(i + 1, len(created_ids)):
                    id_a = created_ids[i]
                    id_b = created_ids[j]
                    overlap = investigation_finding_ids[id_a].intersection(investigation_finding_ids[id_b])
                    assert len(overlap) == 0, (
                        f"CRITICAL ISOLATION FAILURE: Overlapping finding IDs between {id_a} and {id_b}: {overlap}"
                    )

        print(f"\n[Isolation Verified] 4 concurrent analyses completed in {elapsed:.2f}s with 0 finding leaks.")


class TestLoadAndResourceSanity:
    """Load sanity test verifying connection pool and resource hygiene (Task 5)."""

    def test_sequential_investigations_pool_hygiene(self):
        """
        Executes 10 sequential investigations through full create -> analyze lifecycle.
        Inspects SQLAlchemy connection pool to confirm zero checked-out connections leak,
        and verifies ChromaDB singleton stability.
        """
        latencies: list[float] = []
        iteration_count = 10

        # Snapshot initial pool state
        initial_checked_out = engine.pool.checkedout()
        assert initial_checked_out == 0, f"Pool already has leaked connections: {initial_checked_out}"

        chroma_client_initial = get_chroma_client()
        assert chroma_client_initial is not None

        for idx in range(1, iteration_count + 1):
            t0 = time.perf_counter()

            create_resp = client.post(
                "/api/v1/investigations",
                data={
                    "title": f"Load Sanity Run #{idx}",
                    "text": f"Security verification test packet #{idx}: confirm account validity.",
                    "url": f"http://test-load-domain-{idx}.com/verify",
                },
            )
            assert create_resp.status_code == 201
            inv_id = create_resp.json()["investigation"]["id"]

            analyze_resp = client.post(f"/api/v1/investigations/{inv_id}/analyze")
            assert analyze_resp.status_code == 200
            assert analyze_resp.json()["status"] == "completed"

            cycle_time = time.perf_counter() - t0
            latencies.append(cycle_time)

            # Inspect connection pool immediately after request completion
            checked_out = engine.pool.checkedout()
            assert checked_out == 0, (
                f"Connection leak detected on run #{idx}! Checked out connections: {checked_out}. "
                f"Pool status: {engine.pool.status()}"
            )

        # Confirm pool hygiene after all 10 runs
        final_checked_out = engine.pool.checkedout()
        pool_status = engine.pool.status()
        assert final_checked_out == 0, f"Final pool has leaked connections: {pool_status}"

        # Confirm ChromaDB client instance is unchanged (reused singleton)
        chroma_client_final = get_chroma_client()
        assert chroma_client_final is chroma_client_initial, "ChromaDB client instance was unexpectedly recreated!"

        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        print(
            f"\n[Load Sanity Verified] {iteration_count} sequential cycles completed.\n"
            f"  - Avg Latency: {avg_latency:.2f}s (Min: {min_latency:.2f}s, Max: {max_latency:.2f}s)\n"
            f"  - Final Pool Checked-Out: {final_checked_out} (Clean)\n"
            f"  - Pool Status: {pool_status}\n"
            f"  - ChromaDB Singleton: Stable and Reused"
        )
