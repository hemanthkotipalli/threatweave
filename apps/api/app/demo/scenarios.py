"""
apps/api/app/demo/scenarios.py
------------------------------
Defines the 6 curated demo scenarios for ThreatWeave Phase 15.
All scenarios exercise the genuine live ingestion and swarm orchestration pipeline
without mocks, stubs, or hardcoded results.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any

from fastapi import UploadFile

from app.core.errors import NotFoundError
from app.demo.fixtures_builder import ensure_demo_fixtures

logger = logging.getLogger("threatweave-api.demo.scenarios")


@dataclass(frozen=True)
class DemoScenario:
    key: str
    title: str
    description: str
    modalities: list[str]
    text: str | None = None
    url: str | None = None
    image_fixture_key: str | None = None
    voice_fixture_key: str | None = None


# Registry of the 6 curated demonstration scenarios
SCENARIOS: dict[str, DemoScenario] = {
    "phishing_email": DemoScenario(
        key="phishing_email",
        title="Urgent Banking Credentials Lure",
        description="Realistic banking phishing message utilizing coercive urgency language to harvest net banking credentials under false regulatory threats.",
        modalities=["text"],
        text=(
            "URGENT: Your SBI bank account has been temporarily restricted due to unauthorized login attempts. "
            "Immediate Action Required: Verify your security credentials and password within 24 hours to prevent permanent account suspension. "
            "Failure to update will result in complete account blocking under RBI directives."
        ),
    ),
    "malicious_url": DemoScenario(
        key="malicious_url",
        title="Typosquatted Banking Phishing Portal",
        description="A deceptive lookalike domain hosted on a suspicious free TLD (.tk) with deceptive URL paths designed for credential harvesting.",
        modalities=["url"],
        url="http://verify-account.tk/sbi-netbanking/login.php?session=secure",
    ),
    "fake_payment_qr": DemoScenario(
        key="fake_payment_qr",
        title="Mismatched Electricity Bill UPI QR",
        description="A deceptive UPI QR code deep-link where the displayed payee name claims an official electricity utility while the underlying VPA routes to an unknown entity.",
        modalities=["qr"],
        image_fixture_key="fake_payment_qr",
    ),
    "fraudulent_screenshot": DemoScenario(
        key="fraudulent_screenshot",
        title="Fake Payment Confirmation Screenshot",
        description="A forged instant payment confirmation graphic purporting a Rs. 49,999 transfer designed to mislead merchants in offline retail fraud.",
        modalities=["image"],
        image_fixture_key="fraudulent_screenshot",
    ),
    "scam_voice": DemoScenario(
        key="scam_voice",
        title="Automated Bank Compromise Vishing Call",
        description="An automated telephone vishing audio script alerting the victim to a fraudulent account compromise to induce immediate PIN revelation.",
        modalities=["voice"],
        voice_fixture_key="scam_voice",
    ),
    "cross_modal": DemoScenario(
        key="cross_modal",
        title="Coordinated Multi-Channel KYC Phishing Campaign",
        description="A multi-channel banking attack combining an SMS security lure, lookalike verification URL, and forged official bank notification screenshot describing the same underlying scam.",
        modalities=["text", "url", "image"],
        text=(
            "URGENT: Your SBI bank account credentials have expired. "
            "Verify your password and KYC details immediately at http://192.168.1.50/sbi-verify/login.php to avoid account suspension."
        ),
        url="http://192.168.1.50/sbi-verify/login.php",
        image_fixture_key="cross_modal_kyc",
    ),
}


def get_all_scenarios_metadata() -> list[dict[str, Any]]:
    """Returns scenario metadata list (key, title, description, modalities) for public listing."""
    return [
        {
            "key": s.key,
            "title": s.title,
            "description": s.description,
            "modalities": s.modalities,
        }
        for s in SCENARIOS.values()
    ]


def prepare_scenario_inputs(
    scenario_key: str,
    mode: str = "combined"
) -> tuple[str, str | None, str | None, UploadFile | None, UploadFile | None]:
    """
    Constructs concrete evidence inputs for ingestion_service.ingest_investigation().
    
    For the 'cross_modal' scenario, supports mode parameter:
    - 'combined' (default): text + url + image
    - 'text_only': text only
    - 'url_only': url only
    - 'image_only': image only

    Returns:
        (title, text, url, image_file, voice_file)
    """
    scenario = SCENARIOS.get(scenario_key)
    if not scenario:
        raise NotFoundError(message=f"Demo scenario with key '{scenario_key}' does not exist.")

    fixtures = ensure_demo_fixtures()

    title = f"Demo: {scenario.title}"
    text: str | None = None
    url: str | None = None
    image_file: UploadFile | None = None
    voice_file: UploadFile | None = None

    if scenario_key == "cross_modal":
        title = f"Demo: {scenario.title} ({mode})"
        if mode in ("combined", "text_only"):
            text = scenario.text
        if mode in ("combined", "url_only"):
            url = scenario.url
        if mode in ("combined", "image_only") and scenario.image_fixture_key:
            img_path = fixtures.get(scenario.image_fixture_key)
            if img_path and img_path.exists():
                with open(img_path, "rb") as f:
                    image_file = UploadFile(
                        file=io.BytesIO(f.read()),
                        filename=img_path.name,
                    )
    else:
        text = scenario.text
        url = scenario.url

        if scenario.image_fixture_key:
            img_path = fixtures.get(scenario.image_fixture_key)
            if img_path and img_path.exists():
                with open(img_path, "rb") as f:
                    image_file = UploadFile(
                        file=io.BytesIO(f.read()),
                        filename=img_path.name,
                    )

        if scenario.voice_fixture_key:
            v_path = fixtures.get(scenario.voice_fixture_key)
            if v_path and v_path.exists():
                with open(v_path, "rb") as f:
                    voice_file = UploadFile(
                        file=io.BytesIO(f.read()),
                        filename=v_path.name,
                    )

    return title, text, url, image_file, voice_file
