import { api } from './client';
import { API_ENDPOINTS } from './endpoints';
import type {
  HealthAskRequest,
  HealthAskResponse,
  HealthRecommendationsResponse,
  HealthGuidelinesResponse,
  PollutantExplanationResponse,
  HealthStatusResponse,
} from './types';

export interface ImpactMetricPillar {
  pillar: string;
  recommendation: string;
  quantified_impact: string;
  source: string;
  target_groups: string[];
}

export interface ImpactMetricsResponse {
  pillars: ImpactMetricPillar[];
  data_as_of: string;
  disclaimer: string;
}

export const healthApi = {
  /**
   * Interactive conversational health advisor.
   */
  askAssistant: (
    payload: HealthAskRequest,
    signal?: AbortSignal
  ): Promise<HealthAskResponse> =>
    api.post<HealthAskResponse>(API_ENDPOINTS.healthAdvisor.ask, payload, { signal }),

  /**
   * Retrieves structured health recommendations based on current AQI.
   */
  getRecommendations: (
    params: { city: string; station_id?: number },
    signal?: AbortSignal
  ): Promise<HealthRecommendationsResponse> =>
    api.get<HealthRecommendationsResponse>(API_ENDPOINTS.healthAdvisor.recommendations, {
      params,
      signal,
    }),

  /**
   * Retrieves standard NAQI / WHO health guidelines across all AQI categories.
   */
  getGuidelines: (signal?: AbortSignal): Promise<HealthGuidelinesResponse> =>
    api.get<HealthGuidelinesResponse>(API_ENDPOINTS.healthAdvisor.guidelines, { signal }),

  /**
   * Retrieves Challenge 6 winter smog, low-emission routine, indoor hack, and impact guidance.
   */
  getCommunitySolutions: (signal?: AbortSignal): Promise<Record<string, unknown>> =>
    api.get<Record<string, unknown>>(API_ENDPOINTS.healthAdvisor.communitySolutions, { signal }),

  /**
   * Retrieves quantified Challenge 6 health and carbon impact benchmarks.
   */
  getImpactMetrics: (signal?: AbortSignal): Promise<ImpactMetricsResponse> =>
    api.get<ImpactMetricsResponse>(API_ENDPOINTS.healthAdvisor.impactMetrics, { signal }),

  /**
   * Retrieves detailed medical and health impact explanation for a specific pollutant.
   */
  getPollutantExplanation: (
    pollutantCode: string,
    signal?: AbortSignal
  ): Promise<PollutantExplanationResponse> =>
    api.get<PollutantExplanationResponse>(
      API_ENDPOINTS.healthAdvisor.pollutantExplanation(pollutantCode),
      { signal }
    ),

  /**
   * Checks AI provider status, model name, and fallback mode availability.
   */
  getHealthStatus: (signal?: AbortSignal): Promise<HealthStatusResponse> =>
    api.get<HealthStatusResponse>(API_ENDPOINTS.healthAdvisor.status, { signal }),
};

