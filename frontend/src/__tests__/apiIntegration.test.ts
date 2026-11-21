import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  request,
  airQualityApi,
  historyApi,
  healthApi,
  alertsApi,
  forecastApi,
  ApiError,
  formatApiErrorMessage,
} from '../services/api/index';

describe('Frontend-to-Backend API Integration Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // -------------------------------------------------------------------------
  // 1. Core Request & Error Handling
  // -------------------------------------------------------------------------
  describe('Core HTTP Request & Error Normalization', () => {
    it('serializes query parameters including arrays properly', async () => {
      let capturedUrl = '';
      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (url) => {
        capturedUrl = String(url);
        return {
          ok: true,
          status: 200,
          json: async () => ({ status: 'ok' }),
        } as Response;
      });

      await request('/api/v1/history/compare', {
        params: {
          cities: ['Delhi', 'Bengaluru'],
          include_simulated: true,
        },
      });

      expect(capturedUrl).toContain('cities=Delhi');
      expect(capturedUrl).toContain('cities=Bengaluru');
      expect(capturedUrl).toContain('include_simulated=true');
    });

    it('formats Pydantic 422 validation error arrays cleanly', async () => {
      const pydanticErrorResponse = {
        detail: [
          { loc: ['body', 'city'], msg: 'Field required', type: 'missing' },
          { loc: ['body', 'question'], msg: 'String should have at least 1 characters', type: 'string_too_short' },
        ],
      };

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => pydanticErrorResponse,
      } as Response);

      try {
        await request('/api/v1/health/ask', { method: 'POST', body: {} });
        expect.fail('Should have failed with 422');
      } catch (err) {
        expect(err).toBeInstanceOf(ApiError);
        const apiErr = err as ApiError;
        expect(apiErr.status).toBe(422);
        expect(apiErr.code).toBe('VALIDATION_ERROR');
        expect(apiErr.message).toContain('Field required');
        expect(apiErr.message).toContain('String should have at least 1 characters');
      }
    });

    it('transforms timeouts into typed ApiError with status 408', async () => {
      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(() => {
        const error = new DOMException('The operation was aborted.', 'AbortError');
        return Promise.reject(error);
      });

      try {
        await request('/api/v1/health', { timeoutMs: 20 });
        expect.fail('Should have timed out');
      } catch (err) {
        expect(err).toBeInstanceOf(ApiError);
        const apiErr = err as ApiError;
        expect(apiErr.isTimeout).toBe(true);
        expect(apiErr.status).toBe(408);
        expect(formatApiErrorMessage(apiErr)).toContain('timed out');
      }
    });

    it('transforms network drops into NETWORK_ERROR with status 0', async () => {
      vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new TypeError('Failed to fetch'));

      try {
        await request('/api/v1/health');
        expect.fail('Should have thrown network error');
      } catch (err) {
        expect(err).toBeInstanceOf(ApiError);
        const apiErr = err as ApiError;
        expect(apiErr.isNetworkError).toBe(true);
        expect(formatApiErrorMessage(apiErr)).toContain('Ensure the backend server is running');
      }
    });
  });

  // -------------------------------------------------------------------------
  // 2. Air Quality Domain Endpoints
  // -------------------------------------------------------------------------
  describe('Air Quality Domain Endpoints', () => {
    it('fetches registered cities list via GET /api/v1/air-quality/cities', async () => {
      const mockCities = [
        {
          city_id: 1,
          city_name: 'Coimbatore',
          state: 'Tamil Nadu',
          country: 'India',
          data_available: true,
          last_measured_at: '2026-11-20T12:00:00Z',
          is_stale: false,
          station_count: 1,
          source: 'cpcb_mock',
        },
      ];

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockCities,
      } as Response);

      const result = await airQualityApi.getCities();
      expect(result).toHaveLength(1);
      expect(result[0].city_name).toBe('Coimbatore');
      expect(result[0].data_available).toBe(true);
    });

    it('fetches city telemetry via GET /api/v1/air-quality/cities/{city_name}', async () => {
      const mockCityDetails = {
        city_id: 1,
        city_name: 'Coimbatore',
        state: 'Tamil Nadu',
        country: 'India',
        data_available: true,
        source: 'cpcb_mock',
        is_simulated: true,
        is_stale: false,
        data_age_seconds: 120,
        measured_at: '2026-11-20T12:00:00Z',
        fetched_at: '2026-11-20T12:01:00Z',
        pollutants: [
          { code: 'PM2.5', concentration: 42.5, unit: 'µg/m³', measured_at: '2026-11-20T12:00:00Z', source: 'cpcb_mock' },
        ],
        active_stations_count: 1,
        message: null,
      };

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockCityDetails,
      } as Response);

      const result = await airQualityApi.getCityAirQuality('Coimbatore');
      expect(result.city_name).toBe('Coimbatore');
      expect(result.pollutants[0].code).toBe('PM2.5');
      expect(result.is_simulated).toBe(true);
    });

    it('calculates CPCB NAQI via GET /api/v1/aqi/calculate', async () => {
      const mockAqi = {
        city_id: 1,
        city_name: 'Coimbatore',
        station_id: 1,
        station_name: 'SIDCO Industrial Estate',
        aqi: 106,
        category: 'Moderate',
        dominant_pollutant: 'PM2.5',
        pollutant_subindices: {
          'PM2.5': { pollutant_code: 'PM2.5', concentration: 42.5, unit: 'µg/m³', sub_index: 106, category: 'Moderate', averaging_period: '24h', is_valid: true, validation_error: null },
        },
        measurement_timestamp: '2026-11-20T12:00:00Z',
        calculated_at: '2026-11-20T12:00:00Z',
        source: 'cpcb_mock',
        is_simulated: true,
        data_quality: 'sufficient',
        averaging_period: '24h',
        available_pollutants: ['PM2.5', 'PM10'],
        missing_pollutants: [],
        explanation: 'Dominant pollutant PM2.5 defines the index.',
      };

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockAqi,
      } as Response);

      const result = await airQualityApi.calculateAqi({ city: 'Coimbatore' });
      expect(result.aqi).toBe(106);
      expect(result.dominant_pollutant).toBe('PM2.5');
      expect(result.data_quality).toBe('sufficient');
    });

    it('fetches stations list via GET /api/v1/stations', async () => {
      const mockStations = [
        {
          id: 1,
          station_name: 'SIDCO Industrial Estate',
          city_id: 1,
          city_name: 'Coimbatore',
          latitude: 11.0168,
          longitude: 76.9558,
          provider: 'cpcb',
          is_active: true,
        },
      ];

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockStations,
      } as Response);

      const result = await airQualityApi.getStations({ city: 'Coimbatore' });
      expect(result).toHaveLength(1);
      expect(result[0].station_name).toBe('SIDCO Industrial Estate');
    });
  });

  // -------------------------------------------------------------------------
  // 3. Historical Analytics & Comparisons
  // -------------------------------------------------------------------------
  describe('Historical Analytics Domain Endpoints', () => {
    it('fetches historical AQI series via GET /api/v1/history/aqi', async () => {
      const mockHistory = {
        city: 'Delhi',
        station_id: null,
        interval: 'hourly',
        total_records: 24,
        records: [
          { timestamp: '2026-11-20T10:00:00Z', aqi: 240, category: 'Poor', dominant_pollutant: 'PM2.5', source: 'cpcb', is_simulated: true },
        ],
      };

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockHistory,
      } as Response);

      const result = await historyApi.getAqiHistory({ city: 'Delhi', interval: 'hourly' });
      expect(result.city).toBe('Delhi');
      expect(result.records[0].aqi).toBe(240);
    });

    it('fetches location comparison via GET /api/v1/history/compare', async () => {
      const mockComparison = {
        comparison_start: '2026-11-19T00:00:00Z',
        comparison_end: '2026-11-20T00:00:00Z',
        locations_count: 2,
        comparison: [
          { location_name: 'Delhi', city_name: 'Delhi', station_name: null, record_count: 24, average_aqi: 280, min_aqi: 210, max_aqi: 320, predominant_category: 'Poor', primary_dominant_pollutant: 'PM2.5' },
          { location_name: 'Chennai', city_name: 'Chennai', station_name: null, record_count: 24, average_aqi: 75, min_aqi: 60, max_aqi: 90, predominant_category: 'Satisfactory', primary_dominant_pollutant: 'O3' },
        ],
      };

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockComparison,
      } as Response);

      const result = await historyApi.compareLocations({ cities: ['Delhi', 'Chennai'] });
      expect(result.locations_count).toBe(2);
      expect(result.comparison[0].city_name).toBe('Delhi');
      expect(result.comparison[1].city_name).toBe('Chennai');
    });
  });

  // -------------------------------------------------------------------------
  // 4. AI Health Advisor Endpoints
  // -------------------------------------------------------------------------
  describe('AI Health Advisor Domain Endpoints', () => {
    it('sends question and gets medical-grade health advice via POST /api/v1/health/ask', async () => {
      const mockHealthResponse = {
        answer: 'Outdoor cardio in Delhi today is not advised due to elevated PM2.5 levels.',
        recommendations: [
          { title: 'Use N95 Masks', description: 'Wear a well-fitted N95 mask outdoors.', target_group: 'General Public', priority: 'high', reason: 'High particulate concentration' },
        ],
        sources: ['CPCB Guidelines 2014', 'WHO Global Air Quality Guidelines 2021'],
        disclaimer: 'This advice is for informational purposes and does not replace medical consultation.',
        data_freshness: '10 minutes ago',
        response_type: 'ai_generated',
        model: 'gemini-2.0-flash',
      };

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockHealthResponse,
      } as Response);

      const result = await healthApi.askAssistant({
        city: 'Delhi',
        question: 'Is it safe to run outside?',
      });

      expect(result.answer).toContain('Outdoor cardio');
      expect(result.recommendations).toHaveLength(1);
      expect(result.response_type).toBe('ai_generated');
      expect(result.model).toBe('gemini-2.0-flash');
    });

    it('retrieves health guidelines via GET /api/v1/health/guidelines', async () => {
      const mockGuidelines = {
        organization: 'CPCB & WHO',
        standard: 'NAQI-2014',
        categories: [
          { category: 'Good', aqi_range: '0-50', general_advisory: 'Minimal impact', sensitive_groups_advisory: 'None', outdoor_activity: 'Normal', ventilation: 'Recommended' },
        ],
      };

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockGuidelines,
      } as Response);

      const result = await healthApi.getGuidelines();
      expect(result.categories[0].category).toBe('Good');
    });
  });

  // -------------------------------------------------------------------------
  // 5. Alerts & Notification Preferences
  // -------------------------------------------------------------------------
  describe('Alerts & Notifications Domain Endpoints', () => {
    it('retrieves paginated alerts with X-User-Id header via GET /api/v1/alerts', async () => {
      let capturedHeader = '';
      const mockAlerts = {
        page: 1,
        page_size: 10,
        total_records: 1,
        total_pages: 1,
        unread_count: 1,
        alerts: [
          {
            id: 101,
            city_id: 1,
            city_name: 'Delhi',
            station_id: null,
            station_name: null,
            title: 'High PM2.5 Alert',
            description: 'AQI exceeded 250 threshold.',
            severity: 'High',
            alert_type: 'threshold_breach',
            current_aqi: 265,
            previous_aqi: 180,
            threshold_value: 200,
            aqi_category: 'Poor',
            dominant_pollutant: 'PM2.5',
            source: 'cpcb',
            dedup_key: 'delhi-pm25-20261120',
            delivery_status: 'delivered',
            is_read: false,
            is_simulated: true,
            created_at: '2026-11-20T10:00:00Z',
            expires_at: null,
          },
        ],
      };

      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (_url, init) => {
        const headers = init?.headers as Record<string, string>;
        capturedHeader = headers?.['X-User-Id'] || '';
        return {
          ok: true,
          status: 200,
          json: async () => mockAlerts,
        } as Response;
      });

      const result = await alertsApi.listAlerts({ city: 'Delhi' }, 'test_user_42');
      expect(capturedHeader).toBe('test_user_42');
      expect(result.alerts[0].title).toBe('High PM2.5 Alert');
      expect(result.alerts[0].is_read).toBe(false);
    });

    it('marks alert as read via PATCH /api/v1/alerts/{alert_id}/read', async () => {
      let capturedMethod = '';
      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (_url, init) => {
        capturedMethod = init?.method || '';
        return {
          ok: true,
          status: 200,
          json: async () => ({ id: 101, is_read: true }),
        } as Response;
      });

      const result = await alertsApi.markAlertRead(101);
      expect(capturedMethod).toBe('PATCH');
      expect(result.is_read).toBe(true);
    });

    it('updates notification preferences via PUT /api/v1/alerts/preferences', async () => {
      let capturedBody: unknown = null;
      vi.spyOn(globalThis, 'fetch').mockImplementationOnce(async (_url, init) => {
        capturedBody = JSON.parse(String(init?.body || '{}'));
        return {
          ok: true,
          status: 200,
          json: async () => ({
            id: 1,
            user_id: 'default_user',
            city_id: 1,
            city_name: 'Coimbatore',
            station_id: null,
            station_name: null,
            min_aqi_threshold: 150,
            min_severity: 'High',
            is_enabled: true,
            channels: ['in_app', 'email'],
            email: 'user@example.com',
            quiet_hours_start: '22:00',
            quiet_hours_end: '07:00',
            timezone: 'Asia/Kolkata',
            created_at: '2026-11-20T10:00:00Z',
            updated_at: '2026-11-20T10:00:00Z',
          }),
        } as Response;
      });

      const result = await alertsApi.updatePreferences({
        city: 'Coimbatore',
        min_aqi_threshold: 150,
        min_severity: 'High',
        email: 'user@example.com',
      });

      expect((capturedBody as { min_aqi_threshold: number }).min_aqi_threshold).toBe(150);
      expect(result.email).toBe('user@example.com');
    });
  });

  // -------------------------------------------------------------------------
  // 6. Air Quality Forecasting
  // -------------------------------------------------------------------------
  describe('Air Quality Forecasting Domain Endpoints', () => {
    it('fetches multi-horizon predictions via GET /api/v1/forecast/aqi', async () => {
      const mockForecast = {
        city: 'Mumbai',
        station_id: null,
        station_name: null,
        generated_at: '2026-11-20T12:00:00Z',
        model_name: 'LightGBM_AQI_Forecaster',
        model_version: '1.2.0',
        forecasts: [
          {
            city: 'Mumbai',
            forecast_timestamp: '2026-11-20T18:00:00Z',
            generated_at: '2026-11-20T12:00:00Z',
            predicted_aqi: 135,
            predicted_category: 'Moderate',
            dominant_pollutant: 'PM2.5',
            horizon_hours: 6,
            horizon_label: '6h',
            lower_bound: 115,
            upper_bound: 155,
            uncertainty_status: 'normal',
            model_name: 'LightGBM_AQI_Forecaster',
            model_version: '1.2.0',
            training_data_start: '2026-10-20T00:00:00Z',
            training_data_end: '2026-11-20T00:00:00Z',
            training_samples: 720,
            data_quality: 'high',
            source: 'cpcb',
            is_simulated: true,
            is_forecast: true,
            forecast_status: 'predicted',
          },
        ],
        total_horizons: 1,
        data_quality: 'high',
        weather_integrated: true,
      };

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockForecast,
      } as Response);

      const result = await forecastApi.getForecast('Mumbai', { horizon: '6h' });
      expect(result.forecasts[0].predicted_aqi).toBe(135);
      expect(result.forecasts[0].horizon_label).toBe('6h');
      expect(result.model_name).toBe('LightGBM_AQI_Forecaster');
    });

    it('fetches step-by-step hourly forecasts via GET /api/v1/forecast/hourly', async () => {
      const mockHourly = {
        city: 'Bengaluru',
        station_id: null,
        station_name: null,
        hours: 24,
        generated_at: '2026-11-20T12:00:00Z',
        forecasts: [
          {
            city: 'Bengaluru',
            forecast_timestamp: '2026-11-20T13:00:00Z',
            generated_at: '2026-11-20T12:00:00Z',
            predicted_aqi: 68,
            predicted_category: 'Satisfactory',
            dominant_pollutant: 'PM10',
            horizon_hours: 1,
            horizon_label: '1h',
            lower_bound: 55,
            upper_bound: 80,
            uncertainty_status: 'low',
            model_name: 'LightGBM_AQI_Forecaster',
            model_version: '1.2.0',
            training_data_start: null,
            training_data_end: null,
            training_samples: 500,
            data_quality: 'high',
            source: 'cpcb',
            is_simulated: true,
            is_forecast: true,
            forecast_status: 'predicted',
          },
        ],
      };

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockHourly,
      } as Response);

      const result = await forecastApi.getHourlyForecast('Bengaluru', { hours: 24 });
      expect(result.hours).toBe(24);
      expect(result.forecasts[0].predicted_aqi).toBe(68);
    });
  });
});
