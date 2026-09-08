from app.api.deps import get_db
from app.models.agent_finding import AgentFinding  # noqa: F401
from app.models.agent_run import AgentRun  # noqa: F401
from app.models.conflict_log import ConflictLog  # noqa: F401
from app.models.evidence_input import EvidenceInput  # noqa: F401
from app.models.investigation import Investigation  # noqa: F401
from app.models.investigation_report import InvestigationReport  # noqa: F401
from app.models.rag_citation import RagCitation  # noqa: F401
from app.models.risk_breakdown import RiskBreakdown  # noqa: F401
from app.models.user import User


def test_db_connection_read_write() -> None:
    """
    Assert that the real database session is operational by creating a User row,
    querying it back, verifying its parameters, and deleting it cleanly.
    """
    # Instantiate the get_db generator dependency to retrieve the session
    db_generator = get_db()
    db = next(db_generator)
    try:
        # 1. Insert a new test analyst user
        test_email = "db_test_analyst@threatweave.local"
        test_user = User(
            email=test_email,
            password_hash="fake_bcrypt_hash_value_for_testing",
            role="analyst",
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        created_user_id = test_user.id
        
        # 2. Query back the user by primary key ID
        queried_user = db.query(User).filter(User.id == created_user_id).first()
        assert queried_user is not None
        assert queried_user.email == test_email
        assert queried_user.role == "analyst"
        
        # 3. Delete the user to maintain clean state
        db.delete(queried_user)
        db.commit()
        
        # 4. Assert that the record was deleted
        deleted_user = db.query(User).filter(User.id == created_user_id).first()
        assert deleted_user is None
    finally:
        # Close database session cleanly via the generator's teardown block
        try:
            next(db_generator)
        except StopIteration:
            pass
