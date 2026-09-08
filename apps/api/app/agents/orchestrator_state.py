"""
app/agents/orchestrator_state.py
--------------------------------
Defines the LangGraph state schema for ThreatWeave swarm orchestration (Phase 10).
Uses LangGraph's reducer pattern (`Annotated[list[dict], operator.add]`) to allow
safe concurrent appends when specialist agents execute in parallel branches.
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class RoutingTarget(TypedDict):
    """
    Routing target specification identifying an agent and its corresponding evidence input.
    """
    agent_name: str
    evidence_input_id: str
    modality: str
    content_ref: str | None
    file_path: str | None


class InvestigationState(TypedDict):
    """
    State dictionary flowing through the LangGraph orchestrator state machine.

    Attributes:
        investigation_id: UUID string of the active investigation.
        evidence_inputs: Serialized list of raw evidence inputs loaded from DB.
        present_modalities: List of modalities discovered across inputs (text, url, image, voice).
        required_agents: List of RoutingTarget entries detailing agent jobs.
        active_agent_names: Distinct list of agent names that need to run.
        findings: Consolidated list of EvidenceItem dicts, appended via operator.add reducer.
        corroborations: Grouped list of corroborated indicators across agents (Phase 11).
        conflicts: Detected severity divergence conflicts across active agents (Phase 11).
        risk_result: Calculated deterministic risk breakdown and scores (Phase 11).
    """
    investigation_id: str
    evidence_inputs: list[dict[str, Any]]
    present_modalities: list[str]
    required_agents: list[RoutingTarget]
    active_agent_names: list[str]
    findings: Annotated[list[dict[str, Any]], operator.add]
    corroborations: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]
    rag_citations: list[dict[str, Any]]
    risk_result: dict[str, Any] | None

