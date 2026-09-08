"""
app/schemas/rag.py
------------------
Pydantic response schemas for ThreatWeave Phase 12 RAG search and advisory citations.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RagSearchItemResponse(BaseModel):
    """Represents a retrieved and similarity-filtered threat intelligence citation."""
    source_title: str
    source_type: str
    chunk_text: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    category: str | None = None
    url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RagSearchResponse(BaseModel):
    """Response schema for ad-hoc advisory search endpoint."""
    query: str
    threshold: float
    total_results: int
    results: list[RagSearchItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
