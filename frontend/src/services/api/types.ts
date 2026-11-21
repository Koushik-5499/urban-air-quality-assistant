/**
 * TypeScript contract interfaces matching FastAPI backend v1 data schemas.
 */

// ---------------------------------------------------------------------------
// Air Quality & City Telemetry Schemas
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// AQI Calculation & NAQI Processing Schemas
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Historical Data Service Schemas
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// AI Health Advisor Schemas
// ---------------------------------------------------------------------------

export interface HealthAskMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface HealthAskRequest {
  city: string;
  question: string;
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

// ---------------------------------------------------------------------------
// Alerts & Notifications Schemas
// ---------------------------------------------------------------------------

export interface AlertResponse {
  id: number;
  city_id: number;
  city_name: string | null;
  station_id: number | null;
  station_name: string | null;
  aqi_reading_id?: number | null;
  title: string;
  description: string;
  severity: string; // 'Low' | 'Moderate' | 'High' | 'Critical'
  alert_type: string;
  current_aqi: number | null;
  previous_aqi: number | null;
  threshold_value: number | null;
  aqi_category: string | null;
  dominant_pollutant: string | null;
  source: string;
  dedup_key: string | null;
  delivery_status: string;
  is_read: boolean;
  is_simulated: boolean;
  created_at: string;
  expires_at: string | null;
}

export interface AlertPaginatedResponse {
  page: number;
  page_size: number;
  total_records: number;
  total_pages: number;
  unread_count: number;
  alerts: AlertResponse[];
}

export interface AlertUnreadCountResponse {
  unread_count: number;
}

export interface AlertPreferenceResponse {
  id: number;
  user_id: string;
  city_id: number;
  city_name: string;
  station_id: number | null;
  station_name: string | null;
  min_aqi_threshold: number;
  min_severity: string;
  is_enabled: boolean;
  channels: string[];
  email: string | null;
  quiet_hours_start: string | null;
  quiet_hours_end: string | null;
  timezone: string;
  created_at: string;
  updated_at: string;
}

export interface AlertPreferenceCreate {
  city: string;
  station_id?: number | null;
  min_aqi_threshold?: number;
  min_severity?: string;
  is_enabled?: boolean;
  channels?: string[];
  email?: string | null;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
  timezone?: string;
}

export interface AlertStatusResponse {
  alerts_enabled: boolean;
  last_processed_at: string | null;
  last_processing_result: string | null;
  enabled_channels: string[];
  providers: {
    in_app: boolean;
    email: boolean;
    web_push: boolean;
  };
}

// ---------------------------------------------------------------------------
// Air Quality Forecasting Schemas
// ---------------------------------------------------------------------------

export interface AQIForecastItem {
  city: string;
  station_id?: number | null;
  station_name?: string | null;
  forecast_timestamp: string;
  generated_at: string;
  predicted_aqi: number;
  predicted_category: string;
  dominant_pollutant: string | null;
  horizon_hours: number;
  horizon_label: string;
  lower_bound: number | null;
  upper_bound: number | null;
  uncertainty_status: string;
  model_name: string;
  model_version: string;
  training_data_start: string | null;
  training_data_end: string | null;
  training_samples: number;
  data_quality: string;
  source: string;
  is_simulated: boolean;
  is_forecast: boolean;
  forecast_status: string;
}

export interface ForecastListResponse {
  city: string;
  station_id: number | null;
  station_name: string | null;
  generated_at: string;
  model_name: string;
  model_version: string;
  forecasts: AQIForecastItem[];
  total_horizons: number;
  data_quality: string;
  weather_integrated: boolean;
}

export interface HourlyForecastResponse {
  city: string;
  station_id: number | null;
  station_name: string | null;
  hours: number;
  generated_at: string;
  forecasts: AQIForecastItem[];
}

export interface DailyForecastSummary {
  date: string;
  min_predicted_aqi: number;
  max_predicted_aqi: number;
  average_predicted_aqi: number;
  predominant_category: string;
  dominant_pollutant: string | null;
  forecast_points_count: number;
  lower_bound: number | null;
  upper_bound: number | null;
}

export interface DailyForecastResponse {
  city: string;
  station_id: number | null;
  station_name: string | null;
  days: number;
  generated_at: string;
  summaries: DailyForecastSummary[];
}

export interface ForecastRunSummary {
  id: number;
  city_name: string;
  station_name: string | null;
  model_name: string;
  model_version: string;
  generated_at: string;
  training_samples: number;
  evaluation_mae: number | null;
  evaluation_rmse: number | null;
  evaluation_mape: number | null;
  is_simulated: boolean;
  status: string;
  forecast_count: number;
}

export interface ForecastHistoryResponse {
  city: string;
  station_id: number | null;
  total_runs: number;
  runs: ForecastRunSummary[];
}

export interface ModelEvaluationMetric {
  horizon_hours: number;
  sample_count: number;
  mae: number;
  rmse: number;
  mape: number | null;
}

export interface ModelStatusResponse {
  model_name: string;
  model_version: string;
  is_ready: boolean;
  active_provider: string;
  training_data_coverage_hours: number | null;
  training_sample_count: number;
  latest_training_timestamp: string | null;
  supported_horizons: string[];
  baseline_comparison: Record<string, unknown>;
  evaluation_metrics: ModelEvaluationMetric[];
  weather_integration_status: Record<string, unknown>;
}

