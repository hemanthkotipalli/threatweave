from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceInputCompact(BaseModel):
    """
    Compact representation of an evidence input for creation response envelopes.
    """
    id: uuid.UUID
    modality: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationInfo(BaseModel):
    """
    Metadata representation of an investigation.
    """
    id: uuid.UUID
    title: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationCreateResponse(BaseModel):
    """
    Response schema after creating a new investigation with its associated evidence inputs.
    """
    investigation: InvestigationInfo
    evidence_inputs: list[EvidenceInputCompact]

    model_config = ConfigDict(from_attributes=True)


class EvidenceInputDetailResponse(BaseModel):
    """
    Full detail representation of an evidence input.
    """
    id: uuid.UUID
    modality: str
    raw_content_ref: str | None = None
    file_path: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentFindingDetailResponse(BaseModel):
    """
    Detailed response schema for a persisted agent threat finding.
    """
    id: uuid.UUID
    agent_run_id: uuid.UUID
    finding: str
    confidence: float
    severity: str
    indicators: list[str] | dict
    evidence: dict
    reasoning: str
    external_refs: list[dict] | list[str] | dict = []
    status: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentRunDetailResponse(BaseModel):
    """
    Detailed response schema for an agent execution lifecycle record.
    """
    id: uuid.UUID
    agent_name: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    latency_ms: int | None = None
    findings: list[AgentFindingDetailResponse] = []

    model_config = ConfigDict(from_attributes=True)


class RagCitationResponse(BaseModel):
    """
    Response schema for an external threat intelligence citation.
    """
    id: uuid.UUID | str | None = None
    source_title: str
    source_type: str
    chunk_text: str
    similarity_score: float
    url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class InvestigationDetailResponse(BaseModel):
    """
    Full detail representation of an investigation, including evidence inputs,
    agent execution runs, and agent findings.
    """
    id: uuid.UUID
    title: str
    status: str
    created_at: datetime
    final_risk_score: float | None = None
    final_severity: str | None = None
    final_confidence: float | None = None
    evidence_inputs: list[EvidenceInputDetailResponse] = []
    agent_runs: list[AgentRunDetailResponse] = []
    rag_citations: list[RagCitationResponse] = []
    risk: RiskDetailResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class RiskBreakdownItemResponse(BaseModel):
    component: str
    value: float
    weight: float
    contribution: float

    model_config = ConfigDict(from_attributes=True)


class ConflictLogItemResponse(BaseModel):
    id: uuid.UUID
    agent_a: str
    agent_b: str
    conflict_type: str
    resolution_rule: str
    resolution_outcome: str

    model_config = ConfigDict(from_attributes=True)


class RiskDetailResponse(BaseModel):
    score: float | None = None
    severity: str | None = None
    confidence: float | None = None
    low_confidence: bool = False
    breakdown: list[RiskBreakdownItemResponse] = []
    conflicts: list[ConflictLogItemResponse] = []


class InvestigationAnalyzeResponse(BaseModel):
    """
    Summary response envelope returned after running swarm analysis.
    """
    investigation_id: str
    status: str
    active_agents: list[str]
    agent_runs: list[dict]
    findings_count: int
    findings: list[dict] = []
    rag_citations: list[RagCitationResponse] = []
    risk: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class InvestigationListItemResponse(BaseModel):
    """
    Summary representation of an investigation item in paginated list responses.
    """
    id: uuid.UUID
    title: str
    status: str
    created_at: datetime
    final_risk_score: float | None = None
    final_severity: str | None = None
    modalities: list[str] = []

    model_config = ConfigDict(from_attributes=True)

