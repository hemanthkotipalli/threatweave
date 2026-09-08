# =============================================================================
# apps/api/Dockerfile — ThreatWeave API (Production)
# =============================================================================
# Multi-stage build:
#   Stage 1 (builder): installs all Python deps into a venv
#   Stage 2 (runtime): copies venv + app code, pre-caches ML models, runs uvicorn
#
# Base: python:3.11-slim (Debian bookworm-slim) — matches dev Python version
# Target platform: Render (single web service, $PORT env var convention)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1 — builder: install Python dependencies
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# System packages required at pip install time only (compilers, headers).
# These are NOT copied to the final stage.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements first so pip install layer is cached independently from
# application code changes.
COPY requirements.txt .

# Create an isolated venv and install all deps.
# Explicitly install PyTorch CPU wheels first to avoid pulling 5.5GB+ of unused
# NVIDIA CUDA packages into a CPU container.
RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    /venv/bin/pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2 — runtime: lean image with only what is needed to run
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# ─── OS-level runtime libraries ───────────────────────────────────────────────
# Each package is justified by a real runtime dependency:
#
#   libgl1            — opencv-python-headless needs libGL.so.1 even in headless
#                       mode (used by cv2.imdecode in image_agent.py)
#   libglib2.0-0      — required by GLib/GObject which libGL links against
#   libgomp1          — GNU OpenMP runtime; PyTorch uses OpenMP threads for CPU
#                       inference (easyocr / sentence-transformers)
#   ffmpeg            — faster-whisper's CTranslate2 backend uses ffmpeg shared
#                       libs for audio decode; also required by PyAV (voice_agent)
#   libsndfile1       — libsndfile is a transitive dep of soundfile (faster-whisper)
#   libgomp1          — already listed above (explicit for clarity)
#
# We deliberately do NOT install espeak/libespeak — pyttsx3 is in requirements.txt
# but is NOT invoked by any agent at runtime (verified by reading voice_agent.py).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security best practice
RUN useradd -m -u 1001 appuser

WORKDIR /app

# Copy the installed venv from builder stage — this is the core of the
# multi-stage benefit: build tools and .whl caches do NOT enter this stage.
COPY --from=builder /venv /venv

# Copy application source code (no tests, no venv, no .env — see .dockerignore)
COPY alembic/ alembic/
COPY alembic.ini alembic.ini
COPY app/ app/
COPY scripts/ scripts/

# Create writable directories for uploaded files and chroma local storage.
# In docker-compose.prod.yml these are mounted as named volumes.
RUN mkdir -p /app/storage /app/chroma_db && \
    chown -R appuser:appuser /app/storage /app/chroma_db

# ─── Model pre-caching ────────────────────────────────────────────────────────
# Run as appuser so model weights (EasyOCR, faster-whisper) are saved directly
# into /home/appuser with correct ownership.
USER appuser

RUN /venv/bin/python scripts/preload_models.py

# ─── Health check ─────────────────────────────────────────────────────────────
# Render's health check probes /health before marking the service healthy.
# Interval 30s, timeout 10s, 3 retries before marking unhealthy.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/health')" || exit 1

# Expose the default port (overridden by Render via $PORT env var)
EXPOSE 8000

# ─── Entrypoint ───────────────────────────────────────────────────────────────
# Uses $PORT if set by the runtime environment (Render convention), falls back
# to 8000 for local docker-compose runs.
# 2 workers: sufficient for a demo deployment; keeps memory usage manageable
# given the ML model sizes loaded per-worker.
# Alembic runs migrations first to ensure schema is current on every boot.
CMD ["/bin/sh", "-c", \
     "/venv/bin/alembic upgrade head && \
      exec /venv/bin/uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${PORT:-8000} \
        --workers 1 \
        --no-access-log"]
