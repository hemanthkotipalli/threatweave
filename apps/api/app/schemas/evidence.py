from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceItem(BaseModel):
    """
    Evidence item schema representing audit conclusions from individual agents.
    Matches the exact schema shape required for downstream agent orchestration.
    """
    agent: str = Field(..., description="Name of the swarm agent generating this finding.")
    modality: str = Field(..., description="Evidence category modality (e.g. text, url, image, voice).")
    finding: str = Field(..., description="Direct conclusion summary text.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence calculation score from 0.0 to 1.0.")
    severity: Literal["info", "low", "medium", "high", "critical"] = Field(
        ..., description="Severity classification tier of this finding."
    )
    indicators: list[str] = Field(default_factory=list, description="Extracted Indicator of Compromise (IoC) lists.")
    evidence: dict = Field(default_factory=dict, description="Arbitrary nested supporting evidence payload.")
    reasoning: str = Field(..., description="Step-by-step logic breakdown leading to conclusion.")
    external_refs: list[str] = Field(default_factory=list, description="Reference links or citations (RAG details).")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp.")
    status: Literal["ok", "degraded_fallback", "failed", "skipped"] = Field(
        ..., description="Verification status outcome flag."
    )

    model_config = ConfigDict(from_attributes=True)
