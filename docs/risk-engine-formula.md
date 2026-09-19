# ThreatWeave — Mathematical Risk Scoring Engine Specification

> **Document Class:** Technical Specification & Academic Mathematical Formalism  
> **Target Subsystem:** `apps/api/app/agents/risk_engine.py`  
> **Source Version:** ThreatWeave Phase 11 / Phase 12 (Validated in Phase C)  
> **Applicability:** Capstone Defense, Viva Voce Reference, and Academic Project Report Appendix  

---

## 1. Architectural Motivation & Design Guarantees

In autonomous multi-agent cyber threat intelligence systems, aggregating specialist agent telemetry is frequently implemented through naive heuristic averages or stochastic Large Language Model (LLM) prompts (e.g., prompting an LLM to *"rate the threat from 1 to 10"*). Such approaches suffer from well-documented failure modes:
1. **Stochastic Non-Determinism:** Identical evidentiary findings can yield divergent risk assessments across repeated evaluations.
2. **Hallucinated Escalation:** An ungrounded LLM can conflate low-confidence informational warnings with high-severity indicators.
3. **Black-Box Opacity:** Regulatory compliance and security operations center (SOC) triage require explicit, auditable mathematical contributions for each evidence stream.

To solve this, ThreatWeave implements a **pure, deterministic mathematical risk engine** ([`app/agents/risk_engine.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/risk_engine.py)). The engine executes with **zero database access, zero network calls, and zero LLM invocations**. Given an identical list of consolidated findings and threat advisory citations, it produces bitwise-identical risk scores, confidence bounds, and component contributions.

---

## 2. Mathematical Formalization

### 2.1 Severity Weights

Qualitative severity ratings emitted by specialist agents are mapped to fixed scalar weights $W(\text{sev}) \in [0.0, 1.0]$:

| Severity Enum ($\text{sev}$) | Nominal Weight $W(\text{sev})$ | Operational Semantics |
| :--- | :---: | :--- |
| `info` | **$0.00$** | Contextual/informational observation; non-malicious indicator. |
| `low` | **$0.25$** | Minor anomaly, low-probability heuristic deviation. |
| `medium` | **$0.50$** | Suspicious attribute, moderate social engineering or heuristic match. |
| `high` | **$0.75$** | Strong malicious indicator, confirmed deceptive vector. |
| `critical` | **$1.00$** | Definite credential harvesting, poisoned payload, or brand impersonation. |

---

### 2.2 Finding Inclusion & Individual Finding Score

Let $\mathcal{F}_{\text{raw}} = \{f_1, f_2, \dots, f_M\}$ be the raw collection of findings returned by the executed specialist agents (`Text`, `URL`, `QR`, `Image`, `Voice`).

1. **Failure Filter:** Any finding originating from an agent that terminated in an unhandled failure state (`status = 'failed'`) is excluded to prevent ungrounded noise from skewing calculations:
   $$\mathcal{F} = \{ f \in \mathcal{F}_{\text{raw}} \mid \text{status}(f) \neq \text{'failed'} \}$$
   *(Note: Findings marked as `'degraded_fallback'`—where an agent fell back to deterministic regex/heuristics due to rate limits—**are** included, maintaining full pipeline resilience).*

2. **Per-Finding Weighted Score:** For each finding $f_i \in \mathcal{F}$, where $\text{sev}_i$ is its severity and $c_i$ is the agent's reported confidence, confidence is bounded to the unit interval $c_i' = \text{clamp}(c_i, 0.0, 1.0)$. The individual finding score $s_i$ is:
   $$s_i = W(\text{sev}_i) \times c_i'$$

---

### 2.3 Base Score Aggregation

Let $N = |\mathcal{F}|$ be the number of valid included findings.

- If $N = 0$:
  $$\text{base\_score} = 0.0, \quad \bar{c} = 0.0$$
- If $N > 0$:
  $$\text{base\_score} = \frac{1}{N} \sum_{i=1}^{N} s_i = \frac{1}{N} \sum_{i=1}^{N} \left( W(\text{sev}_i) \times c_i' \right)$$
  $$\bar{c} = \frac{1}{N} \sum_{i=1}^{N} c_i'$$

Where $\text{base\_score} \in [0.0, 1.0]$ represents the baseline risk intensity across all active modalities, and $\bar{c}$ represents the average agent confidence.

---

### 2.4 Corroboration Bonus ($\Delta_{\text{corrob}}$)

Multi-modal attacks are distinguished by multiple modalities reinforcing the same campaign indicators (e.g., an SMS message referencing a domain that matches a URL extracted from an image OCR pass).

1. The correlation engine ([`app/agents/correlation.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/app/agents/correlation.py)) evaluates technical indicators across findings.
2. A **corroboration group** $\mathcal{G}_k$ is formed when two or more *distinct* agents report identical canonical indicator strings (e.g., matching domain, VPA, phone number, or urgency token).
3. Each additional distinct agent in group $\mathcal{G}_k$ beyond the first contributes $+0.10$ to the raw corroboration bonus:
   $$\text{raw\_corroboration\_bonus} = \sum_{k} 0.10 \times \left( |\text{Agents}(\mathcal{G}_k)| - 1 \right)$$
4. **Capping Rule:** To prevent an abundance of shared minor tokens from artificially overpowering the base evidence, the corroboration bonus is strictly capped at $+0.25$:
   $$\Delta_{\text{corrob}} = \min(0.25, \text{raw\_corroboration\_bonus})$$

---

### 2.5 Threat Intelligence Grounding Bonus ($\Delta_{\text{intel}}$)

ThreatWeave incorporates Retrieval-Augmented Generation (RAG) over curated advisories from CERT-In and the Reserve Bank of India (RBI).

1. Let $\mathcal{C} = \{c_1, c_2, \dots, c_P\}$ be the set of retrieved threat advisory chunks retrieved from ChromaDB for the investigation's technical observables.
2. Let $\sigma(c_j) \in [0.0, 1.0]$ represent the cosine similarity score between the query embedding and advisory chunk $j$.
3. Let $\tau_{\text{RAG}} = 0.40$ be the system similarity threshold (`settings.RAG_SIMILARITY_THRESHOLD`).
4. **Gating Rule:** If at least one advisory chunk matches observed indicators above the threshold, a discrete grounding bonus of $+0.15$ is awarded:
   $$\Delta_{\text{intel}} = \begin{cases} 0.15 & \text{if } \exists c_j \in \mathcal{C} \text{ such that } \sigma(c_j) \ge 0.40 \\ 0.00 & \text{otherwise} \end{cases}$$

This formalizes the operational principle that threats corroborating known active nation-state or banking fraud bulletins carry higher confirmed urgency.

---

### 2.6 Contradiction Penalty ($\Delta_{\text{contra}}$)

When specialist agents produce conflicting evaluations regarding shared evidence categories (e.g., `Text Agent` detects high-confidence credential phishing while `URL Agent` evaluates the destination domain as an authentic, benign institutional portal), epistemic uncertainty increases.

1. The conflict engine evaluates semantic indicator contradictions between agent pairs.
2. Each detected pairwise conflict $\kappa \in \mathcal{K}$ contributes a $-0.10$ deduction:
   $$\text{raw\_contradiction\_penalty} = 0.10 \times |\mathcal{K}|$$
3. **Capping Rule:** The penalty is bounded to a maximum deduction of $0.30$:
   $$\Delta_{\text{contra}} = \min(0.30, \text{raw\_contradiction\_penalty})$$

---

### 2.7 Final Composite Risk Calculation & Bounded Clamping

The continuous composite risk score $R_{\text{final}}$ is assembled additively from the four orthogonal components:

$$R_{\text{raw}} = \text{base\_score} + \Delta_{\text{corrob}} + \Delta_{\text{intel}} - \Delta_{\text{contra}}$$

To ensure safety and mathematical validity, the final score is strictly clamped to the unit interval $[0.0, 1.0]$:

$$R_{\text{final}} = \text{clamp}(R_{\text{raw}}, 0.0, 1.0) = \max\left(0.0, \min(1.0, R_{\text{raw}})\right)$$

---

### 2.8 Severity Band Classification

The continuous score $R_{\text{final}}$ maps monotonically to discrete operational severity bands for SOC escalation:

$$\text{Severity}(R_{\text{final}}) = \begin{cases}
\text{INFO} & \text{if } 0.00 \le R_{\text{final}} < 0.20 \\
\text{LOW} & \text{if } 0.20 \le R_{\text{final}} < 0.40 \\
\text{MEDIUM} & \text{if } 0.40 \le R_{\text{final}} < 0.60 \\
\text{HIGH} & \text{if } 0.60 \le R_{\text{final}} < 0.80 \\
\text{CRITICAL} & \text{if } 0.80 \le R_{\text{final}} \le 1.00
\end{cases}$$

---

### 2.9 Epistemic Uncertainty Gating (`low_confidence`)

A numerical score alone can be deceptive if calculated from sparse data. ThreatWeave evaluates a deterministic boolean uncertainty flag:

$$\text{low\_confidence} = (N < 2) \lor (\bar{c} < 0.40)$$

When `low_confidence = True`, the SOC UI visually flags the investigation with an uncertainty warning badge, notifying analysts that the assessment is based on either a solitary modality or low-confidence heuristic inference.

---

## 3. Fully Worked Numerical Examples (Real Execution Data)

### Example 1: Multi-Channel KYC Phishing Campaign (`cross_modal` Demo Run)
*Source: Live Playwright E2E run (`e2e/demo-flow.spec.ts`) & LangGraph Orchestrator Execution Log*

#### Inputs:
- Modalities: Text lure, typosquatted URL, forged KYC notice screenshot.
- Active Swarm Agents: `text_agent`, `url_agent`, `image_agent`.
- Retrieved RAG Citations: 5 CERT-In advisories clearing threshold ($\sigma \ge 0.40$).

#### Finding Telemetry:
1. **$f_1$ (`text_agent`):** $\text{sev}_1 = \text{'critical'}$ ($W = 1.00$), $c_1 = 0.90 \implies s_1 = 1.00 \times 0.90 = 0.9000$
2. **$f_2$ (`url_agent`):** $\text{sev}_2 = \text{'high'}$ ($W = 0.75$), $c_2 = 0.85 \implies s_2 = 0.75 \times 0.85 = 0.6375$
3. **$f_3$ (`image_agent`):** $\text{sev}_3 = \text{'medium'}$ ($W = 0.50$), $c_3 = 0.9095 \implies s_3 = 0.50 \times 0.9095 = 0.4548$

#### Arithmetic Steps:
1. **Count & Confidence:**
   $$N = 3$$
   $$\bar{c} = \frac{0.9000 + 0.8500 + 0.9095}{3} = \frac{2.6595}{3} \approx 0.8865$$
2. **Base Score:**
   $$\text{base\_score} = \frac{0.9000 + 0.6375 + 0.4548}{3} = \frac{1.9923}{3} \approx 0.6641$$
3. **Corroboration Bonus:** Distinct target indicators: $\Delta_{\text{corrob}} = +0.0000$
4. **Threat Intel Bonus:** 5 CERT-In advisory matches with $\sigma \ge 0.40$: $\Delta_{\text{intel}} = +0.1500$
5. **Contradiction Penalty:** No conflicting findings detected: $\Delta_{\text{contra}} = 0.0000$
6. **Composite Risk Calculation:**
   $$R_{\text{raw}} = 0.6641 + 0.0000 + 0.1500 - 0.0000 = 0.8141$$
   $$R_{\text{final}} = \text{clamp}(0.8141, 0.0, 1.0) = \mathbf{0.8141}$$
7. **Severity Mapping:** $0.8141 \in [0.80, 1.00] \implies \mathbf{CRITICAL}$
8. **Uncertainty Flag:** $N = 3 \ge 2$ and $\bar{c} = 0.8865 \ge 0.40 \implies \text{low\_confidence} = \mathbf{False}$

---

### Example 2: Cross-Agent Corroboration with Capping (`test_corroboration_bonus_caps_at_0_25`)
*Source: `apps/api/tests/test_risk_engine.py::TestRiskEngineDirect::test_corroboration_bonus_caps_at_0_25`*

#### Inputs:
- 4 specialist agents (`text_agent`, `url_agent`, `qr_agent`, `image_agent`) all independently detect and report the identical malicious indicator token: `"credential_request"`.
- Each finding reports severity $\text{'medium'}$ ($W = 0.50$) with confidence $c = 0.60$.

#### Finding Telemetry:
For each $i \in \{1, 2, 3, 4\}$:
$$s_i = 0.50 \times 0.60 = 0.3000$$

#### Arithmetic Steps:
1. **Base Score:**
   $$\text{base\_score} = \frac{0.3000 \times 4}{4} = 0.3000, \quad \bar{c} = 0.6000$$
2. **Corroboration Bonus Calculation:**
   - 1 corroboration group with 4 distinct agents: $|\text{Agents}(\mathcal{G})| = 4$.
   - Raw bonus: $0.10 \times (4 - 1) = 0.10 \times 3 = +0.3000$.
   - Applying the strict cap:
     $$\Delta_{\text{corrob}} = \min(0.25, 0.3000) = \mathbf{+0.2500}$$
3. **Intel & Penalty:** $\Delta_{\text{intel}} = 0.0000, \Delta_{\text{contra}} = 0.0000$.
4. **Composite Risk Calculation:**
   $$R_{\text{final}} = 0.3000 + 0.2500 + 0.0000 - 0.0000 = \mathbf{0.5500}$$
5. **Severity Mapping:** $0.5500 \in [0.40, 0.60) \implies \mathbf{MEDIUM}$
6. **Uncertainty Flag:** $N = 4 \ge 2$ and $\bar{c} = 0.60 \ge 0.40 \implies \text{low\_confidence} = \mathbf{False}$

---

### Example 3: Direct Multi-Agent Contradiction Penalty (`test_direct_conflict_contradiction_penalty_applied`)
*Source: `apps/api/tests/test_risk_engine.py::TestRiskEngineDirect::test_direct_conflict_contradiction_penalty_applied`*

#### Inputs:
- Multi-modal submission where agents disagree on the core threat nature of the communication.
- $f_1$ (`text_agent`): Flagged as high-urgency credential harvesting: $\text{sev}_1 = \text{'critical'}$ ($W = 1.00$), $c_1 = 0.80$, indicator: `"credential_request"`.
- $f_2$ (`url_agent`): Evaluated destination domain as benign institutional portal: $\text{sev}_2 = \text{'info'}$ ($W = 0.00$), $c_2 = 0.80$, indicator: `"impersonation_claim"`.

#### Arithmetic Steps:
1. **Finding Scores:**
   $$s_1 = 1.00 \times 0.80 = 0.8000, \quad s_2 = 0.00 \times 0.80 = 0.0000$$
2. **Base Score:**
   $$\text{base\_score} = \frac{0.8000 + 0.0000}{2} = \mathbf{0.4000}, \quad \bar{c} = 0.8000$$
3. **Contradiction Evaluation:**
   - Both indicators fall into the shared semantic category `social_engineering`.
   - The severity distance $|\text{sev}_1 - \text{sev}_2| = |1.00 - 0.00| = 1.00 \ge 0.50$ triggers conflict detection.
   - $|\mathcal{K}| = 1 \implies \text{raw penalty} = 0.10 \times 1 = 0.1000$.
   - $\Delta_{\text{contra}} = \min(0.30, 0.1000) = \mathbf{0.1000}$.
   - **Audit Record Generated:** Written to PostgreSQL `conflict_logs` with canonical schema attributes:
     - `conflict_type`: `"severity_divergence"`
     - `resolution_rule`: `"contradiction_penalty_applied"`
     - `resolution_outcome`: `"Contradiction penalty of -0.10 applied to final risk score (Divergent severity between text_agent and url_agent)"`
4. **Composite Risk Calculation:**
   $$R_{\text{raw}} = 0.4000 + 0.0000 + 0.0000 - 0.1000 = \mathbf{0.3000}$$
   $$R_{\text{final}} = \text{clamp}(0.3000, 0.0, 1.0) = \mathbf{0.3000}$$
5. **Severity Mapping:** $0.3000 \in [0.20, 0.40) \implies \mathbf{LOW}$
   *(Note: The contradiction penalty properly suppressed an otherwise medium-risk average, reflecting high epistemic ambiguity).*
6. **Uncertainty Flag:** $N = 2 \ge 2$ and $\bar{c} = 0.80 \ge 0.40 \implies \text{low\_confidence} = \mathbf{False}$

---

## 4. Summary Matrix of Engine Parameters

| Parameter | Identifier | Value / Range | Cap / Clamp | Function / Rationale |
| :--- | :--- | :---: | :---: | :--- |
| **Severity Weights** | $W(\text{sev})$ | $0.00, 0.25, 0.50, 0.75, 1.00$ | Fixed | Monotonic severity escalation table. |
| **Finding Confidence** | $c_i'$ | $[0.0, 1.0]$ | $[0.0, 1.0]$ | Agent epistemic certainty scalar. |
| **Base Aggregation** | $\text{base\_score}$ | $[0.0, 1.0]$ | None | Confidence-weighted arithmetic mean of valid findings. |
| **Corroboration Step** | $\Delta_{\text{corrob}}$ | $+0.10$ per extra agent | **$\le +0.25$** | Rewards multi-agent consensus on shared indicators. |
| **Threat Intel Bonus** | $\Delta_{\text{intel}}$ | $+0.15$ | Discrete | Rewards verification against CERT-In/RBI vector corpus ($\sigma \ge 0.40$). |
| **Conflict Penalty** | $\Delta_{\text{contra}}$ | $-0.10$ per conflict | **$\le 0.30$** | Penalizes contradictory inter-agent threat claims. |
| **Final Output** | $R_{\text{final}}$ | $[0.0, 1.0]$ | **$[0.0, 1.0]$** | Guaranteed bounded operational risk metric. |
| **Uncertainty Threshold** | $\text{low\_confidence}$ | Boolean | $N < 2 \lor \bar{c} < 0.40$ | Prevents overconfident action on sparse evidence. |
