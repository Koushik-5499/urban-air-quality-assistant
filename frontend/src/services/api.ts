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
