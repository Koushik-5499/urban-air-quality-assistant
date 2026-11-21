import { describe, it, expect } from 'vitest';
import { DEMO_LOCATIONS, DASHBOARD_DATA } from '../data/dashboardData';
import { MAP_CITIES } from '../data/mapData';
import { POLLUTANT_DETAILS } from '../data/pollutantDetails';

describe('Centralized Indian Cities & Pollutant Data Integrity', () => {
  it('contains exactly 10 supported Indian metropolitan cities', () => {
    expect(DEMO_LOCATIONS).toHaveLength(10);
    expect(MAP_CITIES).toHaveLength(10);

    // Canonical keys in DASHBOARD_DATA (excluding backward-compatibility alias)
    const canonicalDashboardKeys = Object.keys(DASHBOARD_DATA).filter((k) => k !== 'new-delhi');
    expect(canonicalDashboardKeys).toHaveLength(10);
  });

  it('ensures all city identifiers match across datasets', () => {
    const demoIds = DEMO_LOCATIONS.map((loc) => loc.id).sort();
    const dashboardIds = Object.keys(DASHBOARD_DATA).filter((k) => k !== 'new-delhi').sort();
    const mapIds = MAP_CITIES.map((c) => c.id).sort();

    expect(demoIds).toEqual(dashboardIds);
    expect(dashboardIds).toEqual(mapIds);
  });

  it('verifies geographical coordinates are valid and located in India', () => {
    for (const loc of DEMO_LOCATIONS) {
      expect(loc.coordinates).toBeDefined();
      // Latitude for India: ~8°N to ~37°N
      expect(loc.coordinates!.lat).toBeGreaterThan(7.0);
      expect(loc.coordinates!.lat).toBeLessThan(38.0);
      // Longitude for India: ~68°E to ~97°E
      expect(loc.coordinates!.lng).toBeGreaterThan(67.0);
      expect(loc.coordinates!.lng).toBeLessThan(98.0);
    }
  });

  it('confirms each city has complete and valid pollutant metrics', () => {
    const expectedPollutants = ['pm25', 'pm10', 'co', 'no2', 'so2', 'o3'];

    for (const city of DEMO_LOCATIONS.map((l) => DASHBOARD_DATA[l.id])) {
      expect(city.aqi).toBeGreaterThan(0);
      expect(city.pollutants).toHaveLength(6);

      const cityPollutantIds = city.pollutants.map((p) => p.id);
      for (const expectedId of expectedPollutants) {
        expect(cityPollutantIds).toContain(expectedId);
      }

      // Check units
      const co = city.pollutants.find((p) => p.id === 'co');
      expect(co?.unit).toBe('mg/m³');

      const pm25 = city.pollutants.find((p) => p.id === 'pm25');
      expect(pm25?.unit).toBe('µg/m³');
    }
  });

  it('contains complete metadata for all 6 criteria pollutants', () => {
    const keys = Object.keys(POLLUTANT_DETAILS);
    expect(keys).toEqual(['pm25', 'pm10', 'co', 'no2', 'so2', 'o3']);

    for (const p of Object.values(POLLUTANT_DETAILS)) {
      expect(p.whoLimit).toBeGreaterThan(0);
      expect(p.naaqsLimit).toBeGreaterThan(0);
      expect(p.primarySources.length).toBeGreaterThan(0);
      expect(p.protectiveMeasures.length).toBeGreaterThan(0);
      expect(p.color).toMatch(/^#[0-9A-Fa-f]{6}$/);
    }
  });
});
