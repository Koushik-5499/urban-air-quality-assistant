import type { AQICategory } from './dashboard';

export type AlertSeverity = 'info' | 'moderate' | 'warning' | 'critical' | 'severe';

export interface AirAlert {
  id: string;
  cityId: string;
  city: string;
  state: string;
  country: string;
  station: string;
  aqi: number;
  category: AQICategory;
  severity: AlertSeverity;
  title: string;
  description: string;
  recommendedAction: string;
  dominantPollutant: string;
  timestamp: string;
  dateFormatted: string;
  isRead: boolean;
  isDismissed: boolean;
  isSimulated: boolean;
}

export interface AlertFilterState {
  severity: 'all' | AlertSeverity;
  cityId: string;
  status: 'all' | 'unread' | 'read';
  searchQuery: string;
  sortBy: 'newest' | 'oldest' | 'severity';
}

export interface NotificationPreferences {
  notificationsEnabled: boolean;
  criticalAlerts: boolean;
  unhealthyAlerts: boolean;
  moderateAlerts: boolean;
  goodReports: boolean;
  frequency: 'immediate' | 'daily' | 'weekly';
  quietHours: boolean;
  soundEnabled: boolean;
}

