# AgentShield Frontend Console

The AgentShield Web Console provides an automated, security-focused user interface for configuring, running, and analyzing security evaluations of tool-using AI customer support agents.

Implemented through **PRD Day 23 (Machine-Readable JSON Report Visualizer, Summary Metrics & CSV/JSON Export Views)**.

---

## 1. Stack & Architecture

- **Framework**: React 18 with Vite bundler
- **Language**: TypeScript (strict mode enabled)
- **Styling**: Tailwind CSS (dark security theme, accessible contrast, reduced-motion support)
- **Routing**: React Router DOM v6
- **Icons**: Lucide React
- **Unit & Integration Testing**: Vitest + React Testing Library + JSDOM (66 passing tests across 6 suites)

---

## 2. Prerequisites

- **Node.js**: `v18.0.0` or higher (verified on Node `v24.15.0`)
- **npm**: `v9.0.0` or higher (verified on npm `11.12.1`)
- **AgentShield Backend**: Running FastAPI service (default: `http://127.0.0.1:8000`)

---

## 3. Getting Started

### Installation

```bash
cd frontend
npm install
```

### Environment Configuration

The frontend connects to the FastAPI backend using the `VITE_API_BASE_URL` variable.

Copy the provided `.env.example` template:

```bash
cp .env.example .env
```

Default configuration in `.env.example`:

```env
# AgentShield Backend API Base URL
VITE_API_BASE_URL=http://127.0.0.1:8000
```

> **Security Note**: Never commit `.env` or production credentials to source control. `.env` is ignored by Git.

### Development Server

Start the local Vite dev server with Hot Module Replacement (HMR):

```bash
npm run dev
```

By default, the development server runs at `http://localhost:5173`. Requests to `/api` and `/health` are proxied to `http://127.0.0.1:8000` via `vite.config.ts`.

### Running Tests

Execute the unit and component test suite:

```bash
npm test
```

### Production Build

Typecheck and generate optimized static assets in `dist/`:

```bash
npm run build
```

Preview the production build locally:

```bash
npm run preview
```

---

## 4. Frontend Directory Structure

```
frontend/
├── .env.example            # Environment template for local API URL
├── index.html              # HTML entrypoint with viewport, dark mode, and title
├── package.json            # Scripts, dependencies, and project metadata
├── postcss.config.js       # PostCSS plugins (Tailwind, Autoprefixer)
├── tailwind.config.js      # Security design system color tokens and typography
├── tsconfig.json           # Strict TypeScript configuration
├── tsconfig.node.json      # Node TypeScript configuration for Vite
├── vite.config.ts          # Vite build configuration, aliases, dev proxy, and test runner
├── public/
│   └── shield.svg          # AgentShield brand vector icon
└── src/
    ├── main.tsx            # React DOM root entrypoint with BrowserRouter
    ├── App.tsx             # Application route table and shell integration
    ├── index.css           # Global stylesheet with Tailwind directives and dark theme
    ├── vite-env.d.ts       # Vite client environment type declarations
    ├── api/
    │   ├── client.ts       # Centralized typed HTTP client with timeout & error mapping
    │   ├── config.ts       # Base URL resolution and API route constants
    │   ├── types.ts        # TypeScript schemas mirroring backend Pydantic models
    │   └── index.ts        # Re-export entrypoint for API module
    ├── components/
    │   ├── layout/
    │   │   ├── Header.tsx  # Application header with real-time backend health check
    │   │   ├── Sidebar.tsx # Navigation sidebar with route indicators and badge
    │   │   ├── Layout.tsx  # Responsive layout wrapper with mobile drawer
    │   │   └── index.ts    # Re-export entrypoint for layout components
    │   ├── runs/
    │   │   ├── RunCreateModal.tsx        # Evaluation launch dialog (suite/agent/scenario selectors)
    │   │   ├── RunHistoryTable.tsx       # Paginated run history table with outcomes & metrics
    │   │   ├── RunMetricsOverview.tsx    # Security score, ASR, data exposure, and count cards
    │   │   ├── ScenarioResultsTable.tsx  # Scenario results with actual vs expected status
    │   │   ├── TraceInspector.tsx        # Chronological audit timeline & allow/deny badges
    │   │   ├── FindingsList.tsx          # Grouped security findings by rule and severity
    │   │   └── index.ts                  # Re-export entrypoint for runs components
    │   ├── scenarios/
    │   │   ├── ScenarioCard.tsx          # Card displaying scenario metadata, objective, and link
    │   │   ├── ScenarioFilters.tsx       # Text search, category/risk selects, and clear filters
    │   │   └── ExpectedBehaviorPanel.tsx # Assertions, status badge, PASS/FAIL criteria panel
    │   └── ui/
    │       ├── Badge.tsx         # Semantic status and severity pill badges
    │       ├── Button.tsx        # Accessible interactive button with variants & loading state
    │       ├── Card.tsx          # Layered surface container with header, description & content
    │       ├── EmptyState.tsx    # Accessible empty state card with icon and call-to-action
    │       ├── ErrorAlert.tsx    # Accessible error callout with retry action
    │       ├── Input.tsx         # Accessible text and search input field
    │       ├── LoadingSpinner.tsx# Accessible animated spinner
    │       ├── Select.tsx        # Accessible dropdown select input
    │       ├── StatusBadge.tsx   # Security outcome, severity, and category badges
    │       └── index.ts          # Re-export entrypoint for UI design system
    ├── pages/
    │   ├── Overview.tsx          # Platform landing page, pipeline visualizer & health status
    │   ├── Scenarios.tsx         # Interactive Scenario Catalog & Explorer (PRD Day 20)
    │   ├── ScenarioDetail.tsx    # Comprehensive Scenario Detail View (PRD Day 20)
    │   ├── Runs.tsx              # Evaluation Run Dashboard & History (PRD Days 21–22)
    │   ├── RunDetail.tsx         # Run Detail, Results, Traces & Findings (PRD Days 21–22)
    │   ├── DocsPlaceholder.tsx   # Live links to Swagger, ReDoc, OpenAPI schema, and GitHub
    │   └── NotFound.tsx          # Accessible 404 fallback page
    ├── test/
    │   ├── api-client.test.ts        # API client unit tests (URL parsing, HTTP errors, timeouts)
    │   ├── components.test.tsx       # UI primitive and route rendering integration tests
    │   ├── scenario-explorer.test.tsx# Catalog and detail tests (search, filters, 404, navigation)
    │   ├── runs.test.tsx             # Runs creation, dashboard, traces, findings (15 tests)
    │   └── setup.ts                  # JSDOM test harness setup with fetch mocking
    └── utils/
        └── cn.ts                 # CSS class merger utility (clsx + tailwind-merge)
```

---

## 5. Security Design System Tokens

The interface uses a deliberate, high-contrast dark theme engineered for clarity, readability, and security focus:

| Outcome Token | Color Semantics | Accessibility Standard |
| :--- | :--- | :--- |
| **`PASS`** | Emerald (`#10b981`) | Security assertions satisfied; non-reliance on color alone (includes icon + explicit text). |
| **`FAIL`** | Crimson / Rose (`#ef4444`) | Security policy violation detected (e.g. IDOR, refund limit bypass). |
| **`ERROR`** | Amber / Orange (`#f59e0b`) | Unhandled exception or test harness timeout. |
| **`NOT_RUN`** | Slate / Gray (`#64748b`) | Scenario skipped or pending execution. |

### Execution Status vs. Security Verdict Semantics

The UI strictly differentiates between:
- **Execution Status**: The runtime outcome of the tool or scenario (`success`, `denied`, `error`). For instance, a security policy correctly denying an unauthorized refund returns an execution status of `denied`.
- **Security Evaluation Verdict**: The evaluator's assessment (`PASS`, `FAIL`, `ERROR`, `NOT_RUN`). In the above case, the scenario is marked `PASS` because the unauthorized access was correctly prevented.

---

## 6. Evaluation Run Dashboard & Controls (PRD Days 21–22)

### Run Creation Workflow (`POST /api/v1/runs`)
- **Interactive Modal**: Triggered via "New Evaluation" button across the console.
- **Suite & Agent Selection**: Pre-configured for canonical suite (`support-agent-security-v1`) and target agent (`reference-agent`).
- **Target Selection**: Run all 16 canonical scenarios or selectively choose individual test cases via catalog checkboxes.
- **Execution Controls**: Options to toggle `continue_on_error`, `record_trace`, and configure per-scenario timeout limits (0.01s - 300s).
- **Validation & Duplicate Protection**: Client-side validation prevents submission with zero scenarios or invalid timeouts. Double-submission is prevented while the request runs.
- **Auto-Navigation**: On successful run completion, immediately routes to `/runs/:runId`.

### Run History Dashboard (`/runs`)
- **Live Data Source**: `GET /api/v1/runs?limit=20&offset=0`
- **Paginated Listing**: Real-time evaluation history ordered newest-first with pagination controls.
- **Overview Metrics**: Displays Run ID, suite version, creation timestamp, overall security outcome badge, execution status, scenario count breakdown (P/F/E/NR), and calculated Security Score & ASR.
- **Search & Filter**: Real-time filtering by Run ID, status, or outcome.

### Run Detail Dashboard (`/runs/:runId`)
- **Metadata Banner**: Detailed run identifiers, started/completed timestamps, suite version, and evaluator version.
- **Metrics Overview Strip**: Total scenarios, passed count, failed count, error count, and unexecuted count. Formatted display of Security Score (e.g., `85.0/100`), Pass Rate, Attack Success Rate (ASR), and Sensitive Data Exposure Rate.
- **Scenario Results Table (`GET /api/v1/runs/{id}/results`)**:
  - Lists each evaluated scenario with outcome verdict (`PASS`, `FAIL`, `ERROR`, `NOT_RUN`).
  - Actual execution status vs. expected execution status.
  - Security assertion badges (Attempt Detected, Violation Prevented, Data Protected).
  - Expandable row revealing the evaluator's explanation and associated findings.
  - Quick action to jump directly to the execution trace for that scenario.
- **Chronological Trace Inspector (`GET /api/v1/runs/{id}/trace`)**:
  - Deterministic 1-based chronological timeline of audit events (`sequence`, `timestamp`, `event_type`, `tool_name`).
  - Clear Allow / Deny decision indicators and prominent `AUTHORIZATION DENIED` badges.
  - Scenario filter dropdown allowing drill-down to a single scenario's execution events.
  - Safe sanitized JSON payload inspector with syntax display and one-click clipboard copy.
- **Security Findings Drawer & Filter**:
  - Aggregates all security findings across evaluated scenarios.
  - Filter by severity (`Critical`, `High`, `Medium`, `Low`) and search by rule name or message.
  - Shows rule ID, title, severity, timestamp, and clickable link to the associated scenario.
---

## 7. Report Visualizer, Summary Metrics & CSV/JSON Exports (PRD Day 23)

### Machine-Readable JSON Report Visualizer (`GET /api/v1/runs/{id}/report.json`)
- **Real-Data Source**: Consumes `EvaluationReportExportResponse` containing schema version, export timestamp, evaluator metadata, suite version, outcomes, and computed metrics.
- **Collapsible Interactive Tree View**: Recursive tree rendering of nested JSON objects and arrays with expand/collapse toggles, child count indicators, and depth indentation guides.
- **Syntax Color Coding**: Safe DOM text node rendering with distinct styles for keys (cyan), strings (green), numbers (purple), booleans (amber), and null values (rose). Never renders JSON content as executable HTML.
- **Search & Filter**: Real-time filtering and highlight across JSON keys and primitive values with quick clear action.
- **Expand All / Collapse All**: One-click actions to recursively expand the complete report hierarchy or collapse to root.
- **Raw Formatted JSON View Toggle**: Instant switch between the interactive tree and formatted preformatted code block for copy-paste workflows.
- **Copy & Download Controls**: One-click clipboard copy with animated success/failure feedback, and full downloadable JSON report (`agentshield-report-{run_id}.json`) without truncation.

### Comprehensive Summary Metrics & Visual Breakdowns
- **Suite-Level Security Metrics Grid**:
  - `security_score`: Composite Security Score (weighted evaluation metric).
  - `overall_pass_rate`: Overall Pass Rate.
  - `attack_success_rate`: Adversarial Attack Success Rate (ASR).
  - `unauthorized_prevention_rate`: Unauthorized Tool Prevention Rate.
  - `sensitive_data_exposure_rate`: Sensitive Data / Secret Exposure Rate.
  - `benign_task_success_rate`: Positive Control / Benign Task Success Rate.
  - `policy_enforcement_failure_rate`: Policy Enforcement Failure Rate.
  - `run_completion_rate`: Test Suite Execution Completion Rate.
- **Mathematical Integrity**: Preserves original numerators, denominators, and percentages (`(numerator/denominator)`).
- **Safe Zero-Denominator Handling**: Metrics with 0 denominator display as `N/A` with `(0/0)` without throwing `NaN` or crashing. Distinguishes 0.0% from unavailable data.
- **Outcome Counts Strip**: Displays exact tallies for `PASS`, `FAIL`, `ERROR`, and `NOT_RUN` with semantic badge coloring. Never treats `ERROR` or `NOT_RUN` as `PASS`.
- **Category & Risk-Level Breakdowns**: Structured tables and progress bars displaying pass rates and scenario counts across attack categories and risk levels (Critical, High, Medium, Low).
- **Violations by Rule & Severity**: Summary pill tallies displaying occurrences per security rule and risk tier.
- **Evaluation Limitation Disclosure**: Prominently features the evaluator's `limitation_statement` warning that synthetic test suites do not guarantee universal real-world LLM security.

### CSV Export Utilities (`agentshield-*.csv`)
Provides client-side RFC-4180 compliant CSV exports for downstream security analytics:

| Export Dataset | Filename Pattern | Exported Columns & Descriptions |
| :--- | :--- | :--- |
| **Scenario Results** | `agentshield-scenarios-{runId}.csv` | `Run ID`, `Scenario ID`, `Scenario Name`, `Category`, `Risk Level`, `Outcome`, `Execution Status`, `Actual Status`, `Expected Status`, `Attempt Detected`, `Violation Prevented`, `Data Exposed`, `Findings Count`, `Explanation`, `Evaluated At` |
| **Security Findings** | `agentshield-findings-{runId}.csv` | `Run ID`, `Finding ID`, `Scenario ID`, `Rule ID`, `Rule Name`, `Severity`, `Outcome`, `Message`, `Timestamp`. (Button automatically disabled with descriptive tooltip when findings count is 0) |
| **Evaluation Metrics** | `agentshield-metrics-{runId}.csv` | `Run ID`, `Dataset`, `Metric Key`, `Name`, `Numerator`, `Denominator`, `Value`, `Display Value`, `Formula`, `Description`. Includes Core Metrics, Category Breakdowns, Risk Breakdowns, Rule Violations, and Severity Breakdowns. |

- **Formula-Injection Defense**: Any string beginning with spreadsheet formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) is automatically prefixed with `'` to neutralize malicious formula execution in Microsoft Excel, Google Sheets, and LibreOffice Calc.
- **RFC-4180 Escaping**: Commas, double-quotes (`""`), carriage returns, and newlines are properly wrapped in quotes.

---

## 8. Current Implemented Scope

- [x] Modern React + Vite + TypeScript application scaffolding in `frontend/`.
- [x] Tailored security dark design system tokens, typography, and utility classes.
- [x] Full suite of reusable design system primitives (`Button`, `Badge`, `StatusBadge`, `Card`, `Input`, `Select`, `LoadingSpinner`, `EmptyState`, `ErrorAlert`).
- [x] Responsive application shell with desktop sidebar, mobile drawer, and dynamic header.
- [x] Live backend connectivity monitoring against `GET /health`.
- [x] Comprehensive, typed API client (`ApiClient`, `apiClient`) with timeout protection and structured error handling.
- [x] Complete TypeScript domain models matching backend Pydantic schemas.
- [x] Professional landing/overview page detailing the 6-stage evaluation pipeline and true product scope.
- [x] Interactive Scenario Catalog & Explorer at `/scenarios` (PRD Day 20).
- [x] Detailed Scenario Specification View at `/scenarios/:scenarioId` (PRD Day 20).
- [x] **Evaluation Run Creation Workflow & Controls** via `POST /api/v1/runs` (PRD Day 21).
- [x] **Evaluation Run History Dashboard** at `/runs` via `GET /api/v1/runs` (PRD Day 21).
- [x] **Run Detail & Results Dashboard** at `/runs/:runId` via `GET /api/v1/runs/{id}` and `GET /api/v1/runs/{id}/results` (PRD Day 22).
- [x] **Execution Trace Inspector** with scenario filtering and allow/deny badges via `GET /api/v1/runs/{id}/trace` (PRD Day 22).
- [x] **Security Findings Inspection & Severity Filtering** (PRD Day 22).
- [x] **Machine-Readable JSON Report Visualizer** with collapsible tree, search, and raw JSON view (PRD Day 23).
- [x] **Comprehensive Summary Metrics Breakdown** with 8 core metrics, category & risk breakdowns, and limitation disclosure (PRD Day 23).
- [x] **RFC-4180 CSV Export Utility** for Scenarios, Findings, and Metrics with formula injection mitigation (PRD Day 23).
- [x] Comprehensive unit and integration test suite (66 passing tests across 6 test suites).

---

## 9. Next Milestone (PRD Day 24)

In accordance with PRD planning, the next milestone is:
- **PRD Day 24**: End-to-end demo script, polish, and final documentation.

---

## 9. Security Scope & Scientific Transparency

AgentShield evaluates a **deterministic reference agent** against synthetic customer-support scenarios using strict authorization policies, execution trace auditing, and rule-based security assertions.

- **No Real LLM Claims**: The baseline evaluation demonstrates policy-based guard enforcement and trace auditing on deterministic logic. It does not prove immunity or defense against real-world prompt injection across arbitrary Large Language Models.
- **No Fictional Metrics**: The UI does not display fabricated security scores, fake benchmark charts, or synthetic live telemetry.
