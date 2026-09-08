# ThreatWeave Phase 16: n8n Workflow Automation Setup Guide

This guide walks through configuring and running the automated incident alert integration between ThreatWeave and n8n.

---

## 1. Overview & Architecture

When ThreatWeave's LangGraph multi-agent swarm completes an investigation and assigns a risk assessment meeting or exceeding `N8N_ALERT_SEVERITY_THRESHOLD` (`high` or `critical`), `app.services.webhook_service` dispatches an asynchronous HTTP POST notification to an n8n webhook endpoint.

### Reliability & Fault-Tolerance Principles
- **Non-blocking Side-Effect**: The webhook is dispatched **after** investigation persistence and state transitions are committed.
- **Zero Degradation on Failure**: If the n8n container is stopped, unreachable, or times out, ThreatWeave catches the exception, logs a warning, and completes the investigation with full integrity (`status="completed"`).
- **Zero Overhead when Unconfigured**: If `N8N_WEBHOOK_URL` is empty, zero network calls or socket connections are attempted.

---

## 2. Quickstart: Launching n8n

The n8n container service is defined in `docker-compose.yml`:

```bash
# Start the n8n service in the background
docker compose up -d n8n
```

Verify the container is running:
```bash
docker ps --filter "name=threatweave-n8n"
```
The n8n web dashboard will be available at: **[http://localhost:5678](http://localhost:5678)**

---

## 3. Importing the Alert Workflow

1. Open your browser and navigate to **`http://localhost:5678`**.
2. If this is the first time launching n8n, follow the quick initial prompt to create your local owner account.
3. In the left navigation menu, click **Workflows**.
4. In the top right corner, click the **three dots menu (...)** -> **Import from File**.
5. Select the workflow file located at:
   ```
   n8n/workflows/high_severity_alert.json
   ```
6. The workflow canvas will open displaying three nodes:
   - **ThreatWeave Webhook**: Configured to listen for `POST` requests at `/webhook/threatweave-alert`.
   - **Format Incident Alert**: Formats the incident summary, title, score, severity, and detected indicators into an executive alert payload.
   - **Respond to Webhook**: Returns a `200 OK` JSON response confirming alert receipt.

---

## 4. Activating the Workflow & Retrieving the Webhook URL

1. Double-click the **ThreatWeave Webhook** node.
2. Note the Webhook URLs:
   - **Production URL**: `http://localhost:5678/webhook/threatweave-alert`
   - **Test URL**: `http://localhost:5678/webhook-test/threatweave-alert`
3. In the top-right corner of the workflow editor, toggle the workflow switch to **Active** (turns green).
4. Click **Save** (`Ctrl + S`).

---

## 5. Configuring ThreatWeave to Send Alerts

Add or update the following variables in `apps/api/.env` (and your root `.env`):

```bash
# Set the n8n production webhook URL
N8N_WEBHOOK_URL=http://localhost:5678/webhook/threatweave-alert

# Minimum severity threshold to trigger alerts ("high" or "critical")
N8N_ALERT_SEVERITY_THRESHOLD=high
```

Restart the FastAPI backend server so it picks up the new environment configuration:
```powershell
# From apps/api directory:
.\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000
```

---

## 6. Testing the Integration

### Method A: Using a Curated Demo Scenario
Run any high or critical severity demo scenario from Phase 15:
```bash
curl -X POST http://localhost:8000/api/v1/demo/scenarios/phishing_email/run
```
Or run the multi-modal scenario:
```bash
curl -X POST http://localhost:8000/api/v1/demo/scenarios/cross_modal/run
```

### Method B: Verifying in the n8n UI
1. In the n8n dashboard, open the **Executions** tab in the left sidebar.
2. You will see a successful execution entry marked with a green checkmark.
3. Clicking on the execution displays the exact incoming payload from ThreatWeave:
   - `investigation_id`
   - `title`
   - `final_risk_score`
   - `final_severity`
   - `top_indicators`
   - `received_at`

### Method C: Low Severity Gating
Run an investigation resulting in low severity. Verify that:
- ThreatWeave logs: `severity does not meet threshold, skipping alert webhook`
- n8n Executions log shows **no** new execution, confirming proper threshold filtering.
