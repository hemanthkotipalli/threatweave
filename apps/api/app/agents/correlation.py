"""
app/agents/correlation.py
-------------------------
Evidence correlation and cross-agent conflict detection for ThreatWeave (Phase 11).

Finds corroboration across specialist findings based on shared Indicators of Compromise (IoCs)
and detects significant severity divergences across active findings examining related signals.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.indicators import VALID_INDICATORS

logger = logging.getLogger("threatweave-api.agents.correlation")

# Categorization of indicators into semantic risk categories for conflict evaluation
INDICATOR_CATEGORIES: dict[str, str] = {
    # Social engineering / Urgency / Impersonation
    "urgency_language": "social_engineering",
    "credential_request": "social_engineering",
    "impersonation_claim": "social_engineering",
    "impersonation_banner": "social_engineering",
    "vishing_script_pattern": "social_engineering",
    "generic_greeting": "social_engineering",
    "unusual_sender_pattern": "social_engineering",

    # Payment / Financial manipulation
    "payment_request": "payment_fraud",
    "qr_payment_request": "payment_fraud",
    "fake_payment_confirmation": "payment_fraud",
    "financial_manipulation": "payment_fraud",
    "qr_upi_deeplink_suspicious": "payment_fraud",

    # Technical Infrastructure / Links / URLs
    "suspicious_link_mention": "technical_infrastructure",
    "lookalike_domain": "technical_infrastructure",
    "suspicious_tld": "technical_infrastructure",
    "no_https": "technical_infrastructure",
    "ip_address_url": "technical_infrastructure",
    "excessive_subdomains": "technical_infrastructure",
    "url_shortener": "technical_infrastructure",
    "known_malicious_domain": "technical_infrastructure",
    "suspicious_url_structure": "technical_infrastructure",
    "redirect_chain_detected": "technical_infrastructure",
    "qr_non_url_payload": "technical_infrastructure",

    # Content & Modality Anomalies
    "spelling_grammar_anomaly": "anomaly",
    "embedded_contact_info": "anomaly",
    "robotic_speech_pattern": "anomaly",
    "ai_voice_indicator_weak": "anomaly",
    "ocr_low_confidence": "anomaly",
    "ocr_failed": "anomaly",
    "stt_low_confidence": "anomaly",
    "stt_failed": "anomaly",
    "qr_decode_failed": "anomaly",
}


def find_corroboration(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Groups findings by shared indicator strings across DIFFERENT agents.
    Exact string match against core/indicators.py's vocabulary.

    - Excludes findings with status == 'failed'.
    - Dedupes indicators WITHIN a single agent's own finding first.
    - Only includes indicator groups where 2+ distinct agents share the indicator.

    :param findings: List of raw EvidenceItem dicts.
    :return: List of {"indicator": str, "agents": list[str]} sorted by indicator name.
    """
    indicator_to_agents: dict[str, set[str]] = {}

    for item in findings:
        if item.get("status") == "failed":
            continue

        agent = item.get("agent")
        if not agent:
            continue

        raw_indicators = item.get("indicators", [])
        if isinstance(raw_indicators, dict):
            raw_indicators = list(raw_indicators.keys())

        # Dedupe indicators within a single agent's own finding first
        unique_agent_indicators = {
            ind for ind in raw_indicators if ind in VALID_INDICATORS
        }

        for ind in unique_agent_indicators:
            indicator_to_agents.setdefault(ind, set()).add(agent)

    # Filter to indicators shared by 2+ distinct agents
    corroboration_groups: list[dict[str, Any]] = []
    for ind, agents in sorted(indicator_to_agents.items()):
        if len(agents) >= 2:
            corroboration_groups.append({
                "indicator": ind,
                "agents": sorted(agents),
            })

    return corroboration_groups


def find_conflicts(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Detects cross-agent severity-divergence conflicts.
    Two agents conflict when:
    1. BOTH produced a non-skipped, non-failed finding (status != 'failed').
    2. Severities diverge significantly: one is 'info' or 'low' while another is 'high' or 'critical'.
    3. The findings share or relate to a similar indicator string or indicator category.

    :param findings: List of raw EvidenceItem dicts.
    :return: List of {"agent_a": str, "agent_b": str, "conflict_type": str, "description": str}
    """
    # Filter active, non-failed findings
    active_findings = [f for f in findings if f.get("status") != "failed" and f.get("agent")]

    low_severities = {"info", "low"}
    high_severities = {"high", "critical"}

    conflicts: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str, str]] = set()

    n = len(active_findings)
    for i in range(n):
        for j in range(i + 1, n):
            fa = active_findings[i]
            fb = active_findings[j]

            agent_a = fa.get("agent", "")
            agent_b = fb.get("agent", "")

            # Must be different agents
            if agent_a == agent_b:
                continue

            sev_a = str(fa.get("severity", "info")).lower()
            sev_b = str(fb.get("severity", "info")).lower()

            # Check significant severity divergence
            divergence = (
                (sev_a in low_severities and sev_b in high_severities)
                or (sev_a in high_severities and sev_b in low_severities)
            )
            if not divergence:
                continue

            # Extract indicators
            inds_a = fa.get("indicators", [])
            if isinstance(inds_a, dict):
                inds_a = list(inds_a.keys())
            inds_b = fb.get("indicators", [])
            if isinstance(inds_b, dict):
                inds_b = list(inds_b.keys())

            set_a = set(inds_a)
            set_b = set(inds_b)

            # Check for direct shared indicator or shared category
            shared_direct = set_a & set_b
            cats_a = {INDICATOR_CATEGORIES.get(ind) for ind in set_a if ind in INDICATOR_CATEGORIES}
            cats_b = {INDICATOR_CATEGORIES.get(ind) for ind in set_b if ind in INDICATOR_CATEGORIES}
            shared_categories = cats_a & cats_b

            if shared_direct or shared_categories:
                signal_desc = (
                    f"shared indicators {sorted(shared_direct)}"
                    if shared_direct
                    else f"related category {sorted(shared_categories)}"
                )

                # Canonical ordered pair to prevent duplicate reflections
                pair_key = tuple(sorted([agent_a, agent_b])) + (signal_desc,)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                conflicts.append({
                    "agent_a": agent_a,
                    "agent_b": agent_b,
                    "conflict_type": "severity_divergence",
                    "description": (
                        f"Significant severity divergence between {agent_a} ({sev_a}) "
                        f"and {agent_b} ({sev_b}) on {signal_desc}"
                    ),
                })

    return conflicts
