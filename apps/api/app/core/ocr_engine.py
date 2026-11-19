"""
app/core/ocr_engine.py
-----------------------
Pure-python OCR text extraction engine for ThreatWeave Phase 8.

Uses EasyOCR (PyTorch-based) to extract text and detection confidence scores
from screenshots and images without requiring host-system binary dependencies.

Guaranteed never to raise — returns ("", 0.0) on corrupted, blank, or invalid input.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    import easyocr

logger = logging.getLogger("threatweave-api.core.ocr_engine")

_CACHED_READER: easyocr.Reader | None = None


def _get_reader() -> easyocr.Reader:
    """
    Lazily initializes and caches a singleton EasyOCR Reader instance.
    Configured for CPU execution to ensure cross-platform compatibility.
    """
    global _CACHED_READER
    if _CACHED_READER is None:
        import easyocr

        logger.info("Initializing EasyOCR reader (CPU mode)")
        _CACHED_READER = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _CACHED_READER


def release_ocr_memory() -> None:
    """
    Explicitly releases the cached EasyOCR reader and PyTorch weight buffers
    to prevent memory exhaustion in constrained environments.
    """
    global _CACHED_READER
    if _CACHED_READER is not None:
        logger.info("Releasing EasyOCR reader from memory")
        del _CACHED_READER
        _CACHED_READER = None
        import gc
        gc.collect()


def extract_text(image_bytes: bytes) -> tuple[str, float]:
    """
    Extracts text and an average confidence score from image bytes.

    :param image_bytes: Raw binary bytes of an image (PNG, JPEG, WebP, etc.).
    :return: Tuple of (extracted_text: str, average_confidence: float [0.0 - 1.0]).
             Returns ("", 0.0) on failure, empty input, or unreadable image data.
    """
    if not image_bytes or not isinstance(image_bytes, bytes):
        logger.debug("extract_text received empty or non-bytes input")
        return "", 0.0

    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        if nparr.size == 0:
            logger.debug("extract_text: byte buffer resulted in empty numpy array")
            return "", 0.0

        cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if cv_img is None:
            logger.debug("extract_text: cv2.imdecode failed to parse image bytes")
            return "", 0.0

        # Cap maximum dimension to 1024px to prevent PyTorch CRAFT OOM memory spikes
        h, w = cv_img.shape[:2]
        max_dim = max(h, w)
        if max_dim > 1024:
            scale = 1024.0 / max_dim
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            cv_img = cv2.resize(cv_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

        import torch

        reader = _get_reader()
        # readtext returns list of tuples: (bbox, text, confidence)
        with torch.inference_mode():
            results = reader.readtext(cv_img)

        # Release intermediate image buffer and reclaim unreferenced memory
        del cv_img, nparr
        import gc
        gc.collect()

        if not results:
            logger.debug("extract_text: no text detected in image")
            return "", 0.0

        extracted_lines: list[str] = []
        confidences: list[float] = []

        for item in results:
            if len(item) >= 2:
                text = str(item[1]).strip()
                if text:
                    extracted_lines.append(text)
            if len(item) >= 3:
                try:
                    conf = float(item[2])
                    confidences.append(max(0.0, min(1.0, conf)))
                except (ValueError, TypeError):
                    pass

        joined_text = "\n".join(extracted_lines).strip()
        avg_confidence = (
            round(sum(confidences) / len(confidences), 4) if confidences else 0.5
        )

        return joined_text, avg_confidence

    except Exception as exc:  # noqa: BLE001
        logger.debug("extract_text encountered unhandled error: %s", exc)
        return "", 0.0
