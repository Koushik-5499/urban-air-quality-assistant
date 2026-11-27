import { describe, it, expect, vi, beforeEach } from 'vitest';
import { airQualityApi } from '../services/api/airQualityApi';
import { forecastApi } from '../services/api/forecastApi';
import { healthApi } from '../services/api/healthApi';
import { historyApi } from '../services/api/historyApi';
import { api } from '../services/api/client';
import { ApiError, formatApiErrorMessage } from '../services/api/errors';
import { API_ENDPOINTS } from '../services/api/endpoints';
import {
  calculateAnalyticsSummary,
  calculatePollutantStats,
  generateAnalyticsInsights,
  generateHistoricalData,
} from '../services/analyticsService';
import { DASHBOARD_DATA } from '../data/dashboardData';

describe('API Service Modules & Error Formatter', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('airQualityApi calls expected backend endpoints with params', async () => {
    const getSpy = vi.spyOn(api, 'get').mockResolvedValue({} as never);

    await airQualityApi.getCities();
    await airQualityApi.getCityAirQuality('Delhi');
    await airQualityApi.getObservations({ city: 'Delhi', pollutant: 'PM2.5', limit: 10 });
    await airQualityApi.getSourceStatus();
    await airQualityApi.calculateAqi({ city: 'Delhi' });
    await airQualityApi.getLatestAqi({ city: 'Delhi' });
    await airQualityApi.getPollutantSubindices({ city: 'Delhi' });
    await airQualityApi.getStations({ city: 'Delhi' });

    expect(getSpy).toHaveBeenCalledTimes(8);
    expect(getSpy).toHaveBeenCalledWith(API_ENDPOINTS.airQuality.cityDetails('Delhi'), { signal: undefined });
    expect(getSpy).toHaveBeenCalledWith(API_ENDPOINTS.aqi.subindices, {
      params: { city: 'Delhi' },
      signal: undefined,
    });
  });

  it('forecastApi calls all 5 forecast endpoints', async () => {
    const getSpy = vi.spyOn(api, 'get').mockResolvedValue({} as never);

    await forecastApi.getForecast('Delhi', { horizon: '24h', include_uncertainty: true });
    await forecastApi.getHourlyForecast('Delhi', { hours: 48 });
    await forecastApi.getDailyForecast('Delhi', { days: 5 });
    await forecastApi.getForecastHistory('Delhi', { limit: 5 });
    await forecastApi.getModelStatus('Delhi');

    expect(getSpy).toHaveBeenCalledTimes(5);
    expect(getSpy).toHaveBeenCalledWith(API_ENDPOINTS.forecast.hourly, {
      params: { city: 'Delhi', hours: 48 },
      signal: undefined,
    });
  });

  it('healthApi calls ask, recommendations, guidelines, communitySolutions, impactMetrics, pollutant, status', async () => {
    const getSpy = vi.spyOn(api, 'get').mockResolvedValue({} as never);
    const postSpy = vi.spyOn(api, 'post').mockResolvedValue({} as never);

    await healthApi.askAssistant({ city: 'Delhi', question: 'Winter smog advice?' });
    await healthApi.getRecommendations({ city: 'Delhi' });
    await healthApi.getGuidelines();
    await healthApi.getCommunitySolutions();
    await healthApi.getImpactMetrics();
    await healthApi.getPollutantExplanation('PM2.5');
    await healthApi.getHealthStatus();

    expect(postSpy).toHaveBeenCalledWith(
      API_ENDPOINTS.healthAdvisor.ask,
      { city: 'Delhi', question: 'Winter smog advice?' },
      { signal: undefined }
    );
    expect(getSpy).toHaveBeenCalledTimes(6);
  });

  it('historyApi calls all 5 historical endpoints', async () => {
    const getSpy = vi.spyOn(api, 'get').mockResolvedValue({} as never);

    await historyApi.getAqiHistory({ city: 'Delhi', interval: 'daily', page: 1 });
    await historyApi.getPollutantHistory({ city: 'Delhi', pollutant: 'PM2.5' });
    await historyApi.getSummary({ city: 'Delhi' });
    await historyApi.getTrends({ city: 'Delhi', threshold: 5 });
    await historyApi.compareLocations({ cities: ['Delhi', 'Mumbai'] });

    expect(getSpy).toHaveBeenCalledTimes(5);
  });

  it('formats ApiError and generic error variants properly', () => {
    expect(formatApiErrorMessage(new ApiError('TIMEOUT', 'timeout', 408))).toContain('timed out');
    expect(formatApiErrorMessage(new ApiError('NETWORK_ERROR', 'net', 0))).toContain('backend server');
    expect(formatApiErrorMessage(new ApiError('NOT_FOUND', 'Missing city', 404))).toContain('Missing city');
    expect(formatApiErrorMessage(new ApiError('SERVER_ERROR', 'oops', 503))).toContain('internal error');
    expect(formatApiErrorMessage(new ApiError('BAD_REQUEST', 'Invalid', 400))).toBe('Invalid');
    expect(formatApiErrorMessage(new Error('Custom boom'))).toBe('Custom boom');
    expect(formatApiErrorMessage('raw string')).toContain('unexpected error');
  });
});

describe('Analytics Metrics Calculator & Generators', () => {
  const delhi = DASHBOARD_DATA['delhi'];
  const allCities = Object.values(DASHBOARD_DATA);

  it('calculates summaries, pollutant metrics, and observational insights across ranges', () => {
    const points24h = generateHistoricalData('delhi', '24h');
    const points30d = generateHistoricalData('delhi', '30d');
    const summary = calculateAnalyticsSummary(points24h, delhi);

    expect(summary.highestAQI).toBeGreaterThanOrEqual(summary.lowestAQI);

    (['pm25', 'pm10', 'co', 'no2', 'so2', 'o3'] as const).forEach((pid) => {
      const pSummary = calculatePollutantStats(points30d, pid, delhi);
      expect(pSummary.pollutantId).toBe(pid);
      expect(pSummary.max).toBeGreaterThanOrEqual(pSummary.min);
    });

    const insights = generateAnalyticsInsights(delhi, points24h, summary, allCities);
    expect(insights.length).toBeGreaterThanOrEqual(5);
  });
});
