import { DEMO_LOCATIONS, DASHBOARD_DATA } from './dashboardData';
import type { MapCityData } from '../types/map';
import type { AQICategory } from '../types/dashboard';

export const MAP_DEFAULT_CENTER: [number, number] = [20.5937, 78.9629];
export const MAP_DEFAULT_ZOOM = 5;

export const MAP_CITIES: MapCityData[] = DEMO_LOCATIONS.map((loc) => {
  const dash = DASHBOARD_DATA[loc.id] || DASHBOARD_DATA['coimbatore'];
  const pm25 = dash.pollutants.find((p) => p.id === 'pm25')?.value ?? 25;
  const pm10 = dash.pollutants.find((p) => p.id === 'pm10')?.value ?? 55;
  const lat = loc.coordinates?.lat ?? 11.0168;
  const lng = loc.coordinates?.lng ?? 76.9558;

  return {
    id: loc.id,
    name: loc.name,
    city: loc.city,
    state: loc.state,
    country: loc.country,
    station: loc.station,
    lat,
    lng,
    aqi: dash.aqi,
    category: dash.category,
    pm25,
    pm10,
    temperature: dash.weather.temperature,
    humidity: dash.weather.humidity,
    dominantPollutant: dash.dominantPollutant,
    lastUpdated: dash.lastUpdated,
    fullData: dash,
  };
});

export function getAQIColor(category: AQICategory | string): string {
  switch (category) {
    case 'Good':
      return '#16A34A'; // Green
    case 'Moderate':
      return '#EAB308'; // Amber/Yellow
    case 'Unhealthy for Sensitive Groups':
      return '#F97316'; // Orange
    case 'Unhealthy':
      return '#DC2626'; // Red
    case 'Very Unhealthy':
      return '#9333EA'; // Purple
    case 'Hazardous':
      return '#7F1D1D'; // Dark Red
    default:
      return '#64748B'; // Slate
  }
}

export function getAQIBadgeVariant(category: AQICategory | string): 'success' | 'warning' | 'danger' | 'default' {
  switch (category) {
    case 'Good':
      return 'success';
    case 'Moderate':
      return 'warning';
    case 'Unhealthy for Sensitive Groups':
    case 'Unhealthy':
    case 'Very Unhealthy':
    case 'Hazardous':
      return 'danger';
    default:
      return 'default';
  }
}

