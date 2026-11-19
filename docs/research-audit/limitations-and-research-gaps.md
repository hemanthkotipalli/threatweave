# ThreatWeave: Limitations, Unsupported Claims & Research Gaps
**Document Class:** Academic Critical Self-Audit & Limitations Analysis  
**Audience:** Peer Reviewers, Examiners, and Authors of the Research Paper  
**Standard:** IEEE Transactions on Dependable and Secure Computing / ACM TOPS Integrity Guidelines  

---

## 1. Explicitly Verified Technical Limitations

In any peer-reviewed scientific publication, an honest and precise disclosure of system boundaries strengthens academic rigor and prevents reviewer rejection. The following limitations are verified directly from the ThreatWeave implementation:

### 1.1 Voice Modality Boundaries (No Generative Deepfake Neural Network)
- **Verified Code:** [`apps/api/app/agents/voice_agent.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/voice_agent.py) and [`apps/api/app/core/voice_heuristics.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/voice_heuristics.py).
- **Reality:** ThreatWeave transcribes speech using Faster-Whisper, matches regex patterns for telephone scam coercion (e.g., *digital arrest*, *narcotics parcel*, *OTP demand*), and computes basic acoustic variance (energy variance and zero-crossing rate) to detect monotone robotic cadence.
- **Limitation:** It does **not** employ an end-to-end deep neural network trained on synthetic voice artifacts (such as AASIST, RawNet2, or wav2vec2 feature extractors). It cannot detect high-fidelity generative voice clones that preserve human-like emotional inflections.
- **Academic Disclosure:** The voice modality must be described as *conversational vishing forensics* and *acoustic cadence analysis*, not as an *AI voice deepfake detector*.

### 1.2 URL Detection Boundaries & Tradeoffs
- **Verified Code:** [`apps/api/app/agents/url_agent.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/url_agent.py) and [`apps/api/app/core/url_heuristics.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/url_heuristics.py).
- **Reality:** Following remediation, the URL Agent achieves **100.0% precision and 64.29% recall** ($TP=9, FN=5, TN=10, FP=0$, F1=0.7826) in both LLM-enabled mode and offline heuristic mode. The engine reliably flags token combosquatting (e.g. `sbi-kyc-update.com`), IP-based portals, raw APK downloads, and high-abuse TLDs (`.top`, `.xyz`, `.rest`).
- **Limitation:** The remaining 5 false negatives represent newly registered domains that use benign-looking generic terms on standard `.com`/`.org` TLDs with no overt typosquatting against the curated 17 Indian brand targets, and without Google Safe Browsing reputation history. Offline lexical analysis cannot deduce malicious intent without external live web reputation telemetry or corroborating SMS/email lure text.
- **Academic Disclosure:** Lexical heuristics serve as a rapid zero-day and phishing-kit filter; comprehensive URL detection requires cross-modal correlation with accompanying text lures and live reputation feed lookups.

### 1.2.1 Offline Text Fallback Recall Tradeoff
- **Verified Code:** [`apps/api/app/agents/text_agent.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/text_agent.py).
- **Reality:** In offline heuristic fallback mode, the Text Agent achieves **100.0% precision but 35.71% recall** ($TP=5, FN=9, TN=10, FP=0$).
- **Limitation:** To guarantee zero false alarms in production security operations, the heuristic rules deliberately require contextual co-occurrence (an impersonation claim co-occurring with an urgency keyword and a credential/payment demand). Subtle or conversational social engineering texts that do not match these tight lexical intersections are conservatively rated as `medium` severity, yielding lower recall when LLM reasoning is offline.
- **Academic Disclosure:** Offline heuristic fallback provides a fail-safe against catastrophic total failure (avoiding system outage during API disruptions), but operates as a high-precision, low-recall triage filter compared to full LLM semantic synthesis (92.86% recall).

### 1.3 Image Modality & Payment Fraud Verification
- **Verified Code:** [`apps/api/app/agents/image_agent.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/image_agent.py) and [`apps/api/app/core/image_heuristics.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/core/image_heuristics.py).
- **Reality:** Image analysis relies on EasyOCR to extract visible text and scans for keywords associated with payment confirmations (e.g., *Payment Successful*, *UTR*, *Txn ID*, *PhonePe*, *Google Pay*).
- **Limitation:** ThreatWeave possesses no programmatic interface with banking networks (NPCI, IMPS, RTGS, SWIFT) or institutional databases. It cannot independently verify whether a transaction reference number (UTR) actually settled in a bank account. A sophisticated attacker could forge an image containing a real, valid transaction ID from a different transaction.
- **Academic Disclosure:** The Image Agent detects *lexical and visual forgery markers*, not financial ledger reconciliation.

### 1.4 Scope and Currency of the RAG Knowledge Base
- **Verified Code:** [`apps/api/app/rag/sources/`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/rag/sources/) and [`apps/api/app/rag/retriever.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/rag/retriever.py).
- **Reality:** The vector database is initialized from a static corpus of **24 curated Markdown files** (8 CERT-In, 8 RBI, 8 Scam-Intel).
- **Limitation:** The corpus is curated and static. ThreatWeave does not implement an automated live crawler that ingests daily CERT-In vulnerability bulletins or global CVE feeds in real time.
- **Academic Disclosure:** The RAG subsystem demonstrates domain grounding against authoritative regulatory advisories; continuous automated feed ingestion remains an operational enhancement.

### 1.5 Latency Profile and Deployment Scope
- **Verified Code:** [`apps/api/eval/eval_pipeline.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/eval/eval_pipeline.py) and [`docs/evaluation-results.md`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/docs/evaluation-results.md).
- **Reality:** Active multimodal investigations execute in **1.8 to 9.5 seconds** (average warm execution: 4.76s).
- **Limitation:** The system cannot function as an in-line packet inspection firewall or real-time call interception daemon operating at millisecond wire speed.
- **Academic Disclosure:** ThreatWeave is an *asynchronous investigative triage and decision-support platform* for security operations centers (SOCs) and end-user incident reporting.

### 1.6 Evaluation Dataset Scale
- **Verified Code:** [`apps/api/eval/datasets.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/eval/datasets.py).
- **Reality:** The evaluation was conducted across 94 curated samples (51 malicious, 43 benign).
- **Limitation:** While highly representative of Indian cyber fraud vectors, 94 samples is a small empirical dataset compared to multi-thousand public corpora (e.g., Enron, PhishTank, ASVspoof).
- **Academic Disclosure:** Findings must be presented as an *empirical proof-of-concept benchmark*, accompanied by an explicit call for larger multi-jurisdictional evaluation.

---

## 2. Unsupported Claims to Avoid

The following claims must **never** be made in the research paper:

1. **"ThreatWeave is the first multimodal cybersecurity system."**  
   *Reason:* Multimodal threat analysis has prior literature in spam detection, phishing web page analysis, and email forensics. ThreatWeave's genuine novelty lies in its *agentic LangGraph coordination, cross-agent conflict resolution, and deterministic explainable risk scoring*.
2. **"ThreatWeave achieves 100% detection of all cyber fraud."**  
   *Reason:* Highly unrealistic in peer review. Report empirical metrics exactly: Text Agent achieved 95.8% accuracy (0.963 F1), Image Agent achieved 90.0% accuracy (0.909 F1), and URL Agent achieved 50.0% accuracy in isolation.
3. **"ThreatWeave uses deep neural generative voice detection."**  
   *Reason:* Contradicted by `voice_agent.py:9-13` and `voice_heuristics.py:7-12`.
4. **"RAG dynamically updates from live internet crawlers."**  
   *Reason:* Contradicted by `app/rag/sources/` (24 static files).

---

## 3. Evaluation and Refinement of the Research Question

### Provisional Research Question (User Provided):
> *"Can an orchestrated group of modality-specific agents combine evidence from text, URLs, QR codes, screenshots, and voice into a more coherent and explainable threat assessment than separate modality-level analyses?"*

### Critical Academic Review:
- **Strengths:** Clear, focused on multimodal orchestration, and explicitly highlights *explainability* and *coherence*.
- **Weaknesses:** "Coherent" is somewhat subjective and difficult to evaluate mathematically without human-subject studies. The question does not emphasize *conflict handling* or *deterministic scoring*, which are the strongest verified contributions of ThreatWeave.

### Recommended Improved Research Questions:

#### Primary Research Question (RQ1):
> *"How effectively can a federated multi-agent architecture with dynamic modal routing correlate cross-modal Indicators of Compromise (IoCs) and resolve inter-agent severity conflicts compared to isolated single-modality detectors in multi-vector digital communication fraud?"*

#### Secondary Research Question (RQ2 - Explainability):
> *"Does a closed-form, deterministic mathematical risk engine ($b + \Delta_c + \Delta_i - \Delta_k$) provide verifiable scoring invariance and eliminate hallucinated threat inflation across multimodal cybersecurity investigations?"*

#### Secondary Research Question (RQ3 - Operational Resilience):
> *"What is the performance and accuracy trade-off between cloud-hosted LLM reasoning and local heuristic fallback pipelines when executing under degraded network and resource-constrained environments?"*

---

## 4. Technically Defensible Academic Contributions

When writing the paper's Introduction and Conclusion, emphasize these three contributions:

1. **Dynamic Swarm Routing with Strict Agent Isolation:**
   Implementation of a LangGraph `StateGraph` that inspects multimodal evidence, dispatches only necessary specialist pipelines, and formally records skipped agents, eliminating computational waste while achieving 100% routing accuracy.
2. **Dual-Tier Forensic Processing with Resilient Fallback:**
   Every specialist agent implements a primary deep-reasoning path (LLM / deep OCR / Whisper) and an autonomous, sub-20ms heuristic fallback path, ensuring operational continuity under rate limits or offline conditions.
3. **Deterministic, Conflict-Aware Explainability Engine:**
   Replaces opaque neural classification heads with a mathematically auditable formulation that rewards multi-agent corroboration, penalizes inter-agent contradictions, incorporates similarity-filtered regulatory intelligence, and achieves $\le 0.0001$ empirical residual error across persisted investigation records.
