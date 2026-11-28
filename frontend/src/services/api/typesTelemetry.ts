/**
 * Telemetry, AQI calculation, historical analytics, and AI health advisor API schemas.
 */

export interface PollutantDetail {
  code: string;
  concentration: number;
  unit: string;
  measured_at: string;
  source: string;
}

export interface CityAirQualityResponse {
  city_id: number;
  city_name: string;
  state: string;
  country: string;
  data_available: boolean;
  source: string;
  is_simulated: boolean;
  is_stale: boolean;
  data_age_seconds: number | null;
  measured_at: string | null;
  fetched_at: string;
  pollutants: PollutantDetail[];
  active_stations_count: number;
  message: string | null;
}

export interface CityAvailabilitySummary {
  city_id: number;
  city_name: string;
  state: string;
  country: string;
  data_available: boolean;
  last_measured_at: string | null;
  is_stale: boolean;
  station_count: number;
  source: string;
}

export interface SourceStatusResponse {
  provider_name: string;
  dataset_title: string;
  publisher: string;
  license: string;
  base_url: string;
}

export interface StationResponse {
  id: number;
  station_name: string;
  external_station_id?: string | null;
  city_id: number;
  city_name: string;
  latitude: number | null;
  longitude: number | null;
  provider: string;
  is_active: boolean;
}

export interface PollutantSubIndexResult {
  pollutant_code: string;
  concentration: number;
  unit: string;
  sub_index: number | null;
  category: string | null;
  averaging_period: string;
  is_valid: boolean;
  validation_error: string | null;
}

export interface AQICalculationResponse {
  city_id: number;
  city_name: string;
  station_id: number | null;
  station_name: string | null;
  aqi: number | null;
  category: string | null;
  dominant_pollutant: string | null;
  pollutant_subindices: Record<string, PollutantSubIndexResult>;
  measurement_timestamp: string | null;
  calculated_at: string;
  source: string;
  is_simulated: boolean;
  data_quality: 'sufficient' | 'insufficient_data' | 'invalid_input';
  averaging_period: string;
  available_pollutants: string[];
  missing_pollutants: string[];
  explanation: string;
}

export interface HistoricalAqiPoint {
  timestamp: string;
  aqi: number;
  category: string;
  dominant_pollutant: string | null;
  source: string;
  is_simulated: boolean;
}

export interface HistoricalAqiResponse {
  city: string;
  station_id: number | null;
  interval: string;
  total_records: number;
  records: HistoricalAqiPoint[];
}

export interface HistoricalPollutantPoint {
  timestamp: string;
  pollutant_code: string;
  average: number;
  minimum?: number;
  maximum?: number;
  unit: string;
  sub_index: number | null;
  sub_index_category: string | null;
}

export interface HistoricalPollutantResponse {
  city: string;
  station_id: number | null;
  pollutant: string;
  interval: string;
  total_records: number;
  records: HistoricalPollutantPoint[];
}

export interface HistoricalSummaryResponse {
  city: string;
  station_id: number | null;
  start_date: string | null;
  end_date: string | null;
  record_count: number;
  min_aqi: number | null;
  max_aqi: number | null;
  average_aqi: number | null;
  median_aqi: number | null;
  category_distribution: Record<string, number>;
  dominant_pollutant_distribution: Record<string, number>;
}

export interface HistoricalTrendsResponse {
  city: string;
  station_id: number | null;
  metric: string;
  trend_direction: 'improving' | 'deteriorating' | 'stable' | 'insufficient_data';
  change_rate_per_day: number | null;
  r_squared: number | null;
  start_value: number | null;
  end_value: number | null;
  percent_change: number | null;
  explanation: string;
}

export interface LocationComparisonItem {
  location_name: string;
  city_name: string;
  station_name: string | null;
  record_count: number;
  average_aqi: number | null;
  min_aqi: number | null;
  max_aqi: number | null;
  predominant_category: string | null;
  primary_dominant_pollutant: string | null;
}

export interface LocationComparisonResponse {
  comparison_start: string | null;
  comparison_end: string | null;
  locations_count: number;
  comparison: LocationComparisonItem[];
}

export interface HealthAskMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface HealthAskRequest {
  city: string;
  question: string;
  lifestyle?: string;
  family_context?: string;
  conversation_history?: HealthAskMessage[];
}

export interface HealthRecommendationItem {
  title: string;
  description: string;
  target_group: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  reason: string;
  supporting_source?: string;
}

export interface HealthAskResponse {
  answer: string;
  recommendations: HealthRecommendationItem[];
  aqi_context?: {
    city_name: string;
    station_id?: number | null;
    station_name?: string | null;
    aqi: number;
    category: string;
    dominant_pollutant: string;
    measurement_timestamp: string;
    data_age_seconds: number;
    is_stale: boolean;
    is_simulated: boolean;
    data_source: string;
    trend_direction?: string;
  } | null;
  sources: string[];
  disclaimer: string;
  data_freshness: string;
  response_type: 'ai_generated' | 'knowledge_base_fallback';
  model?: string;
  lifestyle_persona?: string;
  direct_impact_metrics?: string[];
}

export interface HealthRecommendationsResponse {
  city: string;
  aqi: number;
  category: string;
  dominant_pollutant: string;
  generated_at: string;
  recommendations: HealthRecommendationItem[];
  sources: string[];
  disclaimer: string;
}

export interface CategoryGuideline {
  category: string;
  aqi_range: string;
  general_advisory: string;
  sensitive_groups_advisory: string;
  outdoor_activity: string;
  ventilation: string;
}

export interface HealthGuidelinesResponse {
  organization: string;
  standard: string;
  categories: CategoryGuideline[];
}

export interface PollutantExplanationResponse {
  pollutant_code: string;
  name: string;
  formula: string;
  sources: string[];
  health_effects: {
    short_term: string[];
    long_term: string[];
    sensitive_groups: string[];
  };
  who_guideline: string;
  cpcb_standard: string;
  educational_summary: string;
}

export interface HealthStatusResponse {
  ai_enabled: boolean;
  provider: string;
  model: string;
  available: boolean;
  api_key_configured: boolean;
}

