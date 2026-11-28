/**
 * Alerts, notification preferences, and AQI forecasting API schemas.
 */

export interface AlertResponse {
  id: number;
  city_id: number;
  city_name: string | null;
  station_id: number | null;
  station_name: string | null;
  aqi_reading_id?: number | null;
  title: string;
  description: string;
  severity: string;
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

