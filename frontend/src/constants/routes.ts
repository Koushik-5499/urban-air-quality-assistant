export const ROUTES = {
  DASHBOARD: '/',
  LOCATIONS: '/locations',
  POLLUTANTS: '/pollutants',
  MAP: '/map',
  ASSISTANT: '/assistant',
  ALERTS: '/alerts',
  ANALYTICS: '/analytics',
} as const;

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];

