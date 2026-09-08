# ThreatWeave Docker Setup Guide

## Overview

This guide covers building, running, and verifying the full ThreatWeave stack
using Docker. Two images are built:

| Image | Purpose | Deployment target |
|---|---|---|
| `threatweave-api` | FastAPI backend with all ML agents | Render (single web service) |
| `threatweave-web` | Next.js frontend | Vercel (primary) / Docker fallback |

> **Note on apps/web/Dockerfile role:** Vercel natively handles Next.js deployment
> from git push without needing a Dockerfile. The `apps/web/Dockerfile` exists
> for full-stack local verification via `docker-compose.prod.yml` and as a
> deployment fallback if Vercel becomes unavailable. It is NOT used for actual
> Vercel deployments.

---

## Prerequisites

- Docker Engine ≥ 24.0
- Docker Compose plugin v2.x (`docker compose` not `docker-compose`)
- At minimum 8 GB free disk space (PyTorch + ML model weights are large)
- At minimum 4 GB RAM available to Docker

---

## Environment Setup

Copy the example file and fill in real values:

```bash
cp .env.example .env.prod
```

Mandatory variables for prod stack:

```bash
POSTGRES_PASSWORD=<strong-random-password>
GROQ_API_KEY=<your-groq-api-key>
JWT_SECRET_KEY=<64-char-random-secret>
```

---

## Building the Images

### API Image

```bash
cd apps/api
docker build -t threatweave-api .
```

**Expected build time:** 20–35 minutes on first build (downloads PyTorch, EasyOCR
model weights ~50 MB, and faster-whisper base model ~145 MB at build time).
Subsequent builds with unchanged `requirements.txt` use cached pip layer (~2–3 min).

**Model pre-caching step** — you will see this in the build log:
```
INFO  Pre-loading EasyOCR (en, CPU)...
INFO  EasyOCR pre-loaded successfully.
INFO  Pre-loading faster-whisper 'base' model (CPU, int8)...
INFO  faster-whisper 'base' pre-loaded successfully.
INFO  All model weights cached. Image is demo-ready.
```
This confirms model weights are baked into the image layer. A fresh container will
NOT download models on first request.

**Final image size:** ~1.12 GB (optimized with PyTorch CPU-only wheels + pre-cached models; avoids 5.5GB+ NVIDIA CUDA GPU binaries).

### Web Image

```bash
cd apps/web
docker build -t threatweave-web .
```

**Expected build time:** ~2 minutes (npm install + Next.js standalone Turbopack build).
**Final image size:** ~97.3 MB (Next.js standalone output excludes full node_modules).

---

## Running the Full Stack

### Minimal stack (no n8n)

```bash
# From the project root — pass your secrets via env file
docker compose -f docker-compose.prod.yml \
  --env-file .env.prod \
  up -d
```

### Full stack including n8n

```bash
docker compose -f docker-compose.prod.yml \
  --env-file .env.prod \
  --profile n8n \
  up -d
```

### Service ports (defaults)

| Service | Port | Notes |
|---|---|---|
| API backend | 8000 | Override with `API_PORT` env var |
| Web frontend | 3000 | Override with `WEB_PORT` env var |
| n8n (if enabled) | 5678 | Override with `N8N_PORT` env var |

### One-Time Setup: Ingest RAG Threat Intelligence Corpus
> [!IMPORTANT]
> A fresh ChromaDB volume starts without any indexed threat advisories. Until the corpus is ingested, RAG retrieval returns 0 citations and `intel_bonus` defaults to `0.0`.
> 
> Once the stack is up, run the one-time ingestion script inside the API container:
> ```bash
> docker exec threatweave-api-prod /venv/bin/python scripts/ingest_corpus.py
> ```
> For Render cloud deployment (Phase 21), execute this one-time command via Render Shell or a one-off pre-deploy job.

---

## Verifying the Stack is Healthy

### 1. Check container status

```bash
docker compose -f docker-compose.prod.yml ps
```

Expected output — all services `healthy` or `running`:
```
NAME                         STATUS          PORTS
threatweave-postgres-prod    healthy         5432/tcp
threatweave-chromadb-prod    running         8000/tcp
threatweave-api-prod         healthy         0.0.0.0:8000->8000/tcp
threatweave-web-prod         running         0.0.0.0:3000->3000/tcp
```

### 2. Health check the API

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "service": "threatweave-api"}
```

### 3. Run a full multimodal investigation end-to-end

```bash
# Step 1 — Register a user
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"docker-test@threatweave.local","password":"DockerTest123!"}' | jq .

# Step 2 — Login and grab JWT
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"docker-test@threatweave.local","password":"DockerTest123!"}' \
  | jq -r '.access_token')

# Step 3 — Submit multimodal investigation (image + text)
curl -s -X POST http://localhost:8000/api/v1/investigations \
  -H "Authorization: Bearer $TOKEN" \
  -F "title=Docker container verification" \
  -F "text_content=Urgent: Your account has been compromised. Click here to verify your identity immediately." \
  -F "image=@apps/api/sample.png" | jq .
```

---

## Verifying No Secrets Baked Into Image

```bash
docker history threatweave-api --no-trunc | grep -iE "groq|secret|password|api_key"
```

**Expected output:** empty (no matches). API keys and secrets are injected at
runtime via environment variables, never baked into any image layer.

---

## Verifying Models Are Truly Pre-Cached (No Runtime Downloads)

The model pre-caching runs at build time inside `scripts/preload_models.py`.
To confirm no network calls happen during inference:

```bash
# Start an isolated container with network disabled
docker run --rm --network=none \
  -e DATABASE_URL="postgresql://x:x@localhost/x" \
  -e CHROMA_PATH="/tmp/chroma" \
  -e GROQ_API_KEY="test" \
  -e JWT_SECRET_KEY="test-key-32-chars-minimum-length!" \
  threatweave-api \
  /venv/bin/python -c "
from app.core.ocr_engine import extract_text
from app.core.stt_engine import transcribe_audio
import numpy as np, cv2
# Force model load
img = np.zeros((64,256,3), dtype=np.uint8)
_, buf = cv2.imencode('.png', img)
result = extract_text(bytes(buf))
print('EasyOCR offline test PASSED:', result)
"
```

If this succeeds with `--network=none`, models are genuinely pre-cached.

---

## Troubleshooting

### `libGL error: unable to load driver` in container logs

This means `libgl1` is missing. Verify it is in the `apt-get install` line of
`apps/api/Dockerfile`. The current Dockerfile explicitly installs it.

### `OSError: libsndfile not found` from faster-whisper

`libsndfile1` must be installed in the runtime stage. It is included in the
current Dockerfile.

### `ffmpeg: command not found` during audio transcription

`ffmpeg` must be in the runtime stage (not just builder). Verify the runtime
`apt-get install` block includes `ffmpeg`.

### Postgres health check keeps failing

The API container depends on `postgres: condition: service_healthy`. If postgres
takes more than ~30 seconds to initialize (normal on first boot with data volume),
the API container will restart and retry. This is expected — give it 60 seconds.

### Model download attempted at first request (not at build time)

This means the `preload_models.py` script failed silently during build. Check
build logs for `ERROR  EasyOCR pre-load FAILED` or `ERROR  faster-whisper
pre-load FAILED`. Both failures cause `sys.exit(1)`, which will abort the build
rather than silently skip — so if the build succeeded, models are cached.

### `JWT_SECRET_KEY must be set to a strong secret` error on api startup

The `docker-compose.prod.yml` uses `:?` syntax which fails docker compose startup
if `JWT_SECRET_KEY` is not set. Set it in your `.env.prod` file.

---

## Build Times and Image Sizes (Observed)

| Image | First build | Cached build | Final size |
|---|---|---|---|
| `threatweave-api` | ~12 min | ~1.5 min | ~1.12 GB |
| `threatweave-web` | ~2 min | ~30s | ~97.3 MB |

> The API image was reduced from ~8.5 GB to 1.12 GB by leveraging CPU-only PyTorch
> wheels (`--index-url https://download.pytorch.org/whl/cpu`), which omits ~5.5 GB of
> unnecessary NVIDIA CUDA runtime binaries while keeping ML model weights baked in for
> instant offline inference.
