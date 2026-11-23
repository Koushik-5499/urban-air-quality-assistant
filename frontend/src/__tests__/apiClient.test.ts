import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { request } from '../services/api/client';
import { ApiError, formatApiErrorMessage } from '../services/api/errors';
import { API_SETTINGS } from '../services/api/config';

describe('Modern API Client & Services Foundation', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('has valid API configuration defaults registered', () => {
    expect(API_SETTINGS.defaultTimeoutMs).toBe(10000);
    expect(typeof API_SETTINGS.baseUrl).toBe('string');
  });

  it('successfully parses successful responses via request()', async () => {
    const mockData = { aqi: 120, category: 'Moderate' };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => mockData,
    } as Response);

    const result = await request<typeof mockData>('/api/v1/aqi/current?city=Delhi');
    expect(result.aqi).toBe(120);
    expect(result.category).toBe('Moderate');
  });

  it('normalizes HTTP error responses into ApiError instances', async () => {
    const errorResponse = {
      detail: 'Resource not found',
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 404,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => errorResponse,
    } as Response);

    await expect(request('/api/v1/invalid')).rejects.toThrow(ApiError);
  });

  it('handles timeouts safely using AbortController and maps ApiError', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => {
      const error = new DOMException('The operation was aborted.', 'AbortError');
      return Promise.reject(error);
    });

    try {
      await request('/api/v1/slow', { timeoutMs: 50 });
      expect.fail('Should have thrown timeout error');
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).isTimeout).toBe(true);
      expect(formatApiErrorMessage(err)).toContain('timed out');
    }
  });
});
