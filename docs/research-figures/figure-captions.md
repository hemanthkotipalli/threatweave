# ThreatWeave: Publication-Grade Figure Captions and Metadata

This document specifies the formal, publication-grade captions, structural descriptions, and metadata for all architectural and analytical figures incorporated into the ThreatWeave research manuscript (*"ThreatWeave: An Agentic Multimodal Framework for Cross-Modal Digital Communication Threat Analysis"*).

All figures are maintained in four formats under `docs/research-figures/`:
- `.dot`: Graphviz source code for deterministic regeneration and editing.
- `.svg`: High-precision Scalable Vector Graphics for digital and web rendering.
- `.pdf`: Vector-embedded Portable Document Format for direct inclusion in IEEE LaTeX compilation (`\includegraphics`).
- `.png`: 300-DPI high-resolution raster preview for document reviewers.

---

## Figure 1: ThreatWeave End-to-End System Architecture

**File Reference:** `figure1-system-architecture.[dot|svg|pdf|png]`

### IEEE Publication Caption
> **Fig. 1. End-to-end architectural topology of the ThreatWeave agentic framework.** The multi-tier architecture illustrates the complete dataflow across five functional layers: (1) Multimodal Ingestion Layer handling raw SMS/email text (up to 20,000 characters), URLs, QR codes, payment receipts/screenshots (up to 10 MB, clamped to 1024px), and voice audio (up to 15 MB); (2) LangGraph Orchestration Layer maintaining stateful `InvestigationState` and dynamic execution routing; (3) Domain Intelligence Agents executing primary cloud LLM inference (defaulting to Groq Cloud `openai/gpt-oss-120b`, with runtime support for `llama-3.3-70b-versatile`) paired with local deterministic regex/heuristic and ONNX fallbacks alongside semantic RAG retrieval (cosine similarity threshold $\tau_{\text{sim}} = 0.40$, equivalent to maximum cosine distance $d \le 0.60$) from ChromaDB over 24 authoritative CERT-In and RBI advisories; (4) Closed-Form Deterministic Risk Engine executing linear weighted aggregation, multi-source IoC corroboration, and cross-modal contradiction penalties; and (5) Persistence & Dispatch Layer orchestrating PostgreSQL storage, Next.js analyst dashboards, and optional n8n security automation webhooks.

### Detailed Component Description
1. **Ingestion Layer:** Accepts heterogeneous payload vectors including SMS text lures, malicious URLs, QR images (payment QR vs. redirect URL), payment interface screenshots, and voice recordings (WAV/MP3/M4A). Enforces magic-byte validation and strict size ceilings (10 MB image, 15 MB audio, 20,000 chars text).
2. **LangGraph StateGraph Core:** Initializes `InvestigationState` containing extracted indicators of compromise (IoCs), modal payloads, trace metadata, and agent results. Resolves dynamic branching through conditional routing edges based on payload presence.
3. **Specialized Intelligence Tier:**
   - **Text Agent:** Semantic intent analysis, urgency detection, and RAG contextual matching with 9-category regex fallback.
   - **URL Agent:** Domain entropy, age heuristics, IP hosting checks, combosquatting detection, and two-tier severity reconciliation.
   - **QR Agent:** Dual-stage cv2-WeChat delineation distinguishing UPI merchant/payment tokens from web hyperlinks with headless UPI payee uncertainty calibration.
   - **Image Agent:** EasyOCR text extraction and retail invoice layout disambiguation under `torch.inference_mode()` memory bounds.
   - **Voice Agent:** Faster-Whisper local acoustic transcription paired with social engineering dialogue extraction and acoustic cadence analysis.
4. **Deterministic Risk Engine:** Closed-form mathematical evaluation ensuring zero stochastic variation across repeated executions on identical findings ($|\text{residual}| \le 1.0 \times 10^{-4}$).
5. **Persistence & Enterprise Dispatch:** Relational audit logging via PostgreSQL, real-time analyst triage via Next.js 14, and optional remediation webhooks via n8n.

---

## Figure 2: LangGraph State Machine and Conditional DAG Execution

**File Reference:** `figure2-langgraph-workflow.[dot|svg|pdf|png]`

### IEEE Publication Caption
> **Fig. 2. LangGraph state machine execution flow and dynamic fan-out DAG.** Execution initiates at the `Plan` node, which parses input channels and determines active modalities. The orchestrator computes conditional edges, fanning out concurrently to relevant agents while recording deliberate `SKIPPED` markers for inactive modalities. Active agents concurrently populate the shared `InvestigationState` through reducer-backed evidence accumulation. Upon fan-in synchronization, evidence flows through result aggregation, indicator correlation, conflict detection, regulatory RAG retrieval, and deterministic risk calculation before terminating at the `End` state.

### Detailed Execution Mechanics
- **State Initialization:** `InvestigationState` is instantiated with request metadata, tenant boundaries, and payload references.
- **Dynamic Routing:** Conditional edges evaluate active input modalities. Uninvoked agents are marked as `SKIPPED` with null latency and zero resource overhead.
- **Resilient Fallback Loop:** If primary Groq API latency exceeds timeout thresholds or encounters rate limits, execution seamlessly routes to local regex/heuristic engines without breaking the LangGraph state transition.
- **State Aggregation:** All active agent findings, extracted entities, and domain-specific scores are consolidated into an immutable evidence schema for scoring.

---

## Figure 3: Cross-Modal Threat Intelligence Correlation & Indicator Conflict Engine

**File Reference:** `figure3-cross-modal-correlation.[dot|svg|pdf|png]`

### IEEE Publication Caption
> **Fig. 3. Cross-modal threat intelligence correlation and multi-source conflict resolution pipeline.** The pipeline ingests independent modality findings, normalizes extracted entities (URLs, domain names, phone numbers, brands, payment VPAs), and projects them into a shared correlation matrix. The engine executes bidirectional correlation: (a) reinforcing confidence when indicators align across distinct modalities via corroboration bonus $\Delta_{\text{corrob}} = \min\left(0.25, \, \sum 0.10 \cdot (k_i - 1) + \sum 0.05 \cdot (m_c - 1)\right)$, and (b) penalizing composite risk via the deterministic contradiction penalty $\Delta_{\text{contra}} = \min(0.30, \, 0.10 \times N_{\text{conflicts}})$ when cross-modal polar severity contradictions emerge ([info, low] $\leftrightarrow$ [high, critical]), mitigating unilateral false positives.

### Detailed Mathematical Mechanics
- **Indicator Harmonization:** Extracts canonical identifiers: FQDNs, IPv4 addresses, UPI Virtual Private Addresses (VPAs), bank account numbers, and organization entities.
- **Alignment Reinforcement:** If $\text{Domain}_{\text{URL}}$ matches masqueraded brand in $\text{OCR}_{\text{Image}}$ or $\text{Transcript}_{\text{Voice}}$, corroboration bonuses reinforce composite confidence. Agent pairs exhibiting severity divergence conflicts are strictly excluded from category corroboration.
- **Contradiction Penalty Formulation:**
  $$\Delta_{\text{contra}} = \min\left(0.30, \, 0.10 \times N_{\text{conflicts}}\right)$$
- Prevents weaponized false alerts where an attacker embeds a legitimate brand name or benign URL into an otherwise coercive communication.

---

## Figure 4: Closed-Form Deterministic Risk Engine Pipeline

**File Reference:** `figure4-risk-engine.[dot|svg|pdf|png]`

### IEEE Publication Caption
> **Fig. 4. Closed-form deterministic risk engine calculation pipeline and tier mapping.** The mathematical engine processes consolidated agent findings through five sequential stages: (1) confidence-weighted base score calculation across included non-failed findings $\text{base\_score} = \frac{1}{|F_{\text{included}}|} \sum (W(\text{sev}_f) \times c_f)$; (2) multi-agent corroboration bonus $\Delta_{\text{corrob}}$ (up to $+0.25$); (3) regulatory RAG intelligence bonus $\Delta_{\text{intel}} = +0.15$ (triggered when cosine similarity $\ge 0.40$, equivalent to cosine distance $d \le 0.60$); (4) contradiction penalty deduction $\Delta_{\text{contra}}$ (up to $0.30$); and (5) mathematical boundary clamping to $[0.0, 1.0]$. The final composite risk score maps deterministically onto five discrete operational severity bands: Info ($[0.00, 0.19]$), Low ($[0.20, 0.39]$), Medium ($[0.40, 0.59]$), High ($[0.60, 0.79]$), and Critical ($[0.80, 1.00]$), triggering automated containment and analyst escalations.

### Detailed Analytical Formulation
- **Base Score Formulation:**
  $$\text{base\_score} = \frac{1}{|F_{\text{included}}|} \sum_{f \in F_{\text{included}}} \left(W(\text{sev}_f) \times c_f\right)$$
  where severity weights are defined as $W(\text{info}) = 0.00$, $W(\text{low}) = 0.25$, $W(\text{medium}) = 0.50$, $W(\text{high}) = 0.75$, $W(\text{critical}) = 1.00$, and finding confidence $c_f \in [0.0, 1.0]$.
- **Corroboration Bonus:**
  $$\Delta_{\text{corrob}} = \min\left(0.25, \, \sum_{i \in \text{SharedIoC}} 0.10 \cdot (k_i - 1) + \sum_{c \in \text{CategoryMatch}} 0.05 \cdot (m_c - 1)\right)$$
- **Regulatory RAG Grounding Bonus:**
  $$\Delta_{\text{intel}} = \begin{cases} +0.15 & \text{if } \text{sim}_{\max} \ge 0.40 \quad (d \le 0.60) \\ 0.00 & \text{otherwise} \end{cases}$$
- **Contradiction Penalty:**
  $$\Delta_{\text{contra}} = \min\left(0.30, \, 0.10 \times N_{\text{conflicts}}\right)$$
- **Final Composite Metric:**
  $$\text{final\_risk} = \text{clamp}\left(\text{base\_score} + \Delta_{\text{corrob}} + \Delta_{\text{intel}} - \Delta_{\text{contra}}, \; 0.0, \; 1.0\right)$$
- **Operational Severity Bands:**
  - `info`: $0.00 \le \text{final\_risk} < 0.20$
  - `low`: $0.20 \le \text{final\_risk} < 0.40$
  - `medium`: $0.40 \le \text{final\_risk} < 0.60$
  - `high`: $0.60 \le \text{final\_risk} < 0.80$
  - `critical`: $0.80 \le \text{final\_risk} \le 1.00$
- Guarantees strict mathematical invariance ($|\text{residual}| \le 1.0 \times 10^{-4}$), explainability, and full cryptographic auditability for Security Operations Center (SOC) environments.
