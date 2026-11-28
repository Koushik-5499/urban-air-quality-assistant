import { useState, useCallback } from 'react';
import { AlertTriangle, RefreshCw, CheckCircle2, Info, Radio } from 'lucide-react';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useLocation } from '../hooks/useLocation';
import { DashboardHeader } from '../components/dashboard/DashboardHeader';
import { AQIOverviewCard } from '../components/dashboard/AQIOverviewCard';
import { PollutantCard } from '../components/dashboard/PollutantCard';
import { WeatherCard } from '../components/dashboard/WeatherCard';
import { AirQualityChart } from '../components/dashboard/AirQualityChart';
import { HealthRecommendation } from '../components/dashboard/HealthRecommendation';
import { RecentUpdates } from '../components/dashboard/RecentUpdates';
import { DashboardSkeleton } from '../components/dashboard/DashboardSkeleton';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { DataProvenanceBadge } from '../components/common/DataProvenanceBadge';
import type { LocationOption } from '../types/dashboard';

function Dashboard() {
  useDocumentTitle('Dashboard — Air Quality Overview');

  const {
    selectedCityData,
    setSelectedCityId,
    isLiveBackend,
    isLoadingLive,
    liveError,
    isSimulated,
    isStale,
    refreshLiveData,
  } = useLocation();

  const [isRefreshing, setIsRefreshing] = useState(false);

  // Handle location change
  const handleLocationChange = useCallback(
    (newLocation: LocationOption) => {
      setSelectedCityId(newLocation.id);
    },
    [setSelectedCityId]
  );

  // Handle manual refresh triggering live backend fetch
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await refreshLiveData();
    } finally {
      setIsRefreshing(false);
    }
  }, [refreshLiveData]);

  const showSkeleton = isLoadingLive || isRefreshing;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div aria-live="polite" className="sr-only">
        {`Active monitoring city: ${selectedCityData.location.city}. Current AQI: ${selectedCityData.aqi} (${selectedCityData.category}).`}
      </div>
      {/* 1. Header with Location Selector and Refresh */}
      <DashboardHeader
        selectedLocation={selectedCityData.location}
        onLocationChange={handleLocationChange}
        lastUpdated={selectedCityData.lastUpdated}
        isRefreshing={showSkeleton}
        onRefresh={handleRefresh}
      />

      {/* Backend Integration Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          {isLiveBackend ? (
            <Badge variant="success" size="sm" className="flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Live Backend Connected</span>
            </Badge>
          ) : (
            <Badge variant="neutral" size="sm" className="flex items-center gap-1.5 font-medium">
              <Radio className="w-3.5 h-3.5 text-slate-500 animate-pulse" />
              <span>Offline / Standalone Mode</span>
            </Badge>
          )}

          {isSimulated && (
            <Badge variant="info" size="sm" className="flex items-center gap-1">
              <Info className="w-3 h-3 text-sky-500" />
              <span>Simulated Data Provider</span>
            </Badge>
          )}

          {isStale && (
            <Badge variant="warning" size="sm" className="flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-amber-500" />
              <span>Stale Observation (&gt; 1h)</span>
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
          <DataProvenanceBadge />
          <span>Engine: CPCB NAQI Standard (2014)</span>
        </div>
      </div>

      {/* Backend Connection Error Notice */}
      {liveError && (
        <div
          role="alert"
          className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 text-amber-900 dark:text-amber-200 text-sm"
        >
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Backend Telemetry Notice</p>
              <p className="text-xs text-amber-800 dark:text-amber-300 mt-0.5">{liveError}</p>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={handleRefresh}
            disabled={showSkeleton}
            className="self-start sm:self-auto shrink-0 border-amber-300 dark:border-amber-700 hover:bg-amber-100 dark:hover:bg-amber-900/40 text-amber-900 dark:text-amber-100"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${showSkeleton ? 'animate-spin' : ''}`} />
            Retry Backend Connection
          </Button>
        </div>
      )}

      {showSkeleton ? (
        <DashboardSkeleton />
      ) : (
        <>
          {/* 2. Top Grid: Main AQI Overview (8 cols) + Weather Telemetry (4 cols) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            <div className="lg:col-span-8 flex flex-col">
              <AQIOverviewCard data={selectedCityData} />
            </div>
            <div className="lg:col-span-4 flex flex-col">
              <WeatherCard
                weather={selectedCityData.weather}
                locationName={selectedCityData.location.name}
              />
            </div>
          </div>

          {/* 3. Pollutant Cards Grid (6 Pollutants: PM2.5, PM10, CO, NO2, SO2, O3) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  Atmospheric Pollutant Concentrations
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {isSimulated
                    ? 'Environmental telemetry (Simulated CPCB observation)'
                    : 'Real-time environmental sensor breakdown (CPCB NAQI telemetry)'}
                </p>
              </div>
              <span className="text-xs text-slate-400 font-medium hidden sm:inline">
                Standard: µg/m³ & mg/m³
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {selectedCityData.pollutants.map((pollutant) => (
                <PollutantCard key={pollutant.id} pollutant={pollutant} />
              ))}
            </div>
          </div>

          {/* 4. Middle Grid: Trend Chart (8 cols) + Health Recommendation (4 cols) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            <div className="lg:col-span-8 flex flex-col">
              <AirQualityChart trends={selectedCityData.trends} />
            </div>
            <div className="lg:col-span-4 flex flex-col">
              <HealthRecommendation
                aqi={selectedCityData.aqi}
                category={selectedCityData.category}
                cityName={selectedCityData.location.city}
              />
            </div>
          </div>

          {/* 5. Bottom Section: Recent Telemetry Updates Log */}
          <div>
            <RecentUpdates updates={selectedCityData.recentUpdates} />
          </div>
        </>
      )}
    </div>
  );
}

export { Dashboard, Dashboard as DashboardPage };
export default Dashboard;
