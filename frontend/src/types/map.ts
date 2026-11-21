import type { AQICategory, CityDashboardData } from './dashboard';

export interface MapCityData {
  id: string;
  name: string;
  city: string;
  state: string;
  country: string;
  station: string;
  lat: number;
  lng: number;
  aqi: number;
  category: AQICategory;
  pm25: number;
  pm10: number;
  temperature: number;
  humidity: number;
  dominantPollutant: string;
  lastUpdated: string;
  fullData: CityDashboardData;
}

export interface MapFilterState {
  category: 'all' | AQICategory;
  state: string;
  searchQuery: string;
  showHeatmap: boolean;
  showMarkers: boolean;
}

