/**
 * API client configuration and environment resolution.
 */
function resolveBaseUrl(): string {
  const envUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  if (envUrl) {
    return envUrl.replace(/\/+$/, '');
  }
  // In development, default to local FastAPI server on port 8000
  if (import.meta.env.DEV) {
    return 'http://localhost:8000';
  }
  // In production, fallback to same-origin relative URLs
  return '';
}

export const API_SETTINGS = {
  baseUrl: resolveBaseUrl(),
  defaultTimeoutMs: Number(import.meta.env.VITE_API_TIMEOUT_MS) || 10000,
} as const;

