from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import AgentStatus

if TYPE_CHECKING:
    from app.models.agent_finding import AgentFinding
    from app.models.investigation import Investigation


class AgentRun(Base):
    """
    AgentRun model representing the execution state of an individual agent in the swarm.
    """
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[AgentStatus] = mapped_column(
        SQLEnum(*(e.value for e in AgentStatus), name="agent_status_enum"),
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    investigation: Mapped[Investigation] = relationship(
        "Investigation",
        back_populates="agent_runs",
    )
    findings: Mapped[list[AgentFinding]] = relationship(
        "AgentFinding",
        back_populates="agent_run",
        cascade="all, delete-orphan",
    )
