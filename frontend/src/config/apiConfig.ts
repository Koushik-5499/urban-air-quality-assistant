export const API_CONFIG = {
  /**
   * Base URL for the future Air Quality backend services.
   * Configurable via VITE_API_BASE_URL environment variable.
   */
  baseUrl: (import.meta.env.VITE_API_BASE_URL as string) || '',

  /**
   * Default timeout in milliseconds for API operations.
   */
  timeoutMs: Number(import.meta.env.VITE_API_TIMEOUT_MS) || 10000,

  /**
   * Standard backend route registry for future REST/GraphQL microservices.
   */
  endpoints: {
    cities: '/cities',
    cityDetails: (id: string) => `/cities/${id}`,
    liveAQI: (id: string) => `/cities/${id}/aqi`,
    pollutants: (id: string) => `/cities/${id}/pollutants`,
    historicalTrends: (id: string) => `/cities/${id}/trends`,
    forecast: (id: string) => `/cities/${id}/forecast`,
    alerts: '/alerts',
    alertPreferences: '/alerts/preferences',
    assistantChat: '/assistant/chat',
  },
} as const;

