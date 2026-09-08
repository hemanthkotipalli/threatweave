from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.enums import SourceType

if TYPE_CHECKING:
    from app.models.investigation import Investigation


class RagCitation(Base):
    """
    RagCitation model representing referenced external vulnerability or threat intel sources.
    """
    __tablename__ = "rag_citations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_title: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        SQLEnum(*(e.value for e in SourceType), name="source_type_enum"),
        nullable=False,
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    investigation: Mapped[Investigation] = relationship(
        "Investigation",
        back_populates="rag_citations",
    )
