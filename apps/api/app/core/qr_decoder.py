"""
app/core/qr_decoder.py
-----------------------
Pure, network-free QR code decoding module for ThreatWeave Phase 7.

Uses OpenCV's QRCodeDetector to decode QR codes directly from image bytes.
Guaranteed never to raise — returns None on any failure, corruption, or empty input.
"""
from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger("threatweave-api.core.qr_decoder")


def decode_qr(image_bytes: bytes) -> str | None:
    """
    Decodes the text payload from a QR code contained in image bytes.

    :param image_bytes: Raw binary bytes of an image file (PNG, JPEG, WebP, etc.).
    :return: The decoded string payload, or None if no QR code could be found
             or if the image is invalid / unparseable.
    """
    if not image_bytes or not isinstance(image_bytes, bytes):
        logger.debug("decode_qr received empty or non-bytes input")
        return None

    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        if nparr.size == 0:
            logger.debug("decode_qr: byte buffer resulted in empty numpy array")
            return None

        cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if cv_img is None:
            logger.debug("decode_qr: cv2.imdecode failed to parse image bytes")
            return None

        detector = cv2.QRCodeDetector()
        decoded_text, points, _ = detector.detectAndDecode(cv_img)

        if points is not None and decoded_text:
            cleaned = decoded_text.strip()
            if cleaned:
                logger.debug("decode_qr successfully decoded payload of length %d", len(cleaned))
                return cleaned

        logger.debug("decode_qr: no QR code found or decoded payload is empty")
        return None

    except Exception as exc:  # noqa: BLE001
        logger.debug("decode_qr encountered error while decoding: %s", exc)
        return None
