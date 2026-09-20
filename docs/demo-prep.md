# Demo Preparation & Queue Seeding Runbook

This guide documents the procedures for safely preparing, seeding, and resetting the ThreatWeave database before live demonstration sessions, examiner vivas, and staging deployments.

---

## 1. Overview & Safety Architecture

ThreatWeave includes an automated, deterministic seeding and reset utility located at [`apps/api/scripts/seed_demo_queue.py`](file:///d:/ThreatWeave%20—%20Agentic%20Multimodal/threatweave/apps/api/scripts/seed_demo_queue.py).

### Safety Rails
1. **Archive First (Non-Negotiable)**:
   Before any database row is modified or removed, all existing investigations and cascading child rows (`evidence_inputs`, `agent_runs`, `agent_findings`, `rag_citations`, `risk_breakdown`, `conflict_logs`) are serialized and exported to a timestamped JSON backup file under `storage/archives/investigations_archive_{timestamp}.json`.
   If the archive file write fails or contains 0 rows, the script **aborts immediately** before executing any deletion.
2. **Safe By Default (`--confirm` Required)**:
   Running the script without `--confirm` defaults to a safe read-only plan. No database rows are modified without explicit `--confirm`.
3. **Dry-Run Inspection (`--dry-run`)**:
   Provides an explicit report of what *would* be archived, deleted, and seeded without executing write operations.
4. **Deterministic & Idempotent**:
   Running the script multiple times with `--confirm` will never generate duplicate records. Existing seeded items are identified by unique curated markers, ensuring stable demo states.
5. **Thematically Grounded**:
   The seeded queue includes 8 realistic Indian financial cyber fraud incidents (UPI phishing, digital arrest impersonation, KYC APK malware, electricity bill extortion, etc.) spanning all severity tiers (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`, `CLEAN BASELINE`).

---

## 2. Step-by-Step Execution

All commands should be executed from the `apps/api` directory using the virtual environment:

### Step 2.1: Dry-Run Inspection (Non-Destructive)
Verify what the utility will perform without touching the database:

```bash
cd apps/api
venv\Scripts\python scripts/seed_demo_queue.py --dry-run
```

**Expected Output**:
- Displays the current investigation count in the database.
- Displays the proposed archive target path.
- Lists the 8 curated demo incidents that will be seeded.
- Emits a safety reminder that no changes were made because `--confirm` was not passed.

---

### Step 2.2: Execute Reset & Seed with Archive Safety (`--confirm`)
Run the verified migration:

> [!WARNING]
> **Operational Note:** Running `--confirm` wipes any live investigations created since the last seed, including ones created during a demo/testing session — run this only right before presenting, not mid-session.

```bash
cd apps/api
venv\Scripts\python scripts/seed_demo_queue.py --confirm
```

**Execution Stages**:
1. **Archive Export**: Queries all existing records and writes `storage/archives/investigations_archive_{YYYYMMDD_HHMMSS}.json`.
2. **Pre-Delete Verification**: Asserts that the archive file exists on disk and its size is > 0 bytes.
3. **ORM Cascade Delete**: Removes scratch investigations using SQLAlchemy ORM relationships.
4. **Curated Seeding**: Inserts the 8 calibrated investigations with complete agent runs, findings, indicators, RAG citations, and risk breakdowns.
5. **Post-Seed Verification**: Confirms exactly 8 investigations exist and prints their summary table.

---

### Step 2.3: Idempotency Check
To verify that re-running the script does not pollute the queue with duplicates:

```bash
cd apps/api
venv\Scripts\python scripts/seed_demo_queue.py --confirm
```

The script will detect existing seeded records, cleanly refresh the state, and verify the count remains at 8.

---

## 3. Curated Incidents in Seeded Queue

| # | Investigation Title | Severity | Modalities Involved | Fraud Pattern |
|---|---------------------|----------|---------------------|---------------|
| 1 | `[INC-8092] Urgent SBI YONO Account Suspension Phishing via APK & SMS` | **CRITICAL** (0.92) | SMS, URL, APK Screenshot | Fake SBI YONO KYC expiry with malicious `.apk` download |
| 2 | `[INC-7741] Fake CBI Digital Arrest Video Call & Extortion Demand` | **CRITICAL** (0.88) | Voice, Audio, Image | Digital arrest impersonating CBI officer demanding RTGS bail |
| 3 | `[INC-6520] QR Code Reverse-Charge Scam on OLX Marketplace` | **HIGH** (0.76) | QR Code, Chat Transcript | Reverse-charge UPI QR code claiming to deposit money |
| 4 | `[INC-5198] Mahavitran Electricity Disconnection Phishing SMS` | **HIGH** (0.71) | SMS, Phishing URL | Urgent power disconnection notice with rogue bill-pay URL |
| 5 | `[INC-4312] Typosquatted HDFC NetBanking Domain Registration` | **MEDIUM** (0.58) | Domain, DNS, SSL | Homoglyph typosquatted domain (`hdfc-netbank-kyc.top`) |
| 6 | `[INC-3084] Tampered Razorpay Payment Confirmation Screenshot` | **MEDIUM** (0.46) | Image, OCR, Metadata | Font mismatch and altered UTR on fake Razorpay receipt |
| 7 | `[INC-2041] Unsolicited Lottery Prize SMS without Credentials Request` | **LOW** (0.24) | SMS Text | Generic KBC prize lure with unverified WhatsApp contact |
| 8 | `[INC-1002] Verified Corporate Password Expiry Notification (Benign)` | **CLEAN** (0.04) | Email, DKIM, URL | Legitimate internal IT security bulletin with valid SSO link |

---

## 4. Archive Rollback Procedure

If historical test investigations need to be inspected or restored:
1. Archives are located in:
   ```
   apps/api/storage/archives/investigations_archive_{timestamp}.json
   ```
2. Each archive JSON contains the full nested hierarchy:
   - Investigation metadata (UUID, status, risk score, severity, timestamps)
   - Evidence inputs
   - Agent execution runs, latencies, and statuses
   - Findings with indicators and reasoning
   - RAG source citations with similarity scores
   - Mathematical risk breakdowns
   - Consensus conflict resolution logs
