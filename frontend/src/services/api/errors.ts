/**
 * Unified API Error representation for normalized client-side error handling.
 */
export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number = 0,
    public readonly details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }

  get isTimeout(): boolean {
    return this.code === 'TIMEOUT' || this.status === 408;
  }

  get isNetworkError(): boolean {
    return this.code === 'NETWORK_ERROR' || this.status === 0;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isServerError(): boolean {
    return this.status >= 500;
  }
}

/**
 * Formats API errors into user-friendly diagnostic messages.
 */
export function formatApiErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.isTimeout) {
      return 'The connection to the air quality server timed out. Please verify your connection.';
    }
    if (err.isNetworkError) {
      return 'Unable to reach the backend service. Ensure the backend server is running.';
    }
    if (err.isNotFound) {
      return err.message || 'The requested air quality resource or city was not found.';
    }
    if (err.isServerError) {
      return 'The air quality server encountered an internal error. Please try again later.';
    }
    return err.message;
  }

  if (err instanceof Error) {
    return err.message;
  }

  return 'An unexpected error occurred while communicating with the air quality service.';
}

