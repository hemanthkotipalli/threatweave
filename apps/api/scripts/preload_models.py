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
import os
import sys
from pathlib import Path

# Ensure apps/api root is on sys.path so app modules can be imported
_API_ROOT = Path(__file__).resolve().parent.parent
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))

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


def preload_sentence_transformer():
    log.info("Pre-loading sentence-transformers 'all-MiniLM-L6-v2' (CPU)...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
        model.encode("ThreatWeave threat intelligence advisory pre-cache", convert_to_numpy=True)
        log.info("sentence-transformers 'all-MiniLM-L6-v2' pre-loaded successfully.")
        del model
    except Exception as exc:  # noqa: BLE001
        log.error("sentence-transformers pre-load FAILED: %s", exc)
        sys.exit(1)


def preload_chroma_corpus():
    """
    Pre-indexes all 24 advisory documents into ChromaDB during Docker build.
    This bakes the vector collection into the image layer, eliminating memory-intensive
    runtime batch-encoding at startup and preventing Render Free 512MB OOM restarts.
    """
    log.info("Pre-indexing advisory corpus into ChromaDB during Docker build...")
    try:
        import os

        # Provide fallback build-time environment variables for Settings validation
        os.environ.setdefault("DATABASE_URL", "postgresql://build:build@localhost:5432/build")
        os.environ.setdefault("CHROMA_PATH", "/app/chroma_db" if os.path.exists("/app") else "./chroma_db")
        os.environ.setdefault("GROQ_API_KEY", "build_dummy_groq_key")
        os.environ.setdefault("OMP_NUM_THREADS", "1")
        os.environ.setdefault("MKL_NUM_THREADS", "1")
        os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

        from app.rag.ingest import ingest_corpus

        res = ingest_corpus()
        log.info("ChromaDB build-time pre-index complete: %s", res)
    except Exception as exc:  # noqa: BLE001
        log.error("ChromaDB pre-index FAILED: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    preload_easyocr()
    preload_whisper()
    preload_sentence_transformer()
    preload_chroma_corpus()
    log.info("All model weights and vector indices cached. Image is demo-ready.")
