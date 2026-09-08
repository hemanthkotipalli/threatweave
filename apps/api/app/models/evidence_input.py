from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import Modality

if TYPE_CHECKING:
    from app.models.investigation import Investigation


class EvidenceInput(Base):
    """
    EvidenceInput model representing raw source intelligence files, URLs, or recordings.
    """
    __tablename__ = "evidence_inputs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    modality: Mapped[Modality] = mapped_column(
        SQLEnum(*(e.value for e in Modality), name="modality_enum"),
        nullable=False,
    )
    raw_content_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    investigation: Mapped[Investigation] = relationship(
        "Investigation",
        back_populates="evidence_inputs",
    )
