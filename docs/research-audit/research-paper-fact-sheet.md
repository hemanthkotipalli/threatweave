# ThreatWeave: Research Paper Technical Fact Sheet
**Document Class:** Verified Academic Fact Sheet (IEEE Paper Preparation Guide)  
**Target Paper:** *ThreatWeave: An Agentic Multimodal Framework for Cross-Modal Digital Communication Threat Analysis*  
**Scope:** Verified Codebase Facts, Mathematical Formulations, and Citable Constants  

---

## 1. System Identity & Core Paradigm

- **Official Project Title:** ThreatWeave: An Agentic Multimodal Framework for Cross-Modal Digital Communication Threat Analysis.
- **Architectural Paradigm:** Multi-Agent System (MAS) coordinated via Directed Acyclic State Machine (`LangGraph StateGraph`).
- **Core Research Hypothesis:** Orchestrating modality-specific specialist agents with shared indicator corroboration, explicit conflict logging, and domain-grounded RAG intelligence produces a more explainable and structurally consistent threat assessment than monolithic LLM prompting or isolated single-modality scanners.
- **Primary Domain Grounding:** Indian financial cyber fraud vectors (UPI payment scams, electricity bill extortion, KYC expiry smishing, fake judicial/police digital arrest, courier customs narcotics extortion).

---

## 2. Verified Architectural Constants & Parameters

### A. Swarm Composition (Exactly 6 Agents)
1. **Orchestrator Agent:** LangGraph StateGraph state machine (`apps/api/app/agents/graph.py`).
2. **Text Specialist Agent:** Groq LLM (`openai/gpt-oss-120b`) + 9-category regex heuristic fallback (`apps/api/app/agents/text_agent.py`).
3. **URL Specialist Agent:** Pure lexical heuristics (Levenshtein typosquatting against 17 Indian domains, Shannon entropy, raw IP detection, 14 shortener hosts, high-abuse TLDs) + optional Google Safe Browsing API v4 (`apps/api/app/agents/url_agent.py`).
4. **QR Code Specialist Agent:** OpenCV `cv2.QRCodeDetector` / `pyzbar` decoder + UPI `upi://pay` deep-link parameter parser + delegation to URL/Text agents (`apps/api/app/agents/qr_agent.py`).
5. **Image Specialist Agent:** EasyOCR (CRAFT detector + CRNN recognizer) + visual receipt heuristics (`has_payment_confirmation_pattern`, `has_impersonation_claim`) + delegation to URL/Text agents (`apps/api/app/agents/image_agent.py`).
6. **Voice Specialist Agent:** `faster-whisper` (`base` model, CTranslate2 int8 quantization) + PyAV audio demuxer + vishing script regex + lightweight acoustic cadence variance (`apps/api/app/agents/voice_agent.py`).

### B. Risk Assessment Engine Parameters
- **Source Module:** [`apps/api/app/agents/risk_engine.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/risk_engine.py)
- **Mathematical Formula:**
  $$\text{final\_risk} = \text{clamp}\left( \text{base\_score} + \Delta_{\text{corrob}} + \Delta_{\text{intel}} - \Delta_{\text{contra}}, \; 0.0, \; 1.0 \right)$$
- **Base Score Formula:**
  $$\text{base\_score} = \frac{1}{|F_{\text{included}}|} \sum_{f \in F_{\text{included}}} \left( W(\text{sev}_f) \times c_f \right)$$
  - Severity Weights $W(\text{sev})$:
    - `info`: $0.00$
    - `low`: $0.25$
    - `medium`: $0.50$
    - `high`: $0.75$
    - `critical`: $1.00$
  - Finding Inclusions: Excludes findings with `status == 'failed'`; includes findings with `status == 'ok'` and `status == 'degraded_fallback'`.
  - Confidence Clamping: $c_f \in [0.0, 1.0]$.
- **Corroboration Bonus ($\Delta_{\text{corrob}}$):**
  - Shared IoC matching across $\ge 2$ distinct specialist agents.
  - $+0.10$ per additional agent beyond the first per indicator group.
  - Capped strictly at $+0.25$.
- **RAG Intel Bonus ($\Delta_{\text{intel}}$):**
  - $+0.15$ if any retrieved regulatory advisory citation has cosine similarity $\ge 0.40$; otherwise $0.00$.
- **Contradiction Penalty ($\Delta_{\text{contra}}$):**
  - $-0.10$ per detected severity divergence conflict ($[info, low] \leftrightarrow [high, critical]$ on related signals).
  - Capped strictly at $0.30$.
- **Discrete Severity Bands:**
  - $0.00 - 0.19$: `info`
  - $0.20 - 0.39$: `low`
  - $0.40 - 0.59$: `medium`
  - $0.60 - 0.79$: `high`
  - $0.80 - 1.00$: `critical`
- **Uncertainty Rule:** Sets `low_confidence = True` if $|F_{\text{included}}| < 2$ or mean confidence $< 0.40$.

### C. RAG Knowledge Base Parameters
- **Total Curated Documents:** Exactly **24** Markdown advisory documents.
- **Document Breakdown:**
  - 8 CERT-In Advisories (`ci_01` to `ci_08`: Banking phishing, IT refund APKs, subsidy portals, electricity scams, courier SMS, SIM swaps, task fraud, trojans).
  - 8 RBI Public Notices (`rbi_01` to `rbi_08`: UPI collect requests, fake payment receipts, KYC smishing, payment links/QRs, OTP protection, lending apps, ATM skimming, lottery scams).
  - 8 Scam-Intel Advisories (`si_01` to `si_08`: Digital arrest, remote desktop AnyDesk/TeamViewer, customs narcotics parcel extortion, crypto arbitrage, family emergency vishing, LPG subsidy, loan prepayments, Aadhaar biometric lock).
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions, cosine distance metric).
- **Retrieval Threshold:** `RAG_SIMILARITY_THRESHOLD = 0.40`.
- **Top Candidates Retrieved:** `RAG_TOP_K = 5`.
- **Vector Database:** ChromaDB 0.5.5 (`PersistentClient` at `/app/chroma_db` in container, HTTP client on port 8001 in dev).

---

## 3. Verified Empirical Benchmark Statistics

These empirical statistics are drawn directly from the verified 94-sample benchmark harness (`apps/api/eval/eval_results.json` and post-remediation test executions across 137 passing tests):

1. **Benchmark Dataset Size:** 94 labeled Indian-context threat samples (51 malicious, 43 benign) stratified across 5 specialist modalities:
   - Text: 24 samples (14 malicious, 10 benign)
   - URL: 24 samples (14 malicious, 10 benign)
   - Image: 20 samples (10 malicious, 10 benign)
   - QR: 14 samples (7 malicious, 7 benign)
   - Voice: 12 samples (6 malicious, 6 benign)

2. **Primary Production Path (LLM-Enabled Inference):**
   - **Text Agent:** Precision: **100.0%** ($TP=13, FP=0$), Recall: **92.9%** ($FN=1$), $F_1$: **0.963**, Accuracy: **95.8%**, Mean Latency: 2,952 ms.
   - **Image Agent:** Precision: **83.3%** ($TP=10, FP=2$), Recall: **100.0%** ($FN=0$), $F_1$: **0.909**, Accuracy: **90.0%**, Mean Latency: 9,368 ms.
   - **QR Code Agent:** Precision: **75.0%** ($TP=6, FP=2$), Recall: **85.7%** ($FN=1$, up from 57.1%), $F_1$: **0.800** (up from 0.615), Accuracy: **78.6%**, Mean Latency: 4,499 ms.
   - **URL Agent:** Precision: **100.0%** ($TP=9, FP=0$), Recall: **64.3%** ($FN=5$, up from 14.3%), $F_1$: **0.783** (up from 0.250), Accuracy: **79.2%** (up from 50.0%), Mean Latency: 4,094 ms.
   - **Voice Agent:** Verified via offline acoustic and heuristic pipeline; LLM synthesis subject to cloud rate limit throttling.

3. **Offline Resilience Path (100% Local Heuristic Fallback Mode):**
   *Evaluated under simulated zero-cloud connectivity (`ExternalServiceError` on all LLM calls):*
   - **URL Fallback:** Precision: **100.0%**, Recall: **64.3%**, $F_1$: **0.783**, Mean Latency: **13.9 ms** (up from 0.0% recall baseline).
   - **QR Fallback:** Precision: **75.0%**, Recall: **85.7%**, $F_1$: **0.800**, Mean Latency: **45.3 ms** (up from 14.3% recall baseline).
   - **Image Fallback:** Precision: **75.0%**, Recall: **60.0%**, $F_1$: **0.667**, Mean Latency: **5,455 ms** (CPU EasyOCR bounded).
   - **Voice Fallback:** Precision: **75.0%**, Recall: **50.0%**, $F_1$: **0.600**, Mean Latency: **36.5 ms**.
   - **Text Fallback:** Precision: **100.0%**, Recall: **35.7%**, $F_1$: **0.526**, Mean Latency: **2.0 ms** (prioritizes zero false alarms over uncalibrated trigger matches).

4. **Swarm Routing Accuracy:** **100.0%** across 6 distinct input modality permutations (0 execution leaks, all inapplicable agents persisted as `status='skipped'`).
5. **Explainability Invariance:** Maximum residual error across live database investigations $\le \mathbf{0.0001}$.
6. **Regression Integrity:** **137 / 137 unit and integration tests passing** across all 5 specialist agents, correlation engine, and risk scoring formula.

---

## 4. Defensible Claims vs. Unsupported Pitfalls

| Topic | Defensible Statement for IEEE Paper | Pitfall to Avoid (Do Not Claim) |
| :--- | :--- | :--- |
| **Voice Processing** | "Faster-Whisper speech transcription combined with conversational vishing pattern matching and acoustic cadence variance analysis." | "Novel deepfake neural voice detection" (no acoustic deepfake classifier is implemented). |
| **URL Processing** | "Multi-layered URL analysis combining Levenshtein typosquatting, entropy calculation, and raw IP heuristics with Google Safe Browsing integration." | "Real-time global zero-day link interception." |
| **Transaction Verification** | "Optical character recognition (EasyOCR) detecting visual and lexical markers of fake payment confirmation screens." | "Live bank ledger or NPCI transaction verification" (system has no direct banking clearing gateway). |
| **Explainability** | "A closed-form, deterministic four-part mathematical risk scoring formula providing bitwise-consistent and auditable scoring components." | "A black-box neural risk score that predicts human likelihood of falling for scams." |
| **RAG Knowledge Base** | "An offline-indexed domain corpus of 24 curated Indian cybersecurity advisories grounding the investigation in official regulatory warnings." | "A real-time web crawler that continuously ingests all global cybercrime alerts." |
