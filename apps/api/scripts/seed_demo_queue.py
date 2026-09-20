"""
apps/api/scripts/seed_demo_queue.py
-----------------------------------
Safe, archive-first demo queue seeding and database reset utility.

Safety Rails:
1. ARCHIVE FIRST: Serializes all existing investigations and cascading child rows
   to a timestamped JSON file in `storage/archives/` before deletion.
2. CONFIRMATION REQUIRED: Requires `--confirm` flag to execute real mutations.
3. DRY-RUN SAFE: Default behavior or `--dry-run` performs zero mutations.
4. IDEMPOTENT: Running repeatedly produces deterministic, deduplicated seed data.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure apps/api directory is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
API_ROOT = SCRIPT_DIR.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.agent_finding import AgentFinding
from app.models.agent_run import AgentRun
from app.models.conflict_log import ConflictLog
from app.models.enums import AgentStatus, FindingStatus, Modality, Severity, SourceType
from app.models.evidence_input import EvidenceInput
from app.models.investigation import Investigation
from app.models.rag_citation import RagCitation
from app.models.risk_breakdown import RiskBreakdown
from app.models.user import User

ARCHIVE_DIR = API_ROOT / "storage" / "archives"

# 8 Curated, Realistic Incidents Grounded in Indian Cyber Fraud Landscape
CURATED_INCIDENTS: list[dict[str, Any]] = [
    {
        "title": "INC-2024-8821: Multi-Channel SBI KYC Credential Harvester & UPI Phishing Ring",
        "final_risk_score": 0.925,
        "final_severity": Severity.CRITICAL,
        "final_confidence": 0.910,
        "inputs": [
            {"modality": "text", "raw_content_ref": "SMS: SBI Account Blocked. Update KYC at http://192.168.1.50/sbi-verify within 24h."},
            {"modality": "url", "raw_content_ref": "http://192.168.1.50/sbi-verify/login.php"},
            {"modality": "image", "raw_content_ref": "forged_sbi_login_banner.png"},
        ],
        "runs": [
            {
                "agent_name": "text_agent",
                "latency_ms": 780,
                "findings": [
                    {
                        "finding": "Urgent banking credential lure demanding immediate password update to avoid account suspension.",
                        "confidence": 0.92,
                        "severity": Severity.HIGH,
                        "indicators": ["urgency_language", "credential_request", "impersonation_claim"],
                        "reasoning": "Coercive urgency language paired with unauthorized banking credential harvesting pleas.",
                    }
                ],
            },
            {
                "agent_name": "url_agent",
                "latency_ms": 42,
                "findings": [
                    {
                        "finding": "Suspicious raw IP address URL masquerading as State Bank of India netbanking portal.",
                        "confidence": 0.95,
                        "severity": Severity.CRITICAL,
                        "indicators": ["ip_address_url", "no_https", "lookalike_domain", "suspicious_url_structure"],
                        "reasoning": "Direct IPv4 endpoint hosting banking authentication forms without TLS encryption.",
                    }
                ],
            },
            {
                "agent_name": "image_agent",
                "latency_ms": 1120,
                "findings": [
                    {
                        "finding": "OCR extracted deceptive bank logo and security warning banner claiming RBI regulatory action.",
                        "confidence": 0.88,
                        "severity": Severity.HIGH,
                        "indicators": ["impersonation_banner", "urgency_language"],
                        "reasoning": "Visual impersonation of institutional branding designed to deceive retail customers.",
                    }
                ],
            },
        ],
        "breakdown": [
            {"component": "base_score", "value": 0.775, "weight": 1.0, "contribution": 0.775},
            {"component": "corroboration_bonus", "value": 0.200, "weight": 1.0, "contribution": 0.200},
            {"component": "intel_bonus", "value": 0.150, "weight": 1.0, "contribution": 0.150},
            {"component": "contradiction_penalty", "value": 0.000, "weight": 1.0, "contribution": 0.000},
        ],
        "citations": [
            {
                "source_title": "CERT-In CIAD-2024-0012: Phishing Campaigns Targeting Indian Banking NetBanking Portals",
                "source_type": "CERT-In",
                "similarity_score": 0.82,
                "chunk_text": "Threat actors are deploying IP-hosted replicas of major Indian banks using fake KYC SMS lures to harvest credentials.",
            }
        ],
    },
    {
        "title": "INC-2024-8822: Digital Arrest & Fake CBI Impersonation Vishing Campaign",
        "final_risk_score": 0.880,
        "final_severity": Severity.CRITICAL,
        "final_confidence": 0.865,
        "inputs": [
            {"modality": "voice", "raw_content_ref": "cbi_digital_arrest_voicemail.wav"},
            {"modality": "text", "raw_content_ref": "Transcript: This is CBI Cyber Cell New Delhi. Arrest warrant issued under PMLA."},
        ],
        "runs": [
            {
                "agent_name": "voice_agent",
                "latency_ms": 1420,
                "findings": [
                    {
                        "finding": "Automated vishing script coercing victim with fake law enforcement arrest warrant and asset seizure.",
                        "confidence": 0.89,
                        "severity": Severity.CRITICAL,
                        "indicators": ["vishing_script_pattern", "urgency_language", "impersonation_claim", "financial_manipulation"],
                        "reasoning": "Detected psychological extortion pattern typical of digital arrest syndicates; acoustic anomalies noted.",
                    }
                ],
            },
            {
                "agent_name": "text_agent",
                "latency_ms": 650,
                "findings": [
                    {
                        "finding": "Coercive legal extortion demanding immediate fund transfer to temporary government escrow.",
                        "confidence": 0.86,
                        "severity": Severity.HIGH,
                        "indicators": ["urgency_language", "impersonation_claim", "payment_request"],
                        "reasoning": "Language constructs match documented telecommunications fraud playbooks.",
                    }
                ],
            },
        ],
        "breakdown": [
            {"component": "base_score", "value": 0.730, "weight": 1.0, "contribution": 0.730},
            {"component": "corroboration_bonus", "value": 0.100, "weight": 1.0, "contribution": 0.100},
            {"component": "intel_bonus", "value": 0.150, "weight": 1.0, "contribution": 0.150},
            {"component": "contradiction_penalty", "value": 0.000, "weight": 1.0, "contribution": 0.000},
        ],
        "citations": [
            {
                "source_title": "CERT-In CIAD-2024-0038: Advisory on 'Digital Arrest' Extortion Rackets Impersonating Police & CBI",
                "source_type": "CERT-In",
                "similarity_score": 0.87,
                "chunk_text": "Victims receive audio/video calls from fraudsters claiming to represent CBI/ED alleging money laundering.",
            }
        ],
    },
    {
        "title": "INC-2024-8823: Disguised Electricity Bill Disconnection Fake UPI QR Code",
        "final_risk_score": 0.760,
        "final_severity": Severity.HIGH,
        "final_confidence": 0.920,
        "inputs": [
            {"modality": "qr", "raw_content_ref": "mismatched_utility_bill.png"},
            {"modality": "text", "raw_content_ref": "Notice: Electricity disconnection tonight at 9:30 PM due to unpaid balance."},
        ],
        "runs": [
            {
                "agent_name": "qr_agent",
                "latency_ms": 85,
                "findings": [
                    {
                        "finding": "Mismatched UPI deep-link payee routing to private entity rather than official power distribution utility.",
                        "confidence": 1.00,
                        "severity": Severity.HIGH,
                        "indicators": ["qr_payment_request", "qr_upi_deeplink_suspicious"],
                        "reasoning": "Decoded UPI VPA 'powerbill-settle@okaxis' does not match registered Discom merchant identifiers.",
                    }
                ],
            },
            {
                "agent_name": "text_agent",
                "latency_ms": 520,
                "findings": [
                    {
                        "finding": "Threat of same-day disconnection designed to bypass critical inspection through manufactured panic.",
                        "confidence": 0.84,
                        "severity": Severity.HIGH,
                        "indicators": ["urgency_language", "payment_request"],
                        "reasoning": "Time-sensitive service termination notice common in utility bill payment scams.",
                    }
                ],
            },
        ],
        "breakdown": [
            {"component": "base_score", "value": 0.610, "weight": 1.0, "contribution": 0.610},
            {"component": "corroboration_bonus", "value": 0.100, "weight": 1.0, "contribution": 0.100},
            {"component": "intel_bonus", "value": 0.150, "weight": 1.0, "contribution": 0.150},
            {"component": "contradiction_penalty", "value": 0.000, "weight": 1.0, "contribution": 0.000},
        ],
        "citations": [
            {
                "source_title": "CERT-In CIAD-2024-0021: Deceptive Static QR Code Tampering in Public Utility Notices",
                "source_type": "CERT-In",
                "similarity_score": 0.79,
                "chunk_text": "Scammers overwrite legitimate municipal utility QR codes with fraudulent personal merchant accounts.",
            }
        ],
    },
    {
        "title": "INC-2024-8824: Typosquatted HDFC NetBanking Credential Harvester",
        "final_risk_score": 0.720,
        "final_severity": Severity.HIGH,
        "final_confidence": 0.890,
        "inputs": [
            {"modality": "url", "raw_content_ref": "http://netbanking-hdfc-secure.tk/login.php"},
        ],
        "runs": [
            {
                "agent_name": "url_agent",
                "latency_ms": 38,
                "findings": [
                    {
                        "finding": "Domain impersonation using free .tk TLD and targeted brand keywords for credential harvesting.",
                        "confidence": 0.96,
                        "severity": Severity.HIGH,
                        "indicators": ["suspicious_tld", "lookalike_domain", "suspicious_url_structure", "credential_request"],
                        "reasoning": "Domain registration entropy and brand lexical token overlap confirm lookalike phishing asset.",
                    }
                ],
            }
        ],
        "breakdown": [
            {"component": "base_score", "value": 0.570, "weight": 1.0, "contribution": 0.570},
            {"component": "corroboration_bonus", "value": 0.000, "weight": 1.0, "contribution": 0.000},
            {"component": "intel_bonus", "value": 0.150, "weight": 1.0, "contribution": 0.150},
            {"component": "contradiction_penalty", "value": 0.000, "weight": 1.0, "contribution": 0.000},
        ],
        "citations": [
            {
                "source_title": "RBI Advisory DoS.CO.PPG/SEC.03/2023: Countermeasures Against Lookalike Banking Domains",
                "source_type": "RBI",
                "similarity_score": 0.75,
                "chunk_text": "Commercial banks must monitor lookalike domain registrations on free and high-risk TLDs.",
            }
        ],
    },
    {
        "title": "INC-2024-8825: Forged Rs. 49,999 Merchant Payment Receipt Screenshot",
        "final_risk_score": 0.540,
        "final_severity": Severity.MEDIUM,
        "final_confidence": 0.810,
        "inputs": [
            {"modality": "image", "raw_content_ref": "fake_paytm_payment_receipt.png"},
        ],
        "runs": [
            {
                "agent_name": "image_agent",
                "latency_ms": 940,
                "findings": [
                    {
                        "finding": "Optical character inspection reveals altered digital font metrics and invalid 8-digit UTR reference code.",
                        "confidence": 0.82,
                        "severity": Severity.MEDIUM,
                        "indicators": ["fake_payment_confirmation", "financial_manipulation"],
                        "reasoning": "Standard UPI reference numbers adhere to 12-digit transaction hashes. The receipt displays an 8-digit counterfeit.",
                    }
                ],
            }
        ],
        "breakdown": [
            {"component": "base_score", "value": 0.390, "weight": 1.0, "contribution": 0.390},
            {"component": "corroboration_bonus", "value": 0.000, "weight": 1.0, "contribution": 0.000},
            {"component": "intel_bonus", "value": 0.150, "weight": 1.0, "contribution": 0.150},
            {"component": "contradiction_penalty", "value": 0.000, "weight": 1.0, "contribution": 0.000},
        ],
        "citations": [
            {
                "source_title": "CERT-In Advisory CIAD-2024-0019: In-Store Payment Notification Display Manipulation",
                "source_type": "CERT-In",
                "similarity_score": 0.68,
                "chunk_text": "Retail merchants are targeted by rogue mobile apps generating simulated UPI success screens.",
            }
        ],
    },
    {
        "title": "INC-2024-8826: Lottery Prize & Cashback SMS Lure with Generic Shortlink",
        "final_risk_score": 0.320,
        "final_severity": Severity.LOW,
        "final_confidence": 0.740,
        "inputs": [
            {"modality": "text", "raw_content_ref": "Congratulations! You have won Rs. 25,000 cash bonus. Claim: bit.ly/prize25k"},
        ],
        "runs": [
            {
                "agent_name": "text_agent",
                "latency_ms": 480,
                "findings": [
                    {
                        "finding": "Unsolicited promotional lottery incentive directing recipients to third-party URL shortening service.",
                        "confidence": 0.74,
                        "severity": Severity.LOW,
                        "indicators": ["financial_manipulation", "url_shortener", "unusual_sender_pattern"],
                        "reasoning": "Generic spam lottery patterns without targeted spear-phishing urgency indicators.",
                    }
                ],
            }
        ],
        "breakdown": [
            {"component": "base_score", "value": 0.320, "weight": 1.0, "contribution": 0.320},
            {"component": "corroboration_bonus", "value": 0.000, "weight": 1.0, "contribution": 0.000},
            {"component": "intel_bonus", "value": 0.000, "weight": 1.0, "contribution": 0.000},
            {"component": "contradiction_penalty", "value": 0.000, "weight": 1.0, "contribution": 0.000},
        ],
        "citations": [],
    },
    {
        "title": "INC-2024-8827: Routine IT Department Password Expiry Notification",
        "final_risk_score": 0.150,
        "final_severity": Severity.INFO,
        "final_confidence": 0.880,
        "inputs": [
            {"modality": "text", "raw_content_ref": "Notice: Your domain password expires in 14 days. Change via internal intranet."},
        ],
        "runs": [
            {
                "agent_name": "text_agent",
                "latency_ms": 320,
                "findings": [
                    {
                        "finding": "Routine administrative password policy notification referencing official internal intranet portal.",
                        "confidence": 0.90,
                        "severity": Severity.INFO,
                        "indicators": ["generic_greeting"],
                        "reasoning": "Contains no coercive urgency, external credential harvesting links, or suspicious requests.",
                    }
                ],
            }
        ],
        "breakdown": [
            {"component": "base_score", "value": 0.150, "weight": 1.0, "contribution": 0.150},
            {"component": "corroboration_bonus", "value": 0.000, "weight": 1.0, "contribution": 0.000},
            {"component": "intel_bonus", "value": 0.000, "weight": 1.0, "contribution": 0.000},
            {"component": "contradiction_penalty", "value": 0.000, "weight": 1.0, "contribution": 0.000},
        ],
        "citations": [],
    },
    {
        "title": "INC-2024-8828: Benign Official Monthly Account Statement Document",
        "final_risk_score": 0.050,
        "final_severity": Severity.INFO,
        "final_confidence": 0.940,
        "inputs": [
            {"modality": "text", "raw_content_ref": "Attached is your monthly savings statement for period ending August 31."},
            {"modality": "image", "raw_content_ref": "official_bank_statement_header.png"},
        ],
        "runs": [
            {
                "agent_name": "text_agent",
                "latency_ms": 360,
                "findings": [
                    {
                        "finding": "Standard monthly informational transaction summary without call-to-action or credential demands.",
                        "confidence": 0.95,
                        "severity": Severity.INFO,
                        "indicators": [],
                        "reasoning": "Benign corporate banking communication.",
                    }
                ],
            },
            {
                "agent_name": "image_agent",
                "latency_ms": 680,
                "findings": [
                    {
                        "finding": "Verified bank statement layout with authentic digital header signature and correct formatting.",
                        "confidence": 0.93,
                        "severity": Severity.INFO,
                        "indicators": [],
                        "reasoning": "OCR confirms genuine banking table without fraudulent tampering.",
                    }
                ],
            },
        ],
        "breakdown": [
            {"component": "base_score", "value": 0.050, "weight": 1.0, "contribution": 0.050},
            {"component": "corroboration_bonus", "value": 0.000, "weight": 1.0, "contribution": 0.000},
            {"component": "intel_bonus", "value": 0.000, "weight": 1.0, "contribution": 0.000},
            {"component": "contradiction_penalty", "value": 0.000, "weight": 1.0, "contribution": 0.000},
        ],
        "citations": [],
    },
]


def _val(x: Any) -> Any:
    if x is None:
        return None
    if hasattr(x, "value"):
        return x.value
    return str(x)


def serialize_investigations_to_dict(investigations: list[Investigation]) -> list[dict[str, Any]]:
    """Serializes all investigation objects and their cascade relationships into a JSON-serializable list."""
    serialized = []
    for inv in investigations:
        inv_data: dict[str, Any] = {
            "id": str(inv.id),
            "user_id": str(inv.user_id),
            "title": inv.title,
            "status": _val(inv.status),
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "completed_at": inv.completed_at.isoformat() if inv.completed_at else None,
            "final_risk_score": inv.final_risk_score,
            "final_severity": _val(inv.final_severity),
            "final_confidence": inv.final_confidence,
            "evidence_inputs": [
                {
                    "id": str(inp.id),
                    "modality": _val(inp.modality),
                    "raw_content_ref": inp.raw_content_ref,
                    "file_path": inp.file_path,
                    "created_at": inp.created_at.isoformat() if inp.created_at else None,
                }
                for inp in inv.evidence_inputs
            ],
            "agent_runs": [
                {
                    "id": str(run.id),
                    "agent_name": run.agent_name,
                    "status": _val(run.status),
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                    "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                    "latency_ms": run.latency_ms,
                    "findings": [
                        {
                            "id": str(f.id),
                            "finding": f.finding,
                            "confidence": f.confidence,
                            "severity": _val(f.severity),
                            "indicators": f.indicators,
                            "evidence": f.evidence,
                            "reasoning": f.reasoning,
                            "external_refs": f.external_refs,
                            "status": _val(f.status),
                            "timestamp": f.timestamp.isoformat() if f.timestamp else None,
                        }
                        for f in run.findings
                    ],
                }
                for run in inv.agent_runs
            ],
            "rag_citations": [
                {
                    "id": str(c.id),
                    "source_title": c.source_title,
                    "source_type": _val(c.source_type),
                    "chunk_text": c.chunk_text,
                    "similarity_score": c.similarity_score,
                    "url": c.url,
                }
                for c in inv.rag_citations
            ],
            "risk_breakdown": [
                {
                    "id": str(rb.id),
                    "component": rb.component,
                    "value": rb.value,
                    "weight": rb.weight,
                    "contribution": rb.contribution,
                }
                for rb in inv.risk_breakdown
            ],
            "conflict_logs": [
                {
                    "id": str(cl.id),
                    "agent_a": cl.agent_a,
                    "agent_b": cl.agent_b,
                    "conflict_type": cl.conflict_type,
                    "resolution_rule": cl.resolution_rule,
                    "resolution_outcome": cl.resolution_outcome,
                }
                for cl in inv.conflict_logs
            ],
        }
        serialized.append(inv_data)
    return serialized


def archive_existing_investigations(
    db: Session,
    archive_dir: Path = ARCHIVE_DIR,
) -> tuple[Path | None, int]:
    """
    Step A: Exports all current investigations to a timestamped JSON file.
    Verifies that the archive file exists and has non-zero size before returning.
    """
    investigations = db.query(Investigation).all()
    count = len(investigations)
    if count == 0:
        return None, 0

    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_file = archive_dir / f"investigations_archive_{timestamp}.json"

    data = serialize_investigations_to_dict(investigations)
    payload = {
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "total_investigations": count,
        "investigations": data,
    }

    with open(archive_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())

    # Strict verification
    if not archive_file.exists() or archive_file.stat().st_size == 0:
        raise RuntimeError(f"Archive file {archive_file} was not written properly or is empty.")

    return archive_file, count


def ensure_seed_user(db: Session) -> User:
    """Finds or creates a designated SOC analyst user to own seeded records."""
    user = db.query(User).filter(User.email == "soc_analyst@threatweave.local").first()
    if not user:
        # Check if any user exists
        first_user = db.query(User).first()
        if first_user:
            return first_user
        # Otherwise create a designated default analyst
        user = User(
            id=uuid.uuid4(),
            email="soc_analyst@threatweave.local",
            password_hash=hash_password("Analyst123!"),
            role="analyst",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def seed_curated_queue(db: Session, user: User) -> list[Investigation]:
    """
    Seeds the 8 curated incidents into the database.
    Idempotent: skips seeding if records with identical titles already exist.
    """
    created_investigations: list[Investigation] = []
    base_time = datetime.now(timezone.utc)

    for idx, inc in enumerate(CURATED_INCIDENTS):
        # Idempotency check: verify by title
        existing = db.query(Investigation).filter(Investigation.title == inc["title"]).first()
        if existing:
            created_investigations.append(existing)
            continue

        now = base_time
        inv = Investigation(
            id=uuid.uuid4(),
            user_id=user.id,
            title=inc["title"],
            status="completed",
            created_at=now,
            completed_at=now,
            final_risk_score=inc["final_risk_score"],
            final_severity=inc["final_severity"],
            final_confidence=inc["final_confidence"],
        )
        db.add(inv)
        db.flush()

        # Add Evidence Inputs
        for inp_data in inc.get("inputs", []):
            inp = EvidenceInput(
                id=uuid.uuid4(),
                investigation_id=inv.id,
                modality=Modality(inp_data["modality"]),
                raw_content_ref=inp_data.get("raw_content_ref"),
                created_at=now,
            )
            db.add(inp)

        # Add Agent Runs and Findings
        for run_data in inc.get("runs", []):
            run = AgentRun(
                id=uuid.uuid4(),
                investigation_id=inv.id,
                agent_name=run_data["agent_name"],
                status=AgentStatus.DONE,
                started_at=now,
                finished_at=now,
                latency_ms=run_data.get("latency_ms", 500),
            )
            db.add(run)
            db.flush()

            for f_data in run_data.get("findings", []):
                finding = AgentFinding(
                    id=uuid.uuid4(),
                    agent_run_id=run.id,
                    finding=f_data["finding"],
                    confidence=f_data["confidence"],
                    severity=f_data["severity"],
                    indicators=f_data.get("indicators", []),
                    evidence={"source": "seed_curated_data", "verified": True},
                    reasoning=f_data.get("reasoning", ""),
                    external_refs=[],
                    status=FindingStatus.OK,
                    timestamp=now,
                )
                db.add(finding)

        # Add Risk Breakdown Items
        for rb_data in inc.get("breakdown", []):
            rb = RiskBreakdown(
                id=uuid.uuid4(),
                investigation_id=inv.id,
                component=rb_data["component"],
                value=rb_data["value"],
                weight=rb_data["weight"],
                contribution=rb_data["contribution"],
            )
            db.add(rb)

        # Add RAG Citations
        for cit_data in inc.get("citations", []):
            cit = RagCitation(
                id=uuid.uuid4(),
                investigation_id=inv.id,
                source_title=cit_data["source_title"],
                source_type=SourceType(cit_data["source_type"]),
                chunk_text=cit_data["chunk_text"],
                similarity_score=cit_data["similarity_score"],
            )
            db.add(cit)

        created_investigations.append(inv)

    db.commit()
    return created_investigations


def run_reset_and_seed(
    confirm: bool = False,
    dry_run: bool = False,
    archive_dir: Path = ARCHIVE_DIR,
) -> dict[str, Any]:
    """
    Main orchestration function for archiving, deleting, and seeding investigations.
    """
    db = SessionLocal()
    try:
        current_count = db.query(Investigation).count()

        # Check if already seeded and no scratch rows
        curated_titles = {inc["title"] for inc in CURATED_INCIDENTS}
        existing_curated = db.query(Investigation).filter(Investigation.title.in_(curated_titles)).count()

        result: dict[str, Any] = {
            "pre_count": current_count,
            "existing_curated_count": existing_curated,
            "dry_run": dry_run,
            "confirm": confirm,
            "archive_file": None,
            "deleted_count": 0,
            "seeded_count": 0,
            "post_count": current_count,
            "incidents": [],
        }

        # Dry Run Mode or Missing Confirmation
        if dry_run or not confirm:
            print(f"[*] DRY-RUN SUMMARY (Zero mutations performed):")
            print(f"    - Current investigations in DB: {current_count}")
            print(f"    - Existing curated seed items: {existing_curated}")
            print(f"    - Target curated incidents to seed: {len(CURATED_INCIDENTS)}")
            if not confirm:
                print(f"    [!] SAFETY WARNING: '--confirm' flag was NOT provided.")
                print(f"    To perform real archive, deletion, and seeding, run with: --confirm")
            return result

        # Real Confirmation Flow:
        print(f"[+] STEP 1: Archiving {current_count} investigations...")
        archive_path, archived_count = archive_existing_investigations(db, archive_dir=archive_dir)
        result["archive_file"] = str(archive_path) if archive_path else None
        print(f"    [OK] Archived {archived_count} investigations to: {archive_path}")

        print(f"[+] STEP 2: Deleting scratch investigations via ORM cascade...")
        # Delete investigations using SQLAlchemy ORM so cascade deletes related tables
        all_invs = db.query(Investigation).all()
        for inv in all_invs:
            db.delete(inv)
        db.commit()
        result["deleted_count"] = len(all_invs)
        print(f"    [OK] Cleaned out {result['deleted_count']} investigations from database.")

        print(f"[+] STEP 3: Seeding {len(CURATED_INCIDENTS)} curated benchmark incidents...")
        user = ensure_seed_user(db)
        seeded_invs = seed_curated_queue(db, user)
        result["seeded_count"] = len(seeded_invs)
        result["post_count"] = db.query(Investigation).count()
        result["incidents"] = [
            {
                "id": str(inv.id),
                "title": inv.title,
                "severity": _val(inv.final_severity) or "info",
                "risk_score": inv.final_risk_score,
            }
            for inv in seeded_invs
        ]

        print(f"    [OK] Successfully seeded {result['seeded_count']} curated investigations.")
        print(f"    [OK] Final database investigation count: {result['post_count']}")
        return result

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="ThreatWeave Demo Queue Seeding & Reset Utility"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the archiving, clearing, and seeding without modifying the database.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Explicitly authorize destructive archive-then-seed operation.",
    )
    args = parser.parse_args()

    res = run_reset_and_seed(confirm=args.confirm, dry_run=args.dry_run)
    if not args.confirm and not args.dry_run:
        sys.exit(0)


if __name__ == "__main__":
    main()
