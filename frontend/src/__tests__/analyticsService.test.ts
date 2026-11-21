import { describe, it, expect } from 'vitest';
import {
  generateHistoricalData,
  calculateAnalyticsSummary,
  calculatePollutantStats,
  generateSimulatedForecast,
} from '../services/analyticsService';
import { DASHBOARD_DATA } from '../data/dashboardData';

describe('Historical Analytics & Deterministic Forecasting Engine', () => {
  const city = DASHBOARD_DATA['coimbatore'];

  it('generates consistent historical telemetry for 24h, 7d, 30d, and 90d', () => {
    const data24h = generateHistoricalData('coimbatore', '24h');
    expect(data24h).toHaveLength(12);

    const data7d = generateHistoricalData('coimbatore', '7d');
    expect(data7d).toHaveLength(7);

    const data30d = generateHistoricalData('coimbatore', '30d');
    expect(data30d).toHaveLength(15);

    const data90d = generateHistoricalData('coimbatore', '90d');
    expect(data90d).toHaveLength(12);
  });

  it('produces 100% deterministic, reproducible values across multiple calls', () => {
    const runA = generateHistoricalData('bengaluru', '24h');
    const runB = generateHistoricalData('bengaluru', '24h');

    expect(runA).toEqual(runB);
    expect(runA[0].aqi).toBe(runB[0].aqi);
    expect(runA[5].pm25).toBe(runB[5].pm25);
  });

  it('calculates summary statistics accurately from sample points', () => {
    const points = generateHistoricalData('coimbatore', '24h');
    const summary = calculateAnalyticsSummary(points, city);

    expect(summary.currentAQI).toBe(city.aqi);
    expect(summary.historicalAverageAQI).toBeGreaterThan(0);
    expect(summary.highestAQI).toBeGreaterThanOrEqual(summary.lowestAQI);
    expect(['improving', 'worsening', 'stable']).toContain(summary.trendDirection);
  });

  it('calculates pollutant statistics preserving correct units', () => {
    const points = generateHistoricalData('delhi', '7d');
    const delhi = DASHBOARD_DATA['delhi'];

    const coStats = calculatePollutantStats(points, 'co', delhi);
    expect(coStats.unit).toBe('mg/m³');
    expect(coStats.average).toBeGreaterThan(0);

    const pmStats = calculatePollutantStats(points, 'pm25', delhi);
    expect(pmStats.unit).toBe('µg/m³');
    expect(pmStats.average).toBeGreaterThan(0);
  });

  it('generates deterministic short-term forecasts across all horizons', () => {
    const horizons = ['6h', '12h', '24h', '3d'] as const;

    for (const h of horizons) {
      const forecastA = generateSimulatedForecast('mumbai', h);
      const forecastB = generateSimulatedForecast('mumbai', h);

      expect(forecastA).toEqual(forecastB);
      expect(forecastA.dataPoints.length).toBeGreaterThan(0);
      expect(forecastA.precautions.length).toBeGreaterThan(0);

      // Verify confidence bounds: lower <= predicted <= upper
      for (const pt of forecastA.dataPoints) {
        expect(pt.confidenceLower).toBeLessThanOrEqual(pt.predictedAQI);
        expect(pt.predictedAQI).toBeLessThanOrEqual(pt.confidenceUpper);
      }
    }
  });
});

