import '@testing-library/jest-dom';
import { afterEach, beforeEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Default mock for fetch so components checking health don't trigger unhandled fetch errors
beforeEach(() => {
  if (!globalThis.fetch || !vi.isMockFunction(globalThis.fetch)) {
    globalThis.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => ({ status: 'ok', service: 'agentshield-backend', version: '0.1.0' }),
        } as unknown as Response);
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({}),
      } as unknown as Response);
    });
  }
});

// Automatically cleanup after each test
afterEach(() => {
  cleanup();
});
