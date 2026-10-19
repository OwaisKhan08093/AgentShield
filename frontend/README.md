# AgentShield Frontend Console

The AgentShield Web Console provides an automated, security-focused user interface for configuring, running, and analyzing security evaluations of tool-using AI customer support agents.

Implemented through **PRD Day 20 (Scenario Catalog & Explorer)**.

---

## 1. Stack & Architecture

- **Framework**: React 18 with Vite bundler
- **Language**: TypeScript (strict mode enabled)
- **Styling**: Tailwind CSS (dark security theme, accessible contrast, reduced-motion support)
- **Routing**: React Router DOM v6
- **Icons**: Lucide React
- **Unit & Integration Testing**: Vitest + React Testing Library + JSDOM

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
    │   ├── RunsPlaceholder.tsx   # Intentional placeholder with live API runs test (Days 21–22)
    │   ├── DocsPlaceholder.tsx   # Live links to Swagger, ReDoc, OpenAPI schema, and GitHub
    │   └── NotFound.tsx          # Accessible 404 fallback page
    ├── test/
    │   ├── api-client.test.ts        # API client unit tests (URL parsing, HTTP errors, timeouts)
    │   ├── components.test.tsx       # UI primitive and route rendering integration tests
    │   ├── scenario-explorer.test.tsx# Catalog and detail tests (search, filters, 404, navigation)
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

---

## 6. Scenario Catalog & Detail Views (PRD Day 20)

### Scenario Catalog & Explorer (`/scenarios`)
- **Live Data Source**: `GET /api/v1/scenarios`
- **Text Search**: Real-time filtering across `scenario_id`, `name`, `description`, `security_objective`, `category`, and `tags`.
- **Category Filter**: Select from canonical categories dynamically derived from registry data (`benign_task`, `unauthorized_access`, `approval_bypass`, `data_exposure`, `malformed_input`, `direct_injection`, `indirect_injection`).
- **Risk Filter**: Select by severity level (`critical`, `high`, `medium`, `low`, `informational`).
- **Summary Metrics Bar**: Real-time counts of Total Scenarios, Critical Risk, High Risk, Medium Risk, and Low/Info counts.
- **Empty & Error States**: Distinct handling for empty registry, zero search matches (with "Clear All Filters" button), and backend connection failure (with retry button).

### Scenario Detail View (`/scenarios/:scenarioId`)
- **Live Data Source**: `GET /api/v1/scenarios/{scenario_id}`
- **Security Objective**: Dedicated prominent callout emphasizing the target boundary or policy under audit.
- **Expected Behavior & Assertions**:
  - Expected execution status (`success`, `denied`, `error`).
  - Tool-level authorization denial requirement.
  - Prohibited customer identity exposure constraints.
  - Order data confidentiality requirements.
  - Target tool invocation specification.
- **Verdict Criteria**: Explicit criteria defining a `PASS` verdict vs. a `FAIL` security violation.
- **Navigation & Usability**: Back to catalog navigation, copy scenario ID action, race-condition protection against rapid navigation, and 404 Not Found state.

---

## 7. Current Implemented Scope

- [x] Modern React + Vite + TypeScript application scaffolding in `frontend/`.
- [x] Tailored security dark design system tokens, typography, and utility classes.
- [x] Full suite of reusable design system primitives (`Button`, `Badge`, `StatusBadge`, `Card`, `Input`, `Select`, `LoadingSpinner`, `EmptyState`, `ErrorAlert`).
- [x] Responsive application shell with desktop sidebar, mobile drawer, and dynamic header.
- [x] Live backend connectivity monitoring against `GET /health`.
- [x] Comprehensive, typed API client (`ApiClient`, `apiClient`) with timeout protection and structured error handling.
- [x] Complete TypeScript domain models matching backend Pydantic schemas.
- [x] Professional landing/overview page detailing the 6-stage evaluation pipeline and true product scope.
- [x] **Interactive Scenario Catalog & Explorer** at `/scenarios` (PRD Day 20).
- [x] **Detailed Scenario Specification View** at `/scenarios/:scenarioId` (PRD Day 20).
- [x] Comprehensive unit and integration test coverage across API client, UI primitives, and scenario explorer (24 passing tests).

---

## 8. Intentionally Deferred Milestones

In accordance with PRD planning, the following modules are intentionally deferred to subsequent milestones:

- **PRD Days 21–22**: Evaluation Run Dashboard, Execution Controls, Findings Drawer & Sanitized Trace Viewer.
- **PRD Day 23**: Machine-readable JSON Report Visualizer, Summary Metrics & CSV/JSON Export Views.
- **PRD Day 24**: End-to-end demo script, polish, and final documentation.

---

## 9. Security Scope & Scientific Transparency

AgentShield evaluates a **deterministic reference agent** against synthetic customer-support scenarios using strict authorization policies, execution trace auditing, and rule-based security assertions.

- **No Real LLM Claims**: The baseline evaluation demonstrates policy-based guard enforcement and trace auditing on deterministic logic. It does not prove immunity or defense against real-world prompt injection across arbitrary Large Language Models.
- **No Fictional Metrics**: The UI does not display fabricated security scores, fake benchmark charts, or synthetic live telemetry.
