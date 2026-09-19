# ThreatWeave — Viva Voce & Defense Reference Guide

> **Document Class:** Comprehensive Examination Reference & Technical Defense  
> **Applicability:** B.Tech Major Project Final Viva Voce, Academic Examination, and Technical Evaluation  
> **Repository:** `threatweave`  
> **Source Baseline:** Validated across Phases A–D (Zero Aspirational Claims, 100% Code-Grounded)  

---

## 1. Core Architectural & System Design

### Q1: Why six agents? Why not more or fewer?
**Answer:**
Threat vectors arrive across fundamentally heterogeneous data surfaces that cannot share a single parsing model. ThreatWeave implements exactly six agents to establish clear separation of operational concerns:
1. **`Orchestrator Agent`:** Compiles the LangGraph cyclic state graph, coordinates conditional execution edges, retrieves RAG threat intelligence, and executes deterministic risk calculations.
2. **`Text Agent`:** Analyzes textual communications (SMS, email body, chat lures) for coercive urgency, credential requests, and financial intimidation.
3. **`URL Agent`:** Decomposes suspicious links statically, calculating Levenshtein typosquatting distance, IP-literal host detection, suspicious free-TLD risks, and path entropy.
4. **`QR Agent`:** Computer vision pipeline using OpenCV to detect and decode barcode/QR matrices, parsing UPI payment deep-links (`upi://pay`) and validating Virtual Payment Addresses (VPAs).
5. **`Image Agent`:** Extracts textual overlays from payment receipts and bank notifications via neural Optical Character Recognition (`EasyOCR`), validating visual impersonation heuristics.
6. **`Voice Agent`:** Transcribes audio voicemails via `faster-whisper` and extracts acoustic signal properties (zero-crossing rate, RMS energy, spectral rolloff) to evaluate social engineering scripts.

Fewer agents would create fragile, monolithic parsing bottlenecks; more agents would introduce unnecessary inter-agent latency without distinct evidentiary substrates.

---

### Q2: Why LangGraph instead of linear chains (like standard LangChain or Celery)?
**Answer:**
Cyber threat analysis is inherently **stateful, cyclic, and conditional**, not a static linear pipeline. 
- **Dynamic Branching:** An investigation submitted with text and a URL should never execute Whisper or OpenCV; LangGraph conditional edges inspect `InvestigationState["evidence_inputs"]` at the `plan_node` and schedule only active modalities in parallel.
- **Fan-In Consolidation:** The graph provides a clean fan-in barrier at `collect_node`, ensuring all active agents complete their execution cycles before correlation begins.
- **Correlation & Conflict Loops:** LangGraph natively supports routing transitions through `correlate_node`, `conflict_resolution_node`, `rag_node`, and `risk_engine_node`, passing an immutable, type-safe state schema.
- **Resilient State Persistence:** If an agent encounters an external timeout, its status (`degraded_fallback` or `failed`) is tracked directly in state without aborting the overall workflow.

---

### Q3: Why not just prompt one large multimodal model (like GPT-4o or Gemini 1.5 Pro) with everything?
**Answer:**
Relying on a single frontier multimodal LLM has critical architectural, operational, and regulatory flaws:
1. **Economic & Latency Overhead:** Transmitting multi-megabyte audio and image payloads to cloud LLMs for every routine alert is computationally expensive and slow for real-time SOC operations.
2. **Black-Box Stochasticity:** LLMs produce non-deterministic risk scores (e.g., asking an LLM to *"rate threat from 1 to 10"* produces inconsistent outputs across runs). Regulators and SOC managers require auditable, reproducible mathematical breakdowns.
3. **Absence of Specialized Tooling:** LLMs cannot decode QR matrix pixels via computer vision, calculate algorithmic Levenshtein distance against banking domain registries, or compute acoustic zero-crossing rates. Deterministic tools execute these specific calculations (e.g., exact Levenshtein distance, IP classification, matrix decoding) reproducibly and without stochastic variance in milliseconds.
4. **Single Point of Failure:** An API rate-limit (HTTP 429) or cloud outage halts the entire triage process; ThreatWeave isolates failures agent-by-agent.

---

### Q4: How does dynamic routing happen in the swarm?
**Answer:**
Routing occurs at the LangGraph graph boundary based on the modalities present in the investigation's uploaded evidence:
1. `ingestion_service` parses uploaded payloads and records `EvidenceInput` rows tagged with modalities (`text`, `url`, `image`, `qr`, `voice`).
2. When analysis begins, `plan_node` inspects `state["evidence_inputs"]` and determines the active agent targets.
3. The conditional edge `_route_to_active_agents` returns a list of active node names (e.g., `["text_agent", "url_agent"]`).
4. LangGraph executes the scheduled specialist nodes concurrently in the host thread pool, completely bypassing inactive modality nodes.

---

### Q5: How is evidence represented internally across agents?
**Answer:**
Evidence flows through strongly-typed Pydantic schemas (`EvidenceItem`) and SQLAlchemy relational entities (`AgentFinding`, `EvidenceInput`). Each atomic finding includes:
- `agent_name` & `modality`: Originating specialist pipeline.
- `finding`: Concise, human-readable threat summary.
- `confidence`: Epistemic certainty scalar bounded to $[0.0, 1.0]$.
- `severity`: Standardized classification (`info`, `low`, `medium`, `high`, `critical`).
- `indicators`: Normalized list of technical observables (e.g., domains, VPAs, urgency tokens).
- `evidence`: Dictionary of concrete extracted attributes (e.g., matched regex patterns, OCR text, acoustic metrics).
- `reasoning`: Structured explanation justifying the assigned severity.

---

## 2. Risk Engine Mathematics & Conflict Handling

### Q6: How is the composite risk score calculated?
**Answer:**
Risk calculation is a pure, deterministic mathematical function implemented in [`app/agents/risk_engine.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/risk_engine.py) with zero database, network, or LLM calls:
$$R_{\text{final}} = \text{clamp}(\text{base\_score} + \Delta_{\text{corrob}} + \Delta_{\text{intel}} - \Delta_{\text{contra}}, 0.0, 1.0)$$

1. **Base Score ($\text{base\_score}$):** Confidence-weighted arithmetic mean of valid findings:
   $$\text{base\_score} = \frac{1}{N} \sum_{i=1}^N \left( W(\text{sev}_i) \times c_i' \right)$$
   Where severity weights $W \in \{0.00, 0.25, 0.50, 0.75, 1.00\}$.
2. **Corroboration Bonus ($\Delta_{\text{corrob}}$):** $+0.10$ per additional distinct agent confirming shared indicators, capped at $+0.25$.
3. **Threat Intel Bonus ($\Delta_{\text{intel}}$):** $+0.15$ if at least one retrieved RAG advisory clears the cosine similarity threshold ($\sigma \ge 0.40$).
4. **Contradiction Penalty ($\Delta_{\text{contra}}$):** $-0.10$ per detected inter-agent semantic conflict, capped at $0.30$.
5. **Uncertainty Gating:** Flags `low_confidence = True` if fewer than 2 findings exist or average confidence $\bar{c} < 0.40$.

*(Full mathematical formalization and worked examples are documented in [`docs/risk-engine-formula.md`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/docs/risk-engine-formula.md)).*

---

### Q7: How are conflicting agent findings detected and resolved?
**Answer:**
Contradictions are detected deterministically in [`app/agents/correlation.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/correlation.py) (`find_conflicts`):
- **Detection:** Triggers when two agents evaluate findings within the same semantic category (e.g., `social_engineering`), but exhibit a severity discrepancy of $\ge 0.50$ (e.g., `Text Agent` flags `critical` while `URL Agent` reports `info`).
- **Mathematical Deduction:** Each conflict deducts $-0.10$ from the composite risk score via $\Delta_{\text{contra}}$ (capped at $0.30$). This prevents the system from escalating to a high-severity alert when underlying evidence is mutually contradictory.
- **Audit Logging:** The `conflict_resolution_node` records the conflict in the PostgreSQL `conflict_logs` table, capturing conflicting agent names, the conflict type (`severity_divergence`), and the canonical resolution rule (`resolution_rule = "contradiction_penalty_applied"` with `resolution_outcome` detailing the penalty applied).
- **UI Transparency:** The investigation workspace surfaces an amber warning banner detailing the exact disagreement to the human SOC analyst.

---

## 3. Retrieval-Augmented Generation (RAG) & Threat Intelligence

### Q8: How does RAG improve threat detection?
**Answer:**
Specialist agents analyze an input in isolation (e.g., detecting that an SMS has high urgency). RAG connects those isolated observables to **wider adversarial campaigns and recognized threat infrastructure**:
- Dense semantic vectors (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions) index curated threat advisories in ChromaDB.
- When an investigation is analyzed, extracted indicators and lure text are queried against the vector database.
- Retrieved advisories above the strict $0.40$ similarity cutoff:
  1. Ground the final incident narrative in real-world modus operandi without hallucination.
  2. Provide human analysts with direct citations to authoritative national bulletins.
  3. Award an objective, auditable $+0.15$ intelligence bonus ($\Delta_{\text{intel}}$) to the composite risk score.

---

### Q9: Why specifically focus on CERT-In and RBI threat advisories?
**Answer:**
ThreatWeave is tailored to the rapid rise of multi-modal digital financial fraud targeting Indian consumers and enterprises (UPI payment scams, electricity bill termination threats, fake KYC update APKs, digital arrest impersonation).
- **CERT-In (Indian Computer Emergency Response Team):** National nodal agency publishing authoritative technical vulnerability notes and campaign advisories.
- **RBI (Reserve Bank of India):** Central banking authority issuing recurring cyber fraud warnings documenting specific deceptive banking URLs, fake customer care numbers, and social engineering patterns.
- Grounding in these sources ensures regulatory relevance and authentic threat coverage for the targeted domain.

---

### Q10: How do you prevent hallucinations in the RAG and LLM pipeline?
**Answer:**
Hallucination prevention is enforced through four structural boundaries:
1. **Mathematical Scoring Boundary:** An LLM **never** determines the final risk score, severity band, or component bonuses—these are computed strictly by deterministic Python mathematics.
2. **Strict Cosine Threshold Cutoff:** RAG vector search enforces a minimum cosine similarity threshold of $\tau = 0.40$. Low-scoring chunks are rejected, ensuring irrelevant advisories are never injected into the prompt.
3. **Structured Pydantic Schemas:** LLMs operate strictly in JSON mode with Pydantic validation schemas. Malformed or hallucinated attributes are caught and trigger immediate fallback to rule-based heuristics.
4. **Evidence-Bounded Prompts:** Prompts provide the LLM with pre-extracted deterministic heuristics (e.g., exact Levenshtein distance, IP classification, OCR text) and explicitly instruct the model to synthesize only observed evidence.

---

## 4. Resilience, Edge Cases, & External Failures

### Q11: What happens if an external API fails, times out, or rate-limits?
**Answer:**
ThreatWeave implements **defensive multi-tier degradation**:
- **LLM Rate Limits (HTTP 429) & Outages:** All Groq API calls are wrapped in robust retry handlers with jittered exponential backoff. If rate limits persist, agents catch the exception and immediately switch to local, deterministic heuristics (regex tokenization, urgency dictionaries, domain entropy). The finding is marked `status='degraded_fallback'` and preserved in the investigation.
- **Reputation API Timeouts:** If external domain reputation lookups exceed timeout thresholds, the URL agent proceeds using local heuristic scoring (homoglyphs, TLD risk, Levenshtein distance).
- **Graceful Degradation:** An API failure never crashes the investigation or returns an HTTP 500 error; the investigation completes with 200 OK and records an audit trace of the degraded mode.

---

### Q12: Why does ThreatWeave disclaim audio deepfake detection?
**Answer:**
Intellectual honesty is a cornerstone of sound engineering. ThreatWeave **deliberately does not claim to reliably detect AI-generated voice or deepfakes**:
- **Scientific Reality:** Reliable, generalized detection of synthetic speech over compressed, band-limited telephony audio (8kHz–16kHz) remains an unsolved research challenge with high false-positive rates.
- **Implementation Reality:** The Voice Agent extracts basic acoustic telemetry (zero-crossing rate, spectral centroid, RMS energy) as weak advisory cues, explicitly capping acoustic anomaly confidence at $\le 0.40$.
- Threat classification focuses squarely on **vishing behavioral script analysis** (impersonation claims, coercive urgency, bank OTP requests) rather than unproven acoustic biometrics.

---

## 5. Competitive Differentiation

### Q13: What makes ThreatWeave different from existing point solutions (VirusTotal, Windows Defender, Google Safe Browsing, QR scanners, and scam call detectors)?
**Answer:**

| Solution | Operational Paradigm | Critical Vulnerability / Gap | ThreatWeave Differentiation |
| :--- | :--- | :--- | :--- |
| **VirusTotal / Google Safe Browsing** | Single-modality URL/hash lookup against known threat feeds | Blind to zero-day typosquats, ephemeral URLs created minutes earlier, and cross-channel SMS/voice lures. | Evaluates structural heuristic anomalies independently of blacklists and correlates URLs with accompanying text/images. |
| **Windows Defender / Endpoint AV** | Host-based process, memory, and binary artifact inspection | Cannot inspect or correlate incoming social engineering communications across SMS, UPI QR, and telephony. | Operates at the multi-modal communications layer before user execution occurs. |
| **Mobile UPI QR Scanners** | Basic barcode decoding passing raw deep-link to payment app | Display payee name can be spoofed while underlying VPA routes funds to an attacker; no fraud heuristic checks. | Decodes QR, inspects VPA syntax against banking registries, detects payee-VPA mismatches, and flags suspicious payment handles. |
| **Voice Scam Call Filters (e.g. Truecaller)** | Community phone-number reputation and caller ID matching | Ineffective against fresh VoIP numbers, SIM-box rotations, or spoofed Caller ID headers. | Transcribes voicemail audio and evaluates conversational vishing scripts for banking urgency and coercion. |
| **Unified Swarm Advantage** | **Isolated Single-Modality Silos** | **Each component engineered to appear benign in isolation.** | **Detects coordinated cross-modal campaigns where individual signals are subtle, but composite synthesis exposes a critical attack.** |

---

## 6. Report Generation & Enterprise Export Architecture

### Q14: Why maintain both browser print-to-PDF and server-side PDF generation?
**Answer:**
Both export pathways serve distinct, complementary operational requirements:
1. **Browser Print (`window.print()`):**
   - Utilizes CSS `@media print` rules for rich, client-rendered visual output.
   - Allows human analysts to preview the layout, adjust printer margins, and leverage native browser typography without server CPU load.
2. **Server-Side PDF (`GET /api/v1/investigations/{id}/report/pdf`):**
   - Implemented via `reportlab` as a container-independent, lightweight, pure-Python pipeline.
   - Enables headless, automated report generation for automated SOC pipelines, n8n webhook workflows, and offline archiving without requiring an interactive web browser.
   - Generates deterministic, byte-valid PDF files (`%PDF-` signature) with audit logging across Linux containers and Windows hosts.
