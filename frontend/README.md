# AgentShield Frontend Console

The AgentShield Web Console provides an automated, security-focused user interface for configuring, running, and analyzing security evaluations of tool-using AI customer support agents.

Implemented as part of **PRD Day 19 (Frontend Scaffolding, Project Setup & Design System)**.

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
    │   └── ui/
    │       ├── Badge.tsx         # Semantic status and severity pill badges
    │       ├── Button.tsx        # Accessible interactive button with variants & loading state
    │       ├── Card.tsx          # Layered surface container with header, description & content
    │       ├── EmptyState.tsx    # Accessible empty state card with icon and call-to-action
    │       ├── ErrorAlert.tsx    # Accessible error callout with retry action
    │       ├── Input.tsx         # Accessible text and search input field
    │       ├── LoadingSpinner.tsx# Accessible animated spinner
    │       ├── StatusBadge.tsx   # Security outcome (PASS/FAIL/ERROR/NOT_RUN) & severity badges
    │       └── index.ts          # Re-export entrypoint for UI design system
    ├── pages/
    │   ├── Overview.tsx              # Platform landing page, pipeline visualizer & health status
    │   ├── ScenariosPlaceholder.tsx  # Intentional placeholder with live API scenario test
    │   ├── RunsPlaceholder.tsx       # Intentional placeholder with live API runs test
    │   ├── DocsPlaceholder.tsx       # Live links to Swagger, ReDoc, OpenAPI schema, and GitHub
    │   └── NotFound.tsx              # Accessible 404 fallback page
    ├── test/
    │   ├── api-client.test.ts  # API client unit tests (URL parsing, HTTP errors, timeouts)
    │   ├── components.test.tsx # UI primitive and route rendering integration tests
    │   └── setup.ts            # JSDOM test harness setup with fetch mocking
    └── utils/
        └── cn.ts               # CSS class merger utility (clsx + tailwind-merge)
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

## 6. Backend Integration

The frontend connects directly to the AgentShield FastAPI backend:

1. **Live Health Check**: Polled automatically on load and every 30 seconds via `GET /health`. Shows real-time Online / Offline status with timestamp and manual refresh.
2. **Scenarios API**: Ready to query `GET /api/v1/scenarios` and `GET /api/v1/scenarios/{id}`.
3. **Runs API**: Ready to query `POST /api/v1/runs`, `GET /api/v1/runs`, and `GET /api/v1/runs/{id}`.
4. **Results & Traces API**: Ready to query `GET /api/v1/runs/{id}/results`, `GET /api/v1/runs/{id}/trace`, and `GET /api/v1/runs/{id}/export`.

---

## 7. Current Implemented Scope (PRD Day 19)

- [x] Modern React + Vite + TypeScript application scaffolding in `frontend/`.
- [x] Tailored security dark design system tokens, typography, and utility classes.
- [x] Full suite of reusable design system primitives (`Button`, `Badge`, `StatusBadge`, `Card`, `Input`, `LoadingSpinner`, `EmptyState`, `ErrorAlert`).
- [x] Responsive application shell with desktop sidebar, mobile drawer, and dynamic header.
- [x] Live backend connectivity monitoring against `GET /health`.
- [x] Comprehensive, typed API client (`ApiClient`, `apiClient`) with timeout protection and structured error handling.
- [x] Complete TypeScript domain models matching backend Pydantic schemas.
- [x] Professional landing/overview page detailing the 6-stage evaluation pipeline and true product scope.
- [x] Unit and component integration tests verifying API client behavior and design system rendering.

---

## 8. Intentionally Deferred Milestones

In accordance with PRD planning, the following modules are intentionally deferred and have honest placeholder states:

- **PRD Day 20**: Scenario Catalog & Interactive Explorer (category filtering, risk search, payload preview).
- **PRD Days 21–22**: Evaluation Run Dashboard, Execution Controls, Findings Drawer & Sanitized Trace Viewer.
- **PRD Day 23**: Machine-readable JSON Report Visualizer, Summary Metrics & CSV/JSON Export Views.

---

## 9. Security Scope & Scientific Transparency

AgentShield evaluates a **deterministic reference agent** against synthetic customer-support scenarios using strict authorization policies, execution trace auditing, and rule-based security assertions.

- **No Real LLM Claims**: The baseline evaluation demonstrates policy-based guard enforcement and trace auditing on deterministic logic. It does not prove immunity or defense against real-world prompt injection across arbitrary Large Language Models.
- **No Fictional Metrics**: The UI does not display fabricated security scores, fake benchmark charts, or synthetic live telemetry.
