from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.investigation import Investigation


class ConflictLog(Base):
    """
    ConflictLog model tracking consensus discrepancy details and their resolution states.
    """
    __tablename__ = "conflict_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_a: Mapped[str] = mapped_column(Text, nullable=False)
    agent_b: Mapped[str] = mapped_column(Text, nullable=False)
    conflict_type: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_rule: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_outcome: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    investigation: Mapped[Investigation] = relationship(
        "Investigation",
        back_populates="conflict_logs",
    )
