# ThreatWeave — Phase 4.1: Independent Correction Verification Report

**Document ID:** `TW-VERIFY-PHASE4-1`  
**Review Type:** Independent IEEE Conference Manuscript Review & Empirical Artifact Verification  
**Target Paper:** *"ThreatWeave: An Agentic Multimodal Framework for Cross-Modal Digital Communication Threat Analysis"*  
**Repository Working Baseline:** `main` branch @ commit `27fb19e098a54fbc0a85d667b29798c1bedbdefc` (`27fb19e`)  
**Audit Date:** November 19, 2026  
**Auditor:** Independent Research Auditor & Peer Reviewer  

---

## 1. Executive Summary & Final Verdict

An exhaustive, read-only audit of the Phase 4 corrections was conducted across the ThreatWeave research repository. Every correction was independently validated against the physical filesystem, Python Abstract Syntax Trees (ASTs), raw Git diffs, and backend application source code.

```
+-------------------------------------------------------------------------+
|                  INDEPENDENT AUDIT VERIFICATION VERDICT                 |
|                                                                         |
|                           >>> VERIFIED <<<                              |
|                                                                         |
|  All seven Phase 4 corrections are confirmed to be strictly implemented  |
|  and mathematically consistent. Zero obsolete strings, zero citation    |
|  mapping corruptions, and zero application source code alterations were  |
|  detected. The manuscript meets IEEE academic integrity standards.      |
+-------------------------------------------------------------------------+
```

---

## 2. Seven Correction Verdicts

### Correction 1: RAG Threshold Terminology — VERIFIED
- **Audited Standard:** Cosine similarity threshold $\tau_{\text{sim}} = 0.40$, equivalent to maximum cosine distance $d \le 0.60$.
- **Evidence in Codebase:**
  - `apps/api/app/rag/chroma_client.py` (L152): `metadata={"hnsw:space": "cosine"}`.
  - `apps/api/app/rag/retriever.py` (L100–103): `similarity = round(max(0.0, min(1.0, 1.0 - float(dist))), 4)`, filtering via `if similarity >= effective_threshold:` (`RAG_SIMILARITY_THRESHOLD = 0.40`).
- **Evidence in Manuscripts:**
  - `docs/ThreatWeave_Research_Paper.md` (Lines 35, 55, 87, 232, 337, 493): All specify $\tau_{\text{sim}} = 0.40$ ($d \le 0.60$).
  - `docs/ThreatWeave_Research_Paper.tex` (Lines 52, 72, 87, 161, 219, 399): All specify $\tau_{\text{sim}} = 0.40$ ($d \le 0.60$).
  - `docs/research-figures/figure-captions.md` (Lines 18, 70): Fully synchronized.
- **Verdict:** **VERIFIED** (0 inverted occurrences remaining).

### Correction 2: Figure 4 Risk Engine Caption & Severity Bands — VERIFIED
- **Audited Standard:** Additive/subtractive deterministic formula and 5 discrete operational severity bands matching `apps/api/app/agents/risk_engine.py`.
- **Evidence in Codebase:**
  - `apps/api/app/agents/risk_engine.py` (L26–49, L79–140):
    $$\text{final\_risk} = \text{clamp}(\text{base\_score} + \Delta_{\text{corrob}} + \Delta_{\text{intel}} - \Delta_{\text{contra}}, \, 0.0, \, 1.0)$$
    Bands: `info` $[0.00, 0.20)$, `low` $[0.20, 0.40)$, `medium` $[0.40, 0.60)$, `high` $[0.60, 0.80)$, `critical` $[0.80, 1.00]$.
- **Evidence in Artifacts:**
  - `docs/research-figures/figure-captions.md` (Lines 70–90): Fully purged of speculative $M_{urgency} / M_{coercive}$ multipliers; exact formulas and 5 discrete bands documented.
  - `docs/ThreatWeave_Research_Paper.md` (Line 321, ASCII Fig. 4): Corrected to `Info [0.00, 0.19] | Low [0.20, 0.39] | Medium [0.40, 0.59] | High [0.60, 0.79] | Critical [0.80, 1.00]`.
  - `docs/research-figures/figure4-risk-engine.dot` (L25–29): Re-inspected; confirms the figure artwork was already 100% correct.
- **Verdict:** **VERIFIED**.

### Correction 3: Primary LLM Model Identifier — VERIFIED
- **Audited Standard:** Explicitly designate `openai/gpt-oss-120b` as the default configured model on Groq Cloud, noting architectural flexibility for open-weight models like `llama-3.3-70b-versatile`.
- **Evidence in Codebase:**
  - `apps/api/app/core/config.py` (L83): `TEXT_AGENT_MODEL: str = Field("openai/gpt-oss-120b")`.
  - `.env` (L18): `TEXT_AGENT_MODEL=openai/gpt-oss-120b`.
- **Evidence in Manuscripts:**
  - `docs/ThreatWeave_Research_Paper.md` (Lines 35, 54, 140, 232): Accurately identifies `openai/gpt-oss-120b` while noting modular support for `llama-3.3-70b-versatile`.
  - `docs/ThreatWeave_Research_Paper.tex` (Lines 52, 71, 161): Identical framing.
  - `docs/research-figures/figure-captions.md` (Line 18): Identical framing.
- **Verdict:** **VERIFIED**.

### Correction 4: Ingestion Payload Limits — VERIFIED
- **Audited Standard:** 10 MB images, 15 MB audio, and 20,000 raw text characters.
- **Evidence in Codebase:**
  - `apps/api/app/core/config.py` (L75–77): `MAX_IMAGE_SIZE_MB = 10`, `MAX_AUDIO_SIZE_MB = 15`, `MAX_TEXT_CHARS = 20000`.
  - `apps/api/app/core/file_validation.py` (L16, L53): Enforces size ceilings directly against `settings`.
- **Evidence in Manuscripts:**
  - `docs/ThreatWeave_Research_Paper.md` (Lines 160, 447): Updated to 10 MB image, 15 MB audio, 20,000 chars text.
  - `docs/ThreatWeave_Research_Paper.tex` (Lines 123, 356): Updated to 10 MB image, 15 MB audio, 20,000 chars text.
  - `docs/research-figures/figure-captions.md` (Line 18): Updated to 10 MB image, 15 MB audio, 20,000 chars text.
- **Verdict:** **VERIFIED** (0 occurrences of obsolete 25 MB or 10,000 text limits).

### Correction 5: Bibliography & BibTeX Key Synchronization — VERIFIED
- **Audited Standard:** All 30 references resolve to canonical keys matching `references.bib` with zero key discrepancies.
- **Verification Evidence:**
  - Independent AST script verified that all 8 divergent keys (`kim2021koreanvoice`, `tounsi2018cti`, `wang2024agentsurvey`, `nist2012risk`, `wooldridge2009mas`, `munir2024multimodalrag`, `rbi2021digitalpayment`, `wilson1927probable`) were replaced by canonical keys (`kim2021vishing`, `tounsi2018threatintel`, `wang2024surveyagents`, `nist80030r1`, `wooldridge2009multiagent`, `munir2024transitrag`, `rbi2021security`, `wilson1927score`).
  - Key count in `references.bib`: **30**
  - Bibitem count in `ThreatWeave_Research_Paper.tex`: **30**
  - Match rate: **100.0%** (30/30 identical keys in identical order).
- **Verdict:** **VERIFIED**.

### Correction 6: IEEE First-Appearance Citation Ordering — VERIFIED
- **Audited Standard:** Strictly sequential first-appearance numbering `[1]` through `[30]` across all in-text citations, tables, and the bibliography.
- **Verification Evidence:**
  - Regex AST scan of the entire Markdown body (`ThreatWeave_Research_Paper.md`) revealed:
    $$\text{First Appearance Order: } [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]$$
  - LaTeX `\bibitem` ordering in `\begin{thebibliography}` matches this exact sequence 1..30.
  - Mapping integrity checked: 0 publications scrambled, 0 references removed.
- **Verdict:** **VERIFIED**.

### Correction 7: QR Baseline & Post-Remediation Disclosure — VERIFIED
- **Audited Standard:** Transparent disclosure distinguishing the uncalibrated defensive baseline (57.1% accuracy) from the post-remediation benchmark (78.6% accuracy).
- **Verification Evidence:**
  - `docs/ThreatWeave_Research_Paper.md` (Sec. VII-D, Lines 423–427): Fully documents the earlier uncalibrated baseline ($TP=8, FP=6, TN=0, FN=0$, Accuracy = 57.1%, $F_1 = 0.727$) and attributes the improvement to the headless UPI payee disambiguation logic ($TP=6, FP=2, TN=5, FN=1$, Accuracy = 78.6%, $F_1 = 0.800$).
  - `docs/ThreatWeave_Research_Paper.tex` (Sec. VII-D, Lines 288–290): Identical academic framing integrated.
  - Confirmed: The ₹2,000 threshold is honestly scoped as an empirical micro-merchant parameter, not a universal guarantee.
- **Verdict:** **VERIFIED**.

---

## 3. Comprehensive Reference Traceability Matrix (Post-Renumbering)

Every citation was verified against its original publication identity:

| New ID `[n]` | Canonical BibTeX Key | First Author & Title | Publication Venue | Year | Verification Status |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **[1]** | `xiang2011cantina` | G. Xiang et al., *CANTINA+* | ACM TISSEC | 2011 | ✅ Verified |
| **[2]** | `sonowal2020smishing` | G. Sonowal, *Detecting Phishing SMS* | SN Computer Science | 2020 | ✅ Verified |
| **[3]** | `certin2024annual` | CERT-In, *Annual Cyber Security Report* | MeitY, India | 2024 | ✅ Verified |
| **[4]** | `marchal2014phishstorm` | S. Marchal et al., *PhishStorm* | IEEE TNSM | 2014 | ✅ Verified |
| **[5]** | `vidas2013qrishing` | T. Vidas et al., *QRishing* | Springer FC | 2013 | ✅ Verified |
| **[6]** | `rafsanjani2023qsecr` | A. S. Rafsanjani et al., *QsecR* | IEEE Access | 2023 | ✅ Verified |
| **[7]** | `lin2021phishpedia` | Y. Lin et al., *Phishpedia* | USENIX Security | 2021 | ✅ Verified |
| **[8]** | `abdelnabi2020visualphishnet` | S. Abdelnabi et al., *VisualPhishNet* | ACM CCS | 2020 | ✅ Verified |
| **[9]** | `kim2021vishing` | D.-H. Kim et al., *Korean Voice Phishing* | J. Ambient Intell. | 2021 | ✅ Verified |
| **[10]** | `capuano2022xai` | N. Capuano et al., *Explainable AI in CyberSecurity*| IEEE Access | 2022 | ✅ Verified |
| **[11]** | `tounsi2018threatintel` | W. Tounsi & H. M. Rais, *Technical CTI Survey* | Computers & Security | 2018 | ✅ Verified |
| **[12]** | `wang2024surveyagents` | L. Wang et al., *Survey on LLM Autonomous Agents* | Front. Comput. Sci. | 2024 | ✅ Verified |
| **[13]** | `gao2023ragsurvey` | Y. Gao et al., *RAG for LLMs: A Survey* | arXiv / Survey | 2023 | ✅ Verified |
| **[14]** | `nist80030r1` | NIST, *Guide for Conducting Risk Assessments* | NIST SP 800-30 Rev 1 | 2012 | ✅ Verified |
| **[15]** | `hong2024metagpt` | S. Hong et al., *MetaGPT* | ICLR (Oral) | 2024 | ✅ Verified |
| **[16]** | `wu2023autogen` | Q. Wu et al., *AutoGen* | arXiv / MSFT | 2023 | ✅ Verified |
| **[17]** | `boukari2021smishing` | B. E. Boukari et al., *ML for SMiShing Frauds* | IEEE CCNC | 2021 | ✅ Verified |
| **[18]** | `wooldridge2009multiagent` | M. Wooldridge, *An Introduction to MultiAgent Systems*| John Wiley & Sons | 2009 | ✅ Verified |
| **[19]** | `qian2024chatdev` | C. Qian et al., *ChatDev* | ACL 2024 | 2024 | ✅ Verified |
| **[20]** | `lewis2020rag` | P. Lewis et al., *Retrieval-Augmented Generation* | NeurIPS | 2020 | ✅ Verified |
| **[21]** | `reimers2019sbert` | N. Reimers & I. Gurevych, *Sentence-BERT* | EMNLP-IJCNLP | 2019 | ✅ Verified |
| **[22]** | `malkov2020hnsw` | Y. A. Malkov & D. A. Yashunin, *HNSW Graph Search* | IEEE TPAMI | 2020 | ✅ Verified |
| **[23]** | `munir2024transitrag` | M. B. Munir et al., *Multimodal RAG for Cyber Attacks*| IEEE TPS-ISA | 2024 | ✅ Verified |
| **[24]** | `gao2023threatkg` | P. Gao et al., *ThreatKG* | ACM LEAM | 2023 | ✅ Verified |
| **[25]** | `rbi2021security` | Reserve Bank of India, *Digital Payment Security* | RBI Notification | 2021 | ✅ Verified |
| **[26]** | `radford2023whisper` | A. Radford et al., *Robust Speech Recognition (Whisper)*| ICML (PMLR) | 2023 | ✅ Verified |
| **[27]** | `baek2019craft` | Y. Baek et al., *CRAFT Text Detection* | IEEE CVPR | 2019 | ✅ Verified |
| **[28]** | `shi2017crnn` | B. Shi et al., *CRNN Sequence Recognition* | IEEE TPAMI | 2017 | ✅ Verified |
| **[29]** | `jung2022aasist` | J. Jung et al., *AASIST Audio Anti-Spoofing* | IEEE ICASSP | 2022 | ✅ Verified |
| **[30]** | `wilson1927score` | E. B. Wilson, *Wilson Score Interval* | J. Am. Stat. Assoc. | 1927 | ✅ Verified |

---

## 4. Markdown vs. LaTeX Technical Consistency

Cross-document parsing confirmed 100% concordance between `ThreatWeave_Research_Paper.md` and `ThreatWeave_Research_Paper.tex`:
1. **Title & Authorship:** Identical (Dharma Teja, Hemanth, Prabash; Guide: Mr. Mohammad Amanullah; GIET Autonomous).
2. **Abstract & Empirical Scores:** Identical metrics (95.8% Text, 90.0% Image, 79.2% URL, 78.6% QR, 66.7% Voice, 227 tests).
3. **Mathematical Risk Formula:** Identical clamped formulation with bitwise invariance ($|\text{residual}| \le 1.0 \times 10^{-4}$).
4. **Band Thresholds:** Identical 5 tiers (Info, Low, Medium, High, Critical in 0.20 intervals).
5. **Ingestion Limits:** Identical ceilings (10 MB image, 15 MB audio, 20,000 characters text, 1024px downscaling).
6. **QR Baseline Disclosure:** Identical dual-mode explanation in Section VII-D.

---

## 5. Actual Git State Audit

```bash
$ git branch --show-current
main

$ git rev-parse HEAD
27fb19e098a54fbc0a85d667b29798c1bedbdefc

$ git status --short
?? docs/ThreatWeave_Research_Paper.md
?? docs/ThreatWeave_Research_Paper.tex
?? docs/research-figures/figure-captions.md
?? docs/research-audit/references.bib
?? docs/research-audit/reference-verification-matrix.md
?? docs/research-audit/phase-4-correction-completion-report.md
... (other untracked evaluation and research artifacts)
```

- **Tracked Modified Files:** **0** (`git diff --stat` is completely empty).
- **Tracked Staged Files:** **0** (`git diff --cached` is completely empty).
- **Git Commits Created in Phase 4 / 4.1:** **0** (HEAD remains `27fb19e`).
- **Remote Branch Alignment:** `origin/main` is up to date.
- **Untracked Documentation Files:** Modified and created documentation files reside cleanly in the working tree as untracked files pending formal commit approval.
- **Application Source Files:** Unaltered. Zero lines modified in `apps/api/app/`, `apps/api/tests/`, `apps/api/alembic/`, `apps/api/eval/`, or `apps/web/`.
- **Figure Artwork Files:** Unaltered. All 16 `.dot`, `.svg`, `.pdf`, `.png` files retain their original Phase 2 timestamps.

---

## 6. Unresolved Discrepancies
**None.** No mathematical, factual, terminological, or structural discrepancies remain.

---

## 7. Final Verification Verdict

$$\mathbf{FINAL \; AUDIT \; VERDICT: \; VERIFIED}$$

The ThreatWeave research paper is completely verified, mathematically rigorous, citation-consistent, and fully aligned with verified codebase reality.

> **STOP:** Independent Phase 4.1 verification is complete. Awaiting user review and authorization.
