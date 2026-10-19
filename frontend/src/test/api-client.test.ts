import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiClient, ApiError } from '../api/client';

describe('ApiClient', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('uses the provided base URL and normalizes trailing slashes', () => {
    const client = new ApiClient({ baseUrl: 'http://example.com/api/' });
    expect(client.getBaseUrl()).toBe('http://example.com/api');
  });

  it('parses successful JSON responses', async () => {
    const mockData = { status: 'ok', service: 'agentshield-backend', version: '0.1.0' };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockData,
    } as unknown as Response);

    const client = new ApiClient({ baseUrl: 'http://127.0.0.1:8000' });
    const result = await client.checkHealth();

    expect(result).toEqual(mockData);
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    expect((globalThis.fetch as any).mock.calls[0][0]).toBe('http://127.0.0.1:8000/health');
  });

  it('handles HTTP error responses and parses FastAPI detail object', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ detail: 'Run not found: run-123' }),
    } as unknown as Response);

    const client = new ApiClient({ baseUrl: 'http://127.0.0.1:8000' });

    await expect(client.getRun('run-123')).rejects.toThrow(ApiError);

    try {
      await client.getRun('run-123');
    } catch (err) {
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(404);
      expect(apiErr.message).toContain('Run not found: run-123');
      expect(apiErr.detail).toEqual({ detail: 'Run not found: run-123' });
    }
  });

  it('handles network failure as unavailable backend error', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    const client = new ApiClient({ baseUrl: 'http://127.0.0.1:8000' });

    await expect(client.checkHealth()).rejects.toThrow(ApiError);

    try {
      await client.checkHealth();
    } catch (err) {
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(0);
      expect(apiErr.isNetworkError).toBe(true);
      expect(apiErr.message).toContain('Failed to fetch');
    }
  });

  it('correctly constructs query parameters for listScenarios and listRuns', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ total: 0, items: [] }),
    } as unknown as Response);

    const client = new ApiClient({ baseUrl: 'http://127.0.0.1:8000' });
    await client.listScenarios({ category: 'prompt_injection', risk_level: 'critical' });

    const calledUrl = (globalThis.fetch as any).mock.calls[0][0];
    expect(calledUrl).toContain('/api/v1/scenarios?');
    expect(calledUrl).toContain('category=prompt_injection');
    expect(calledUrl).toContain('risk_level=critical');
  });
});
