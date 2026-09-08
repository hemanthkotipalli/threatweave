# Known Limitations & Engineering Boundaries

ThreatWeave is designed as an agentic, multimodal cyber threat intelligence and incident response orchestrator. This document candidly outlines the architectural boundaries, operational constraints, and intentional design trade-offs of the system as implemented through Phase 18. 

Documenting these limitations is a deliberate engineering practice: knowing precisely where a system's guarantees end is essential for production readiness and academic credibility.

---

## 1. URL Analysis & Redirect Chain Depth
* **Current Behavior:** The `URL Agent` extracts domain components, IP address representations, homoglyphs, brand typosquatting targets, suspicious TLDs, and path entropy statically using heuristic parsing and regex tokenization.
* **Limitation:** ThreatWeave does **not** execute live HTTP request dispatching, headless browser execution (e.g., Playwright/Puppeteer), or multi-hop redirect-chain following.
* **Engineering Justification & Trade-off:** Following live untrusted links inside an automated analysis pipeline introduces server-side request forgery (SSRF) attack vectors and risks notifying malicious threat actors that their infrastructure is being actively probed. In a production deployment, this would be delegated to a sandboxed external crawler (e.g., URLScan or VirusTotal API), but within ThreatWeave's self-contained pipeline, analysis is intentionally performed statically.

---

## 2. Threat Intelligence Knowledge Base (Static vs. Real-Time RAG)
* **Current Behavior:** The RAG retrieval pipeline (`Phase 12`) indexes curated threat intelligence advisories — specifically CERT-In (Indian Computer Emergency Response Team) security advisories, RBI (Reserve Bank of India) cyber fraud alerts, and curated Indian-context scam intelligence — in ChromaDB using dense semantic embeddings (`sentence-transformers/all-MiniLM-L6-v2`).
* **Limitation:** ThreatWeave does **not** ingest live, real-time threat intelligence feeds (e.g., TAXII/STIX streams, commercial TIP feeds, or automated CERT-In RSS/API pipelines). The vector corpus represents a curated baseline snapshot of advisories relevant to the Indian financial and digital fraud threat landscape.
* **Operational Impact:** Newly emerged scam campaigns, phishing kits, or fraud indicators published after the corpus indexing date will not have exact advisory correlation matches, relying instead on the specialist agents' heuristic and LLM zero-shot classification.

---

## 3. Multilingual & Script Generalization
* **Current Behavior:** ThreatWeave accepts and processes arbitrary UTF-8 text, including Cyrillic, East Asian, Arabic, and Devanagari scripts, as well as emojis, without database encoding errors or pipeline crashes.
* **Limitation:** Threat analysis quality, heuristic keyword matching, and tone classification are noticeably weaker on non-English text than on English inputs.
* **Reasoning:**
  - Urgency and scare-tactic heuristic dictionaries (`app/core/text_heuristics.py`) are primarily modeled in English.
  - OCR (`EasyOCR`) is configured with English language weights (`['en']`) by default for throughput reasons, meaning non-Latin alphabet screenshot extraction has significantly degraded confidence.
  - While Groq's underlying LLMs possess multilingual capabilities, prompt engineering and few-shot guidance are optimized for English incident response.

---

## 4. Voice Agent & Deepfake/Synthetic Audio Scope
* **Current Behavior:** The `Voice Agent` (`Phase 9`) transcribes audio via `faster-whisper`, extracts acoustic telemetry (zero-crossing rate, spectral centroid, spectral rolloff, RMS energy), and inspects transcripts for social engineering/vishing script patterns.
* **Deliberate Anti-Proof Claim:** As established in Phase 9, ThreatWeave **deliberately does not claim to reliably detect AI-generated voice or deepfakes**.
* **Scientific Reality:** Reliable, generalized deepfake audio detection on compressed telephony/voicemail audio (8kHz–16kHz) remains an unsolved research problem prone to high false-positive rates. Acoustic indicators of synthetic speech are strictly treated as **weak advisory signals** (capped at a confidence of `<= 0.40`), and the system never outputs an assertion that audio is "proven synthetic." Threat classification focuses squarely on behavioral social engineering indicators (urgency, impersonation, credential harvesting pleas).

---

## 5. Groq Free-Tier Rate Limits & Fallback Degradation
* **Current Behavior:** LLM synthesis across specialist agents and the final incident summary utilizes Groq's cloud inference endpoint (`llama-3.3-70b-versatile` and `llama-3.1-8b-instant`). If the API key is missing, network fails, or HTTP 429 (Rate Limit Exceeded) is returned, agents seamlessly fall back to local rule-based heuristics.
* **Limitation Under Concurrency:** Under heavy concurrent load (such as multiple simultaneous users triggering investigations in parallel or rapid sequential demo runs), Groq's free-tier rate limits (requests per minute and tokens per minute) can be saturated.
* **Graceful Degradation Trade-off:** When rate-limited, investigations continue to complete successfully without throwing 500 errors, but analysis depth falls back to purely deterministic heuristics, resulting in less detailed narrative reasoning and static indicator summaries.

---

## 6. Single-Server Architectural Footprint
* **Current Behavior:** The API backend is architected as an asynchronous FastAPI application backed by a single PostgreSQL instance and local ChromaDB storage/HTTP service.
* **Limitation:** The current deployment model does not support distributed, horizontally-scaled worker pools (e.g., Celery/RabbitMQ, Redis queue brokers, or Kubernetes worker replicas).
* **Implications:**
  - Heavy CPU-bound workloads (such as EasyOCR neural text extraction and Whisper audio transcription) run within thread pools on the host machine.
  - Concurrent requests share CPU and GPU/RAM resources. While session isolation in database transactions is strictly guaranteed (verified in `test_concurrency.py`), total throughput is bounded by the host machine's compute cores.

---

## 7. Authentication Storage & Deployment Boundaries
* **Current Behavior:** JWT authentication (`Phase 17`) persists tokens in the browser's `localStorage`, with an automated `AuthGuard` protecting investigation-creation routes while keeping `/demo/*` endpoints universally accessible.
* **Limitation:** In a hardened multi-tenant SaaS environment, session tokens should ideally be stored in `httpOnly`, `Secure`, `SameSite=Strict` cookies to provide defense-in-depth against cross-site scripting (XSS).
* **Development Trade-off:** `localStorage` was deliberately selected to support cross-origin decoupled execution during local evaluation (`localhost:3000` Next.js frontend communicating with `localhost:8000` FastAPI backend without CORS/cookie-domain complications).

---

## Summary Matrix

| Capability Dimension | Production Ideal | ThreatWeave Current Implementation | Architectural Rationale |
| :--- | :--- | :--- | :--- |
| **URL Crawling** | Live headless browser sandbox | Static parsing & heuristic decomposition | Eliminates SSRF risks and active-scan detection |
| **Threat Feeds** | Real-time STIX/TAXII pipelines | Curated ChromaDB vector collection | Self-contained, reproducible offline evaluation |
| **Multilingual** | Multi-model multilingual OCR/NLP | English-optimized with UTF-8 safety | High accuracy on target language without bloating models |
| **Voice Deepfake** | Neural biometrics / vocoder artifacts | Vishing script analysis + weak acoustic cues | Honest refusal to claim unproven detection capability |
| **LLM Inference** | Dedicated enterprise LLM cluster | Groq API with deterministic heuristic fallback | Resilient operation without mandatory paid infrastructure |
| **Scaling** | Distributed task queue (Celery/K8s) | Async FastAPI + ThreadPool worker pools | Low operational complexity for evaluation & demonstration |
