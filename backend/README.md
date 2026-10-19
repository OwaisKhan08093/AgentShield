# AgentShield Backend API Service

FastAPI-powered security evaluation engine and persistence layer for **AgentShield**.

---

## 1. Architecture Overview

The backend is built around a clean, deterministic architecture designed for reproducible security auditing without external LLM API costs or token variability:

```
backend/
├── app/
│   ├── main.py                  # FastAPI application entrypoint & middleware
│   ├── agent/                   # BaseAgent interface and deterministic ReferenceAgent
│   ├── api/                     # REST API routers, schemas, dependencies & error handlers
│   ├── evaluator/               # Security assertions engine, rule checks & metrics calculators
│   ├── models/                  # Pydantic v2 domain schemas (Event, Finding, Scenario)
│   ├── scenarios/               # Canonical 16-scenario catalog, runner & registry
│   ├── security/                # ToolAuthorizationGuard with RBAC and boundary enforcement
│   ├── storage/                 # Atomic SQLite persistence layer (Repository pattern)
│   └── tools/                   # Mock customer support tools (lookup_order, refund policy, approval)
└── tests/                       # Comprehensive pytest suite (245 unit & integration tests)
```

---

## 2. Prerequisites

- **Python**: Version `3.11.0` or higher
- **Virtual Environment**: Standard Python `venv`

---

## 3. Local Setup & Startup

### Setup Virtual Environment

From the repository root:

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install --upgrade pip
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### Run the FastAPI Service

From the repository root:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

Or run the helper script:

```powershell
.\scripts\start_backend.ps1
```

Interactive documentation will be available immediately at:
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`
- **Health Check**: `http://127.0.0.1:8000/health`

---

## 4. REST API Endpoint Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status check. |
| `GET` | `/` | Service identity and version metadata. |
| `GET` | `/api/v1/scenarios` | List registered canonical security scenarios (supports `category` and `tag` filters). |
| `GET` | `/api/v1/scenarios/{scenario_id}` | Retrieve full scenario specification and expected security behavior. |
| `POST` | `/api/v1/runs` | Execute an evaluation run across all or selected scenarios. |
| `GET` | `/api/v1/runs` | Paginated list of completed evaluation run records (`limit`, `offset`). |
| `GET` | `/api/v1/runs/{run_id}` | Aggregate summary metrics and outcome tally for a specific run. |
| `GET` | `/api/v1/runs/{run_id}/results` | Per-scenario evaluation results, findings, and explanations. |
| `GET` | `/api/v1/runs/{run_id}/trace` | Chronological audit trace events with authorization decisions (`scenario_id` filter). |
| `GET` | `/api/v1/runs/{run_id}/report.json` | Download structured machine-readable evaluation report JSON. |

---

## 5. Running Tests

Run the full pytest suite (245 tests):

```powershell
.\backend\.venv\Scripts\python.exe -m pytest -q
```

Or run specific test modules:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/test_authorization.py -q
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/test_evaluator.py -q
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/test_api_runs.py -q
```

---

## 6. Database Storage & Persistence

- **Engine**: SQLite with foreign keys and WAL mode enabled.
- **Location**: Default path `agentshield.db` in repository root (or configured via `AGENTSHIELD_DB_PATH`).
- **Initialization**: Automatically creates tables on startup if not present (`CREATE TABLE IF NOT EXISTS`).
- **Cleanup**: To start with a fresh database, stop the server and delete `agentshield.db`.
