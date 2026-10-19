/**
 * Centralized API configuration for AgentShield backend communication.
 */

export const API_CONFIG = {
  baseUrl: (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, ''),
  timeoutMs: 15000,
  endpoints: {
    health: '/health',
    root: '/',
    scenarios: '/api/v1/scenarios',
    scenarioDetail: (id: string) => `/api/v1/scenarios/${encodeURIComponent(id)}`,
    runs: '/api/v1/runs',
    runDetail: (id: string) => `/api/v1/runs/${encodeURIComponent(id)}`,
    runResults: (id: string) => `/api/v1/runs/${encodeURIComponent(id)}/results`,
    runTrace: (id: string) => `/api/v1/runs/${encodeURIComponent(id)}/trace`,
    runReportJson: (id: string) => `/api/v1/runs/${encodeURIComponent(id)}/report.json`,
  },
} as const;
