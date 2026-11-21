import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiClient, ApiError } from '../services/apiClient';
import { API_CONFIG } from '../config/apiConfig';

describe('API Client Foundation & Backend Readiness', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('has valid API configuration endpoints registered', () => {
    expect(API_CONFIG.endpoints.cities).toBe('/cities');
    expect(API_CONFIG.endpoints.cityDetails('delhi')).toBe('/cities/delhi');
    expect(API_CONFIG.endpoints.liveAQI('chennai')).toBe('/cities/chennai/aqi');
    expect(API_CONFIG.endpoints.forecast('mumbai')).toBe('/cities/mumbai/forecast');
    expect(API_CONFIG.endpoints.assistantChat).toBe('/assistant/chat');
    expect(API_CONFIG.timeoutMs).toBe(10000);
  });

  it('successfully parses successful responses', async () => {
    const mockData = { aqi: 120, category: 'Unhealthy for Sensitive Groups' };
    const mockResponse = {
      success: true,
      data: mockData,
      timestamp: '2026-11-20T12:00:00Z',
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    } as Response);

    const result = await apiClient<typeof mockData>('/cities/delhi/aqi');
    expect(result.success).toBe(true);
    expect(result.data.aqi).toBe(120);
  });

  it('normalizes HTTP error responses into ApiError instances', async () => {
    const errorResponse = {
      success: false,
      error: { code: 'NOT_FOUND', message: 'City not found' },
      timestamp: '2026-11-20T12:00:00Z',
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: async () => errorResponse,
    } as Response);

    await expect(apiClient('/cities/invalid')).rejects.toThrow(ApiError);
  });

  it('handles timeouts safely using AbortController', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => {
      const error = new DOMException('The operation was aborted.', 'AbortError');
      return Promise.reject(error);
    });

    try {
      await apiClient('/cities', { timeoutMs: 50 });
      expect.fail('Should have thrown timeout error');
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      expect((err as ApiError).code).toBe('TIMEOUT');
    }
  });
});
