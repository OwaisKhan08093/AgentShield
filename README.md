# AgentShield — AI Agent Security Evaluation Platform

**AgentShield** is an AI agent security evaluation platform designed to systematically probe, analyze, and benchmark the security posture and alignment robustness of autonomous AI agents.

---

## Project Structure

```text
AgentShield/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Application package root
│   │   ├── main.py              # FastAPI application entrypoint
│   │   ├── config.py            # Settings and environment configuration
│   │   ├── models/              # Schemas and domain models
│   │   │   └── __init__.py
│   │   ├── agent/               # AI Agent execution and orchestration
│   │   │   └── __init__.py
│   │   ├── tools/               # Tool sandbox and execution interfaces
│   │   │   └── __init__.py
│   │   ├── security/            # Security probes, attack simulations, red-teaming
│   │   │   └── __init__.py
│   │   └── evaluator/           # Evaluation metrics and scoring engines
│   │       └── __init__.py
│   ├── tests/                   # Backend automated test suite
│   │   ├── __init__.py
│   │   └── test_main.py         # Endpoint sanity tests
│   ├── requirements.txt         # Core backend dependencies
│   └── .env.example             # Template environment variables
├── frontend/                    # Web UI dashboard (planned)
├── docs/                        # Specifications, threat models, and research
├── .gitignore                   # Version control exclusion rules
└── README.md                    # Project documentation
```

---

## Prerequisites

- **Python**: Version 3.11+ (Python 3.11.0 recommended)
- **pip** / **venv**

---

## Getting Started

### 1. Environment Setup

Navigate to the `backend/` directory:

```powershell
cd backend
```

Create a virtual environment:

```powershell
py -3.11 -m venv .venv
```

Activate the virtual environment:

- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

### 2. Install Dependencies

Install the core dependencies:

```powershell
pip install -r requirements.txt
```

### 3. Environment Variables

Create your local `.env` configuration from the template:

```powershell
cp .env.example .env
```

---

## Running the Backend

Start the development server with hot-reload enabled:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server will be reachable at:
- **API Base URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Initial Endpoints

| Method | Endpoint | Description | Sample Response |
|---|---|---|---|
| `GET` | `/` | Service identity and status | `{"name": "AgentShield", "status": "online", "version": "0.1.0"}` |
| `GET` | `/health` | Liveness health check | `{"status": "ok"}` |

---

## Running Tests

Execute the automated test suite with `pytest`:

```powershell
pytest
```

---

## Project Status

- **Phase**: Day 1 — Foundation Setup
- **Status**: Core backend structure, FastAPI skeleton, configuration module, test harness, and dependency baselines established. Feature modules (agent orchestration, tools, security evaluators, and frontend UI) are staged for subsequent phases.
