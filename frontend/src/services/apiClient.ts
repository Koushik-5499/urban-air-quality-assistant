// @deprecated This is a legacy API client. Use the new client at './api/client' instead. This file is retained for backwards compatibility with existing test imports only.
import { API_CONFIG } from '../config/apiConfig';
import type { ApiResponse, RequestOptions } from '../types/api';

export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status?: number,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Standard typed API client foundation designed for seamless future backend integration.
 * Incorporates request timeouts, parameter serialization, error normalization, and safe headers.
 */
export async function apiClient<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<ApiResponse<T>> {
  const {
    timeoutMs = API_CONFIG.timeoutMs,
    params,
    headers: customHeaders,
    ...restInit
  } = options;

  // Build full URL
  const baseUrl = API_CONFIG.baseUrl.replace(/\/+$/, '');
  let fullUrl = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint}`;

  if (params) {
    const urlObj = new URL(fullUrl, window.location.origin);
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        urlObj.searchParams.append(key, String(val));
      }
    });
    fullUrl = urlObj.toString();
  }

  // AbortController for safe timeout handling
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(fullUrl, {
      ...restInit,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...customHeaders,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        // Fallback for non-JSON errors
      }

      throw new ApiError(
        errorData?.error?.code || `HTTP_${response.status}`,
        errorData?.error?.message || `Request failed with status ${response.status}`,
        response.status,
        errorData?.error?.details
      );
    }

    const json = await response.json();
    return json as ApiResponse<T>;
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    if (err instanceof ApiError) {
      throw err;
    }

    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError('TIMEOUT', `Request timed out after ${timeoutMs}ms`, 408);
    }

    const message = err instanceof Error ? err.message : 'Unknown network failure';
    throw new ApiError('NETWORK_ERROR', message, 0, err);
  }
}

