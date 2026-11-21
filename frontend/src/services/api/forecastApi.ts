import { api } from './client';
import { API_ENDPOINTS } from './endpoints';
import type {
  ForecastListResponse,
  HourlyForecastResponse,
  DailyForecastResponse,
  ForecastHistoryResponse,
  ModelStatusResponse,
} from './types';

export const forecastApi = {
  /**
   * Retrieves standard AQI predictions for supported horizons (1h, 6h, 12h, 24h, 48h, 72h).
   */
  getForecast: (
    city: string,
    params?: {
      station_id?: number;
      horizon?: string;
      include_uncertainty?: boolean;
    },
    signal?: AbortSignal
  ): Promise<ForecastListResponse> =>
    api.get<ForecastListResponse>(API_ENDPOINTS.forecast.aqi, {
      params: { city, ...params },
      signal,
    }),

  /**
   * Retrieves step-by-step hourly forecasts up to the requested hours.
   */
  getHourlyForecast: (
    city: string,
    params?: { station_id?: number; hours?: number },
    signal?: AbortSignal
  ): Promise<HourlyForecastResponse> =>
    api.get<HourlyForecastResponse>(API_ENDPOINTS.forecast.hourly, {
      params: { city, ...params },
      signal,
    }),

  /**
   * Retrieves day-by-day aggregated multi-day forecast summaries.
   */
  getDailyForecast: (
    city: string,
    params?: { station_id?: number; days?: number },
    signal?: AbortSignal
  ): Promise<DailyForecastResponse> =>
    api.get<DailyForecastResponse>(API_ENDPOINTS.forecast.daily, {
      params: { city, ...params },
      signal,
    }),

  /**
   * Retrieves forecast run execution audit log and historical runs.
   */
  getForecastHistory: (
    city: string,
    params?: { station_id?: number; limit?: number },
    signal?: AbortSignal
  ): Promise<ForecastHistoryResponse> =>
    api.get<ForecastHistoryResponse>(API_ENDPOINTS.forecast.history, {
      params: { city, ...params },
      signal,
    }),

  /**
   * Retrieves ML forecasting model metadata, baseline comparisons, and error metrics.
   */
  getModelStatus: (
    city?: string,
    signal?: AbortSignal
  ): Promise<ModelStatusResponse> =>
    api.get<ModelStatusResponse>(API_ENDPOINTS.forecast.modelStatus, {
      params: { city },
      signal,
    }),
};

