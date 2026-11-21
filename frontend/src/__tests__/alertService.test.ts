import { describe, it, expect, beforeEach } from 'vitest';
import {
  generateInitialAlerts,
  filterAlerts,
  loadSavedAlerts,
  saveAlerts,
  loadNotificationPreferences,
  saveNotificationPreferences,
  loadMonitoredCities,
  saveMonitoredCities,
} from '../services/alertService';
import type { AlertFilterState } from '../types/alerts';

// Mock localStorage for node test environment
const storage: Record<string, string> = {};
const mockLocalStorage = {
  getItem: (k: string) => storage[k] ?? null,
  setItem: (k: string, v: string) => {
    storage[k] = v;
  },
  removeItem: (k: string) => {
    delete storage[k];
  },
  clear: () => {
    Object.keys(storage).forEach((k) => delete storage[k]);
  },
  length: 0,
  key: () => null,
};
Object.defineProperty(globalThis, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
});

describe('Alerts Service & Local Persistence', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
  });

  it('generates sample alerts for all 10 cities', () => {
    const alerts = generateInitialAlerts();
    expect(alerts.length).toBe(10);

    // Verify properties
    const first = alerts[0];
    expect(first.id).toBeDefined();
    expect(first.city).toBeDefined();
    expect(first.aqi).toBeGreaterThan(0);
    expect(['info', 'moderate', 'warning', 'critical', 'severe']).toContain(first.severity);
  });

  it('filters alerts by city and severity', () => {
    const alerts = generateInitialAlerts();

    // Filter by city
    const filterCity: AlertFilterState = {
      searchQuery: '',
      severity: 'all',
      cityId: 'delhi',
      status: 'all',
      sortBy: 'newest',
    };
    const delhiResults = filterAlerts(alerts, filterCity);
    expect(delhiResults).toHaveLength(1);
    expect(delhiResults[0].cityId).toBe('delhi');

    // Filter by search query
    const filterSearch: AlertFilterState = {
      searchQuery: 'Kolkata',
      severity: 'all',
      cityId: 'all',
      status: 'all',
      sortBy: 'newest',
    };
    const searchResults = filterAlerts(alerts, filterSearch);
    expect(searchResults).toHaveLength(1);
    expect(searchResults[0].city).toBe('Kolkata');
  });

  it('persists and restores alert states in localStorage', () => {
    const initial = generateInitialAlerts();
    initial[0].isRead = true;
    saveAlerts(initial);

    const loaded = loadSavedAlerts();
    expect(loaded).toHaveLength(10);
    expect(loaded[0].isRead).toBe(true);
  });

  it('persists notification preferences and monitored cities correctly', () => {
    const prefs = loadNotificationPreferences();
    prefs.quietHours = true;
    saveNotificationPreferences(prefs);

    const loadedPrefs = loadNotificationPreferences();
    expect(loadedPrefs.quietHours).toBe(true);

    const monitored = ['delhi', 'chennai', 'mumbai'];
    saveMonitoredCities(monitored);

    const loadedMonitored = loadMonitoredCities();
    expect(loadedMonitored).toEqual(monitored);
  });
});
