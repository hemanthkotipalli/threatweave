# ThreatWeave CI/CD Setup Guide

## Overview

ThreatWeave uses **GitHub Actions** for automated Continuous Integration (CI) and Continuous Deployment (CD).

The pipeline adheres strictly to the target deployment architecture:
* **Backend API (`apps/api`):** Deployed to **Render** as a Dockerized Web Service.
* **Frontend Web (`apps/web`):** Deployed to **Vercel** as a high-performance Next.js 16 application.
* **AWS tooling is explicitly excluded.**
* **Registry-Free Build Sanity:** Docker containers are verified via Buildx without requiring Docker Hub or GHCR registry credentials.

---

## 1. Pipeline Architecture

```
                       [ Push / Pull Request ]
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
       [ api-ci (Python 3.11) ]         [ web-ci (Node 20) ]
       - postgres:16 service container  - eslint app components lib
       - CPU-optimized PyTorch wheels   - next build (standalone)
       - ruff check .                                     │
       - alembic upgrade head                             │
       - pytest (197+ test suite)                         │
                 │                                        │
                 └────────────────┬───────────────────────┘
                                  ▼
                     [ docker-sanity (Buildx) ]
                     - Build threatweave-api (push: false, GHA cache)
                     - Build threatweave-web (push: false, GHA cache)
                     - Audit image layers for secrets
                     - Validate non-root users (appuser / nextjs)
                                  │
       ┌──────────────────────────┴──────────────────────────┐
       │ GATED: workflow_run on CI Pipeline success on main  │
       └──────────────────────────┬──────────────────────────┘
                                  ▼
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
       [ deploy-api-render ]             [ deploy-web-vercel ]
       - POST RENDER_DEPLOY_HOOK         - amondnet/vercel-action@v25
       - Zero-downtime container         - Edge deployment
       - Post-deploy /health polling     - Post-deploy edge verification
```

---

## 2. Workflows Reference

### A. Continuous Integration (`.github/workflows/ci.yml`)

**Trigger Scope**:
* Any `pull_request` targeting `main`, `master`, or `develop`.
* Any `push` to `main`, `master`, or `develop`.
* Ignores documentation files (`docs/**`, `**.md`, `.gitignore`).

**Jobs**:
1. **`api-ci`**:
   * Runs on `ubuntu-latest` with a native `postgres:16-alpine` service container.
   * Installs required OS runtime libraries (`libgl1`, `ffmpeg`, `libsndfile1`, `libgomp1`, `libglib2.0-0`).
   * Installs PyTorch CPU wheels (`--index-url https://download.pytorch.org/whl/cpu`) first to eliminate 5.5 GB+ CUDA bloat and keep CI builds under 3 minutes.
   * Runs static analysis (`ruff check .`).
   * Applies schema migrations (`alembic upgrade head`) against the active PostgreSQL service.
   * Executes the full automated test suite (`pytest -v --maxfail=5`).
2. **`web-ci`**:
   * Runs on `ubuntu-latest` with Node.js 20 and npm cache.
   * Executes static analysis (`npm run lint`).
   * Validates the production build (`npm run build`) in Next.js 16 Turbopack standalone mode.
3. **`docker-sanity`**:
   * Depends on `[api-ci, web-ci]` passing.
   * Utilizes Docker Buildx with GitHub Actions caching (`type=gha,mode=max`).
   * Dry-run builds both production Dockerfiles (`push: false`, `load: true`).
   * **Requires ZERO registry credentials**: Render builds directly from repository git commits, so no Docker Hub or GHCR push steps or secrets are needed.
   * Audits runtime user security (`appuser` UID 1001, `nextjs` UID 1001) and inspects image layer history for leaked credentials.

### B. Continuous Deployment (`.github/workflows/cd.yml`)

**Strict CI Gating**:
* Triggered via `workflow_run` event listening specifically to `"CI Pipeline"` completion on branch `main`.
* Executed only when `github.event.workflow_run.conclusion == 'success'` (or via manual `workflow_dispatch`).
* **Guarantees that broken code can NEVER be deployed to live production**.

**Jobs**:
1. **`deploy-api-render`**:
   * Triggers Render's automated deployment webhook via HTTPS POST.
   * **Active Post-Deploy Smoke Test**: Continuously polls `GET $RENDER_API_URL/health` every 15 seconds (up to 10 minutes). The workflow only marks success once the live Render container responds with HTTP 200 `{"status": "ok", "service": "threatweave-api"}`.
2. **`deploy-web-vercel`**:
   * Deploys the production web application directly to Vercel's global edge network using `amondnet/vercel-action@v25`.
   * **Active Edge Verification**: Performs an HTTP request against the live Vercel domain to confirm edge propagation.

---

## 3. GitHub Secrets Configuration Guide

To enable automated CD and post-deploy smoke tests, configure the following secrets in GitHub under:
**Repository Settings &rarr; Secrets and variables &rarr; Actions &rarr; Repository secrets**

| Secret Name | Service | Purpose | Mandatory? | How to Obtain |
|---|---|---|---|---|
| `RENDER_DEPLOY_HOOK_URL` | Render | Webhook URL to trigger automatic backend rebuild & deploy | **Yes** | Render Dashboard &rarr; API Service &rarr; **Settings** &rarr; **Deploy Hook** &rarr; Copy URL |
| `RENDER_API_URL` | Render | Base URL of deployed API for post-deploy smoke testing | Recommended | E.g. `https://threatweave-api.onrender.com` (found on service dashboard) |
| `VERCEL_TOKEN` | Vercel | Personal access token for authenticating Vercel deployments | **Yes** | Vercel Account &rarr; **Settings** &rarr; **Tokens** &rarr; **Create Token** |
| `VERCEL_ORG_ID` | Vercel | Identifier for your Vercel organization/team account | **Yes** | Run `npx vercel link` locally or find in `.vercel/project.json` |
| `VERCEL_PROJECT_ID` | Vercel | Identifier for the ThreatWeave web project on Vercel | **Yes** | Vercel Project &rarr; **Settings** &rarr; **General** &rarr; **Project ID** |
| `VERCEL_APP_URL` | Vercel | Production URL for edge verification | Optional | E.g. `https://threatweave.vercel.app` |

---

## 4. One-Time Setup: Ingest RAG Threat Intelligence Corpus

> [!IMPORTANT]
> A fresh ChromaDB persistent volume on Render starts with zero threat advisories. Until the corpus is ingested, RAG vector retrieval yields 0 citations and `intel_bonus` defaults to `0.0`.

### Procedure on First Deployment to Render:
1. Navigate to the Render Dashboard &rarr; select the `threatweave-api` service &rarr; open the **Shell** tab.
2. Run the one-time corpus ingestion command:
   ```bash
   python scripts/ingest_corpus.py
   ```
3. Expected output:
   ```
   INFO  Parsing CISA, MITRE, and PhishTank advisory feeds...
   INFO  Generating sentence-transformer embeddings...
   INFO  Ingested 142 threat intelligence documents into 'threat_advisories' collection.
   INFO  Corpus ingestion complete.
   ```
4. Confirm RAG grounding by triggering a test investigation or running:
   ```bash
   python -c "import chromadb; c = chromadb.PersistentClient(path='/data/chroma'); print('Advisories count:', c.get_collection('threat_advisories').count())"
   ```

---

## 5. Branch Protection Rules

To protect production stability, configure a branch protection rule for `main`:

1. In GitHub, navigate to **Settings &rarr; Branches &rarr; Add branch protection rule**.
2. **Branch name pattern:** `main`
3. Check the following options:
   * **Require a pull request before merging:**
     - Require approvals: 1
   * **Require status checks to pass before merging:**
     - Check: `API Backend Lint & Test`
     - Check: `Web Frontend Lint & Build`
     - Check: `Docker Container Build Sanity`
   * **Do not allow bypassing the above settings.**

---

## 6. Deployment Verification & Rollbacks

### A. Health Monitoring
* **Backend Health Check:** `https://<your-render-app>.onrender.com/health` returns `{"status": "ok", "service": "threatweave-api"}`.
* **Frontend Production URL:** `https://threatweave.vercel.app`.

### B. Rollback Procedures
* **Render Rollback:** In Render Dashboard &rarr; **Deploys** &rarr; Select previous successful build &rarr; Click **Rollback to this deploy**.
* **Vercel Rollback:** In Vercel Dashboard &rarr; **Deployments** &rarr; Locate previous production deployment &rarr; Click **...** &rarr; **Promote to Production**.
