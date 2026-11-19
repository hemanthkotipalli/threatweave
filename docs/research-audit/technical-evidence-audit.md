# ThreatWeave: Technical Evidence Audit Report
**Document Class:** Academic & Engineering Architectural Evidence Audit  
**Project:** ThreatWeave: An Agentic Multimodal Framework for Cross-Modal Digital Communication Threat Analysis  
**Repository Working Directory:** `d:\ThreatWeave — Agentic Multimodal\threatweave`  
**Audit Date:** November 19, 2026  
**Auditor:** Senior Software Architect & Cybersecurity Academic Reviewer  

---

## 1. Executive Summary

This document presents a comprehensive, evidence-based technical audit of the **ThreatWeave** codebase. Every claim in this document is traced directly to physical files, line numbers, function definitions, database models, and test fixtures within the repository.

ThreatWeave is an agentic, multimodal cybersecurity analysis platform designed to ingest and correlate multi-vector cyber fraud evidence across five distinct modalities: text (SMS/email), web links (URLs), QR codes, image screenshots (payment receipts, fake government notices), and voice recordings (vishing phone calls). The architecture coordinates these specialist analysis channels through a compiled **LangGraph StateGraph** orchestration machine, enriches findings using an offline **Retrieval-Augmented Generation (RAG)** corpus of 24 Indian regulatory advisories (CERT-In, RBI, Scam-Intel), and computes an explainable threat assessment using a deterministic, four-part mathematical risk engine.

---

## 2. Technology Stack & Component Verification

The following table provides an exhaustive verification of every major technology utilized across ThreatWeave. Every entry has been verified by inspecting package manifests, runtime code imports, and active container configurations.

| Subsystem / Layer | Technology Name | Exact Version (if verified) | Architectural Role / Purpose | Concrete Repository Evidence / File Path | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Backend Framework** | FastAPI | 0.115.0 (`requirements.txt:13`) | Asynchronous REST API routing, request validation, lifespan management | [`apps/api/app/main.py:1-70`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/main.py#L1-L70) | Implemented & Verified |
| **ASGI Server** | Uvicorn (standard) | 0.30.6 (`requirements.txt:14`) | High-concurrency asynchronous HTTP server | [`apps/api/Dockerfile:109-115`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/Dockerfile#L109-L115) | Implemented & Verified |
| **Data Validation & Typing** | Pydantic / Pydantic Settings | 2.8.2 / 2.4.0 (`requirements.txt:16-17`) | Strictly typed schema enforcement, input coercion, environment config | [`apps/api/app/core/config.py:1-112`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/config.py#L1-L112), [`apps/api/app/schemas/`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/schemas/) | Implemented & Verified |
| **Relational Database** | PostgreSQL | 16 (Debian/Alpine base) | ACID persistence for investigations, evidence inputs, agent runs, findings, conflicts, risk breakdowns | [`docker-compose.yml:4-15`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/docker-compose.yml#L4-L15), [`apps/api/app/models/`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/models/) | Implemented & Verified |
| **Database ORM & Migrations** | SQLAlchemy / Alembic | 2.0.32 / 1.13.2 (`requirements.txt:1-2`) | Declarative schema definitions, relational cascade deletes, schema migrations | [`apps/api/app/db/base_class.py:1-12`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/db/base_class.py#L1-L12), [`apps/api/alembic/`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/alembic/) | Implemented & Verified |
| **Database Driver** | psycopg (v3) / psycopg2-binary | 3.1.18 / 2.9.9 (`requirements.txt:3-4`) | High-performance Python-to-PostgreSQL binary communication protocol | [`apps/api/app/db/session.py:1-25`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/db/session.py#L1-L25) | Implemented & Verified |
| **Agent Orchestration** | LangGraph / LangChain Core | 0.2.14 / 0.2.34 (`requirements.txt:28-29`) | Directed cyclic/acyclic state machine (`StateGraph`), dynamic parallel fan-out and fan-in | [`apps/api/app/agents/graph.py:1-110`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/graph.py#L1-L110) | Implemented & Verified |
| **Primary LLM Provider** | Groq Cloud API | SDK 0.9.0 (`requirements.txt:32`) | Fast cloud inference for JSON threat synthesis; default model `openai/gpt-oss-120b` | [`apps/api/app/agents/llm_client.py:1-135`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/llm_client.py#L1-L135) | Implemented & Verified |
| **Vector Database** | ChromaDB | 0.5.5 (`requirements.txt:24`) | Dense vector storage, persistent cosine similarity search, offline HNSW index | [`apps/api/app/rag/chroma_client.py:1-153`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/rag/chroma_client.py#L1-L153) | Implemented & Verified |
| **Embedding Engine** | Sentence-Transformers | 3.0.1 (`requirements.txt:25`) | Local CPU dense embedding computation; model `all-MiniLM-L6-v2` (384 dimensions) | [`apps/api/app/rag/embeddings.py:1-100`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/rag/embeddings.py#L1-L100) | Implemented & Verified |
| **Deep Learning Framework** | PyTorch (CPU wheel) | 2.4.0+cpu (`Dockerfile:36`) | Execution backend for Sentence-Transformers, EasyOCR recognizer, PyAV tensors | [`apps/api/Dockerfile:36`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/Dockerfile#L36), [`apps/api/app/rag/embeddings.py:14-25`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/rag/embeddings.py#L14-L25) | Implemented & Verified |
| **OCR Text Extraction** | EasyOCR | 1.7.1 (`requirements.txt:37`) | Two-stage deep learning optical character recognition (CRAFT text detector + CRNN recognizer) | [`apps/api/app/core/ocr_engine.py:1-85`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/ocr_engine.py#L1-L85) | Implemented & Verified |
| **Computer Vision** | OpenCV (headless) | 4.10.0.84 (`requirements.txt:38`) | Image decoding (`imdecode`), QR code location & detection (`QRCodeDetector`), bounding boxes | [`apps/api/app/core/qr_decoder.py:1-75`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/qr_decoder.py#L1-L75) | Implemented & Verified |
| **Alternative Barcode Decoder** | PyZbar | 0.1.9 (`requirements.txt:39`) | Secondary fallback QR/barcode scanning engine | [`apps/api/app/core/qr_decoder.py:35-50`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/qr_decoder.py#L35-L50) | Implemented & Verified |
| **Speech-to-Text (STT)** | faster-whisper | 1.0.3 (`requirements.txt:44`) | CTranslate2-accelerated offline Whisper transcription; default model `base` (int8 quantized) | [`apps/api/app/core/stt_engine.py:1-90`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/stt_engine.py#L1-L90) | Implemented & Verified |
| **Audio Container Decoding** | PyAV | 12.3.0 (`requirements.txt:45`) | FFmpeg Python binding for probing and demuxing arbitrary audio containers (WAV, MP3, AAC, OGG) | [`apps/api/app/agents/voice_agent.py:160-185`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/voice_agent.py#L160-L185) | Implemented & Verified |
| **PDF Report Generation** | ReportLab | 4.2.2 (`requirements.txt:48`) | Programmatic generation of formal forensic investigation audit certificates in PDF format | [`apps/api/app/services/report_service.py:1-180`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/services/report_service.py#L1-L180) | Implemented & Verified |
| **Frontend Framework** | Next.js (App Router) | 16.3.1 (`package.json:14`) | React server & client components, dynamic routing, streaming UI | [`apps/web/package.json:14`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/web/package.json#L14), [`apps/web/app/`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/web/app/) | Implemented & Verified |
| **UI Library & Components** | React / Lucide React | 19.2.8 / 1.32.0 (`package.json:13-16`) | Component rendering, hooks, reactive state, SVG cybersecurity iconography | [`apps/web/components/`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/web/components/) | Implemented & Verified |
| **Styling & Design System** | Tailwind CSS | 4.0.0 (`package.json:26`) | Utility-first responsive CSS design, dark/light security dashboard theme | [`apps/web/app/globals.css:1-60`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/web/app/globals.css#L1-L60) | Implemented & Verified |
| **Workflow Automation** | n8n | latest container (`docker-compose.yml:29`) | Webhook event ingestion and automated security alerting pipeline | [`docker-compose.yml:29-49`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/docker-compose.yml#L29-L49), [`apps/api/app/services/webhook_service.py:1-65`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/services/webhook_service.py#L1-L65) | Implemented & Verified |
| **Authentication & Tokens** | python-jose / passlib (bcrypt) | 3.3.0 / 1.7.4 (`requirements.txt:20-21`) | JWT access token creation/validation, salted bcrypt password hashing | [`apps/api/app/core/security.py:1-60`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/security.py#L1-L60), [`apps/api/app/api/deps.py:1-120`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/api/deps.py#L1-L120) | Implemented & Verified |
| **CI / CD Pipeline** | GitHub Actions | Workflows `ci.yml`, `cd.yml` | Automated unit testing, linting, build verification, and deployment triggering | [`.github/workflows/ci.yml`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/.github/workflows/ci.yml), [`.github/workflows/cd.yml`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/.github/workflows/cd.yml) | Implemented & Verified |
| **End-to-End Testing** | Playwright | 1.63.0 (`package.json:19`) | Headless browser automation testing auth, investigation uploads, and demo views | [`apps/web/e2e/`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/web/e2e/) | Implemented & Verified |

---

## 3. Discrepancy Analysis: Stated vs. Actual Implementation

In academic research, misalignments between documentation/presentations and actual codebase reality weaken research credibility. The following table identifies all verified discrepancies:

| Topic / Area | Stated / Documented Claim | Verified Codebase Reality | Research Paper Positioning Recommendation |
| :--- | :--- | :--- | :--- |
| **Voice Detection** | "AI-generated voice / deepfake detection" | Speech transcription (Faster-Whisper) + regex vishing keyword detection + acoustic pause/pitch variance heuristics (`app/agents/voice_agent.py`). No deep neural generative voice classifier (e.g., RawNet2 or AASIST) exists. | State clearly: "Multimodal Voice Agent performs Faster-Whisper transcription, vishing social-engineering heuristic pattern matching, and acoustic cadence variance analysis; deep generative neural voice detection is scoped for future work." |
| **Processing Latency** | "Real-time call screening / instant interception" | Batch asynchronous investigation pipeline. Full multimodal runs require between 1.5s and 6.0s depending on Whisper and OCR workloads (`docs/evaluation-results.md:80-92`). | Position as: "Near-real-time asynchronous forensic investigation platform", not a sub-millisecond network wire blocker. |
| **Cloud Deployment** | "AWS EC2, Nginx reverse proxy" | Fully containerized with Docker Compose locally (`docker-compose.yml`), deployed in production across Render Free (FastAPI backend), Vercel Hobby (Next.js), and Supabase (PostgreSQL pooler). | Document as: "Containerized Microservices Architecture validated on zero-expenditure cloud tiers (Render, Vercel, Supabase) and container-ready for AWS EC2/Nginx." |
| **URL Reputation** | "Comprehensive global live reputation intelligence" | `reputation_client.py` supports Google Safe Browsing API v4, but gracefully falls back to purely lexical/structural heuristics if unconfigured (`url_heuristics.py`). | Report that URL analysis combines static lexical heuristics (Levenshtein typosquatting, entropy, IP hosts) with optional threat feed integration. |
| **RAG Knowledge Base** | "Comprehensive scam intelligence engine" | Seeded with exactly 24 curated Indian cybersecurity advisories (8 CERT-In, 8 RBI, 8 Scam-Intel). Highly domain-specific, but not an exhaustive global database. | Emphasize: "Domain-grounded threat intelligence corpus comprising 24 official Indian regulatory and banking advisories." |

---

## 4. Architectural Summary

ThreatWeave's core technical strength is its **deterministic separation of concern**:
1. Specialist agents extract features and classify threats independently.
2. The LangGraph state machine enforces strictly non-blocking dynamic routing and concurrency.
3. The RAG retriever provides verifiable semantic citations without hallucinating external threats.
4. The Risk Engine enforces mathematical transparency ($b + \Delta_c + \Delta_i - \Delta_k$), guaranteeing that risk scores are reproducible and auditable by security analysts.
