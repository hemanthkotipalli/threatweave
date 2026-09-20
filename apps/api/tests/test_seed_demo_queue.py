"""
apps/api/tests/test_seed_demo_queue.py
--------------------------------------
Automated test suite for the demo queue seeding and database reset utility.
Verifies archive creation, dry-run safety, idempotency, and data completeness.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import Severity
from app.models.investigation import Investigation
from app.models.user import User
from scripts.seed_demo_queue import (
    CURATED_INCIDENTS,
    archive_existing_investigations,
    ensure_seed_user,
    run_reset_and_seed,
    seed_curated_queue,
)


@pytest.fixture
def db_session():
    """Provides a transactional database session for unit testing."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def temp_archive_dir(tmp_path: Path):
    """Provides an isolated temporary directory for test archive outputs."""
    archive_dir = tmp_path / "archives"
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


class TestSeedDemoQueue:
    """Test suite validating safety, idempotency, and data completeness of seed script."""

    def test_archive_existing_investigations_writes_valid_json(
        self,
        db_session: Session,
        temp_archive_dir: Path,
    ):
        """Validates that archiving serializes existing investigations to verified JSON."""
        # Query existing count in DB
        initial_count = db_session.query(Investigation).count()
        if initial_count == 0:
            # Create a test investigation if DB is empty
            user = db_session.query(User).first()
            if not user:
                user = User(
                    id=uuid.uuid4(),
                    email="test_archive_user@threatweave.local",
                    password_hash=hash_password("Pass123!"),
                    role="analyst",
                )
                db_session.add(user)
                db_session.commit()

            test_inv = Investigation(
                id=uuid.uuid4(),
                user_id=user.id,
                title="TEST-ARCHIVE-INV",
                status="completed",
                final_risk_score=0.85,
                final_severity=Severity.HIGH,
            )
            db_session.add(test_inv)
            db_session.commit()
            initial_count = 1

        archive_file, archived_count = archive_existing_investigations(
            db_session,
            archive_dir=temp_archive_dir,
        )

        assert archive_file is not None
        assert archive_file.exists()
        assert archive_file.stat().st_size > 0
        assert archived_count == initial_count

        # Validate JSON payload structure
        with open(archive_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "archived_at" in data
        assert data["total_investigations"] == initial_count
        assert len(data["investigations"]) == initial_count
        assert "evidence_inputs" in data["investigations"][0]
        assert "agent_runs" in data["investigations"][0]

    def test_dry_run_safety_does_not_modify_db(self, db_session: Session, temp_archive_dir: Path):
        """Validates that running without --confirm or with --dry-run performs zero mutations."""
        pre_count = db_session.query(Investigation).count()

        result = run_reset_and_seed(confirm=False, dry_run=True, archive_dir=temp_archive_dir)

        post_count = db_session.query(Investigation).count()
        assert pre_count == post_count
        assert result["dry_run"] is True
        assert result["archive_file"] is None
        assert result["deleted_count"] == 0

    def test_idempotency_running_twice_does_not_duplicate_rows(
        self,
        db_session: Session,
    ):
        """Validates that seed_curated_queue can be executed repeatedly without duplicate rows."""
        user = ensure_seed_user(db_session)

        # Run 1
        seeded_first = seed_curated_queue(db_session, user)
        count_after_first = db_session.query(Investigation).filter(
            Investigation.title.startswith("INC-2024-")
        ).count()

        # Run 2
        seeded_second = seed_curated_queue(db_session, user)
        count_after_second = db_session.query(Investigation).filter(
            Investigation.title.startswith("INC-2024-")
        ).count()

        assert count_after_first == len(CURATED_INCIDENTS)
        assert count_after_second == len(CURATED_INCIDENTS)
        assert len(seeded_first) == len(seeded_second)

    def test_seeded_investigations_have_valid_complete_data(
        self,
        db_session: Session,
    ):
        """Validates that all seeded incidents contain complete, realistic scores and relationships."""
        user = ensure_seed_user(db_session)
        seed_curated_queue(db_session, user)

        seeded_invs = db_session.query(Investigation).filter(
            Investigation.title.startswith("INC-2024-")
        ).all()

        assert len(seeded_invs) == len(CURATED_INCIDENTS)

        severities_found = set()
        for inv in seeded_invs:
            assert inv.final_risk_score is not None
            assert 0.0 <= inv.final_risk_score <= 1.0
            assert inv.final_severity is not None
            assert inv.final_confidence is not None
            assert inv.status == "completed"
            assert len(inv.evidence_inputs) > 0
            assert len(inv.agent_runs) > 0
            assert len(inv.risk_breakdown) == 4

            severities_found.add(inv.final_severity)

        # Must span critical, high, medium, info
        assert Severity.CRITICAL in severities_found
        assert Severity.HIGH in severities_found
        assert Severity.MEDIUM in severities_found
        assert Severity.INFO in severities_found
