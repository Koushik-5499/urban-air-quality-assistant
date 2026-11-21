import { api } from './client';
import { API_ENDPOINTS } from './endpoints';
import type {
  CityAvailabilitySummary,
  CityAirQualityResponse,
  SourceStatusResponse,
  StationResponse,
  AQICalculationResponse,
  PollutantSubIndexResult,
} from './types';

export interface PollutantObservationResponse {
  id: number;
  station_id: number;
  station_name: string;
  city_name: string;
  pollutant_code: string;
  concentration: number;
  unit: string;
  averaging_period: string;
  measured_at: string;
  source: string;
  is_simulated: boolean;
}

export const airQualityApi = {
  /**
   * Retrieves summary availability of all registered Indian cities.
   */
  getCities: (signal?: AbortSignal): Promise<CityAvailabilitySummary[]> =>
    api.get<CityAvailabilitySummary[]>(API_ENDPOINTS.airQuality.cities, { signal }),

  /**
   * Retrieves latest live pollutant observations and metadata for a specific city.
   */
  getCityAirQuality: (cityName: string, signal?: AbortSignal): Promise<CityAirQualityResponse> =>
    api.get<CityAirQualityResponse>(API_ENDPOINTS.airQuality.cityDetails(cityName), { signal }),

  /**
   * Retrieves raw pollutant observations with optional filters.
   */
  getObservations: (
    params?: { city?: string; pollutant?: string; limit?: number },
    signal?: AbortSignal
  ): Promise<PollutantObservationResponse[]> =>
    api.get<PollutantObservationResponse[]>(API_ENDPOINTS.airQuality.observations, {
      params,
      signal,
    }),

  /**
   * Retrieves telemetry data provider and license details.
   */
  getSourceStatus: (signal?: AbortSignal): Promise<SourceStatusResponse> =>
    api.get<SourceStatusResponse>(API_ENDPOINTS.airQuality.sourceStatus, { signal }),

  /**
   * Calculates CPCB NAQI on demand from the latest pollutant observations for a city or station.
   */
  calculateAqi: (
    params?: { city?: string; station_id?: number },
    signal?: AbortSignal
  ): Promise<AQICalculationResponse> =>
    api.get<AQICalculationResponse>(API_ENDPOINTS.aqi.calculate, { params, signal }),

  /**
   * Fetches latest stored AQI reading for a city or station.
   */
  getLatestAqi: (
    params?: { city?: string; station_id?: number },
    signal?: AbortSignal
  ): Promise<AQICalculationResponse> =>
    api.get<AQICalculationResponse>(API_ENDPOINTS.aqi.latest, { params, signal }),

  /**
   * Fetches computed pollutant sub-indices for a city or station.
   */
  getPollutantSubindices: (
    params?: { city?: string; station_id?: number },
    signal?: AbortSignal
  ): Promise<Record<string, PollutantSubIndexResult>> =>
    api.get<Record<string, PollutantSubIndexResult>>(API_ENDPOINTS.aqi.subindices, {
      params,
      signal,
    }),

  /**
   * Retrieves monitoring stations with optional filters.
   */
  getStations: (
    params?: { city?: string; state?: string; provider?: string },
    signal?: AbortSignal
  ): Promise<StationResponse[]> =>
    api.get<StationResponse[]>(API_ENDPOINTS.stations, { params, signal }),
};

