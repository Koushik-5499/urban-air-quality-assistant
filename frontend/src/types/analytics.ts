import type { AQICategory, PollutantId } from './dashboard';

export type AnalyticsTimeRange = '24h' | '7d' | '30d' | '90d';

export type ForecastHorizon = '6h' | '12h' | '24h' | '3d';

export type TrendDirection = 'improving' | 'worsening' | 'stable';

export interface HistoricalDataPoint {
  time: string;
  fullDate: string;
  timestamp: number;
  aqi: number;
  category: AQICategory;
  pm25: number; // µg/m³
  pm10: number; // µg/m³
  co: number; // mg/m³
  no2: number; // µg/m³
  so2: number; // µg/m³
  o3: number; // µg/m³
  dominantPollutant: string;
}

export interface ForecastDataPoint {
  time: string;
  label: string;
  timestamp: number;
  predictedAQI: number;
  predictedCategory: AQICategory;
  confidenceLower: number;
  confidenceUpper: number;
  pm25Estimate: number;
  pm10Estimate: number;
}

export interface AnalyticsSummary {
  currentAQI: number;
  currentCategory: AQICategory;
  historicalAverageAQI: number;
  averageCategory: AQICategory;
  highestAQI: number;
  highestAQITime: string;
  lowestAQI: number;
  lowestAQITime: string;
  trendDirection: TrendDirection;
  trendPercentageChange: number;
  mostDominantPollutant: string;
  dominantPollutantFormula: string;
  dominantPollutantFrequency: number; // percentage, e.g. 85
}

export interface PollutantStats {
  pollutantId: PollutantId;
  name: string;
  formula: string;
  current: number;
  average: number;
  min: number;
  max: number;
  unit: string;
  trendDirection: TrendDirection;
  changePercentage: number;
  whoLimit: number;
  naaqsLimit: number;
}

export interface AnalyticsInsightItem {
  id: string;
  type: 'peak' | 'trough' | 'dominant' | 'trend' | 'comparison' | 'pattern';
  title: string;
  description: string;
  severity: 'info' | 'positive' | 'warning' | 'critical';
  metricValue?: string;
  recommendation?: string;
}

export interface ForecastReport {
  horizon: ForecastHorizon;
  dataPoints: ForecastDataPoint[];
  overallCategory: AQICategory;
  direction: 'improving' | 'worsening' | 'stable';
  summary: string;
  precautions: string[];
  averagePredictedAQI: number;
  peakPredictedAQI: number;
  confidenceRangeText: string;
}

export interface AnalyticsFilterState {
  cityId: string;
  timeRange: AnalyticsTimeRange;
  selectedPollutant: PollutantId;
  forecastHorizon: ForecastHorizon;
  activeTab: 'overview' | 'trends' | 'pollutants' | 'forecast' | 'comparison' | 'insights';
}

