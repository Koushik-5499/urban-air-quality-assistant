import type { CityDashboardData, AQICategory } from './dashboard';

export type LocationFilter = 'all' | 'good' | 'moderate' | 'unhealthy';
export type LocationSort = 'name' | 'aqi-asc' | 'aqi-desc' | 'pm25-desc';

export interface CitySummaryItem {
  id: string;
  name: string;
  city: string;
  state: string;
  country: string;
  station: string;
  aqi: number;
  category: AQICategory;
  pm25: number;
  pm10: number;
  temperature: number;
  humidity: number;
  windSpeed: number;
  lastUpdated: string;
}

export interface CityComparisonData {
  city: string;
  aqi: number;
  pm25: number;
  pm10: number;
  category: AQICategory;
  color: string;
}

export interface LocationSearchResult {
  city: CityDashboardData;
  matchedFields: ('name' | 'city' | 'state' | 'country')[];
}

