import { useState, useMemo, useCallback, useEffect } from 'react';
import { useLocation } from '../hooks/useLocation';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { AlertsHeaderAndTabs, type AlertsTab } from '../components/alerts/AlertsHeaderAndTabs';
import { AlertSummaryCards } from '../components/alerts/AlertSummaryCards';
import { AlertFilters } from '../components/alerts/AlertFilters';
import { AlertList } from '../components/alerts/AlertList';
import { AlertDetailsModal } from '../components/alerts/AlertDetailsModal';
import { ClearAlertsModal } from '../components/alerts/ClearAlertsModal';
import { NotificationPreferences } from '../components/alerts/NotificationPreferences';
import { MonitoredCities } from '../components/alerts/MonitoredCities';
import { DEMO_LOCATIONS } from '../data/dashboardData';
import {
  loadSavedAlerts,
  saveAlerts,
  loadNotificationPreferences,
  saveNotificationPreferences,
  loadMonitoredCities,
} from '../services/alertService';
import { alertsApi } from '../services/api/alertsApi';
import type { AlertResponse } from '../services/api/types';
import type { AirAlert, AlertFilterState, AlertSeverity, NotificationPreferences as PrefsType } from '../types/alerts';
import type { AQICategory } from '../types/dashboard';

function mapBackendAlertToAirAlert(alt: AlertResponse): AirAlert {
  const cityLower = (alt.city_name || 'delhi').toLowerCase();
  const matchedLoc = DEMO_LOCATIONS.find(
    (l) => l.city.toLowerCase() === cityLower || l.id === cityLower
  );

  const rawSeverity = alt.severity?.toLowerCase() || 'moderate';
  let severity: AlertSeverity = 'moderate';
  if (rawSeverity === 'critical') severity = 'critical';
  else if (rawSeverity === 'high' || rawSeverity === 'severe') severity = 'warning';
  else if (rawSeverity === 'low') severity = 'info';

  const category: AQICategory = (alt.aqi_category as AQICategory) || 'Moderate';

  return {
    id: String(alt.id),
    cityId: matchedLoc?.id || cityLower,
    city: alt.city_name || 'Regional Monitoring Area',
    state: matchedLoc?.state || 'India',
    country: 'India',
    station: alt.station_name || matchedLoc?.station || 'Urban Air Monitoring Station',
    aqi: alt.current_aqi || 100,
    category,
    severity,
    title: alt.title,
    description: alt.description,
    recommendedAction: 'Limit strenuous outdoor activities and wear an N95 mask.',
    dominantPollutant: alt.dominant_pollutant || 'PM2.5',
    timestamp: new Date(alt.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    dateFormatted: new Date(alt.created_at).toLocaleDateString(),
    isRead: alt.is_read,
    isDismissed: false,
    isSimulated: alt.is_simulated,
  };
}

function Alerts() {
  useDocumentTitle('Alerts & Notifications — Urban Air Quality Assistant');

  const { selectedCityId, setSelectedCityId, selectedCityData } = useLocation();
  const [activeTab, setActiveTab] = useState<AlertsTab>('feed');
  const [alerts, setAlerts] = useState<AirAlert[]>(() => loadSavedAlerts());
  const [preferences, setPreferences] = useState<PrefsType>(() => loadNotificationPreferences());
  const [monitoredCityIds, setMonitoredCityIds] = useState<string[]>(() => loadMonitoredCities());
  const [selectedAlertForModal, setSelectedAlertForModal] = useState<AirAlert | null>(null);
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);

  const [filters, setFilters] = useState<AlertFilterState>({
    severity: 'all',
    cityId: 'all',
    status: 'all',
    searchQuery: '',
    sortBy: 'newest',
  });

  useEffect(() => {
    let isMounted = true;
    alertsApi
      .listAlerts({ page_size: 20 })
      .then((data) => {
        if (!isMounted) return;
        if (data && data.alerts && data.alerts.length > 0) {
          const mapped = data.alerts.map(mapBackendAlertToAirAlert);
          setAlerts(mapped);
          saveAlerts(mapped);
        }
      })
      .catch(() => {
        // Retain saved alerts on failure
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const updateAlerts = useCallback((updater: (prev: AirAlert[]) => AirAlert[]) => {
    setAlerts((prev) => {
      const updated = updater(prev);
      saveAlerts(updated);
      return updated;
    });
  }, []);

  const handleToggleRead = (alertId: string) => {
    const numId = Number(alertId);
    if (!isNaN(numId)) {
      alertsApi.markAlertRead(numId).catch(() => {});
    }
    updateAlerts((prev) =>
      prev.map((alt) => (alt.id === alertId ? { ...alt, isRead: !alt.isRead } : alt))
    );
  };

  const handleDismiss = (alertId: string) => {
    updateAlerts((prev) => prev.filter((alt) => alt.id !== alertId));
  };

  const handleMarkAllRead = () => {
    alertsApi.markAllRead().catch(() => {});
    updateAlerts((prev) => prev.map((alt) => ({ ...alt, isRead: true })));
  };

  const handleConfirmClearAll = () => {
    updateAlerts(() => []);
  };

  const handleResetFilters = () => {
    setFilters({
      severity: 'all',
      cityId: 'all',
      status: 'all',
      searchQuery: '',
      sortBy: 'newest',
    });
  };

  const handlePreferencesChange = (newPrefs: PrefsType) => {
    setPreferences(newPrefs);
    saveNotificationPreferences(newPrefs);
  };

  const filteredAlerts = useMemo(() => {
    return alerts
      .filter((alt) => {
        if (filters.severity !== 'all' && alt.severity !== filters.severity) return false;
        if (filters.cityId !== 'all' && alt.cityId !== filters.cityId) return false;
        if (filters.status === 'unread' && alt.isRead) return false;
        if (filters.status === 'read' && !alt.isRead) return false;
        if (filters.searchQuery.trim()) {
          const q = filters.searchQuery.toLowerCase().trim();
          const matches =
            alt.title.toLowerCase().includes(q) ||
            alt.city.toLowerCase().includes(q) ||
            alt.state.toLowerCase().includes(q) ||
            alt.description.toLowerCase().includes(q) ||
            alt.dominantPollutant.toLowerCase().includes(q);
          if (!matches) return false;
        }
        return true;
      })
      .sort((a, b) => {
        if (filters.sortBy === 'severity') {
          const order: Record<AlertSeverity, number> = {
            critical: 5,
            severe: 4,
            warning: 3,
            moderate: 2,
            info: 1,
          };
          return (order[b.severity] || 0) - (order[a.severity] || 0);
        }
        if (filters.sortBy === 'oldest') {
          return a.id.localeCompare(b.id);
        }
        return b.id.localeCompare(a.id);
      });
  }, [alerts, filters]);

  const unreadCount = useMemo(() => alerts.filter((a) => !a.isRead).length, [alerts]);
  const criticalCount = useMemo(
    () => alerts.filter((a) => a.severity === 'critical' || a.severity === 'severe').length,
    [alerts]
  );

  const isFiltered =
    filters.severity !== 'all' ||
    filters.cityId !== 'all' ||
    filters.status !== 'all' ||
    filters.searchQuery.trim() !== '' ||
    filters.sortBy !== 'newest';

  const latestAlertsPerCity = useMemo(() => {
    const map: Record<string, string> = {};
    alerts.forEach((alt) => {
      if (!map[alt.cityId]) {
        map[alt.cityId] = alt.title;
      }
    });
    return map;
  }, [alerts]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 animate-in fade-in duration-300">
      <AlertsHeaderAndTabs
        activeCityName={selectedCityData.location.city}
        activeTab={activeTab}
        onTabChange={setActiveTab}
        unreadCount={unreadCount}
        monitoredCount={monitoredCityIds.length}
        totalCitiesCount={DEMO_LOCATIONS.length}
      />

      <AlertSummaryCards
        totalAlerts={alerts.length}
        unreadAlerts={unreadCount}
        criticalAlerts={criticalCount}
        monitoredCitiesCount={monitoredCityIds.length}
        totalCitiesCount={DEMO_LOCATIONS.length}
      />

      {activeTab === 'feed' && (
        <div className="space-y-4">
          <AlertFilters
            searchQuery={filters.searchQuery}
            onSearchChange={(q) => setFilters((prev) => ({ ...prev, searchQuery: q }))}
            selectedSeverity={filters.severity}
            onSeverityChange={(s) => setFilters((prev) => ({ ...prev, severity: s }))}
            selectedCityId={filters.cityId}
            onCityChange={(c) => setFilters((prev) => ({ ...prev, cityId: c }))}
            selectedStatus={filters.status}
            onStatusChange={(st) => setFilters((prev) => ({ ...prev, status: st }))}
            sortBy={filters.sortBy}
            onSortByChange={(s) => setFilters((prev) => ({ ...prev, sortBy: s }))}
            availableCities={DEMO_LOCATIONS.map((l) => ({ id: l.id, name: l.city }))}
            onResetFilters={handleResetFilters}
            isFiltered={isFiltered}
            totalFilteredCount={filteredAlerts.length}
          />

          <AlertList
            alerts={filteredAlerts}
            unreadCount={unreadCount}
            onToggleRead={handleToggleRead}
            onDismiss={handleDismiss}
            onViewDetails={(alt) => setSelectedAlertForModal(alt)}
            onMarkAllRead={handleMarkAllRead}
            onClearAll={() => setIsClearModalOpen(true)}
            onResetFilters={handleResetFilters}
          />
        </div>
      )}

      {activeTab === 'preferences' && (
        <NotificationPreferences
          preferences={preferences}
          onPreferencesChange={handlePreferencesChange}
        />
      )}

      {activeTab === 'cities' && (
        <MonitoredCities
          monitoredCityIds={monitoredCityIds}
          onMonitoredCityChange={(updated) => setMonitoredCityIds(updated)}
          activeDashboardCityId={selectedCityId}
          onSelectForDashboard={(cId) => setSelectedCityId(cId)}
          latestAlerts={latestAlertsPerCity}
        />
      )}

      <AlertDetailsModal
        alert={selectedAlertForModal}
        isOpen={Boolean(selectedAlertForModal)}
        onClose={() => setSelectedAlertForModal(null)}
        onToggleRead={handleToggleRead}
        onDismiss={handleDismiss}
        onSelectForDashboard={(cId) => setSelectedCityId(cId)}
        isActiveDashboardCity={selectedAlertForModal?.cityId === selectedCityId}
      />

      <ClearAlertsModal
        isOpen={isClearModalOpen}
        onClose={() => setIsClearModalOpen(false)}
        onConfirm={handleConfirmClearAll}
      />
    </div>
  );
}

export { Alerts, Alerts as AlertsPage };
export default Alerts;
