import { API_SETTINGS } from './config';
import { ApiError } from './errors';

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  params?: Record<string, string | number | boolean | undefined | null | (string | number)[]>;
  body?: unknown;
  timeoutMs?: number;
}

/**
 * Core HTTP fetch wrapper configured for the FastAPI backend.
 * Provides query parameter serialization, timeout with AbortSignal,
 * JSON serialization, and normalized error mapping.
 */
export async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const {
    params,
    body,
    timeoutMs = API_SETTINGS.defaultTimeoutMs,
    headers: customHeaders,
    signal: callerSignal,
    ...restInit
  } = options;

  // 1. Resolve URL
  const baseUrl = API_SETTINGS.baseUrl.replace(/\/+$/, '');
  let fullUrl = path.startsWith('http') ? path : `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`;

  // 2. Query Parameters
  if (params) {
    const origin =
      typeof window !== 'undefined' && window.location?.origin
        ? window.location.origin
        : 'http://localhost:8000';
    const urlObj = new URL(fullUrl, origin);
    Object.entries(params).forEach(([key, val]) => {
      if (val === undefined || val === null) return;
      if (Array.isArray(val)) {
        val.forEach((item) => {
          if (item !== undefined && item !== null) {
            urlObj.searchParams.append(key, String(item));
          }
        });
      } else {
        urlObj.searchParams.append(key, String(val));
      }
    });
    fullUrl = urlObj.toString();
  }

  // 3. Timeout & Abort Controller
  const controller = new AbortController();
  let timedOut = false;
  const timeoutId = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);

  // Link caller signal if provided
  const handleCallerAbort = () => controller.abort();
  if (callerSignal) {
    if (callerSignal.aborted) {
      clearTimeout(timeoutId);
      throw new ApiError('CANCELLED', 'Request was cancelled before execution', 0);
    }
    callerSignal.addEventListener('abort', handleCallerAbort);
  }

  try {
    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...((customHeaders as Record<string, string>) || {}),
    };

    let serializedBody: BodyInit | null | undefined = undefined;
    if (body !== undefined && body !== null) {
      if (typeof body === 'string' || body instanceof FormData || body instanceof Blob) {
        serializedBody = body as BodyInit;
      } else {
        headers['Content-Type'] = 'application/json';
        serializedBody = JSON.stringify(body);
      }
    }

    const response = await fetch(fullUrl, {
      ...restInit,
      headers,
      body: serializedBody,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    if (callerSignal) {
      callerSignal.removeEventListener('abort', handleCallerAbort);
    }

    // 4. Handle HTTP Errors
    if (!response.ok) {
      let errorBody: unknown;
      let errorMessage = `Request failed with status ${response.status}`;
      let errorCode = `HTTP_${response.status}`;

      try {
        errorBody = await response.json();
        if (errorBody && typeof errorBody === 'object') {
          const eb = errorBody as Record<string, unknown>;
          if (typeof eb.detail === 'string') {
            errorMessage = eb.detail;
          } else if (Array.isArray(eb.detail)) {
            // FastAPI Pydantic validation error list
            errorMessage = eb.detail
              .map((d: { msg?: string; loc?: string[] }) => d.msg || 'Validation error')
              .join(', ');
            errorCode = 'VALIDATION_ERROR';
          } else if (eb.error && typeof eb.error === 'object') {
            const errObj = eb.error as Record<string, unknown>;
            if (typeof errObj.message === 'string') errorMessage = errObj.message;
            if (typeof errObj.code === 'string') errorCode = errObj.code;
          } else if (typeof eb.message === 'string') {
            errorMessage = eb.message;
          }
        }
      } catch {
        // Response was not JSON
      }

      throw new ApiError(errorCode, errorMessage, response.status, errorBody);
    }

    // 204 No Content
    if (response.status === 204) {
      return undefined as unknown as T;
    }

    const data = await response.json();
    return data as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (callerSignal) {
      callerSignal.removeEventListener('abort', handleCallerAbort);
    }

    if (err instanceof ApiError) {
      throw err;
    }

    if (timedOut) {
      throw new ApiError('TIMEOUT', `Request timed out after ${timeoutMs}ms`, 408);
    }

    if (callerSignal?.aborted) {
      throw new ApiError('CANCELLED', 'Request was cancelled', 0);
    }

    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError('TIMEOUT', `Request was aborted or timed out after ${timeoutMs}ms`, 408);
    }

    const message = err instanceof Error ? err.message : 'Unknown network failure';
    throw new ApiError('NETWORK_ERROR', message, 0, err);
  }
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'POST', body }),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'DELETE' }),
};
