# ThreatWeave: Multi-Agent Quality Improvement Audit
**Document Class:** Comprehensive Quality, Robustness & Vulnerability Audit  
**Auditor:** Senior AI Engineer & Cybersecurity Researcher  
**Target Codebase:** `threatweave/apps/api/app/agents/*`, `apps/api/app/core/*`, `apps/api/eval/*`  
**Date:** November 19, 2026  

---

## 1. Executive Summary

This audit assesses the functional reliability, input validation, error resiliency, heuristic fallback fidelity, and false-positive/negative risks across all six ThreatWeave agents:
1. **Orchestrator Agent** (`graph.py`, `orchestrator_nodes.py`, `orchestrator_state.py`)
2. **Text Specialist Agent** (`text_agent.py`)
3. **URL Specialist Agent** (`url_agent.py`, `url_heuristics.py`)
4. **QR Code Specialist Agent** (`qr_agent.py`)
5. **Image Specialist Agent** (`image_agent.py`, `ocr_engine.py`, `image_heuristics.py`)
6. **Voice Specialist Agent** (`voice_agent.py`, `stt_engine.py`, `voice_heuristics.py`)

The platform's overarching LangGraph state machine and deterministic risk formula are fundamentally sound. However, critical domain-level failure modes were identified:
- An architectural override rule in the **URL Agent** that silences LLM threat severity, causing a **14.3% recall collapse**.
- A missing parameter check in the **QR Agent** that bypasses fraud detection when attackers omit the payee name (`pn`).
- A brittle regex vocabulary in the **Text Agent fallback** that achieved **0.0% recall** when disconnected from cloud LLMs.
- A WAV-only audio parsing limitation in the **Voice Agent heuristics** that crashes on MP3/AAC inputs.
- Indicator semantic fragmentation in the **Orchestrator correlation engine** that prevents cross-modal corroboration bonuses.

---

## 2. Agent 1: Text Specialist Agent Audit

### 2.1 Implementation Verification
- **Primary Source:** [`apps/api/app/agents/text_agent.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/text_agent.py)
- **Prompt Definition:** [`apps/api/app/agents/prompts/text_agent_prompt.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/prompts/text_agent_prompt.py)
- **Architecture:** 3-tier structure (Primary Groq LLM `gpt-oss-120b` $\to$ Heuristic Fallback $\to$ Safety Net).

### 2.2 Functional & Logical Weaknesses
- **Heuristic Vocabulary Disconnect:** The regex heuristic layer (lines 96–136) contains only 45 static phrases. Key Indian scam vectors are absent:
  - Electricity disconnection: `power cut`, `disconnected`, `tonight`, `bescom`, `bill desk`.
  - Banking/KYC: `kyc`, `pan card`, `yono`, `aadhaar`, `dormant`, `unblock`.
  - Judicial coercion: `digital arrest`, `narcotics`, `customs`, `cbi`, `police warrant`.
  - Financial lures: `task`, `youtube like`, `part-time job`, `cibil score`, `loan approved`.
- **Empirical Failure:** When the LLM path was disabled during offline benchmark testing (`eval_results.json`), the heuristic fallback scored **Recall: 0.0% ($FN=14/14$), F1: 0.000, Accuracy: 41.7%**.

### 2.3 Input Validation & Error Handling
- **Strengths:** `clean_json_response()` strips markdown fences; JSON decode errors trigger immediate fallback; all exceptions are trapped by the outer safety net.
- **Weakness:** Content truncation is not performed on excessively large texts before sending to the Groq API. Extremely long text strings (>10,000 words) risk HTTP 413 or token-window exhaustion.

### 2.4 False-Positive / False-Negative Risks
- **False Negative Risk (High):** When Groq API is degraded or offline, almost 100% of malicious Indian scam messages bypass detection because the fallback keywords do not match.
- **False Positive Risk (Low):** In LLM mode, zero false positives were observed ($FP=0, \text{Precision}=100\%$).

---

## 3. Agent 2: URL Specialist Agent Audit

### 3.1 Implementation Verification
- **Primary Sources:** [`apps/api/app/agents/url_agent.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/url_agent.py), [`apps/api/app/core/url_heuristics.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/url_heuristics.py)
- **Reputation Client:** [`apps/api/app/agents/reputation_client.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/reputation_client.py)

### 3.2 Critical Architectural Defect: LLM Severity Silencing
- **Finding:** In `url_agent.py` lines 31–35:
  > *"Final severity is driven by the heuristic layer's suggested_severity. The LLM synthesis step produces 'finding' and 'reasoning' text ONLY — it CANNOT override the severity computed from structural heuristics."*
- **Mechanism of Failure:**
  1. `run_heuristics()` requires at least 2 structural flags to elevate severity beyond `medium`.
  2. A sophisticated phishing link such as `http://sbi-kyc-verification.top/update` has only 1 structural flag (`suspicious_tld: .top`).
  3. `lookalike_score` compares the registered domain `sbi-kyc-verification` against `sbi.co.in` and `onlinesbi.com` using whole-string Levenshtein distance. Because the length difference is large, edit distance $>10$, so typosquatting score is $0.0$.
  4. Heuristics assign `medium` severity.
  5. The LLM correctly diagnoses the domain as fraudulent, but `url_agent.py` discards the LLM's severity rating and enforces `medium`.
  6. The evaluation harness maps `medium` to Benign ($\hat{y} = 0$).
  7. **Result:** In `eval_results.json`, URL Agent achieved **100% precision but only 14.3% recall ($FN=12/14$)**.

### 3.3 Input Validation & Normalization
- `run_heuristics()` safely catches malformed URLs via `urlparse` and `ipaddress`.
- **Limitation:** Does not normalize Unicode homoglyphs (e.g., Cyrillic 'а' replacing Latin 'a') or unquote obfuscated hex-encoded path parameters before computing entropy.

---

## 4. Agent 3: QR Code Specialist Agent Audit

### 4.1 Implementation Verification
- **Primary Source:** [`apps/api/app/agents/qr_agent.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/qr_agent.py)
- **Core Decoders:** [`apps/api/app/core/qr_decoder.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/qr_decoder.py)

### 4.2 Critical Parameter Omission Vulnerability in UPI Parsing
- **Finding:** In `qr_agent.py` line 148:
  ```python
  if pn and pa and (vpa_sim < 0.4 or has_authority_impersonation or (suspicious_amount and vpa_sim < 0.6)):
      indicators.append("qr_upi_deeplink_suspicious")
  ```
- **Vulnerability:** If an attacker sends a QR code with `pa` (VPA) and `am` (Amount) but intentionally omits `pn` (Payee Name), e.g.:
  `upi://pay?pa=scammerchant99@ybl&am=7500&tn=Electricity+Bill+Refund`
- **Result:** Because `pn` is an empty string, `pn and pa` evaluates to `False`. The check is bypassed entirely. The indicator `qr_upi_deeplink_suspicious` is not added. Severity defaults to `low`. The transaction request goes unflagged.

### 4.3 Decoder Robustness
- Relies on `cv2.QRCodeDetector` with fallback to `pyzbar`.
- **Limitation:** Fails on curved, low-contrast, or tilted mobile screenshots without prior image binarization or perspective correction.

---

## 5. Agent 4: Image Specialist Agent Audit

### 5.1 Implementation Verification
- **Primary Sources:** [`apps/api/app/agents/image_agent.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/image_agent.py), [`apps/api/app/core/ocr_engine.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/ocr_engine.py), [`apps/api/app/core/image_heuristics.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/image_heuristics.py)

### 5.2 False-Positive Inflation on Legitimate Receipts
- **Finding:** `has_payment_confirmation_pattern()` inspects OCR text for strings like `payment successful`, `transaction id`, `utr`, `amount paid`.
- If detected, it unconditionally emits `fake_payment_confirmation`.
- **Consequence:** In `eval_results.json`, Image Agent produced **2 false positives ($FP=2/10$)**, dropping precision to **83.3%**. Legitimate transaction receipts uploaded by victims as evidence are misclassified as fake payment receipts.

### 5.3 Optical Extraction Limitations
- `ocr_engine.py` passes raw image arrays directly to `reader.readtext(cv_img)` without grayscale conversion, contrast enhancement (CLAHE), or thresholding. Low-resolution mobile screenshots or dark-mode themes result in dropped text segments.

---

## 6. Agent 5: Voice Specialist Agent Audit

### 6.1 Implementation Verification
- **Primary Sources:** [`apps/api/app/agents/voice_agent.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/voice_agent.py), [`apps/api/app/core/stt_engine.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/stt_engine.py), [`apps/api/app/core/voice_heuristics.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/voice_heuristics.py)

### 6.2 Format Parsing Flaw in Acoustic Analysis
- **Finding:** In `voice_heuristics.py` lines 101–102:
  ```python
  stream = io.BytesIO(audio_bytes)
  with wave.open(stream, "rb") as wf:
  ```
- **Defect:** `wave.open()` is strictly limited to RIFF/WAV files. While `voice_agent.py` uses PyAV to accept MP3, AAC, and OGG formats, passing those audio bytes directly into `analyze_acoustic_features()` triggers an unhandled `wave.Error` (caught by broad try/except).
- **Result:** Acoustic variance analysis is silently aborted for all non-WAV audio files, defaulting to zero variance.

### 6.3 Synthetic Benchmark Limitation
- In `apps/api/eval/datasets.py`, voice samples were generated using programmatic tone buffers without human speech. Faster-Whisper transcribed empty strings, producing **0.0% recall ($FN=6/6$)** in automated batch evaluation. Authentic speech files are required for scientific validity.

---

## 7. Agent 6: Orchestrator Agent & Swarm Pipeline Audit

### 7.1 Implementation Verification
- **Primary Sources:** [`apps/api/app/agents/graph.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/graph.py), [`apps/api/app/agents/orchestrator_nodes.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/orchestrator_nodes.py), [`apps/api/app/agents/correlation.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/correlation.py)

### 7.2 Semantic Disconnect in Cross-Agent Corroboration
- **Finding:** In `correlation.py:62-105`, corroboration requires **exact string identity** of indicators across distinct agents.
- **Problem:** If the Text Agent discovers `payment_request` and the QR Agent discovers `qr_payment_request`, they are treated as non-matching indicators!
- **Consequence:** Cross-modal corroboration bonuses ($\Delta_{\text{corrob}}$) are missed even when text and QR codes both urge fraudulent payment, reducing the system's ability to reward multi-agent agreement.

---

## 8. Summary Audit Findings Matrix

| Finding ID | Agent | Severity | Flaw / Weakness | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | URL Agent | **CRITICAL** | `url_agent.py` prevents LLM from escalating severity above static heuristics. | 14.3% URL recall ($FN=12$); high-risk phishing domains bypassed. |
| **SEC-02** | QR Agent | **HIGH** | `qr_agent.py` requires `pn` parameter to flag suspicious UPI deep-links. | QR payment scams with omitted payee names are classified as `low`. |
| **SEC-03** | Text Agent | **HIGH** | Fallback regex vocabulary contains only 45 static keywords; misses Indian fraud lexicon. | 0.0% recall in fallback mode when cloud LLM is offline or rate-limited. |
| **SEC-04** | Voice Agent | **HIGH** | `analyze_acoustic_features()` uses `wave.open()`, failing on MP3/AAC/OGG uploads. | Silent acoustic analysis failure for all compressed audio formats. |
| **SEC-05** | Image Agent | **MEDIUM** | `has_payment_confirmation_pattern` unconditionally flags legitimate receipts as fraud. | 83.3% precision ($FP=2/10$); legitimate payment receipts flagged. |
| **SEC-06** | Orchestrator | **MEDIUM** | Corroboration requires exact indicator string match; misses semantic category overlap. | Cross-modal payment fraud misses corroboration bonus ($\Delta_c$). |
| **SEC-07** | Voice Agent | **MEDIUM** | Automated evaluation harness uses synthetic silent tone buffers rather than spoken audio. | Voice agent recall cannot be validated in automated batch tests. |
