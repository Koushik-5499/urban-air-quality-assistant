import { api } from './client';
import { API_ENDPOINTS } from './endpoints';
import type {
  AlertPaginatedResponse,
  AlertResponse,
  AlertStatusResponse,
} from './types';

export const alertsApi = {
  /**
   * Retrieves paginated air quality alerts with optional filtering.
   * Public endpoint - no user account, user ID, or identity header required.
   */
  listAlerts: (
    params?: {
      city?: string;
      station_id?: number;
      severity?: string;
      is_read?: boolean;
      start_date?: string;
      end_date?: string;
      is_simulated?: boolean;
      page?: number;
      page_size?: number;
    },
    signal?: AbortSignal
  ): Promise<AlertPaginatedResponse> =>
    api.get<AlertPaginatedResponse>(API_ENDPOINTS.alerts.list, {
      params,
      signal,
    }),

  /**
   * Marks a single alert as read locally in the UI session.
   * Note: Remote per-user mutation endpoints are retired in public mode.
   */
  markAlertRead: async (alertId: number): Promise<AlertResponse> => {
    return {
      id: alertId,
      city_id: 0,
      city_name: null,
      station_id: null,
      station_name: null,
      title: '',
      description: '',
      severity: 'Low',
      alert_type: 'threshold_breach',
      current_aqi: null,
      previous_aqi: null,
      threshold_value: null,
      aqi_category: null,
      dominant_pollutant: null,
      source: 'public',
      dedup_key: null,
      delivery_status: 'delivered',
      is_read: true,
      is_simulated: false,
      created_at: new Date().toISOString(),
      expires_at: null,
    };
  },

  /**
   * Marks all alerts as read locally in the UI session.
   * Note: Remote per-user mutation endpoints are retired in public mode.
   */
  markAllRead: async (): Promise<{ updated_count: number }> => {
    return { updated_count: 0 };
  },

  /**
   * Retrieves delivery engine status and enabled channels.
   */
  getStatus: (signal?: AbortSignal): Promise<AlertStatusResponse> =>
    api.get<AlertStatusResponse>(API_ENDPOINTS.alerts.status, { signal }),
};

