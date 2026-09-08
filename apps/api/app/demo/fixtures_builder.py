"""
apps/api/app/demo/fixtures_builder.py
-------------------------------------
Utility to build and verify binary test fixtures (PNG, WAV) for ThreatWeave Demo Mode.
Automatically runs at application startup or on first access to ensure all required
curated demonstration assets are present on disk.
"""
from __future__ import annotations

import logging
import math
import struct
import wave
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("threatweave-api.demo.fixtures")

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def get_fixtures_dir() -> Path:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIXTURES_DIR


def ensure_demo_fixtures() -> dict[str, Path]:
    """
    Ensures all 4 binary fixture files exist on disk in app/demo/fixtures/:
    1. fake_payment_qr.png
    2. fraudulent_screenshot.png
    3. scam_voice.wav
    4. cross_modal_kyc.png
    """
    f_dir = get_fixtures_dir()

    qr_path = f_dir / "fake_payment_qr.png"
    if not qr_path.exists():
        _generate_upi_qr(qr_path)

    screenshot_path = f_dir / "fraudulent_screenshot.png"
    if not screenshot_path.exists():
        _generate_fake_payment_screenshot(screenshot_path)

    voice_path = f_dir / "scam_voice.wav"
    if not voice_path.exists():
        _generate_vishing_audio(voice_path)

    cross_modal_img_path = f_dir / "cross_modal_kyc.png"
    if not cross_modal_img_path.exists():
        _generate_cross_modal_image(cross_modal_img_path)

    return {
        "fake_payment_qr": qr_path,
        "fraudulent_screenshot": screenshot_path,
        "scam_voice": voice_path,
        "cross_modal_kyc": cross_modal_img_path,
    }


def _generate_upi_qr(target_path: Path) -> None:
    """Generates mismatched UPI QR payload."""
    payload = "upi://pay?pa=scammer8831@fakebank&pn=Electricity+Board+Official&am=15000&cu=INR"
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(str(target_path), format="PNG")
    logger.info("Generated demo QR fixture: %s", target_path)


def _get_font(size: int = 24) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    for font_name in ("C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/arial.ttf", "consola.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(font_name, size)
        except (OSError, TypeError, ValueError):
            pass
    try:
        return ImageFont.load_default(size=size)
    except (TypeError, ValueError):
        return ImageFont.load_default()


def _generate_fake_payment_screenshot(target_path: Path) -> None:
    """Generates fake payment confirmation screenshot."""
    img = Image.new("RGB", (800, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_large = _get_font(28)
    font_small = _get_font(18)

    draw.rectangle([20, 20, 780, 80], fill=(34, 139, 34))
    draw.text((40, 35), "Payment Successful!", fill=(255, 255, 255), font=font_large)

    draw.text((40, 110), "Rs. 49,999.00 received from Ramesh Kumar", fill=(0, 0, 0), font=font_large)
    draw.text((40, 160), "Transaction ID: UPI/2026/894723984", fill=(100, 100, 100), font=font_small)
    draw.text((40, 190), "Beneficiary VPA: scammer8831@fakebank", fill=(100, 100, 100), font=font_small)
    draw.text((40, 220), "Status: COMPLETED (Instant Settlement)", fill=(34, 139, 34), font=font_small)

    img.save(str(target_path), format="PNG")
    logger.info("Generated fake payment screenshot fixture: %s", target_path)


def _generate_cross_modal_image(target_path: Path) -> None:
    """Generates cross-modal KYC phishing alert screenshot."""
    img = Image.new("RGB", (900, 450), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = _get_font(26)
    font_body = _get_font(18)

    # Red security banner
    draw.rectangle([20, 20, 880, 80], fill=(180, 0, 0))
    draw.text((40, 35), "STATE BANK OF INDIA - URGENT SECURITY NOTICE", fill=(255, 255, 255), font=font_title)

    draw.text((40, 110), "Dear Valued Customer,", fill=(0, 0, 0), font=font_body)
    draw.text((40, 145), "Your NetBanking and UPI facility has been temporarily restricted.", fill=(0, 0, 0), font=font_body)
    draw.text((40, 180), "Reason: Mandatory PAN / KYC document re-verification is pending.", fill=(180, 0, 0), font=font_body)
    draw.text((40, 215), "Immediate Action Required: Update credentials within 24 hours to prevent account closure.", fill=(0, 0, 0), font=font_body)
    draw.text((40, 270), "Official Portal: http://192.168.1.50/sbi-verify/login.php", fill=(0, 0, 200), font=font_body)
    draw.text((40, 310), "Failure to comply will result in permanent debit freeze under RBI Section 35A.", fill=(100, 100, 100), font=font_body)

    img.save(str(target_path), format="PNG")
    logger.info("Generated cross-modal KYC fixture: %s", target_path)


def _generate_vishing_audio(target_path: Path) -> None:
    """
    Synthesizes vishing audio script via pyttsx3 or generates modulated tone WAV.
    Text: 'This is an automated call from your bank. Your account has been compromised. Press 1 now to verify your PIN. Do not hang up.'
    """
    vishing_text = (
        "This is an automated call from your bank. Your account has been compromised. "
        "Press 1 now to verify your PIN. Do not hang up."
    )
    # Attempt local TTS
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.save_to_file(vishing_text, str(target_path))
        engine.runAndWait()
        if target_path.exists() and target_path.stat().st_size > 1000:
            logger.info("Generated synthetic speech vishing fixture: %s", target_path)
            return
    except (RuntimeError, OSError, ImportError, AttributeError) as exc:
        logger.warning("pyttsx3 not available or failed: %s; falling back to modulated synthetic WAV", exc)

    # Fallback: create valid modulated PCM WAV file
    sample_rate = 16000
    duration_sec = 3.0
    num_samples = int(sample_rate * duration_sec)
    freq = 440.0  # 440 Hz

    with wave.open(str(target_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            # Add slight modulation
            mod = math.sin(2.0 * math.pi * 5.0 * (i / sample_rate))
            value = int(10000 * math.sin(2.0 * math.pi * (freq + 20.0 * mod) * (i / sample_rate)))
            frames.extend(struct.pack("<h", value))
        wf.writeframes(frames)

    logger.info("Generated modulated PCM WAV fixture: %s", target_path)
