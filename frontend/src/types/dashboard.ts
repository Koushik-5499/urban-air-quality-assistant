export type AQICategory =
  | 'Good'
  | 'Moderate'
  | 'Unhealthy for Sensitive Groups'
  | 'Unhealthy'
  | 'Very Unhealthy'
  | 'Hazardous';

export interface LocationCoordinates {
  lat: number;
  lng: number;
}

export interface LocationOption {
  id: string;
  name: string;
  city: string;
  state: string;
  country: string;
  station: string;
  coordinates?: LocationCoordinates;
}

export type PollutantId = 'pm25' | 'pm10' | 'co' | 'no2' | 'so2' | 'o3';

export interface PollutantMetric {
  id: PollutantId;
  name: string;
  formula: string;
  fullName: string;
  value: number;
  unit: string;
  status: string;
  badgeVariant: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'default';
  changePercent: number;
  isIncrease: boolean;
  period: string;
  standardLimit: string;
}

export interface WeatherData {
  temperature: number;
  humidity: number;
  windSpeed: number;
  windDirection: string;
  condition: string;
  pressure: number;
  uvIndex: number;
}

export type ChartTimeRange = '24h' | '7d' | '30d';

export interface TrendDataPoint {
  time: string;
  aqi: number;
  pm25: number;
  pm10: number;
  o3: number;
}

export interface HealthAdvice {
  general: string;
  sensitiveGroups: string;
  outdoorActivity: string;
  protectiveMeasures: string[];
  disclaimer: string;
  winterSmogAdvice?: string;
  lowEmissionRoutines?: string[];
  indoorAirHacks?: string[];
  sustainableAlternatives?: string[];
  impactExplanation?: string;
}

export interface RecentUpdateItem {
  id: string;
  time: string;
  aqi: number;
  category: AQICategory;
  station: string;
  dominantPollutant: string;
}

export interface CityDashboardData {
  location: LocationOption;
  aqi: number;
  category: AQICategory;
  dominantPollutant: string;
  summary: string;
  pollutants: PollutantMetric[];
  weather: WeatherData;
  trends: Record<ChartTimeRange, TrendDataPoint[]>;
  recentUpdates: RecentUpdateItem[];
  lastUpdated: string;
}

