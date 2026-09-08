"""
app/agents/graph.py
-------------------
LangGraph StateGraph orchestration machine for ThreatWeave (Phase 10).
Wired for dynamic modal routing, parallel agent execution, and result aggregation.

Flow:
START -> classify -> plan -[conditional parallel fan-out]-> {text, url, qr, image, voice} -> collect -> END

Extension Hook:
Phase 11 (Risk Engine) and Phase 12 (RAG Retrieval) connect to collect_node.
"""
from __future__ import annotations

import logging
from collections.abc import Sequence

from langgraph.graph import END, START, StateGraph

from app.agents.orchestrator_nodes import (
    classify_node,
    collect_node,
    conflict_resolution_node,
    correlate_node,
    image_agent_node,
    plan_node,
    qr_agent_node,
    rag_node,
    risk_engine_node,
    text_agent_node,
    url_agent_node,
    voice_agent_node,
)
from app.agents.orchestrator_state import InvestigationState

logger = logging.getLogger("threatweave-api.agents.graph")


def _route_to_specialists(state: InvestigationState) -> Sequence[str]:
    """
    Conditional routing function evaluating which specialist nodes should be invoked.
    Returns a sequence of active agent node names to fan out in parallel.
    If no specialists are required, routes directly to collect.
    """
    active = state.get("active_agent_names", [])
    if not active:
        logger.info("No active agents required -> routing directly to collect")
        return ["collect"]

    logger.info("Routing conditional edge from plan to active agents: %s", active)
    return active


def build_investigation_graph() -> StateGraph:
    """
    Constructs the ThreatWeave investigation LangGraph state machine.
    """
    workflow = StateGraph(InvestigationState)

    # 1. Add all graph nodes
    workflow.add_node("classify", classify_node)
    workflow.add_node("plan", plan_node)
    workflow.add_node("text_agent", text_agent_node)
    workflow.add_node("url_agent", url_agent_node)
    workflow.add_node("qr_agent", qr_agent_node)
    workflow.add_node("image_agent", image_agent_node)
    workflow.add_node("voice_agent", voice_agent_node)
    workflow.add_node("collect", collect_node)
    workflow.add_node("correlate", correlate_node)
    workflow.add_node("conflict_resolution", conflict_resolution_node)
    workflow.add_node("rag_node", rag_node)
    workflow.add_node("risk_engine", risk_engine_node)

    # 2. Sequential pipeline from START
    workflow.add_edge(START, "classify")
    workflow.add_edge("classify", "plan")

    # 3. Dynamic parallel fan-out from plan_node
    workflow.add_conditional_edges(
        "plan",
        _route_to_specialists,
        {
            "text_agent": "text_agent",
            "url_agent": "url_agent",
            "qr_agent": "qr_agent",
            "image_agent": "image_agent",
            "voice_agent": "voice_agent",
            "collect": "collect",
        },
    )

    # 4. Fan-in: all specialists converge into collect_node
    workflow.add_edge("text_agent", "collect")
    workflow.add_edge("url_agent", "collect")
    workflow.add_edge("qr_agent", "collect")
    workflow.add_edge("image_agent", "collect")
    workflow.add_edge("voice_agent", "collect")

    # 5. Sequential correlation, conflict resolution, RAG intelligence, and risk engine (Phases 11 & 12)
    workflow.add_edge("collect", "correlate")
    workflow.add_edge("correlate", "conflict_resolution")
    workflow.add_edge("conflict_resolution", "rag_node")
    workflow.add_edge("rag_node", "risk_engine")
    workflow.add_edge("risk_engine", END)

    return workflow


# Compiled singleton graph for runtime invocation by services
investigation_graph = build_investigation_graph().compile()
