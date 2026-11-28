import type { AirAlert, NotificationPreferences, AlertSeverity, AlertFilterState } from '../types/alerts';
import type { AQICategory } from '../types/dashboard';
import {
  DEFAULT_MONITORED_CITIES,
  DEFAULT_NOTIFICATION_PREFERENCES,
  INITIAL_SAMPLE_ALERTS,
} from './alertSeedData';

export {
  DEFAULT_MONITORED_CITIES,
  DEFAULT_NOTIFICATION_PREFERENCES,
  INITIAL_SAMPLE_ALERTS,
};

const STORAGE_KEY_ALERTS = 'uaqa_air_alerts';
const STORAGE_KEY_PREFS = 'uaqa_notification_preferences';
const STORAGE_KEY_MONITORED = 'uaqa_monitored_cities';

/**
 * Loads persisted alerts from localStorage or falls back to INITIAL_SAMPLE_ALERTS.
 */
export function loadSavedAlerts(): AirAlert[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_ALERTS);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    }
  } catch {
    // storage error
  }
  return INITIAL_SAMPLE_ALERTS;
}

/**
 * Persists alerts to localStorage.
 */
export function saveAlerts(alerts: AirAlert[]): void {
  try {
    localStorage.setItem(STORAGE_KEY_ALERTS, JSON.stringify(alerts));
  } catch {
    // storage error
  }
}

/**
 * Loads notification preferences from localStorage.
 */
export function loadNotificationPreferences(): NotificationPreferences {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_PREFS);
    if (raw) {
      const parsed = JSON.parse(raw);
      return { ...DEFAULT_NOTIFICATION_PREFERENCES, ...parsed };
    }
  } catch {
    // storage error
  }
  return DEFAULT_NOTIFICATION_PREFERENCES;
}

/**
 * Persists notification preferences to localStorage.
 */
export function saveNotificationPreferences(prefs: NotificationPreferences): void {
  try {
    localStorage.setItem(STORAGE_KEY_PREFS, JSON.stringify(prefs));
  } catch {
    // storage error
  }
}

/**
 * Loads monitored city IDs from localStorage.
 */
export function loadMonitoredCities(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_MONITORED);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) return parsed;
    }
  } catch {
    // storage error
  }
  return DEFAULT_MONITORED_CITIES;
}

/**
 * Persists monitored city IDs to localStorage.
 */
export function saveMonitoredCities(cityIds: string[]): void {
  try {
    localStorage.setItem(STORAGE_KEY_MONITORED, JSON.stringify(cityIds));
  } catch {
    // storage error
  }
}

/**
 * Maps AQI category to alert severity.
 */
export function getSeverityFromCategory(cat: AQICategory): AlertSeverity {
  switch (cat) {
    case 'Good':
      return 'info';
    case 'Moderate':
      return 'moderate';
    case 'Unhealthy for Sensitive Groups':
      return 'warning';
    case 'Unhealthy':
      return 'critical';
    case 'Very Unhealthy':
    case 'Hazardous':
      return 'severe';
    default:
      return 'info';
  }
}

/**
 * Returns initial sample alerts for all 10 cities.
 */
export function generateInitialAlerts(): AirAlert[] {
  return [...INITIAL_SAMPLE_ALERTS];
}

/**
 * Centralized alert filtering and sorting utility.
 */
export function filterAlerts(alerts: AirAlert[], filters: AlertFilterState): AirAlert[] {
  return alerts
    .filter((alt) => {
      if (filters.severity !== 'all' && alt.severity !== filters.severity) {
        return false;
      }
      if (filters.cityId !== 'all' && alt.cityId !== filters.cityId) {
        return false;
      }
      if (filters.status === 'unread' && alt.isRead) return false;
      if (filters.status === 'read' && !alt.isRead) return false;
      if (filters.searchQuery.trim()) {
        const q = filters.searchQuery.toLowerCase().trim();
        const matches =
          alt.title.toLowerCase().includes(q) ||
          alt.city.toLowerCase().includes(q) ||
          alt.state.toLowerCase().includes(q) ||
          alt.description.toLowerCase().includes(q);
        if (!matches) return false;
      }
      return true;
    })
    .sort((a, b) => {
      if (filters.sortBy === 'oldest') {
        return a.timestamp.localeCompare(b.timestamp);
      }
      if (filters.sortBy === 'severity') {
        const rank: Record<AlertSeverity, number> = {
          severe: 5,
          critical: 4,
          warning: 3,
          moderate: 2,
          info: 1,
        };
        return rank[b.severity] - rank[a.severity];
      }
      return b.timestamp.localeCompare(a.timestamp);
    });
}
