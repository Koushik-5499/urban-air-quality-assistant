import { useState, useMemo, useCallback, useEffect } from 'react';
import {
  Bell,
  Sliders,
  Building2,
  Sparkles,
  ExternalLink,
} from 'lucide-react';
import { useLocation } from '../hooks/useLocation';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { DataProvenanceBadge } from '../components/common/DataProvenanceBadge';
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
import { Link } from 'react-router-dom';

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

  // Active view tab
  const [activeTab, setActiveTab] = useState<'feed' | 'preferences' | 'cities'>('feed');

  // Alerts state loaded from localStorage initially
  const [alerts, setAlerts] = useState<AirAlert[]>(() => loadSavedAlerts());

  // Preferences state
  const [preferences, setPreferences] = useState<PrefsType>(() => loadNotificationPreferences());

  // Monitored city IDs
  const [monitoredCityIds, setMonitoredCityIds] = useState<string[]>(() => loadMonitoredCities());

  // Modal states
  const [selectedAlertForModal, setSelectedAlertForModal] = useState<AirAlert | null>(null);
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);

  // Filters state
  const [filters, setFilters] = useState<AlertFilterState>({
    severity: 'all',
    cityId: 'all',
    status: 'all',
    searchQuery: '',
    sortBy: 'newest',
  });

  // Query Backend for Live Alerts on Mount
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

  // Save alerts wrapper
  const updateAlerts = useCallback((updater: (prev: AirAlert[]) => AirAlert[]) => {
    setAlerts((prev) => {
      const updated = updater(prev);
      saveAlerts(updated);
      return updated;
    });
  }, []);

  // Handlers for individual alerts
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

  // Filtered & sorted alerts
  const filteredAlerts = useMemo(() => {
    return alerts
      .filter((alt) => {
        // Severity filter
        if (filters.severity !== 'all' && alt.severity !== filters.severity) {
          return false;
        }

        // City filter
        if (filters.cityId !== 'all' && alt.cityId !== filters.cityId) {
          return false;
        }

        // Read/unread status
        if (filters.status === 'unread' && alt.isRead) return false;
        if (filters.status === 'read' && !alt.isRead) return false;

        // Search query
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
        // Default: newest
        return b.id.localeCompare(a.id);
      });
  }, [alerts, filters]);

  // Overall Unread Count
  const unreadCount = useMemo(() => alerts.filter((a) => !a.isRead).length, [alerts]);

  // Critical Alerts Count
  const criticalCount = useMemo(
    () => alerts.filter((a) => a.severity === 'critical' || a.severity === 'severe').length,
    [alerts]
  );

  // Filter Active Check
  const isFiltered =
    filters.severity !== 'all' ||
    filters.cityId !== 'all' ||
    filters.status !== 'all' ||
    filters.searchQuery.trim() !== '' ||
    filters.sortBy !== 'newest';

  // Latest Alert per City for Monitored Cities section (Record<string, string>)
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
      {/* 1. Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="p-2 rounded-xl bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-400 border border-teal-200/60 dark:border-teal-800/60">
              <Bell className="w-5 h-5" aria-hidden="true" />
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Air Quality Alerts & Advisories
            </h1>
            <DataProvenanceBadge />
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 max-w-3xl">
            Real-time environmental threshold notifications, rapid deterioration warnings, and sensitive group advisories for monitored urban regions across India.
          </p>
        </div>

        {/* Global Context Quick Link */}
        <div className="text-xs text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800/60 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700/60 flex items-center gap-1.5 self-start md:self-auto">
          <span>Active City:</span>
          <span className="font-semibold text-slate-800 dark:text-slate-200">
            {selectedCityData.location.city}
          </span>
          <span className="text-slate-300 dark:text-slate-600">•</span>
          <Link
            to="/dashboard"
            className="text-teal-600 dark:text-teal-400 hover:underline inline-flex items-center gap-0.5"
          >
            Dashboard
            <ExternalLink className="w-3 h-3" />
          </Link>
        </div>
      </div>

      {/* 2. Summary Metric Cards */}
      <AlertSummaryCards
        totalAlerts={alerts.length}
        unreadAlerts={unreadCount}
        criticalAlerts={criticalCount}
        monitoredCitiesCount={monitoredCityIds.length}
        totalCitiesCount={DEMO_LOCATIONS.length}
      />

      {/* 3. Sub-Navigation Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-2">
        <div className="inline-flex p-1 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs font-semibold self-start">
          <button
            type="button"
            onClick={() => setActiveTab('feed')}
            className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'feed'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Bell className="w-3.5 h-3.5" />
            <span>Alert Feed</span>
            {unreadCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-rose-500 text-white text-[10px] font-bold">
                {unreadCount}
              </span>
            )}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('preferences')}
            className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'preferences'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Threshold Preferences</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('cities')}
            className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'cities'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Monitored Cities ({monitoredCityIds.length}/{DEMO_LOCATIONS.length})</span>
          </button>
        </div>

        <span className="text-xs text-slate-400 flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-teal-600" />
          Synchronized with FastAPI Alert & Notification Engine
        </span>
      </div>

      {/* 4. Tab Content */}
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

      {/* 5. Modals */}
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
