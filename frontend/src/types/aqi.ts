export type AQICategory =
  | 'Good'
  | 'Moderate'
  | 'Unhealthy for Sensitive Groups'
  | 'Unhealthy'
  | 'Very Unhealthy'
  | 'Hazardous';

export interface AQIBand {
  category: AQICategory;
  min: number;
  max: number;
  color: string;
  badgeVariant: 'success' | 'warning' | 'danger' | 'info' | 'default';
  description: string;
}

