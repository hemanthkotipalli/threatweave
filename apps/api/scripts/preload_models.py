"""
apps/api/scripts/preload_models.py
-----------------------------------
Executed during Docker image build (not at runtime) to force model weight
downloads into the image layer. After this script completes, the container
will have all model files cached and will NOT attempt any network calls
to download models during a live demo or first request.

Models pre-cached:
  - EasyOCR 'en' (CRAFT text detector + CRNN recogniser, ~50 MB total)
  - faster-whisper 'base' model (CTranslate2 int8 format, ~145 MB)
"""
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("model-preload")


def preload_easyocr():
    log.info("Pre-loading EasyOCR (en, CPU)...")
    try:
        import easyocr
        import numpy as np
        reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        # Force a trivial inference to confirm the model is functional
        dummy = np.zeros((64, 256, 3), dtype=np.uint8)
        reader.readtext(dummy)
        log.info("EasyOCR pre-loaded successfully.")
    except Exception as exc:  # noqa: BLE001
        log.error("EasyOCR pre-load FAILED: %s", exc)
        sys.exit(1)


def preload_whisper():
    log.info("Pre-loading faster-whisper 'base' model (CPU, int8)...")
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        log.info("faster-whisper 'base' pre-loaded successfully.")
        del model
    except Exception as exc:  # noqa: BLE001
        log.error("faster-whisper pre-load FAILED: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    preload_easyocr()
    preload_whisper()
    log.info("All model weights cached. Image is demo-ready.")
