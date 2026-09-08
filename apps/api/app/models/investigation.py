from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import Severity

if TYPE_CHECKING:
    from app.models.agent_run import AgentRun
    from app.models.conflict_log import ConflictLog
    from app.models.evidence_input import EvidenceInput
    from app.models.investigation_report import InvestigationReport
    from app.models.rag_citation import RagCitation
    from app.models.risk_breakdown import RiskBreakdown
    from app.models.user import User


class Investigation(Base):
    """
    Investigation model representing a security swarm audit task.
    """
    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    final_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_severity: Mapped[Severity | None] = mapped_column(
        SQLEnum(*(e.value for e in Severity), name="severity_enum"),
        nullable=True,
    )
    final_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="investigations")
    
    evidence_inputs: Mapped[list[EvidenceInput]] = relationship(
        "EvidenceInput",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    agent_runs: Mapped[list[AgentRun]] = relationship(
        "AgentRun",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    rag_citations: Mapped[list[RagCitation]] = relationship(
        "RagCitation",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    risk_breakdown: Mapped[list[RiskBreakdown]] = relationship(
        "RiskBreakdown",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    investigation_reports: Mapped[list[InvestigationReport]] = relationship(
        "InvestigationReport",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    conflict_logs: Mapped[list[ConflictLog]] = relationship(
        "ConflictLog",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
