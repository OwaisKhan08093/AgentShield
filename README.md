# AgentShield — AI Agent Security Evaluation Platform

**AgentShield** is an automated security evaluation platform designed to systematically probe, analyze, benchmark, and audit autonomous AI customer-support agents against OWASP LLM security risks, unauthorized data access, privilege escalation, and adversarial prompt injections.

---

## Key Features

- **Deterministic Reference Agent**: A reproducible, rule-based reference customer-support agent with realistic synthetic test data (customers, orders, refund requests) for predictable benchmark evaluations without external LLM API costs or token variance.
- **Tool Authorization Guard**: Defense-in-depth policy enforcement engine validating caller identities, resource ownership, parameter ranges, and action permissions with structured denial logging.
- **Canonical Security Scenario Suite (16 Scenarios)**: High-fidelity test cases covering:
  - *Positive Controls & Benign Tasks*: Authorized order lookups, policy inquiries, valid refund requests.
  - *Unauthorized Access & IDOR*: Cross-customer order queries, horizontal resource access attempts.
  - *Approval Boundaries*: Exceeding refund thresholds, negative-amount exploits, malformed payloads.
  - *Prompt Injections (Direct & Indirect)*: Adversarial system prompt overrides, action hijacking, and poisoned database/order note injections.
- **Trace Capture & Sanitization**: Chronological audit recording of every prompt, tool call, authorization verdict, and response, with automatic regex scrubbing of sensitive credentials and PII.
- **Discrete Assertion & Scoring Engine**: Strict distinction between `PASS`, `FAIL`, `ERROR`, and `NOT_RUN`. Mathematical calculation of Attack Success Rate (ASR), Protection Success Rate (PSR), Sensitive Data Exposure Rate, and composite Security Scores.
- **Atomic SQLite Persistence**: ACID-compliant relational storage storing runs, scenario evaluations, findings, metric snapshots, and traces with automatic rollback on persistence failure.
- **RESTful Inspection & Export API**: Endpoints to trigger evaluation runs, query paginated histories, inspect per-scenario findings, inspect chronological traces, and export machine-readable JSON reports.
- **Web Evaluation Console (React + TypeScript + Vite)**: Interactive Scenario Explorer (`/scenarios`), Run Execution Controls (`POST /api/v1/runs`), Evaluation Run Dashboard (`/runs`), Scenario Result Drilldown (`/runs/:id`), Chronological Trace Inspector, Security Findings Drawer, Collapsible JSON Report Visualizer, Summary Metrics Breakdowns, and Formula-Safe CSV Exports (Scenarios, Findings, Metrics).

---

## Architecture & Evaluation Workflow

```
                                  +------------------------------------+
                                  |       REST API Client / CI         |
                                  +------------------------------------+
                                                    |
                                      POST /api/v1/runs (HTTP)
                                                    v
                                  +------------------------------------+
                                  |    FastAPI Application Router      |
                                  |      (backend/app/main.py)         |
                                  +------------------------------------+
                                                    |
                                                    v
                                  +------------------------------------+
                                  |      Scenario Execution Runner     |
                                  |   (backend/app/scenarios/runner)   |
                                  +------------------------------------+
                                        |                        |
                   Executes Scenario    |                        | Enforces Timeout &
                   through Agent        v                        v Traps Crashes
                         +-----------------------+      +-----------------------+
                         | ReferenceAgent        |      | ToolAuthorizationGuard|
                         | (Synthetic Fixtures)  |----->| (RBAC & Boundary)     |
                         +-----------------------+      +-----------------------+
                                        |                        |
                                        +------------+-----------+
                                                     |
                                                     v Produces Execution Trace
                                  +------------------------------------+
                                  |      Security Assertion Engine     |
                                  |     (backend/app/evaluator/)       |
                                  +------------------------------------+
                                                     |
                                                     v Computes Metrics (ASR, PSR)
                                  +------------------------------------+
                                  |     SQLite Persistence Layer       |
                                  |  (Atomic Transaction / Repository) |
                                  +------------------------------------+
                                                     |
                                                     v
                                  +------------------------------------+
                                  |   JSON Report & Trace Endpoints    |
                                  |    GET /api/v1/runs/{id}/report    |
                                  +------------------------------------+
```

---

## Deterministic Reference Agent vs. Real-LLM Testing

- **Deterministic Reference Agent (Current MVP Baseline)**:
  AgentShield currently evaluates agents using a deterministic, rule-based reference agent. This design ensures that security assertions, authorization boundaries, and trace recorders can be evaluated with 100% reproducibility, zero network latency, and zero LLM API costs.
- **External Real-LLM Adapters (Post-MVP)**:
  The evaluation architecture is designed around abstract interfaces (`BaseAgent`, `SupportTools`, `ExecutionTrace`). Integrating external LLM providers (e.g., OpenAI, Anthropic, Gemini) involves providing an adapter implementing `BaseAgent.execute(request)` without altering scenarios, assertion rules, storage schemas, or API contracts.

---

## Prerequisites

- **Python**: Version 3.11+ (Python 3.11.0 recommended)
- **PowerShell** or **Command Prompt** (Windows), or **Bash** (macOS/Linux)
- **Git**

---

## Local Setup & Quickstart

### 1. Clone & Navigate to Project

```powershell
git clone https://github.com/OwaisKhan08093/AgentShield.git
cd AgentShield
```

### 2. Set Up Virtual Environment

On Windows (PowerShell):
```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

On Linux / macOS:
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example environment template:
```powershell
Copy-Item .env.example .env
```

To configure a custom SQLite database file location, set the `DATABASE_URL` or `AGENTSHIELD_DB_PATH` in `.env`:
```ini
AGENTSHIELD_DB_PATH="agentshield.db"
```

---

## Running the Automated Test Suite

AgentShield maintains a strict 100% passing test baseline with zero deprecation warnings:

From the repository root:
```powershell
backend\.venv\Scripts\python.exe -m pytest
```

Or from within the `backend/` directory:
```powershell
pytest
```

To run tests with full verbose output:
```powershell
pytest -v
```

---

## Starting the API Server

From the `backend/` directory with virtualenv active:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The service will start at:
- **Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger OpenAPI Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Interactive Documentation**: `http://127.0.0.1:8000/redoc`

---

## API Reference & Usage Guide

### 1. Health & Status Endpoints

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `GET` | `/` | Service identity and status metadata | `200` |
| `GET` | `/health` | Liveness health check | `200` |

### 2. Scenario Catalog

| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `GET` | `/api/v1/scenarios` | `category` (optional), `tag` (optional) | List safe summaries of all registered evaluation scenarios. |
| `GET` | `/api/v1/scenarios/{scenario_id}` | None | Retrieve full scenario definition and security objective. |

**Example**: Filter scenarios by category:
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/scenarios?category=unauthorized_access"
```

### 3. Triggering an Evaluation Run

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/runs` | Execute a security evaluation suite against the reference agent, evaluate security rules, and persist findings. |

**Request Payload (`CreateRunRequest`)**:
```json
{
  "suite_id": "support-agent-security-v1",
  "agent_id": "reference-agent",
  "scenario_ids": [
    "BENIGN-ORDER-LOOKUP-001",
    "AUTHZ-CROSS-ORDER-001",
    "INJECT-DIRECT-OVERRIDE-REASON-001"
  ],
  "options": {
    "continue_on_error": true,
    "record_trace": true,
    "timeout_seconds": 5.0
  }
}
```

*Note*: If `scenario_ids` is omitted or `null`, all 16 canonical benchmark scenarios are evaluated.

**Example `curl`**:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/runs" \
     -H "Content-Type: application/json" \
     -d "{\"suite_id\": \"support-agent-security-v1\", \"agent_id\": \"reference-agent\"}"
```

**Response (`201 Created`)**:
```json
{
  "run_id": "run_a1b2c3d4e5f6",
  "report_id": "rpt_9876543210ab",
  "suite_id": "support-agent-security-v1",
  "status": "completed",
  "overall_outcome": "pass",
  "started_at": "2026-10-19T18:00:00.000000+00:00",
  "completed_at": "2026-10-19T18:00:00.150000+00:00",
  "total_scenarios": 16,
  "passed_count": 16,
  "failed_count": 0,
  "error_count": 0,
  "not_run_count": 0,
  "summary_counts": {
    "total_scenarios": 16,
    "passed_count": 16,
    "failed_count": 0,
    "error_count": 0,
    "not_run_count": 0
  },
  "metrics_summary": {
    "overall_pass_rate": {
      "name": "Overall Pass Rate",
      "value": 1.0,
      "display_value": "100.0%"
    },
    "security_score": {
      "name": "Security Score (Composite)",
      "value": 1.0,
      "display_value": "100.0/100"
    },
    "attack_success_rate": {
      "name": "Attack Success Rate (ASR)",
      "value": 0.0,
      "display_value": "0.0%"
    },
    "unauthorized_prevention_rate": {
      "name": "Unauthorized-Access Prevention Rate",
      "value": 1.0,
      "display_value": "100.0%"
    }
  }
}
```

### 4. Inspecting Runs & Detailed Evidence

| Method | Endpoint | Query Parameters | Description |
|---|---|---|---|
| `GET` | `/api/v1/runs` | `limit` (default: 20), `offset` (default: 0) | Paginated list of completed evaluation run summaries. |
| `GET` | `/api/v1/runs/{run_id}` | None | Aggregate summary and metrics for a specific run. |
| `GET` | `/api/v1/runs/{run_id}/results` | None | Per-scenario evaluation results, findings, and explanations. |
| `GET` | `/api/v1/runs/{run_id}/trace` | `scenario_id` (optional) | Ordered, sanitized execution trace events. |
| `GET` | `/api/v1/runs/{run_id}/report.json` | None | Download complete structured evaluation report JSON. |

**Example: Inspect per-scenario findings**:
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/runs/run_a1b2c3d4e5f6/results"
```

**Example: Export report JSON to file**:
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/runs/run_a1b2c3d4e5f6/report.json" -o evaluation_report.json
```

---

## Security Boundaries & Limitations

1. **Synthetic Scope**: Evaluation results apply strictly to the registered synthetic scenarios and reference tool definitions. Passing synthetic benchmarks does not certify an agent as immune to novel or zero-day adversarial attacks.
2. **Transparent Uncertainty**: The engine maintains a strict separation between `PASS`, `FAIL`, `ERROR`, and `NOT_RUN`. Runner exceptions, execution timeouts, and skipped scenarios are **never** treated as security passes.
3. **Execution Isolation**: In the current synchronous execution model, per-scenario timeouts are enforced using thread pooling. Scenarios that exceed `timeout_seconds` fail closed with `ERROR`.
4. **Data Redaction**: Trace sanitization scrubbers mask credentials, passwords, and payment information before saving to SQLite or returning via REST APIs.

---

## Frontend Web Console Quickstart

The AgentShield Web Console is located in `frontend/`:

```bash
cd frontend
npm install
npm run dev
```

See [frontend/README.md](frontend/README.md) for comprehensive instructions on environment configuration (`VITE_API_BASE_URL`), build commands, and design system tokens.

---

## Roadmap & Milestone Progress

- [x] **Day 1**: Project Foundation & FastAPI Scaffold
- [x] **Day 2**: Domain Models, Authorization Guard & Secure Tools
- [x] **Day 3**: Reference Agent, 16 Scenario Library, Runner & Security Evaluator
- [x] **Day 4**: SQLite Persistence Layer, Scenario & Run APIs, Traces & Reports
- [x] **Day 5 (PRD Days 17–18)**: API Integration Testing, Real Timeout Handling, Failure Semantics & Documentation
- [x] **Day 6 (PRD Day 19)**: Frontend Scaffolding, Project Setup & Security Design System (React, Vite, TS, Tailwind, Router, Typed API Client)
- [x] **Day 8 (PRD Days 21–22)**: Evaluation Run Dashboard, Execution Controls & Trace Inspector
- [x] **Day 9 (PRD Day 23)**: Machine-Readable JSON Report Visualizer, Summary Metrics & CSV/JSON Export Views
- [ ] **PRD Day 24**: End-to-end Demo Script, Polish & Final Documentation
