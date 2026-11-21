import { api } from './client';
import { API_ENDPOINTS } from './endpoints';
import type {
  HistoricalAqiResponse,
  HistoricalPollutantResponse,
  HistoricalSummaryResponse,
  HistoricalTrendsResponse,
  LocationComparisonResponse,
} from './types';

export const historyApi = {
  /**
   * Retrieves historical AQI points with configurable aggregation interval.
   */
  getAqiHistory: (
    params?: {
      city?: string;
      station_id?: number;
      start_date?: string;
      end_date?: string;
      interval?: 'hourly' | 'daily' | 'monthly';
      page?: number;
      page_size?: number;
      include_simulated?: boolean;
    },
    signal?: AbortSignal
  ): Promise<HistoricalAqiResponse> =>
    api.get<HistoricalAqiResponse>(API_ENDPOINTS.history.aqi, { params, signal }),

  /**
   * Retrieves historical pollutant concentrations and sub-indices over time.
   */
  getPollutantHistory: (
    params?: {
      city?: string;
      station_id?: number;
      pollutant?: string;
      start_date?: string;
      end_date?: string;
      interval?: 'hourly' | 'daily' | 'monthly';
      page?: number;
      page_size?: number;
      include_simulated?: boolean;
    },
    signal?: AbortSignal
  ): Promise<HistoricalPollutantResponse> =>
    api.get<HistoricalPollutantResponse>(API_ENDPOINTS.history.pollutants, { params, signal }),

  /**
   * Generates statistical summary metrics (min, max, mean, distribution).
   */
  getSummary: (
    params?: {
      city?: string;
      station_id?: number;
      start_date?: string;
      end_date?: string;
      include_simulated?: boolean;
    },
    signal?: AbortSignal
  ): Promise<HistoricalSummaryResponse> =>
    api.get<HistoricalSummaryResponse>(API_ENDPOINTS.history.summary, { params, signal }),

  /**
   * Evaluates air quality trend direction and rate of change.
   */
  getTrends: (
    params?: {
      city?: string;
      station_id?: number;
      pollutant?: string;
      start_date?: string;
      end_date?: string;
      interval?: string;
      threshold?: number;
      min_records_per_period?: number;
      include_simulated?: boolean;
    },
    signal?: AbortSignal
  ): Promise<HistoricalTrendsResponse> =>
    api.get<HistoricalTrendsResponse>(API_ENDPOINTS.history.trends, { params, signal }),

  /**
   * Compares air quality between multiple cities or stations over time.
   */
  compareLocations: (
    params: {
      cities?: string[];
      stations?: number[];
      start_date?: string;
      end_date?: string;
      include_simulated?: boolean;
    },
    signal?: AbortSignal
  ): Promise<LocationComparisonResponse> =>
    api.get<LocationComparisonResponse>(API_ENDPOINTS.history.compare, {
      params: {
        cities: params.cities,
        stations: params.stations,
        start_date: params.start_date,
        end_date: params.end_date,
        include_simulated: params.include_simulated,
      },
      signal,
    }),
};

