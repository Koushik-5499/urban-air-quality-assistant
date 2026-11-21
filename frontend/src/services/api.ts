// @deprecated This file is a legacy re-export shim. Import from './api/index' or the specific sub-modules (e.g. './api/alertsApi') directly. This file is retained for backwards compatibility with existing test imports only.
export * from './api/index';

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  status: number;
}

export const apiConfig = {
  baseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
} as const;
