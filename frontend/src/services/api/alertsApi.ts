import { api } from './client';
import { API_ENDPOINTS } from './endpoints';
import { API_SETTINGS } from './config';
import type {
  AlertPaginatedResponse,
  AlertUnreadCountResponse,
  AlertResponse,
  AlertPreferenceResponse,
  AlertPreferenceCreate,
  AlertStatusResponse,
} from './types';

export const alertsApi = {
  /**
   * Retrieves paginated air quality alerts with optional filtering.
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
    userId: string = API_SETTINGS.defaultUserId,
    signal?: AbortSignal
  ): Promise<AlertPaginatedResponse> =>
    api.get<AlertPaginatedResponse>(API_ENDPOINTS.alerts.list, {
      params,
      headers: { 'X-User-Id': userId },
      signal,
    }),

  /**
   * Retrieves count of unread alerts for a user.
   */
  getUnreadCount: (
    userId: string = API_SETTINGS.defaultUserId,
    signal?: AbortSignal
  ): Promise<AlertUnreadCountResponse> =>
    api.get<AlertUnreadCountResponse>(API_ENDPOINTS.alerts.unreadCount, {
      headers: { 'X-User-Id': userId },
      signal,
    }),

  /**
   * Marks a single alert as read.
   */
  markAlertRead: (alertId: number, signal?: AbortSignal): Promise<AlertResponse> =>
    api.patch<AlertResponse>(API_ENDPOINTS.alerts.markRead(alertId), undefined, { signal }),

  /**
   * Marks all alerts as read for a user.
   */
  markAllRead: (
    userId: string = API_SETTINGS.defaultUserId,
    signal?: AbortSignal
  ): Promise<{ updated_count: number }> =>
    api.patch<{ updated_count: number }>(API_ENDPOINTS.alerts.markAllRead, undefined, {
      headers: { 'X-User-Id': userId },
      signal,
    }),

  /**
   * Retrieves alert notification preferences for a user.
   */
  getPreferences: (
    userId: string = API_SETTINGS.defaultUserId,
    signal?: AbortSignal
  ): Promise<AlertPreferenceResponse> =>
    api.get<AlertPreferenceResponse>(API_ENDPOINTS.alerts.preferences, {
      headers: { 'X-User-Id': userId },
      signal,
    }),

  /**
   * Updates or creates alert notification preferences for a user.
   */
  updatePreferences: (
    preferences: AlertPreferenceCreate,
    userId: string = API_SETTINGS.defaultUserId,
    signal?: AbortSignal
  ): Promise<AlertPreferenceResponse> =>
    api.put<AlertPreferenceResponse>(API_ENDPOINTS.alerts.preferences, preferences, {
      headers: { 'X-User-Id': userId },
      signal,
    }),

  /**
   * Retrieves delivery engine status and enabled channels.
   */
  getStatus: (signal?: AbortSignal): Promise<AlertStatusResponse> =>
    api.get<AlertStatusResponse>(API_ENDPOINTS.alerts.status, { signal }),
};

