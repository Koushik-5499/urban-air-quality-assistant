import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  airQualityApi,
  healthApi,
  alertsApi,
  forecastApi,
  formatApiErrorMessage,
  ApiError,
} from '../services/api/index';
import { DASHBOARD_DATA } from '../data/dashboardData';
import { generateHistoricalData, calculateAnalyticsSummary } from '../services/analyticsService';
import { generateAssistantResponse } from '../services/assistantEngine';

describe('Critical User Journeys — End-to-End Simulation Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // -------------------------------------------------------------------------
  // Journey 1: Dashboard, City Selection & AQI Loading
  // -------------------------------------------------------------------------
  it('Journey Step 1-3: Loads dashboard for Coimbatore and validates telemetry', async () => {
    const coimbatoreData = DASHBOARD_DATA['coimbatore'];
    expect(coimbatoreData).toBeDefined();
    expect(coimbatoreData.location.city).toBe('Coimbatore');
    expect(coimbatoreData.aqi).toBeGreaterThan(0);
    expect(coimbatoreData.category).toBeDefined();
    expect(coimbatoreData.pollutants).toHaveLength(6);

    // Mock API fetch for Coimbatore live calculation
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        city_id: 1,
        city_name: 'Coimbatore',
        aqi: 106,
        category: 'Moderate',
        dominant_pollutant: 'PM2.5',
        pollutant_subindices: {
          'PM2.5': { pollutant_code: 'PM2.5', concentration: 42.5, sub_index: 106 },
        },
        calculated_at: '2026-11-20T12:00:00Z',
        source: 'cpcb_mock',
        is_simulated: true,
        data_quality: 'sufficient',
      }),
    } as Response);

    const aqiResult = await airQualityApi.calculateAqi({ city: 'Coimbatore' });
    expect(aqiResult.city_name).toBe('Coimbatore');
    expect(aqiResult.aqi).toBe(106);
    expect(aqiResult.dominant_pollutant).toBe('PM2.5');
  });

  // -------------------------------------------------------------------------
  // Journey 2: Pollutant Analysis Breakdown
  // -------------------------------------------------------------------------
  it('Journey Step 4: Analyzes criteria atmospheric pollutants (PM2.5, PM10, CO, NO2, SO2, O3)', () => {
    const city = DASHBOARD_DATA['coimbatore'];
    const pollutantIds = city.pollutants.map((p) => p.id);

    expect(pollutantIds).toContain('pm25');
    expect(pollutantIds).toContain('pm10');
    expect(pollutantIds).toContain('co');
    expect(pollutantIds).toContain('no2');
    expect(pollutantIds).toContain('so2');
    expect(pollutantIds).toContain('o3');

    city.pollutants.forEach((p) => {
      expect(p.value).toBeGreaterThanOrEqual(0);
      expect(p.unit).toBeDefined();
      expect(p.standardLimit).toBeDefined();
    });
  });

  // -------------------------------------------------------------------------
  // Journey 3: Historical Analytics & Trajectories
  // -------------------------------------------------------------------------
  it('Journey Step 5: Generates historical analytics trajectories and statistical summary', () => {
    const historical = generateHistoricalData('coimbatore', '24h');
    expect(historical.length).toBeGreaterThan(0);

    const summary = calculateAnalyticsSummary(historical, DASHBOARD_DATA['coimbatore']);
    expect(summary.currentAQI).toBeGreaterThan(0);
    expect(summary.highestAQI).toBeGreaterThanOrEqual(summary.lowestAQI);
    expect(['improving', 'worsening', 'stable']).toContain(summary.trendDirection);
  });

  // -------------------------------------------------------------------------
  // Journey 4: AI Health Assistant Interaction
  // -------------------------------------------------------------------------
  it('Journey Step 6-7: Consults AI Health Assistant with context and medical disclaimers', async () => {
    const mockAdvice = {
      answer: 'Given the moderate AQI in Coimbatore today, sensitive individuals should limit prolonged outdoor exertion.',
      recommendations: [
        {
          title: 'Morning Running Advisory',
          description: 'Jog during early afternoon when particulate concentration is lowest.',
          target_group: 'General Public',
          priority: 'medium',
          reason: 'Diurnal particulate dispersion',
        },
      ],
      sources: ['CPCB NAQI 2014', 'WHO Guidelines 2021'],
      disclaimer: 'This recommendation is educational and does not constitute medical advice.',
      data_freshness: 'fresh',
      response_type: 'ai_generated',
      model: 'gemini-2.0-flash',
    };

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockAdvice,
    } as Response);

    const response = await healthApi.askAssistant({
      city: 'Coimbatore',
      question: 'Is it safe to run this morning?',
    });

    expect(response.answer).toContain('Coimbatore');
    expect(response.recommendations).toHaveLength(1);
    expect(response.disclaimer).toContain('does not constitute medical advice');

    // Verify local fallback engine consistency
    const fallbackText = generateAssistantResponse('Is it safe to run this morning?', DASHBOARD_DATA['coimbatore']);
    expect(fallbackText).toBeDefined();
    expect(fallbackText.length).toBeGreaterThan(20);
  });

  // -------------------------------------------------------------------------
  // Journey 5: Alerts Feed & Read Status Mutation
  // -------------------------------------------------------------------------
  it('Journey Step 8-9: Retrieves alerts feed and marks an alert as read', async () => {
    // 1. List alerts
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        page: 1,
        page_size: 10,
        total_records: 1,
        total_pages: 1,
        unread_count: 1,
        alerts: [
          {
            id: 201,
            city_id: 1,
            city_name: 'Coimbatore',
            title: 'High PM2.5 Advisory',
            description: 'Elevated particulate levels detected.',
            severity: 'High',
            alert_type: 'threshold_breach',
            is_read: false,
            created_at: '2026-11-20T10:00:00Z',
          },
        ],
      }),
    } as Response);

    const alertsFeed = await alertsApi.listAlerts();
    expect(alertsFeed.alerts).toHaveLength(1);
    expect(alertsFeed.alerts[0].is_read).toBe(false);

    // 2. Mark read mutation
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        id: 201,
        is_read: true,
      }),
    } as Response);

    const readResult = await alertsApi.markAlertRead(201);
    expect(readResult.is_read).toBe(true);
  });

  // -------------------------------------------------------------------------
  // Journey 6: AQI Forecasting & ML Status
  // -------------------------------------------------------------------------
  it('Journey Step 10: Retrieves AQI predictions across multiple horizons', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        city: 'Coimbatore',
        model_name: 'LightGBM_AQI_Forecaster',
        model_version: '1.2.0',
        forecasts: [
          {
            city: 'Coimbatore',
            forecast_timestamp: '2026-11-21T00:00:00Z',
            predicted_aqi: 110,
            horizon_label: '24h',
            lower_bound: 95,
            upper_bound: 125,
            is_forecast: true,
          },
        ],
        total_horizons: 1,
        data_quality: 'high',
        weather_integrated: true,
      }),
    } as Response);

    const forecastData = await forecastApi.getForecast('Coimbatore');
    expect(forecastData.forecasts[0].predicted_aqi).toBe(110);
    expect(forecastData.model_name).toBe('LightGBM_AQI_Forecaster');
  });

  // -------------------------------------------------------------------------
  // Journey 7: City Switching & Context Isolation
  // -------------------------------------------------------------------------
  it('Journey Step 11-12: Switches active city to Delhi and validates contextual isolation', async () => {
    const delhiData = DASHBOARD_DATA['delhi'];
    expect(delhiData).toBeDefined();
    expect(delhiData.location.city).toBe('Delhi');

    // Ensure Delhi data is strictly distinct from Coimbatore
    expect(delhiData.location.city).not.toBe(DASHBOARD_DATA['coimbatore'].location.city);

    // Mock live Delhi calculation
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        city_id: 6,
        city_name: 'Delhi',
        aqi: 340,
        category: 'Very Poor',
        dominant_pollutant: 'PM2.5',
        pollutant_subindices: {
          'PM2.5': { pollutant_code: 'PM2.5', concentration: 185.0, sub_index: 340 },
        },
        calculated_at: '2026-11-20T12:00:00Z',
        source: 'cpcb_mock',
        is_simulated: true,
      }),
    } as Response);

    const delhiResult = await airQualityApi.calculateAqi({ city: 'Delhi' });
    expect(delhiResult.city_name).toBe('Delhi');
    expect(delhiResult.aqi).toBe(340);
    expect(delhiResult.category).toBe('Very Poor');
  });

  // -------------------------------------------------------------------------
  // Journey 8: Error Recovery & Graceful Offline Behavior
  // -------------------------------------------------------------------------
  it('Journey Error Recovery: Formats error diagnostics when server drops', () => {
    const networkErr = new ApiError('NETWORK_ERROR', 'Failed to fetch', 0);
    expect(formatApiErrorMessage(networkErr)).toContain('Ensure the backend server is running');

    const timeoutErr = new ApiError('TIMEOUT', 'Timeout', 408);
    expect(formatApiErrorMessage(timeoutErr)).toContain('timed out');

    const notFoundErr = new ApiError('NOT_FOUND', 'City not found', 404);
    expect(formatApiErrorMessage(notFoundErr)).toBe('City not found');
  });
});
