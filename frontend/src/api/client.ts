/**
 * Typed HTTP API client for AgentShield backend communication.
 * Strictly wraps fetch with timeout protection and structured error parsing.
 */

import { API_CONFIG } from './config';
import type {
  CreateRunRequest,
  EvaluationReportExportResponse,
  EvaluationRunRecord,
  HealthResponse,
  RootResponse,
  RunCreateResponse,
  ScenarioDetailResponse,
  ScenarioResultResponse,
  ScenarioSummaryResponse,
  TraceEvent,
} from './types';

export class ApiClientError extends Error {
  public readonly status: number;
  public readonly detail: unknown;
  public readonly isNetworkError: boolean;

  constructor(status: number, message: string, detail?: unknown, isNetworkError: boolean = false) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.detail = detail ?? message;
    this.isNetworkError = isNetworkError;
  }
}

export type ApiError = ApiClientError;
export const ApiError = ApiClientError;

export interface ClientOptions {
  baseUrl?: string;
  timeoutMs?: number;
}

export interface ListScenariosOptions {
  category?: string;
  tag?: string;
  risk_level?: string;
}

export class AgentShieldClient {
  private readonly baseUrl: string;
  private readonly timeoutMs: number;

  constructor(baseUrlOrOptions?: string | ClientOptions, timeoutMs?: number) {
    if (typeof baseUrlOrOptions === 'object' && baseUrlOrOptions !== null) {
      this.baseUrl = (baseUrlOrOptions.baseUrl || API_CONFIG.baseUrl).replace(/\/+$/, '');
      this.timeoutMs = baseUrlOrOptions.timeoutMs ?? API_CONFIG.timeoutMs;
    } else {
      this.baseUrl = (baseUrlOrOptions || API_CONFIG.baseUrl).replace(/\/+$/, '');
      this.timeoutMs = timeoutMs ?? API_CONFIG.timeoutMs;
    }
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      if (!response.ok) {
        let detailData: unknown = null;
        let message = `HTTP ${response.status} ${response.statusText}`;
        try {
          detailData = await response.json();
          if (typeof (detailData as { detail?: unknown })?.detail === 'string') {
            message = (detailData as { detail: string }).detail;
          } else if (Array.isArray((detailData as { detail?: unknown })?.detail)) {
            message = (detailData as { detail: Array<{ msg?: string }> }).detail
              .map((e) => e.msg || 'Validation error')
              .join(', ');
          }
        } catch {
          // If response is not JSON, retain default status text
        }
        throw new ApiClientError(response.status, message, detailData, false);
      }

      return (await response.json()) as T;
    } catch (err: unknown) {
      if (err instanceof ApiClientError) {
        throw err;
      }
      if (err instanceof DOMException && err.name === 'AbortError') {
        throw new ApiClientError(408, `Request timed out after ${this.timeoutMs}ms`, undefined, false);
      }
      const message = err instanceof Error ? err.message : 'Network request failed';
      throw new ApiClientError(0, `Cannot connect to AgentShield backend: ${message}`, undefined, true);
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Ping backend healthcheck endpoint.
   */
  public async checkHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>(API_CONFIG.endpoints.health);
  }

  /**
   * Query backend root endpoint for identity and version metadata.
   */
  public async getRoot(): Promise<RootResponse> {
    return this.request<RootResponse>(API_CONFIG.endpoints.root);
  }

  /**
   * List all registered security scenarios with optional category, tag, or risk level filtering.
   */
  public async listScenarios(
    paramsOrCategory?: string | ListScenariosOptions,
    tagParam?: string
  ): Promise<ScenarioSummaryResponse[]> {
    const params = new URLSearchParams();
    if (typeof paramsOrCategory === 'object' && paramsOrCategory !== null) {
      if (paramsOrCategory.category) params.set('category', paramsOrCategory.category);
      if (paramsOrCategory.tag) params.set('tag', paramsOrCategory.tag);
      if (paramsOrCategory.risk_level) params.set('risk_level', paramsOrCategory.risk_level);
    } else {
      if (paramsOrCategory) params.set('category', paramsOrCategory);
      if (tagParam) params.set('tag', tagParam);
    }
    const queryString = params.toString();
    const endpoint = queryString
      ? `${API_CONFIG.endpoints.scenarios}?${queryString}`
      : API_CONFIG.endpoints.scenarios;
    return this.request<ScenarioSummaryResponse[]>(endpoint);
  }

  /**
   * Retrieve full scenario definition by its unique identifier.
   */
  public async getScenario(scenarioId: string): Promise<ScenarioDetailResponse> {
    return this.request<ScenarioDetailResponse>(API_CONFIG.endpoints.scenarioDetail(scenarioId));
  }

  /**
   * Execute a security evaluation suite against the reference agent.
   */
  public async createRun(payload: CreateRunRequest): Promise<RunCreateResponse> {
    return this.request<RunCreateResponse>(API_CONFIG.endpoints.runs, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  /**
   * Retrieve paginated evaluation runs ordered newest first.
   */
  public async listRuns(limit: number = 20, offset: number = 0): Promise<EvaluationRunRecord[]> {
    const endpoint = `${API_CONFIG.endpoints.runs}?limit=${limit}&offset=${offset}`;
    return this.request<EvaluationRunRecord[]>(endpoint);
  }

  /**
   * Retrieve evaluation run summary by run ID.
   */
  public async getRun(runId: string): Promise<EvaluationRunRecord> {
    return this.request<EvaluationRunRecord>(API_CONFIG.endpoints.runDetail(runId));
  }

  /**
   * Retrieve detailed per-scenario evaluation outcomes for a run.
   */
  public async getRunResults(runId: string): Promise<ScenarioResultResponse[]> {
    return this.request<ScenarioResultResponse[]>(API_CONFIG.endpoints.runResults(runId));
  }

  /**
   * Retrieve sanitized execution trace events for an evaluation run.
   */
  public async getRunTrace(runId: string, scenarioId?: string): Promise<TraceEvent[]> {
    const base = API_CONFIG.endpoints.runTrace(runId);
    const endpoint = scenarioId ? `${base}?scenario_id=${encodeURIComponent(scenarioId)}` : base;
    return this.request<TraceEvent[]>(endpoint);
  }

  /**
   * Download and parse the full JSON evaluation report.
   */
  public async exportRunReport(runId: string): Promise<EvaluationReportExportResponse> {
    return this.request<EvaluationReportExportResponse>(API_CONFIG.endpoints.runReportJson(runId));
  }
}

// Aliases
export { AgentShieldClient as ApiClient };

// Global singleton instance for app-wide use
export const apiClient = new AgentShieldClient();
