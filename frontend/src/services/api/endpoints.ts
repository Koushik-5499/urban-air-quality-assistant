/**
 * Authoritative registry of FastAPI v1 backend endpoints.
 */
export const API_ENDPOINTS = {
  // Service Health
  health: '/api/v1/health',

  // Air Quality & Telemetry
  airQuality: {
    cities: '/api/v1/air-quality/cities',
    cityDetails: (cityName: string) => `/api/v1/air-quality/cities/${encodeURIComponent(cityName)}`,
    observations: '/api/v1/air-quality',
    sourceStatus: '/api/v1/air-quality/source-status',
  },

  // CPCB NAQI Processing Engine
  aqi: {
    calculate: '/api/v1/aqi/calculate',
    latest: '/api/v1/aqi/latest',
    subindices: '/api/v1/aqi/pollutant-subindices',
    history: '/api/v1/aqi/history',
  },

  // Monitoring Stations
  stations: '/api/v1/stations',

  // Historical Data Service
  history: {
    aqi: '/api/v1/history/aqi',
    pollutants: '/api/v1/history/pollutants',
    summary: '/api/v1/history/summary',
    trends: '/api/v1/history/trends',
    compare: '/api/v1/history/compare',
  },

  // AI Health Advisor
  healthAdvisor: {
    ask: '/api/v1/health/ask',
    recommendations: '/api/v1/health/recommendations',
    guidelines: '/api/v1/health/guidelines',
    communitySolutions: '/api/v1/health/community-solutions',
    impactMetrics: '/api/v1/health/impact-metrics',
    pollutantExplanation: (code: string) => `/api/v1/health/pollutants/${encodeURIComponent(code)}`,
    status: '/api/v1/health/status',
  },

  // Alerts & Notifications
  alerts: {
    list: '/api/v1/alerts',
    unreadCount: '/api/v1/alerts/unread-count',
    markRead: (alertId: number) => `/api/v1/alerts/${alertId}/read`,
    markAllRead: '/api/v1/alerts/read-all',
    preferences: '/api/v1/alerts/preferences',
    status: '/api/v1/alerts/status',
  },

  // Air Quality Forecasting
  forecast: {
    aqi: '/api/v1/forecast/aqi',
    hourly: '/api/v1/forecast/hourly',
    daily: '/api/v1/forecast/daily',
    history: '/api/v1/forecast/history',
    modelStatus: '/api/v1/forecast/model-status',
    generate: '/api/v1/forecast/generate',
  },
} as const;

