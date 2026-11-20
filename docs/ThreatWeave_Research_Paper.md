# ThreatWeave: An Agentic Multimodal Framework for Cross-Modal Digital Communication Threat Analysis

**Authors:**  
**Mr. Mohammad Amanullah**  
*Assistant Professor*  
*Dept of CSE*  
*Godavari Institute of Engineering & Technology (A)*  
*Rajahmundry, AP, India*  
*Email: mohammad.amanullah@giet.ac.in*  

**Ravulapalli Dharma Teja**  
*UG Student*  
*Dept of CSE*  
*Godavari Institute of Engineering & Technology (A)*  
*Rajahmundry, AP, India*  
*Email: 23551A05D1@giet.ac.in*  

**Kotipalli Hemanth**  
*UG Student*  
*Dept of CSE*  
*Godavari Institute of Engineering & Technology (A)*  
*Rajahmundry, AP, India*  
*Email: 24555A0508@giet.ac.in*  

**Gaddigopula Prabash**  
*UG Student*  
*Dept of CSE*  
*Godavari Institute of Engineering & Technology (A)*  
*Rajahmundry, AP, India*  
*Email: 23551A0545@giet.ac.in*  

---

## Abstract

Social engineering and financial fraud increasingly span multiple digital communication channels, combining phishing SMS messages, deceptive hyperlinks, fraudulent quick-response (QR) payment codes, fabricated transaction receipts, and voice calls within coordinated campaigns. Existing security operations center (SOC) defenses rely on isolated single-modality scanners or black-box neural classifiers that inspect payloads independently, creating cross-channel blind spots and non-deterministic risk scores that fluctuate across identical inputs. In this paper, we present **ThreatWeave**, an agentic multimodal cybersecurity framework coordinating threat analysis across five modalities: Text, URL, QR Code, Image, and Voice. Governed by a stateful LangGraph directed acyclic graph (DAG), ThreatWeave routes payloads dynamically to observed modalities, logging skipped channels without redundant computation. To ensure auditable and reproducible assessments, the framework replaces unconstrained language model scoring with a closed-form, deterministic risk calculation:
$$\text{final\_risk} = \text{clamp}\left(\text{base\_score} + \Delta_{\text{corrob}} + \Delta_{\text{intel}} - \Delta_{\text{contra}}, \; 0.0, \; 1.0\right)$$
This engine adjusts composite risk via multi-source Indicator of Compromise (IoC) corroboration, cross-modal contradiction penalties, and regulatory context retrieved from 24 CERT-In and RBI advisories using ChromaDB (cosine similarity threshold $\tau_{\text{sim}} = 0.40$, maximum cosine distance $d \le 0.60$). Each specialist agent pairs cloud language model reasoning (defaulting to Groq Cloud `openai/gpt-oss-120b`, with support for `llama-3.3-70b-versatile`) with local deterministic heuristics (sub-20ms for Text and URL) for resilient offline continuity during API disruptions. Evaluated on a curated proof-of-concept benchmark of 94 Indian-context cyber-threat fixtures (51 malicious, 43 benign), ThreatWeave achieved detection accuracies of 95.8% on Text ($F_1 = 0.963$), 90.0% on Image ($F_1 = 0.909$), 79.2% on URL ($F_1 = 0.783$), and 78.6% on QR ($F_1 = 0.800$). Local fallback execution maintained sub-50ms latency for lightweight modalities (Text, URL, QR, and Voice) in the evaluated configuration (while Image fallback was OCR-bounded), and the state machine achieved 100% routing correctness across 227 automated backend test cases verifying state routing.

**Index Terms / Keywords:**  
Cyber Threat Intelligence, Multimodal Threat Detection, Multi-Agent Systems, LangGraph, Retrieval-Augmented Generation, Phishing Detection, Cross-Modal Correlation, Deterministic Risk Scoring.

---

## I. INTRODUCTION

Digital communication channels are increasingly targeted by coordinated social engineering and financial fraud campaigns. Rather than relying solely on isolated single-channel lures such as email phishing [1], [2], threat actors now frequently orchestrate multi-stage attacks across multiple media. In a typical cross-modal fraud incident, a target receives an urgent SMS alert warning of an imminent utility disconnection [3], opens an obfuscated short URL directing to an imitation payment portal [4], scans a fraudulent quick-response (QR) code embedding a headless Unified Payments Interface (UPI) collect request [5], [6], reviews a fabricated transaction screenshot presented as proof of payment [7], [8], and receives a follow-up voice phishing (vishing) telecommunication call to pressure compliance [9].

Despite the multi-modal nature of these attacks, conventional security operations center (SOC) defenses remain fragmented into isolated, modality-specific point solutions [10]. Organizations typically deploy independent tools for URL reputation lookup, barcode decoding, optical character recognition (OCR), and SMS keyword filtering. Because these standalone tools inspect payloads in isolation, they cannot correlate Indicators of Compromise (IoCs) distributed across different channels. Security analysts must therefore manually cross-reference evidence across separate consoles, leading to analyst fatigue, delayed incident triage, and higher operational overhead [10], [11].

Recent attempts to consolidate multimodal detection using end-to-end Large Language Models (LLMs) or multimodal deep neural networks introduce distinct operational challenges in enterprise security workflows [12], [13]. When prompted to assign risk scores directly, monolithic foundation models produce non-deterministic outputs that vary across repeated evaluations of identical evidence—a limitation that conflicts with forensic audit requirements and the NIST Special Publication 800-30 risk assessment framework [14]. Additionally, general-purpose vision-language models often require 8–15 seconds per request, remain susceptible to hallucinations, and become completely unavailable during cloud service interruptions because they lack local offline fallback mechanisms [13].

To address these limitations, we developed **ThreatWeave**, an agentic multimodal framework for cross-modal digital communication threat analysis. ThreatWeave organizes investigation workflows as a directed acyclic graph (DAG) managed by LangGraph [15], [16]. The orchestrator coordinates five dedicated forensic agents—Text Agent, URL Agent, QR Agent, Image Agent, and Voice Agent—routing execution dynamically to the specific modalities present in a given incident. Rather than relying on an opaque end-to-end neural classifier, ThreatWeave pairs cloud language model reasoning with local deterministic heuristic fallbacks (sub-20ms for Text and URL, and sub-50ms for QR and Voice).

ThreatWeave builds upon established open-source foundations: FastAPI for asynchronous request serving, the Groq Cloud API for language model inference, EasyOCR (PyTorch CRAFT and CRNN) for optical character recognition, OpenCV for barcode localization, Faster-Whisper for local acoustic transcription, and ChromaDB with Sentence-Transformers for dense vector storage. The scientific contributions of this work do not claim new low-level perceptual models; rather, our contributions focus on the dynamic agentic orchestration architecture, the closed-form deterministic risk algebra, domain-specific security disambiguation for digital payments, and resilient dual-tier fallback mechanics.

The primary contributions of this paper are summarized as follows:
1. **Dynamic Multi-Agent Orchestration Architecture:** A stateful LangGraph Directed Acyclic Graph (DAG) state machine that dynamically inspects heterogeneous input vectors, fanning out execution concurrently to active specialist pipelines while logging skipped modalities without redundant computation.
2. **Dual-Tier Resilient Fallback Mechanics:** An operational continuity architecture pairing cloud language model inference (defaulting to Groq Cloud `openai/gpt-oss-120b`, with runtime support for `llama-3.3-70b-versatile`) with local deterministic heuristics (sub-20ms for Text and URL, sub-50ms for QR and Voice) to preserve incident triage during external API disruptions.
3. **Closed-Form Deterministic Risk Engine:** A mathematically bounded risk engine that replaces stochastic LLM ratings with bitwise reproducible scores ($|\text{residual}| \le 1.0 \times 10^{-4}$), integrating cross-modal IoC corroboration, severity divergence contradiction penalties, and regulatory vector retrieval (ChromaDB, cosine similarity threshold $\tau_{\text{sim}} = 0.40$, $d \le 0.60$).
4. **Domain-Specific Disambiguation & Headless UPI Parsing:** An uncertainty calibration heuristic for Unified Payments Interface (UPI) payloads (`_analyze_upi_payload`) that addresses the micro-merchant false positive dilemma, reducing false alarms on retail QR codes while preserving high threat recall.
5. **Empirical Multi-Modal Benchmark Evaluation:** A systematic evaluation on a curated 94-sample proof-of-concept benchmark calibrated against Indian cybercrime vectors (CERT-In and RBI), reporting precision, recall, $F_1$, accuracy, latency profiles, and 95% Wilson confidence intervals across all operational modes.

---

## II. RELATED WORK

The architecture of ThreatWeave intersects five distinct research domains: single-modality automated threat detection, multi-agent large language model frameworks, explainable cyber threat intelligence, retrieval-augmented generation, and multimodal perceptual models. This section reviews relevant literature across these areas, highlights operational limitations in existing methods, and establishes the specific research gaps addressed by our framework.

```
+------------------------------------------------------------------------------------+
|                                RELATED WORK TAXONOMY                               |
+--------------------------+----------------------------+----------------------------+
| Single-Modality Tools    | Multi-Agent Systems        | Explainable Risk & RAG     |
| - Phishpedia (Image)     | - MetaGPT (SOP DAG)        | - Capuano et al. (XAI)     |
| - CANTINA+ (DOM/URL)     | - ChatDev (Agents)         | - NIST SP 800-30           |
| - QRishing (QR)          | - AutoGen (Conv)           | - Lewis et al. (RAG)       |
| - Sonowal (SMS)          | - Wang et al. (Survey)     | - Reimers (S-BERT)         |
| - PhishStorm (URL)       | - Wooldridge (MAS)         | - Munir et al. (MM-RAG)    |
+--------------------------+----------------------------+----------------------------+
```

### A. Single-Modality Threat Detection Point Solutions
Automated threat detection has historically evolved within isolated modality boundaries. In web and URL defense, feature-based classifiers such as CANTINA+ [1] and PhishStorm [4] analyze lexical attributes—including Shannon entropy, token lengths, and domain registration metadata—to identify malicious links. Optical barcode filtering emerged following findings by Vidas et al. [5] on mobile QR vulnerabilities, leading to tools like QsecR by Rafsanjani et al. [6]. In mobile telecommunications, smishing detectors developed by Sonowal [2] and Boukari et al. [17] classify deceptive messages through keyword co-occurrence, while Kim et al. [9] established speech transcription pipelines for voice phishing (vishing) detection. Visual brand spoofing is addressed by computer vision systems such as Phishpedia [7] and VisualPhishNet [8], which couple object detection with visual similarity models. While effective within their respective domains, these point solutions operate independently. They lack mechanisms to share intermediate state or correlate distributed Indicators of Compromise (IoCs). ThreatWeave bridges this gap by unifying these distinct forensic capabilities beneath a coordinated multi-agent state machine.

### B. Multi-Agent Systems and Collaborative LLM Frameworks
To overcome the reasoning limitations of monolithic prompts, collaborative multi-agent architectures distribute complex analytical tasks across specialized roles [12]. Classical multi-agent systems theory provides the formal foundation for distributed problem solving, task allocation, and coordination protocols [18]. In software engineering, frameworks such as MetaGPT [15] demonstrated that structuring agent interactions around Standard Operating Procedures (SOPs) significantly reduces hallucination and coordination drift compared to single-prompt generation. ChatDev [19] formalized communicative dialogue chains for iterative code refinement, while AutoGen [16] introduced conversational agent workflows. However, free-form conversational agents can introduce non-deterministic loops and execution delays that are unsuitable for real-time security operations. ThreatWeave adapts multi-agent coordination principles to defensive cybersecurity by using LangGraph to enforce a directed acyclic graph (DAG), ensuring predictable routing, bounded execution, and stateful evidence accumulation.

### C. Explainable Risk Scoring and Cyber Threat Intelligence
In operational security environments, diagnostic transparency is critical to mitigate alert fatigue and establish reliable audit trails [10]. Reviewing cyber threat intelligence (CTI) architectures, Tounsi and Rais [11] emphasized that effective threat management requires structured normalization of Indicators of Compromise (IoCs) and automated correlation across disparate sensors. The National Institute of Standards and Technology (NIST) Special Publication 800-30 Revision 1 [14] advocates systematic, documented risk assessment processes where threat likelihood and operational impact are evaluated using transparent, repeatable methodologies. Delegating risk scoring to unconstrained language models conflicts with these auditability principles, as generative ratings often fluctuate across repeated evaluations of identical evidence. ThreatWeave resolves this friction by decoupling qualitative evidence gathering from risk scoring: specialist agents extract structured findings, while a closed-form mathematical risk engine computes final scores deterministically.

### D. Retrieval-Augmented Generation (RAG) in Cybersecurity
Retrieval-Augmented Generation (RAG) architectures [20] ground parametric model reasoning in verified non-parametric knowledge bases, reducing factual hallucinations. Modern dense retrieval pipelines rely on siamese transformer embeddings—pioneered by Sentence-BERT [21]—coupled with approximate nearest-neighbor indexing structures like Hierarchical Navigable Small World (HNSW) graphs [22]. Surveys by Gao et al. [13] trace the evolution of RAG into modular pipelines incorporating structured knowledge filtering. In cybersecurity, Munir et al. [23] developed multimodal RAG for attack detection, while Gao et al. [24] introduced ThreatKG to anchor threat extraction in formal knowledge graphs. Rather than indexing broad internet corpora, ThreatWeave focuses retrieval on regulatory cybersecurity advisories, embedding 24 advisories from CERT-In and the Reserve Bank of India (RBI) [25], [3] into an offline ChromaDB store. Enforcing a cosine similarity threshold of $\tau_{\text{sim}} = 0.40$ ($d \le 0.60$) ensures that only highly pertinent regulatory precedents influence composite risk calculations.

### E. Acoustic Processing and Visual Feature Extraction
Multimodal threat analysis relies on specialized sub-symbolic perceptual models to extract structured text and acoustic representations from raw input streams. In speech recognition, Radford et al. [26] introduced Whisper, achieving robust transcription across diverse accents and noisy environments through weakly supervised pre-training. In computer vision, Baek et al. [27] formulated Character Region Awareness for Text Detection (CRAFT), and Shi et al. [28] introduced Convolutional Recurrent Neural Networks (CRNN) for visual sequence recognition—the two core engines powering EasyOCR. While specialized deepfake speech classifiers like AASIST [29] inspect raw spectrograms for synthetic voice artifacts, they do not examine the deceptive intent of the caller. ThreatWeave focuses its voice analysis on conversational semantics and acoustic cadence (energy and zero-crossing rate variance), deliberately establishing clear boundaries between conversational social engineering detection and high-order generative acoustic forensics.

---

## III. PROBLEM DEFINITION & RESEARCH OBJECTIVES

### A. Mathematical Threat Model
Let a multimodal digital communication artifact be defined as a tuple:
$$X = (\mathcal{T}, \mathcal{U}, \mathcal{Q}, \mathcal{I}, \mathcal{V})$$
where:
- $\mathcal{T} \in \Sigma^*$ represents raw textual content (SMS text, email body, chat lure).
- $\mathcal{U} \in \text{URI}$ represents extracted or submitted Uniform Resource Locators.
- $\mathcal{Q} \in \{0, 1\}^{W \times H}$ represents quick-response (QR) matrix barcode image bitmaps.
- $\mathcal{I} \in \mathbb{R}^{H \times W \times C}$ represents optical raster images (payment receipts, legal notices, fake credentials).
- $\mathcal{V} \in \mathbb{R}^T$ represents one-dimensional acoustic waveforms sampled at 16,000 Hz.

A multimodal threat investigation is defined as the mapping:
$$\Phi: X \longrightarrow \left(\mathcal{R}, \mathcal{C}, \mathcal{F}, \mathcal{I}_{\text{IoC}}\right)$$
where $\mathcal{R} \in [0.0, 1.0]$ is a deterministic composite risk score, $\mathcal{C} \in \{\text{Low}, \text{Medium}, \text{High}, \text{Critical}\}$ is an operational severity band, $\mathcal{F} = \{f_1, f_2, \dots, f_k\}$ is a set of structured evidence findings, and $\mathcal{I}_{\text{IoC}}$ is an aggregated set of validated Indicators of Compromise.

### B. Research Questions
This investigation addresses three fundamental research questions:
- **RQ1 (Orchestration Efficiency & Isolation):** Can a dynamic Directed Acyclic Graph (DAG) state machine coordinate heterogeneous multimodal specialist agents without incurring computational leakage, state desynchronization, or latency penalties for unobserved modalities?
- **RQ2 (Deterministic Explainability):** Can a closed-form mathematical risk engine guarantee bitwise scoring invariance ($|\text{residual}| \le 1.0 \times 10^{-4}$) while accurately reflecting cross-agent corroboration, regulatory intelligence grounding, and inter-modality conflict penalties?
- **RQ3 (Operational Resilience):** Can a dual-tier architecture pairing cloud LLM inference with sub-50ms deterministic heuristic fallbacks for lightweight modalities maintain acceptable defensive precision ($> 75\%$) during complete external API and network disruptions?

---

## IV. PROPOSED THREATWEAVE ARCHITECTURE

The architecture of ThreatWeave is organized into five functional layers, as illustrated in Fig. 1: Ingestion, LangGraph Orchestration, Specialist Domain Intelligence Agents, Deterministic Risk Engine, and Persistence/Dispatch. This modular organization separates input validation, control flow, forensic analysis, and numerical risk scoring.

```
+---------------------------------------------------------------------------------------------------+
|                        FIG. 1. THREATWEAVE END-TO-END SYSTEM ARCHITECTURE                         |
+---------------------------------------------------------------------------------------------------+
|  1. INGESTION LAYER                                                                               |
|     [SMS / Email Text]   [URL / Links]   [QR Barcodes]   [Payment Receipts]   [Voice Audio]       |
+---------------------------------------------------------------------------------------------------+
                                                  | (Multi-part REST Ingest)
+-------------------------------------------------v-------------------------------------------------+
|  2. LANGGRAPH ORCHESTRATION LAYER (StateGraph Execution Machine)                                  |
|     - InvestigationState Schema (Shared Reducer-Backed Evidence Accumulator)                      |
|     - Plan Node: Payload Inspection, Modality Delineation, & Dynamic Routing                      |
|     - Conditional Fan-Out Edges (Text, URL, QR, Image, Voice)                                     |
+---------------------------------------------------------------------------------------------------+
         |                  |                  |                  |                  |
+--------v-------+  +-------v-------+  +-------v-------+  +-------v-------+  +-------v-------+
| 3. SPECIALIST  |  | 3. SPECIALIST  |  | 3. SPECIALIST  |  | 3. SPECIALIST  |  | 3. SPECIALIST  |
|    TEXT AGENT  |  |    URL AGENT  |  |    QR AGENT   |  |   IMAGE AGENT |  |   VOICE AGENT |
| - gpt-oss-120b |  | - Combosquat  |  | - cv2/WeChat  |  | - EasyOCR     |  | - Faster-     |
| - 9-Class Regex|  | - Shannon Ent |  | - UPI Parser  |  | - Layout Spoof|  |   Whisper     |
| - ChromaDB RAG |  | - Levenshtein |  | - Fallback Heu|  | - Retail Match|  | - Acoustic Cad|
+--------+-------+  +-------+-------+  +-------+-------+  +-------+-------+  +-------+-------+
         |                  |                  |                  |                  |
+--------v------------------v------------------v------------------v------------------v--------------+
|  4. DETERMINISTIC RISK ENGINE                                                                     |
|     [Base Linear Aggregation] -> [Threat Multipliers] -> [IoC Boost] -> [Conflict Penalty]       |
|     -> Bounded Composite Score in [0.0, 1.0] -> Discrete Tiers (Low, Medium, High, Critical)      |
+---------------------------------------------------------------------------------------------------+
                                                  |
+-------------------------------------------------v-------------------------------------------------+
|  5. PERSISTENCE & DISPATCH LAYER                                                                  |
|     - PostgreSQL Audit Tables    - Next.js 14 SOC Dashboard    - Optional n8n Webhook Dispatch    |
+---------------------------------------------------------------------------------------------------+
```

*(Refer to vector graphic: `docs/research-figures/figure1-system-architecture.svg` and preview: `docs/research-figures/figure1-system-architecture.png`)*

### A. Ingestion Layer
The ingestion layer exposes authenticated REST endpoints (`/api/v1/investigate`) accepting multi-part payloads. Binary assets undergo pre-ingestion validation via magic byte inspection (`file_validation.py`), verifying JPEG (`\xff\xd8\xff`), PNG (`\x89PNG\r\n\x1a\n`), WebP (`RIFF....WEBP`), WAV (`RIFF....WAVE`), MP3 (`ID3`/sync), and M4A (`ftyp`) containers. Enforced payload size ceilings—10 MB for raster images, 15 MB for audio recordings, and 20,000 characters for raw text—prevent memory exhaustion attacks. Ingested media files are stored under randomized UUID4 identifiers within isolated directories, eliminating path-traversal risks.

### B. LangGraph Orchestration Layer
ThreatWeave models the investigative lifecycle as a stateful Directed Acyclic Graph (DAG) compiled with LangGraph:
$$\mathcal{G} = (\mathcal{V}, \mathcal{E})$$
where $\mathcal{V} = \{\text{Plan}, \text{Text}, \text{URL}, \text{QR}, \text{Image}, \text{Voice}, \text{Aggregate}, \text{Synthesize}, \text{End}\}$. The central state object, `InvestigationState`, serves as a reducer-backed accumulator that coordinates payload references, intermediate Indicators of Compromise (IoCs), standardized finding objects, execution flags, and timing telemetry across nodes.

### C. Specialized Domain Intelligence Agents Layer
Five autonomous specialist agents operate within the execution graph:
1. **Text Agent:** Analyzes message semantics, urgency cues, credential phishing intents, and regulatory context via dense vector RAG.
2. **URL Agent:** Evaluates lexical domain properties, combosquatting distance, IP host routing, and brand impersonation.
3. **QR Agent:** Executes dual-stage barcode detection, deep-link parameter parsing, and headless UPI payment analysis.
4. **Image Agent:** Performs multi-scale OCR, receipt geometry analysis, and retail tax invoice structural validation.
5. **Voice Agent:** Demuxes audio streams, transcribes conversational speech, and measures acoustic cadence metrics.

### D. Closed-Form Deterministic Risk Engine
Positioned downstream of specialist agent execution, the risk engine calculates composite threat scores through exact, deterministic algebra. Decoupling numerical risk aggregation from qualitative language model generation prevents hallucinated ratings and ensures reproducible assessment scores across investigations.

### E. Persistence and Dispatch Layer
All investigation traces, agent execution statuses, findings, and calculated metrics are committed to PostgreSQL using SQLAlchemy 2.0. A Next.js 14 dashboard provides real-time analyst triage, while an optional n8n workflow integration enables automated webhook alerting and SOAR dispatch.

---

## V. METHODOLOGY & AGENT ORCHESTRATION

```
+---------------------------------------------------------------------------------------------------+
|                     FIG. 2. LANGGRAPH STATE MACHINE & CONDITIONAL DAG ROUTING                     |
+---------------------------------------------------------------------------------------------------+
                                            +---------+
                                            |  START  |
                                            +----+----+
                                                 |
                                            +----v----+
                                            |  Plan   |
                                            +----+----+
                                                 |
                   +-----------------------------+-----------------------------+
                   | (has_text)   | (has_url)    | (has_qr)    | (has_img)     | (has_voice)
                   |              |              |             |               |
             +-----v----+   +-----v----+   +-----v----+  +-----v----+    +-----v----+
             |   Text   |   |   URL    |   |    QR    |  |  Image   |    |  Voice   |
             |  Agent   |   |  Agent   |   |  Agent   |  |  Agent   |    |  Agent   |
             +-----+----+   +-----+----+   +-----+----+  +-----+----+    +-----+----+
                   |              |              |             |               |
                   +-----------------------------+-----------------------------+
                                                 |
                                           +-----v-----+
                                           | Aggregate | (Risk Engine Execution)
                                           +-----+-----+
                                                 |
                                           +-----v-----+
                                           | Synthesize| (Executive Narrative)
                                           +-----+-----+
                                                 |
                                           +-----v-----+
                                           |    END    |
                                           +-----------+
```

*(Refer to vector graphic: `docs/research-figures/figure2-langgraph-workflow.svg` and preview: `docs/research-figures/figure2-langgraph-workflow.png`)*

The ThreatWeave investigative workflow progresses from input payload inspection to parallel specialist evaluation and structured evidence extraction.

### A. Dynamic StateGraph Routing
The orchestrator coordinates agent execution through a stateful LangGraph Directed Acyclic Graph (DAG) state machine, as depicted in Fig. 2. Upon receiving an incident payload $X$, the `Plan` node inspects the submitted artifacts to identify active modalities:
$$\mathcal{M}(X) \subseteq \{\text{text}, \text{url}, \text{qr}, \text{image}, \text{voice}\}$$
Execution is dispatched exclusively to the active specialist agents $\mathcal{V}_{\text{active}} = \{A_m \mid m \in \mathcal{M}(X)\}$. For every unobserved modality $k \notin \mathcal{M}(X)$, the orchestrator persists a structured skipped record:
$$\text{agent\_status}[A_k] \longleftarrow \text{'skipped'}, \quad \text{latency}[A_k] \longleftarrow 0.0\,\text{ms}$$
This dynamic fan-out ensures that compute resources and external API calls are allocated strictly to channels observed in the incident.

### B. Specialist Agent Pipelines & Dual-Tier Fallback Mechanics
Each specialist agent pairs cloud language model reasoning with local deterministic heuristics to ensure operational triage continuity during external API or network disruptions.

#### 1. Text Agent & Regulatory RAG
The Text Agent performs primary inference through Groq Cloud (default configured model `openai/gpt-oss-120b`, with runtime support for `llama-3.3-70b-versatile`), constrained by strict Pydantic JSON schemas. Concurrently, the text is queried against an offline ChromaDB vector repository comprising 24 curated CERT-In and RBI advisories using `all-MiniLM-L6-v2` dense embeddings (384 dimensions). When maximum cosine similarity satisfies $\text{sim}_{\max} \ge 0.40$ (cosine distance $d \le 0.60$), a regulatory grounding bonus $\Delta_{\text{intel}} = +0.15$ is awarded. In offline mode, the agent transitions to a 9-category regex rulebase calibrated against regional scam patterns. To avoid false alarms on administrative notifications, the fallback enforces a **contextual co-occurrence requirement**: an impersonation pattern must co-occur with both an urgency trigger and a financial call-to-action to warrant a `high` severity assessment.

#### 2. URL Agent & Combosquatting Heuristics
The URL Agent evaluates link structures through lexical heuristics: Shannon entropy $H(s) = -\sum p_i \log_2 p_i$, raw IPv4/IPv6 host validation, high-abuse top-level domains (`.top`, `.xyz`, `.rest`, `.buzz`), and Levenshtein edit distance against 17 registered Indian financial institutions. Combosquatting logic flags legitimate brand keywords combined with deceptive suffixes (e.g., `sbi-kyc-verification.top`). The final severity is reconciled deterministically:
$$\mathcal{S}_{\text{URL}} = \begin{cases} 
\max(\mathcal{S}_{\text{heur}}, \mathcal{S}_{\text{LLM}}) & \text{if } |\text{flags}| \ge 2 \text{ and } \mathcal{S}_{\text{LLM}} \in \{\text{high}, \text{critical}\} \\
\mathcal{S}_{\text{heur}} & \text{otherwise}
\end{cases}$$

#### 3. QR Agent & Headless UPI Parsing
The QR Agent extracts matrix barcodes using OpenCV (`cv2.wechat_qrcode` and `cv2.QRCodeDetector`) alongside PyZbar. When a Unified Payments Interface (UPI) URI is extracted (`upi://pay`), the parser extracts parameters: payee address ($pa$), payee name ($pn$), transaction amount ($am$), currency ($cu$), and note ($tn$). To address the **Headless UPI Payee Dilemma**—where legitimate micro-merchants generate QR codes lacking the optional payee name ($pn$)—ThreatWeave treats a missing name as an indicator of uncertainty rather than confirmed fraud:
- If $pn$ is missing and amount $am < 2000 \text{ INR}$ with no deceptive note, severity is clamped to `medium` or `low`.
- If $pn$ is missing and $am \ge 2000 \text{ INR}$ or note $tn$ contains deceptive urgency phrases, severity escalates to `high` or `critical`.

#### 4. Image Agent & Retail Receipt Layout Analysis
The Image Agent executes optical character recognition using EasyOCR (CRAFT detection + CRNN sequence recognition). Ingested images are clamped to a 1024 pixel maximum dimension via area interpolation (`cv2.INTER_AREA`) and evaluated inside `torch.inference_mode()` to maintain memory consumption below 250 MB RSS. Extracted text tokens are scanned for payment confirmation markers (*Payment Successful*, *UTR*, *Google Pay*, *PhonePe*). To prevent false positives on genuine retail receipts, the agent analyzes document layout: identifying itemized tax tables, valid GSTIN identifiers, and formal *Tax Invoice* headers, classifying genuine retail proofs as benign.

#### 5. Voice Agent & Acoustic Cadence Analysis
The Voice Agent demuxes incoming audio streams via PyAV, standardizing audio into 16-bit mono PCM buffers sampled at 16,000 Hz. Conversational speech is transcribed locally using `faster-whisper` (int8 quantized). Concurrently, acoustic cadence analysis measures speech-energy variance $\sigma_E^2$ and zero-crossing rate variance $\sigma_{\text{ZCR}}^2$. Flat, robotic pitch cadences characteristic of basic synthetic speech generators receive an auxiliary confidence cap $c \le 0.40$, ensuring acoustic cues inform the assessment without overriding semantic transcript findings.

---

## VI. CROSS-MODAL CORRELATION & RISK SCORING

Multi-channel cyber campaigns distribute indicators across distinct payloads, requiring an analytical framework that correlates evidence without relying on opaque neural heuristics. ThreatWeave addresses this challenge through a multi-stage evidence correlation pipeline (Fig. 3) paired with a closed-form, deterministic mathematical risk engine (Fig. 4).

```
+---------------------------------------------------------------------------------------------------+
|               FIG. 3. CROSS-MODAL THREAT INTELLIGENCE & INDICATOR CONFLICT ENGINE                 |
+---------------------------------------------------------------------------------------------------+
   [Text Findings]       [URL Indicators]       [QR Tokens]       [Image OCR]       [Voice Audio]
          |                     |                    |                 |                  |
          +---------------------+--------------------+-----------------+------------------+
                                                     |
                                   +-----------------v-----------------+
                                   | Normalized IoC Extraction Matrix  |
                                   | (Domains, IPs, VPAs, Phone, Brand)|
                                   +-----------------+-----------------+
                                                     |
                     +-------------------------------+-------------------------------+
                     |                                                               |
        +------------v------------+                                     +------------v------------+
        | Cross-Modal Alignment   |                                     | Modal Severity Conflict |
        | (Corroborating Evidence)|                                     | (Polar Contradictions)  |
        +------------+------------+                                     +------------+------------+
                     |                                                               |
      +--------------v--------------+                                 +--------------v--------------+
      | Award Corroboration Bonus   |                                 | Deduct Contradiction Penalty|
      |   Delta_corrob in [0, 0.25] |                                 |   Delta_contra in [0, 0.30] |
      +--------------+--------------+                                 +--------------+--------------+
                     |                                                               |
                     +-------------------------------+-------------------------------+
                                                     |
                                   +-----------------v-----------------+
                                   | Unified Threat Vector Synthesis   |
                                   +-----------------------------------+
```

*(Refer to vector graphic: `docs/research-figures/figure3-cross-modal-correlation.svg` and preview: `docs/research-figures/figure3-cross-modal-correlation.png`)*

### A. Mathematical Formulation of Composite Risk
To eliminate non-deterministic scoring volatility and guarantee evidentiary auditability, ThreatWeave aggregates specialist evidence into a bounded composite risk score:

$$\text{final\_risk} = \text{clamp}\left(\text{base\_score} + \Delta_{\text{corrob}} + \Delta_{\text{intel}} - \Delta_{\text{contra}}, \; 0.0, \; 1.0\right)$$

```
+---------------------------------------------------------------------------------------------------+
|                     FIG. 4. CLOSED-FORM DETERMINISTIC RISK ENGINE PIPELINE                        |
+---------------------------------------------------------------------------------------------------+
  Active Agent Findings {f_i} 
             |
             v
  [1. Base Score Calculation] ------> base_score = (1 / |F|) * Sum( W(sev_i) * conf_i )
             |
             v
  [2. Corroboration Bonus] ---------> Delta_corrob = min( Sum(0.10*(k_i-1)) + Sum(0.05*(m_c-1)), 0.25 )
             |
             v
  [3. Regulatory RAG Bonus] --------> Delta_intel = +0.15 (if sim_max >= 0.40)
             |
             v
  [4. Contradiction Penalty] -------> Delta_contra = min( 0.10 * N_conflicts, 0.30 )
             |
             v
  [5. Mathematical Clamping] -------> final_risk = min(1.0, max(0.0, base + corrob + intel - contra))
             |
             v
  [6. Operational Band Mapping] ----> Info [0.00, 0.19] | Low [0.20, 0.39] | Medium [0.40, 0.59] | High [0.60, 0.79] | Critical [0.80, 1.00]
```

*(Refer to vector graphic: `docs/research-figures/figure4-risk-engine.svg` and preview: `docs/research-figures/figure4-risk-engine.png`)*

#### 1. Confidence-Weighted Base Score ($\text{base\_score}$)
The baseline risk is computed as the confidence-weighted mean across all valid specialist findings $F_{\text{included}}$. Findings generated under degraded heuristic fallbacks are retained alongside standard outputs, while failed executions are excluded:
$$\text{base\_score} = \frac{1}{|F_{\text{included}}|} \sum_{f \in F_{\text{included}}} \left( W(\text{sev}_f) \times c_f \right)$$
where severity weights are defined as $W(\text{info}) = 0.00$, $W(\text{low}) = 0.25$, $W(\text{medium}) = 0.50$, $W(\text{high}) = 0.75$, and $W(\text{critical}) = 1.00$, with finding confidence $c_f \in [0.0, 1.0]$. If no valid findings are produced, $\text{base\_score} = 0.0$.

#### 2. Semantic Cross-Agent Corroboration ($\Delta_{\text{corrob}}$)
When multiple agents independently detect related indicators, ThreatWeave awards an additive corroboration bonus through two complementary mechanisms:
$$\Delta_{\text{corrob}} = \min\left( \sum_{i \in \text{SharedIoC}} 0.10 \cdot (k_i - 1) + \sum_{c \in \text{CategoryMatch}} 0.05 \cdot (m_c - 1), \; 0.25 \right)$$
First, exact indicator matches across two or more distinct agents award $+0.10$ per additional agent ($k_i - 1$) citing that indicator from the controlled taxonomy. Second, when agents share high-signal threat categories ($\mathcal{C} \in \{\text{payment\_fraud}, \text{social\_engineering}\}$) without exact string overlap, a semantic bonus of $+0.05$ per additional agent ($m_c - 1$) is granted. The total bonus is capped at $+0.25$. Agent pairs with severe severity divergence ($[\text{info}, \text{low}] \leftrightarrow [\text{high}, \text{critical}]$) on related signals are strictly excluded from category bonuses.

#### 3. Regulatory Knowledge Grounding ($\Delta_{\text{intel}}$)
Findings are queried against the offline ChromaDB advisory corpus. When the maximum cosine similarity satisfies $\text{sim}_{\max} \ge 0.40$ (cosine distance $d \le 0.60$), an intelligence grounding bonus is applied:
$$\Delta_{\text{intel}} = \begin{cases} +0.15 & \text{if } \text{sim}_{\max} \ge 0.40 \\ 0.00 & \text{otherwise} \end{cases}$$

#### 4. Contradiction Penalty ($\Delta_{\text{contra}}$)
When distinct agents evaluate related signals (sharing indicators or categories) but produce polar-opposite severities, ThreatWeave applies a contradiction penalty to mitigate unilateral false alarms:
$$\Delta_{\text{contra}} = \min\left( 0.10 \times N_{\text{conflicts}}, \; 0.30 \right)$$
where $N_{\text{conflicts}}$ denotes the number of pairwise divergences, capped at $0.30$.

#### 5. Operational Band Mapping & Uncertainty Handling
The resulting $\text{final\_risk}$ maps to discrete operational tiers: Info ($[0.00, 0.19]$), Low ($[0.20, 0.39]$), Medium ($[0.40, 0.59]$), High ($[0.60, 0.79]$), and Critical ($[0.80, 1.00]$). A `low_confidence` flag is asserted whenever $|F_{\text{included}}| < 2$ or average finding confidence falls below $0.40$, signaling human analysts to conduct manual review.

### B. Numerical Determinism & Evidentiary Auditability
Across database-backed investigation records, the difference between the stored score and the mathematical calculation yields a maximum residual bound:
$$|\text{final\_risk}_{\text{actual}} - \text{final\_risk}_{\text{computed}}| \le 1.0 \times 10^{-4}$$
Every score is persisted as a decomposed vector $(\text{base\_score}, \Delta_{\text{corrob}}, \Delta_{\text{intel}}, \Delta_{\text{contra}})$ alongside agent timing telemetry and extracted IoCs, establishing an auditable evidentiary trail for incident responders.

---

## VII. EXPERIMENTAL EVALUATION & RESULTS

### A. Benchmark Dataset & Ground Truth Stratification
We evaluated ThreatWeave on a curated benchmark of **94 threat and benign communications** reflecting Indian cybercrime patterns (CERT-In), institutional banking notices (RBI), and verified communications. The benchmark dataset is implemented as reproducible Python test fixtures in `eval/datasets.py`. Synthetic and semi-synthetic artifacts (rendered QR and image bitmaps, simulated audio PCM waveforms) were programmatically generated alongside canonical transcripts to reproduce representative Indian fraud archetypes under controlled ground-truth conditions:

#### TABLE I: Benchmark Dataset Partition and Threat Archetypes
| Modality Partition | Malicious ($y=1$) | Benign ($y=0$) | Total | Key Threat Vectors Represented |
| :--- | :---: | :---: | :---: | :--- |
| **Text** | 14 | 10 | 24 | BESCOM power disconnection, KYC suspension, customs parcel extortion, digital arrest. |
| **URL** | 14 | 10 | 24 | Raw IP logins, combosquatting banking domains, high-abuse TLDs, APK download links. |
| **QR Code** | 7 | 7 | 14 | Headless UPI collect links, OLX reverse-charge payment traps, lottery fee QR codes. |
| **Image** | 10 | 10 | 20 | Forged Google Pay/PhonePe receipts, bank suspension notices, retail tax invoices. |
| **Voice** | 6 | 6 | 12 | Bank impersonation IVRs, law enforcement coercion calls, customer service appointments. |
| **Total** | **51** | **43** | **94** | Comprehensive Indian Digital Communication Attack Surface |

*Statistical Scope and Partition Sizing:* While the 94 samples were curated by the authors as proof-of-concept fixtures based on typical Indian multimodal fraud archetypes to eliminate ground-truth label ambiguity, the dataset size is modest ($N=94$). Modality-specific partitions contain 12 to 24 samples (12 Voice, 14 QR, 20 Image, 24 Text, 24 URL). Consequently, while point estimates indicate strong threat detection capability, the corresponding Wilson 95% confidence intervals are wide (e.g., Voice recall $[18.8\%, 81.2\%]$ and QR accuracy $[52.4\%, 92.4\%]$). These results must be interpreted as empirical proof-of-concept benchmark evidence rather than population-level statistical generalizations. External validation across multi-thousand enterprise datasets, international banking rails, and diverse human telephony speech remains critical future work.

### B. Decision Rule
An agent predicts malicious ($\hat{y} = 1$) if its assigned finding severity $\text{severity} \in \{\text{high}, \text{critical}\}$. If $\text{severity} \in \{\text{info}, \text{low}, \text{medium}\}$, the prediction is benign ($\hat{y} = 0$).

### C. Benchmark Performance with Wilson 95% Confidence Intervals
To provide rigorous statistical grounding given the sample size, all metric estimates are reported alongside their 95% Wilson score confidence intervals [30]:
$$CI_{95\%} = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}, \quad z = 1.96$$

#### TABLE II: Multi-Modal Benchmark Performance with 95% Wilson Score Confidence Intervals
| Specialist Agent | Evaluation Mode | TP | FP | TN | FN | Accuracy [95% CI] | Precision [95% CI] | Recall [95% CI] | $F_1$ Score | Mean Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Text Agent** | Cloud LLM (Groq) | 13 | 0 | 10 | 1 | **95.8%** [79.8%, 99.3%] | **100.0%** [77.2%, 100%] | **92.9%** [68.5%, 98.7%] | **0.963** | 2,951.8 ms |
| | Offline Heuristic | 5 | 0 | 10 | 9 | **62.5%** [42.7%, 78.8%] | **100.0%** [56.6%, 100%] | **35.7%** [16.3%, 61.2%] | **0.526** | **2.0 ms** |
| **URL Agent** | Cloud LLM (Groq) | 9 | 0 | 10 | 5 | **79.2%** [59.5%, 90.8%] | **100.0%** [70.1%, 100%] | **64.3%** [38.8%, 83.7%] | **0.783** | 4,093.8 ms |
| | Offline Heuristic | 9 | 0 | 10 | 5 | **79.2%** [59.5%, 90.8%] | **100.0%** [70.1%, 100%] | **64.3%** [38.8%, 83.7%] | **0.783** | **13.9 ms** |
| **QR Agent** | Cloud LLM (Groq) | 6 | 2 | 5 | 1 | **78.6%** [52.4%, 92.4%] | **75.0%** [40.9%, 92.9%] | **85.7%** [48.7%, 97.4%] | **0.800** | 4,499.0 ms |
| | Offline Heuristic | 6 | 2 | 5 | 1 | **78.6%** [52.4%, 92.4%] | **75.0%** [40.9%, 92.9%] | **85.7%** [48.7%, 97.4%] | **0.800** | **45.3 ms** |
| **Image Agent** | Cloud LLM (Groq) | 10 | 2 | 8 | 0 | **90.0%** [69.9%, 97.2%] | **83.3%** [55.2%, 95.3%] | **100.0%** [72.2%, 100%] | **0.909** | 9,368.4 ms |
| | Offline Heuristic | 6 | 2 | 8 | 4 | **70.0%** [48.1%, 85.5%] | **75.0%** [40.9%, 92.9%] | **60.0%** [31.3%, 83.2%] | **0.667** | **5,455.4 ms** |
| **Voice Agent** | Offline Heuristic | 3 | 1 | 5 | 3 | **66.7%** [39.1%, 86.2%] | **75.0%** [30.1%, 95.4%] | **50.0%** [18.8%, 81.2%] | **0.600** | **36.5 ms** |

Across the five modalities, primary cloud LLM inference demonstrates strong threat detection capability while preserving high precision on benign inputs:
- **Text Agent:** Achieved 95.8% accuracy ($F_1 = 0.963$) and 92.9% recall with zero false positives on benign communications, effectively identifying regional SMS impersonation schemes (e.g., BESCOM power disconnection alerts and KYC deactivations).
- **URL Agent:** Achieved 79.2% accuracy ($F_1 = 0.783$) with zero false alarms. Both cloud LLM and offline heuristic modes yielded identical confusion matrices ($TP=9, FP=0, TN=10, FN=5$) because deterministic lexical token parsing and Levenshtein distance checks against the 17-bank registry provide the primary discriminative signal.
- **Image Agent:** Achieved 90.0% accuracy ($F_1 = 0.909$) and 100.0% recall in cloud mode, though it incurred 2 false positives on promotional retail receipts featuring discount banners that mimicked cash-back reward fraud. Under offline fallback, Image recall decreased to 60.0% ($TP=6, FN=4$) due to the absence of cloud semantic reasoning on subtle layout tampering.
- **Voice Agent:** Evaluated under local heuristic mode on synthetic PCM audio fixtures and canonical transcripts, achieving 66.7% accuracy ($F_1 = 0.600$, recall 50.0%). Acoustic cadence features ($\sigma_E^2, \sigma_{\text{ZCR}}^2$) serve strictly as auxiliary heuristics capped at confidence $c \le 0.40$; the system does not claim validated forensic deepfake voice detection or real-time call interception on unconstrained human telephony speech.

#### TABLE III: Cross-Modal Correlation and Conflict Resolution Performance
| Experimental Scenario | Sample Count | Alignment Accuracy | Conflict Deduction Rate | Mean Risk Shift ($\Delta \mathcal{R}$) |
| :--- | :---: | :---: | :---: | :---: |
| **Multi-Agent IoC Corroboration** | 12 | 100.0% (12/12) | 0.0% (0/12) | +0.183 |
| **Severe Inter-Modality Contradiction** | 8 | 100.0% (8/8) | 100.0% (8/8) | -0.150 |
| **Single Modality Baseline** | 74 | N/A (Isolated) | 0.0% (0/74) | 0.000 |

#### TABLE IV: Operational Fallback Continuity Latency and Precision-Recall Trade-Off
| Specialist Agent | Cloud LLM Latency | Local Fallback Latency | Fallback Latency Ratio | Cloud Recall | Fallback Recall | Missed Threats (FN) | Precision Preservation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Text Agent** | 2,951.8 ms | 2.0 ms | **1,475x** | 92.9% (13/14) | 35.7% (5/14) | 9 / 14 | 100.0% (Zero FP) |
| **URL Agent** | 4,093.8 ms | 13.9 ms | **294x** | 64.3% (9/14) | 64.3% (9/14) | 5 / 14 | 100.0% (Zero FP) |
| **QR Agent** | 4,499.0 ms | 45.3 ms | **99x** | 85.7% (6/7) | 85.7% (6/7) | 1 / 7 | 75.0% (Parity) |
| **Image Agent** | 9,368.4 ms | 5,455.4 ms | **1.7x** | 100.0% (10/10) | 60.0% (6/10) | 4 / 10 | 75.0% (-8.3%) |
| **Voice Agent** | N/A (Local) | 36.5 ms | N/A | N/A | 50.0% (3/6) | 3 / 6 | 75.0% (Local-only) |

*Interpretation of Operational Fallback Metrics:* We emphasize that the $1,475\times$ fallback latency ratio observed for the Text Agent reflects the operational transition from a public cloud WAN roundtrip (encompassing network transit from India to Groq US servers, TLS session establishment, queueing, and autoregressive generation) to an in-memory regex co-occurrence scanner. Crucially, this latency reduction does **not** represent an algorithmic speedup on equivalent computational work: the local regex fallback prioritizes operational continuity and zero false alarms (100% precision), but incurs a substantial recall reduction (falling from 92.9% to 35.7% and missing 9 of 14 threats). The dual-tier architecture is designed as a degraded-mode safety net ensuring triage continuity during external cloud outages, rather than a lossless replacement for full semantic reasoning.

#### TABLE V: System Resource Utilization and Memory Footprint
| Component / Worker Process | Peak Resident Set Size (RSS) | Idle Baseline RSS | CPU Utilization (Inference) |
| :--- | :---: | :---: | :---: |
| **FastAPI Core + LangGraph Engine** | 114.2 MB | 62.1 MB | 4.2% |
| **EasyOCR Engine (CRAFT + CRNN)** | 248.6 MB | 84.5 MB | 28.4% (Multi-thread) |
| **Faster-Whisper Engine (int8)** | 186.3 MB | 41.2 MB | 19.8% |
| **ChromaDB + Sentence-Transformers** | 142.1 MB | 55.8 MB | 6.1% |
| **Total Unified Container Runtime** | **482.4 MB** | **188.4 MB** | **< 60%** (1 vCPU) |

*Process RSS vs. Allocation Spikes:* As reported in Table V, total unified container resident set size (RSS) peaked at 482.4 MB (idle baseline 188.4 MB) during concurrent execution, remaining strictly within the 512 MB memory boundary common to cloud micro-instances (e.g. Render Free Tier). EasyOCR CRAFT+CRNN execution accounts for 248.6 MB peak RSS (84.5 MB idle). When the orchestrator processes pure standalone QR codes ($\text{coverage\_ratio} \ge 0.45$ and canvas area differential $\le 200,000\text{ px}^2$), dynamic DAG scheduling routes exclusively to OpenCV and completely bypasses EasyOCR initialization. This avoids an estimated ~455 MB PyTorch heap memory allocation spike during cold startup, preventing out-of-memory termination without sacrificing detection coverage. In addition, all 227 automated backend tests pass consistently, validating DAG routing, fallback exception handling, and schema integrity, though passing unit tests are recognized as software verification rather than empirical proof of operational defense against novel threats.

#### TABLE VI: End-to-End Latency Profile Across Invocation Permutations
| Ingestion Modality Permutation | Active Agent Set | Mean End-to-End Latency | StateGraph Routing Overhead |
| :--- | :--- | :---: | :---: |
| **Text Only** | {Text} | 2,968.2 ms | 16.4 ms |
| **URL Only** | {URL} | 4,112.5 ms | 18.7 ms |
| **Text + URL** | {Text, URL} (Parallel Fan-Out) | 4,145.1 ms | 21.2 ms |
| **QR Code (Image)** | {QR} | 4,522.6 ms | 23.6 ms |
| **Payment Receipt Screenshot** | {Image} | 9,391.8 ms | 23.4 ms |
| **Voice Audio Stream** | {Voice} | 1,482.3 ms | 19.1 ms |
| **Full Cross-Modal Incident** | {Text, URL, Image, Voice} | 9,428.6 ms | 27.8 ms |

### D. Detailed Error Analysis and Empirical Limitations
1. **QR Code Detection Trade-Offs (Uncalibrated Baseline vs. Remediated Heuristics):**
   - *Uncalibrated Defensive Baseline:* In initial stabilization testing, the QR Agent operated under an uncalibrated defensive heuristic where any extracted UPI payment URI lacking merchant parameter validation was flagged as malicious. On the 14-sample QR partition (7 malicious, 7 benign), this naive configuration flagged every input as malicious, achieving 100.0% recall on the 7 malicious samples ($TP=7, FN=0$) but misclassifying all 7 benign retail samples as threats ($FP=7, TN=0$). This resulted in an uncalibrated baseline accuracy of **50.0%** [26.8%, 73.2%], precision of **50.0%** [26.8%, 73.2%], and $F_1 = 0.667$.
   - *Post-Remediation Benchmark:* To resolve this high false-alarm rate without compromising threat detection, we implemented the headless UPI payee disambiguation logic (`_analyze_upi_payload`). This heuristic treats missing payee names ($pn$) in low-value transactions ($< 2,000 \text{ INR}$) as uncertainty rather than definitive fraud, escalating to high severity only when accompanied by deceptive transaction notes ($tn$) or high requested amounts ($\ge 2,000 \text{ INR}$). Under this remediated configuration, accuracy improved to **78.6%** ($11/14$), precision reached **75.0%** ($TP=6, FP=2, TN=5, FN=1$), and recall was maintained at **85.7%** ($F_1 = 0.800$).
   - *Operational Calibration:* We emphasize that the 2,000 INR parameter is an empirical operational threshold calibrated to regional Indian peer-to-peer and micro-merchant transaction distributions, rather than a universal mathematical fraud boundary.
2. **Voice Agent Recall Boundary (50.0%) and Evaluation Scope:** Evaluated under offline heuristic mode on synthetic PCM audio fixtures and canonical transcripts, the Voice Agent achieved 50.0% recall ($TP=3, FP=1, TN=5, FN=3$). Acoustic cadence features ($\sigma_E^2, \sigma_{\text{ZCR}}^2$) serve strictly as auxiliary heuristics capped at confidence $c \le 0.40$; the evaluation does not test compressed, noisy telephony audio or human voice biometric authenticity, and the framework does not claim validated forensic deepfake voice detection or real-time call interception.
3. **OCR Background Clutter:** The Image Agent produced 2 false positives on retail receipts featuring promotional discount banners that mimicked cash-back reward fraud templates.
4. **Software Verification vs. Operational Defense:** All 227 automated backend tests across unit and integration suites pass deterministically. While this confirms state machine routing, fallback exception handling, and schema integrity, passing software test suites is recognized as software verification rather than empirical proof of operational defense against novel adversary campaigns in the wild.

---

## VIII. COMPARATIVE ANALYSIS & DISCUSSION

```
+---------------------------------------------------------------------------------------------------+
|               FIG. 5. ARCHITECTURAL PARADIGM COMPARISON IN CTI DEFENSE                            |
+---------------------------------------------------------------------------------------------------+
  (A) Monolithic LLM: Ingests all data into 1 prompt -> Opaque, volatile scores, cloud-dependent.
  (B) Point Scanners: URL scanner + OCR scanner + AV -> Siloed, cross-modal blind, alert fatigue.
  (C) ThreatWeave: 5 Specialist Agents -> LangGraph DAG -> Deterministic Math Engine -> 100% Auditable.
```

Table VII presents a qualitative architectural comparison of ThreatWeave against four prominent CTI paradigms evaluated in literature [1], [4], [8], [12], [17]. Rather than asserting blanket superiority over commercial platforms operating on proprietary multi-million sample datasets, this analysis delineates fundamental structural trade-offs.

#### TABLE VII: Comprehensive Architectural Comparison with State-of-the-Art Paradigms
| Architectural Dimension | Monolithic LLM [12] | Traditional Point Scanners [1], [4] | Traditional ML Classifiers [17] | Black-Box Deep Nets [8] | **ThreatWeave (Proposed)** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Modality Coverage** | Architecture-dependent | Single modality (Siloed) | Modality tabular vectors | Dual modality (Text+Img) | **5 Modalities** (Text, URL, QR, Image, Voice) |
| **Specialist Isolation** | ❌ Monolithic prompt | ⚠️ Isolated, uncoordinated | ❌ Feature concatenation | ❌ End-to-end hidden layers | ✅ **5 Isolated Agents** + LangGraph |
| **Dynamic Routing** | ❌ Uniform processing | ❌ Manual analyst triage | ❌ Static input dimension | ❌ Fixed neural layers | ✅ **Dynamic DAG Fan-Out** (`skipped`) |
| **Cross-Modal Correlation** | ⚠️ Implicit in attention | ❌ Completely absent | ❌ Concatenated weights | ⚠️ Latent cross-attention | ✅ **Explicit IoC Matching & Corroboration** |
| **Conflict & Contradiction** | ❌ Unhandled; hallucination | ❌ Independent, uncoordinated | ❌ Score averaging | ❌ Averaged latent vectors | ✅ **Formal Divergence Penalty** ($\Delta_{\text{contra}}$) |
| **Scoring Transparency** | ❌ Volatile prompt rating | ⚠️ Heuristic or tool-specific | ⚠️ Opaque model output | ❌ Black-box softmax prob | ✅ **Deterministic Math** ($\le 10^{-4}$ residual) |
| **Regulatory RAG Grounding** | ⚠️ Parametric hallucination | ❌ Static blacklists | ❌ Fixed training features | ❌ Pre-trained weights | ✅ **Offline ChromaDB RAG** (24 Advisories) |
| **Offline Fallback Resilience**| ❌ Total cloud outage | ✅ Local execution | ✅ Local inference | ⚠️ High local GPU need | ✅ **Dual-Tier Heuristics (Sub-50ms Lightweight Modalities)** |
| **Evidence Auditability** | ⚠️ Free-form narrative | ⚠️ Per-tool disjoint output | ❌ Opaque feature weights | ❌ Hidden representation | ✅ **Structured Findings & IoC Trail** |

### A. Architectural Distinctions in Multimodal Defense
Traditional point scanners [1], [4] achieve high processing throughput and domain specialization within their single target modality, but suffer from cross-modal blindness when an adversary distributes threat indicators across separate delivery channels (e.g., embedding a phishing URL inside a QR payment invoice). Conversely, monolithic multimodal LLMs [12] provide centralized natural language reasoning across modalities, but introduce scoring non-determinism, prompt token bloat, and cascading hallucinations when an isolated benign entity is misclassified. Unified multimodal deep neural networks [8] capture latent feature interactions across text and images, but operate as end-to-end black boxes, masking intermediate evidence and preventing incident responders from isolating which specific modal indicator drove the classification.

ThreatWeave navigates these trade-offs by decoupling specialist feature extraction from risk scoring. Specialist agents analyze isolated modalities independently, while the LangGraph state machine selectively fans out execution based on observed inputs. The closed-form risk engine then synthesizes findings through explicit mathematical operations ($\text{base}, \Delta_{\text{corrob}}, \Delta_{\text{intel}}, \Delta_{\text{contra}}$). This guarantees scoring determinism ($\le 1.0 \times 10^{-4}$ residual) and full forensic auditability without delegating numerical risk calculation to generative language models.

### B. Operational Utility and Engineering Trade-Offs
The primary operational utility of ThreatWeave lies in automated investigative triage for Security Operations Centers (SOCs). By consolidating disparate communication signals into structured findings and persisting an auditable four-component vector, the framework accelerates tier-1 analyst workflows. However, this architecture introduces distinct systems trade-offs:
- **Latency Envelope:** End-to-end cloud-assisted investigation averages 2.9 to 9.4 seconds across modalities. While suitable for asynchronous email and message screening, this latency envelope is not designed for line-rate packet filtering on network firewalls.
- **Fallback Coverage Trade-off:** Dual-tier local heuristics guarantee continuous sub-50ms operation for lightweight modalities during cloud API disruptions, but deliberately trade detection coverage (e.g., Text recall drops from 92.9% to 35.7%) to prevent false alarms in defensive mode.
- **Memory Footprint:** Co-locating perceptual models (EasyOCR CRAFT+CRNN and Faster-Whisper int8) requires disciplined memory controls to operate within the 512 MB constraints of cloud micro-instances.

---

## IX. SECURITY & ETHICAL CONSIDERATIONS

### A. Data Privacy and Personally Identifiable Information (PII)
ThreatWeave processes sensitive digital communications containing personal phone numbers, financial accounts, and transaction records. 
1. **Access Control & Session Security:** API endpoints are secured via HMAC-SHA256 signed JSON Web Tokens (JWT) with salted bcrypt password hashing (`passlib[bcrypt]`). Role-based access control segregates `analyst` and `admin` privileges.
2. **Evidence Segregation:** Ingested media assets are persisted with non-deterministic UUID4 filenames on dedicated storage volumes.
3. **Data Sovereignty Disclaimer:** In cloud LLM mode, extracted text is transmitted over TLS-encrypted connections to the Groq Cloud API. Organizations handling classified or strictly confidential data may operate ThreatWeave exclusively in its 100% local heuristic fallback mode, ensuring zero byte transmission outside local network perimeters.

### B. Secure File Processing & Sandboxing
Pre-ingestion validation enforces magic byte sniffing on all binary uploads, discarding forged file extensions and malformed containers. Images exceeding 1024px dimension are downscaled prior to OCR inference, bounding memory consumption and preventing image-bomb denial-of-service exploits.

### C. Responsible Disclosure & Bias Considerations
ThreatWeave serves as a defensive diagnostic assistant and does not execute active counter-attacks, network penetration, or automated asset blocking without human-in-the-loop confirmation. Curated training heuristics were calibrated against publicly disclosed advisories from CERT-In and RBI, ensuring ethical compliance with regional cybersecurity research standards.

---

## X. LIMITATIONS & FUTURE WORK

We explicitly delineate six technical boundaries of the current ThreatWeave implementation:
1. **Curated Benchmark Scope & Statistical Power:** The evaluation was conducted on a curated proof-of-concept benchmark of 94 Indian-context cyber-threat fixtures. While statistically balanced (51 malicious, 43 benign) to eliminate ground-truth label ambiguity across regional attack archetypes, modality partitions are small ($N \in [12, 24]$), producing wide Wilson 95% confidence intervals (e.g., Voice recall $[18.8\%, 81.2\%]$). These findings demonstrate empirical proof-of-concept rather than broad population-level generalization.
2. **Synthetic Voice Fixture Scope:** The Voice Agent was evaluated under local heuristic mode on synthetic PCM audio fixtures and canonical transcripts ($TP=3, FP=1, TN=5, FN=3$). Acoustic cadence features ($\sigma_E^2, \sigma_{\text{ZCR}}^2$) serve as auxiliary heuristics capped at confidence $c \le 0.40$; the system does not claim validated forensic deepfake voice detection or real-time call interception on unconstrained human telephony speech.
3. **Absence of Real-Time Bank Rail Verification:** ThreatWeave detects visual, optical, and textual indicators of fraudulent payment receipts and UPI payloads. It possesses no programmatic access to NPCI, IMPS, or core banking ledgers, and cannot verify whether extracted 12-digit UTR reference numbers settled on banking rails. The 2,000 INR UPI parameter is an empirical project-specific heuristic for micro-merchants, not a universal fraud boundary.
4. **Operational Fallback Recall Boundaries:** Local heuristic fallbacks trade semantic recall (missing 9 of 14 threats in the Text partition) to maintain zero false alarms and sub-50ms triage continuity for lightweight modalities during external cloud outages. The $1,475\times$ Text latency ratio represents an operational transition between cloud WAN transit and local regex scanning, not an algorithmic speedup on equivalent work.
5. **Static Regulatory Advisory Corpus:** The ChromaDB knowledge base indexes 24 static advisories from CERT-In and RBI. Cosine similarity matching ($\tau_{\text{sim}} \ge 0.40$) provides contextual retrieval rather than definitive proof of maliciousness, and the offline corpus does not execute live crawling of zero-day vulnerability feeds.
6. **Software Testing vs. Operational Defense:** While all 227 automated backend tests collected via pytest pass deterministically, software unit testing verifies state-machine routing, exception handling, and schema integrity rather than operational defense against novel or adaptive adversary tactics.

### Future Work
Future research will focus on: (1) expanding and independently validating benchmark datasets across international banking rails, enterprise corpora, and multilingual dialects; (2) integrating on-device quantized Small Language Models (SLMs) such as Phi-3.5 or LLaMA 3.2 3B via ONNX Runtime to replace cloud API dependencies while improving offline recall; (3) investigating spectro-temporal graph attention networks (e.g., AASIST [29]) for telephony speech forensics under acoustic reverberation and background noise; (4) establishing continuous RAG corpus synchronization with authoritative threat intelligence feeds; and (5) conducting formal usability studies with operational SOC analysts to measure incident triage efficiency.

---

## XI. CONCLUSION

Digital communication fraud increasingly coordinates deceptive lures across distinct payloads, combining phishing SMS messages, deceptive hyperlinks, fraudulent payment QR codes, fabricated receipts, and social engineering audio within multi-channel campaigns. In this paper, we presented **ThreatWeave**, an agentic multimodal cybersecurity framework designed to counter cross-modal blind spots without delegating numerical risk calculation to unconstrained generative models. Coordinated by a stateful LangGraph directed acyclic graph, ThreatWeave organizes threat analysis across six agents—one central orchestrator and five isolated specialist agents spanning Text, URL, QR, Image, and Voice modalities—dynamically routing payloads exclusively to observed channels.

To eliminate scoring volatility and guarantee evidentiary auditability, the framework replaces black-box neural ratings with a closed-form, deterministic mathematical risk engine:
$$\text{final\_risk} = \text{clamp}\left(\text{base\_score} + \Delta_{\text{corrob}} + \Delta_{\text{intel}} - \Delta_{\text{contra}}, \; 0.0, \; 1.0\right)$$
Findings are aggregated into a bounded composite score ($\le 1.0 \times 10^{-4}$ numerical residual) incorporating Indicator of Compromise corroboration bonuses, severity divergence contradiction penalties, and contextual intelligence retrieved from 24 regulatory CERT-In and RBI advisories via ChromaDB. Evaluated on a curated proof-of-concept benchmark of 94 Indian-context cyber-threat fixtures (51 malicious, 43 benign), ThreatWeave demonstrated strong proof-of-concept diagnostic performance across cloud-assisted modalities (95.8% accuracy on Text, 90.0% on Image, 79.2% on URL, and 78.6% on QR). Local deterministic heuristics preserved sub-50ms offline triage continuity for lightweight modalities (Text, URL, QR, and Voice) during external API disruptions, while Image fallback was bounded by OCR computation. Operational trade-offs—such as the Text fallback's recall reduction to 35.7% and the $1,475\times$ operational latency ratio—reflect deliberate prioritization of zero false alarms on the tested offline Text benchmark over exhaustive semantic coverage.

As an exploratory research prototype, ThreatWeave is bounded by important constraints detailed in Section X, including modest partition sample sizes ($N \in [12, 24]$) that produce wide Wilson confidence intervals, voice evaluation conducted on synthetic audio fixtures without validated deepfake detection, and the absence of direct programmatic verification on real-time banking settlement rails. Future research will explore on-device quantized Small Language Models to enhance offline semantic reasoning, spectro-temporal acoustic models for telephony speech forensics, and continuous regulatory index synchronization. While these findings establish the technical feasibility of coordinating modular forensic agents under deterministic risk governance, comprehensive independent evaluation across multi-thousand enterprise datasets, international banking rails, and operational Security Operations Centers remains essential prior to broad real-world deployment.

---



## REFERENCES

[1] G. Xiang, J. I. Hong, C. P. Rosé, and L. F. Cranor, "CANTINA+: A Feature-Rich Machine Learning Framework for Detecting Phishing Web Sites," *ACM Trans. Inf. Syst. Secur.*, vol. 14, no. 2, pp. 21:1–21:28, 2011. doi: 10.1145/2019599.2019606.

[2] G. Sonowal, "Detecting Phishing SMS Based on Multiple Correlation Algorithms," *SN Comput. Sci.*, vol. 1, no. 6, p. 334, 2020. doi: 10.1007/s42979-020-00377-8.

[3] Indian Computer Emergency Response Team (CERT-In), "Annual Cyber Security Report 2023–2024," *Ministry of Electronics and Information Technology*, New Delhi, India, 2024. [Online]. Available: https://www.cert-in.org.in

[4] S. Marchal, J. François, R. State, and T. Engel, "PhishStorm: Detecting Phishing With Streaming Analytics," *IEEE Trans. Netw. Serv. Manage.*, vol. 11, no. 4, pp. 458–471, 2014. doi: 10.1109/TNSM.2014.2377295.

[5] T. Vidas, E. Owusu, S. Wang, C. Zeng, L. F. Cranor, and N. Christin, "QRishing: The Susceptibility of Smartphone Users to QR Code Phishing Attacks," in *Financial Cryptography and Data Security (FC 2013 Workshops)*, LNCS 7862, Springer, 2013, pp. 52–69. doi: 10.1007/978-3-642-41320-9_4.

[6] A. S. Rafsanjani, N. M. Kamaruddin, H. M. Rusli, and M. Dabbagh, "QsecR: Secure QR Code Scanner According to a Novel Malicious URL Detection Framework," *IEEE Access*, vol. 11, pp. 92523–92539, 2023. doi: 10.1109/ACCESS.2023.3291811.

[7] Y. Lin, R. Liu, D. M. Divakaran, J. Y. Ng, Q. Z. Chan, Y. Lu, Y. Si, F. Zhang, and J. S. Dong, "Phishpedia: A Hybrid Deep Learning Based Approach to Visually Identify Phishing Webpages," in *Proc. 30th USENIX Security Symp. (USENIX Security 21)*, 2021, pp. 3793–3810.

[8] S. Abdelnabi, K. Krombholz, and M. Fritz, "VisualPhishNet: Zero-Day Phishing Website Detection by Visual Similarity," in *Proc. 2020 ACM SIGSAC Conf. Comput. Commun. Secur. (CCS '20)*, 2020, pp. 1681–1698. doi: 10.1145/3372297.3417233.

[9] D.-H. Kim, H.-M. Park, B.-M. Jung, and S.-K. Kim, "Real-Time Korean Voice Phishing Detection Based on Machine Learning Approaches," *J. Ambient Intell. Humaniz. Comput.*, pp. 1–12, 2021. doi: 10.1007/s12652-021-03587-x.

[10] N. Capuano, G. Fenza, V. Loia, and C. Stanzione, "Explainable Artificial Intelligence in CyberSecurity: A Survey," *IEEE Access*, vol. 10, pp. 93575–93600, 2022. doi: 10.1109/ACCESS.2022.3204171.

[11] W. Tounsi and H. M. Rais, "A Survey on Technical Threat Intelligence in the Age of Sophisticated Cyber Attacks," *Comput. Secur.*, vol. 72, pp. 212–233, 2018. doi: 10.1016/j.cose.2017.09.001.

[12] L. Wang, C. Ma, X. Feng, Z. Zhang, H. Yang, J. Zhang, Z. Chen, J. Tang, X. Chen, Y. Lin, W. X. Zhao, Z. Wei, and J.-R. Wen, "A Survey on Large Language Model Based Autonomous Agents," *Front. Comput. Sci.*, vol. 18, no. 6, p. 186345, 2024. doi: 10.1007/s11704-024-40231-1.

[13] Y. Gao, Y. Xiong, X. Gao, K. Jia, J. Pan, Y. Bi, Y. Dai, J. Sun, and H. Wang, "Retrieval-Augmented Generation for Large Language Models: A Survey," *arXiv preprint arXiv:2312.10997*, 2023. doi: 10.48550/arXiv.2312.10997.

[14] National Institute of Standards and Technology, "Guide for Conducting Risk Assessments," *NIST Special Publication (SP) 800-30 Rev. 1*, Gaithersburg, MD, 2012. doi: 10.6028/NIST.SP.800-30r1.

[15] S. Hong, M. Zhuge, J. Chen, X. Zheng, C. Cheng, C. Zhang, J. Wang, Z. Wang, S. K. S. Yau, Z. Lin, L. Zhou, C. Ran, L. Xiao, C. Wu, and Q. Chen, "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework," in *Proc. Int. Conf. Learn. Represent. (ICLR 2024)*, 2024. [Online]. Available: https://openreview.net/forum?id=VtmBAGCN7o

[16] Q. Wu, G. Bansal, J. Zhang, Y. Wu, B. Li, E. Zhu, L. Jiang, X. Zhang, S. Zhang, J. Liu, A. H. Awadallah, R. W. White, D. Burger, and H. Wang, "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation," *arXiv preprint arXiv:2308.08155*, 2023. doi: 10.48550/arXiv.2308.08155.

[17] B. E. Boukari, A. Ravi, and M. Msahli, "Machine Learning Detection for SMiShing Frauds," in *Proc. IEEE Consum. Commun. Netw. Conf. (CCNC)*, 2021, pp. 1–6. doi: 10.1109/CCNC49032.2021.9369640.

[18] M. Wooldridge, *An Introduction to MultiAgent Systems*, 2nd ed. Chichester, U.K.: John Wiley & Sons, 2009.

[19] C. Qian, X. Cong, C. Yang, W. Chen, Y. Su, J. Xu, Z. Liu, and M. Sun, "ChatDev: Communicative Agents for Software Development," in *Proc. 62nd Annu. Meeting Assoc. Comput. Linguist. (ACL 2024)*, 2024, pp. 15174–15186. doi: 10.18653/v1/2024.acl-long.810.

[20] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W.-t. Yih, T. Rocktäschel, S. Riedel, and D. Kiela, "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks," in *Proc. Adv. Neural Inf. Process. Syst. (NeurIPS 2020)*, vol. 33, 2020, pp. 9459–9474.

[21] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," in *Proc. 2019 Conf. Empirical Methods Nat. Lang. Process. (EMNLP-IJCNLP)*, 2019, pp. 3982–3992. doi: 10.18653/v1/D19-1410.

[22] Y. A. Malkov and D. A. Yashunin, "Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs," *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. 42, no. 4, pp. 824–836, 2020. doi: 10.1109/TPAMI.2018.2889473.

[23] M. B. Munir, Y. Cai, L. Khan, and B. Thuraisingham, "Leveraging Multimodal Retrieval-Augmented Generation for Cyber Attack Detection," in *Proc. IEEE 6th Int. Conf. Trust, Privacy & Secur. Intell. Syst. Appl. (TPS-ISA)*, 2024, pp. 288–297. doi: 10.1109/tps-isa62245.2024.00046.

[24] P. Gao, X. Liu, E. Choi, B. Hu, Z. Zheng, F. Shao, and M. Zitnik, "ThreatKG: An AI-Powered System for Automated Open-Source Cyber Threat Intelligence Gathering," in *Proc. 1st ACM Workshop Large AI Syst. Models (LEAM '23)*, 2023, pp. 1–8. doi: 10.1145/3627535.3638464.

[25] Reserve Bank of India, "Master Direction on Digital Payment Security Controls," *Reserve Bank of India Notification RBI/2020-21/74*, Mumbai, India, Feb. 2021. [Online]. Available: https://www.rbi.org.in

[26] A. Radford, J. W. Kim, T. Xu, G. Brockman, C. McLeavey, and I. Sutskever, "Robust Speech Recognition via Large-Scale Weak Supervision," in *Proc. 40th Int. Conf. Mach. Learn. (ICML 2023)*, PMLR 202, 2023, pp. 28492–28518.

[27] Y. Baek, B. Lee, D. Han, S. Yun, and H. Lee, "Character Region Awareness for Text Detection," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2019, pp. 9365–9374. doi: 10.1109/CVPR.2019.00959.

[28] B. Shi, X. Bai, and C. Yao, "An End-to-End Trainable Neural Network for Image-Based Sequence Recognition and Its Application to Scene Text Recognition," *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. 39, no. 11, pp. 2298–2304, 2017. doi: 10.1109/TPAMI.2016.2646371.

[29] J. Jung, H.-S. Heo, H. Tak, H.-j. Shim, J. S. Chung, B.-J. Lee, H.-J. Yu, and N. Evans, "AASIST: Audio Anti-Spoofing Using Integrated Spectro-Temporal Graph Attention," in *Proc. IEEE Int. Conf. Acoust., Speech Signal Process. (ICASSP)*, 2022, pp. 6367–6371. doi: 10.1109/ICASSP43922.2022.9747766.

[30] E. B. Wilson, "Probable Inference, the Law of Succession, and Statistical Inference," *J. Am. Stat. Assoc.*, vol. 22, no. 158, pp. 209–212, 1927. doi: 10.1080/01621459.1927.10502953.
