import { useState, useMemo, useCallback, useEffect } from 'react';
import { BarChart3, Info, MapPin, CheckCircle2 } from 'lucide-react';
import { useLocation } from '../hooks/useLocation';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { Badge } from '../components/ui/Badge';
import { forecastApi } from '../services/api/forecastApi';
import {
  generateHistoricalData,
  calculateAnalyticsSummary,
  calculatePollutantStats,
  generateSimulatedForecast,
  generateAnalyticsInsights,
} from '../services/analyticsService';
import { AnalyticsFilters, type AnalyticsTab } from '../components/analytics/AnalyticsFilters';
import { AnalyticsSummaryCards } from '../components/analytics/AnalyticsSummaryCards';
import { AQITrendChart } from '../components/analytics/AQITrendChart';
import { PollutantTrendChart } from '../components/analytics/PollutantTrendChart';
import { AnalyticsCityComparison } from '../components/analytics/AnalyticsCityComparison';
import { ForecastChart } from '../components/analytics/ForecastChart';
import { AnalyticsInsights } from '../components/analytics/AnalyticsInsights';
import type { AnalyticsTimeRange, ForecastHorizon } from '../types/analytics';
import type { PollutantId } from '../types/dashboard';

export function Analytics() {
  useDocumentTitle('Historical Analytics & Forecasting | Urban Air Quality Assistant');

  const {
    selectedCityId,
    selectedCityData,
    setSelectedCityId,
    allCities,
    comparisonCityIds,
    addComparisonCity,
    removeComparisonCity,
    clearComparison,
  } = useLocation();

  // Filters & Sub-view states
  const [timeRange, setTimeRange] = useState<AnalyticsTimeRange>('24h');
  const [selectedPollutant, setSelectedPollutant] = useState<PollutantId>('pm25');
  const [forecastHorizon, setForecastHorizon] = useState<ForecastHorizon>('24h');
  const [activeTab, setActiveTab] = useState<AnalyticsTab>('overview');

  // Time-range human label
  const timeRangeLabels: Record<AnalyticsTimeRange, string> = {
    '24h': 'Past 24 Hours',
    '7d': 'Past 7 Days',
    '30d': 'Past 30 Days',
    '90d': 'Past 90 Days',
  };

  // 1. Historical series generation (memoized)
  const historicalData = useMemo(() => {
    return generateHistoricalData(selectedCityId, timeRange);
  }, [selectedCityId, timeRange]);

  // 2. Summary statistics calculation (memoized)
  const summary = useMemo(() => {
    return calculateAnalyticsSummary(historicalData, selectedCityData);
  }, [historicalData, selectedCityData]);

  // 3. Pollutant-specific statistics (memoized)
  const pollutantStats = useMemo(() => {
    return calculatePollutantStats(historicalData, selectedPollutant, selectedCityData);
  }, [historicalData, selectedPollutant, selectedCityData]);

  // 4. Deterministic short-term simulated forecast (memoized)
  const forecast = useMemo(() => {
    return generateSimulatedForecast(selectedCityId, forecastHorizon);
  }, [selectedCityId, forecastHorizon]);

  // 5. Data-driven insights generation (memoized)
  const insights = useMemo(() => {
    return generateAnalyticsInsights(selectedCityData, historicalData, summary, allCities);
  }, [selectedCityData, historicalData, summary, allCities]);

  // Reset filters callback
  const handleResetFilters = useCallback(() => {
    setTimeRange('24h');
    setSelectedPollutant('pm25');
    setForecastHorizon('24h');
    setActiveTab('overview');
  }, []);

  // Check Backend Forecasting Service Status
  const [modelReady, setModelReady] = useState(false);
  useEffect(() => {
    let isMounted = true;
    forecastApi
      .getModelStatus(selectedCityData.location.city)
      .then((status) => {
        if (isMounted && status?.is_ready) {
          setModelReady(true);
        }
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, [selectedCityData.location.city]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
              <BarChart3 className="w-6 h-6" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                Historical Analytics & Forecasting
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Empirical telemetry trajectories, particulate dynamics, and deterministic predictive modeling
              </p>
            </div>
          </div>
        </div>

        {/* Badges / Active Station Metadata */}
        <div className="flex flex-wrap items-center gap-2 self-start md:self-auto">
          {modelReady && (
            <Badge variant="success" size="sm" className="flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>LightGBM ML Forecaster Active</span>
            </Badge>
          )}
          <Badge variant="neutral" size="sm" className="flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>
              {selectedCityData.location.city}, {selectedCityData.location.state}
            </span>
          </Badge>
          <Badge variant="info" size="sm" className="flex items-center gap-1">
            <Info className="w-3 h-3" />
            <span>Simulated Telemetry</span>
          </Badge>
        </div>
      </div>

      {/* Global Filter & Tab Controls */}
      <AnalyticsFilters
        selectedCityId={selectedCityId}
        onCityChange={setSelectedCityId}
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
        allCities={allCities}
        onResetFilters={handleResetFilters}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Primary Summary Metric Cards (Shown on overview, trends, pollutants, insights) */}
      {(activeTab === 'overview' || activeTab === 'trends' || activeTab === 'insights') && (
        <AnalyticsSummaryCards
          summary={summary}
          cityName={selectedCityData.location.city}
          timeRangeLabel={timeRangeLabels[timeRange]}
        />
      )}

      {/* Tab: Overview (All Modules Stacked Elegantly) */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Section 1: AQI Trajectory */}
          <AQITrendChart
            data={historicalData}
            timeRange={timeRange}
            onTimeRangeChange={setTimeRange}
            trendDirection={summary.trendDirection}
            trendPercentageChange={summary.trendPercentageChange}
            cityName={selectedCityData.location.city}
          />

          {/* Section 2: Pollutant Historical Analysis */}
          <PollutantTrendChart
            data={historicalData}
            selectedPollutant={selectedPollutant}
            onPollutantChange={setSelectedPollutant}
            stats={pollutantStats}
            timeRangeLabel={timeRangeLabels[timeRange]}
          />

          {/* Section 3: Predictive Simulated Forecast */}
          <ForecastChart
            forecast={forecast}
            currentAQI={selectedCityData.aqi}
            cityName={selectedCityData.location.city}
            horizon={forecastHorizon}
            onHorizonChange={setForecastHorizon}
          />

          {/* Section 4: Multi-City Environmental Comparison */}
          <AnalyticsCityComparison
            comparisonCityIds={comparisonCityIds}
            allCities={allCities}
            onAddCity={addComparisonCity}
            onRemoveCity={removeComparisonCity}
            onClearAll={clearComparison}
            activeDashboardCityId={selectedCityId}
            onSelectForDashboard={setSelectedCityId}
          />

          {/* Section 5: Calculated Insights */}
          <AnalyticsInsights
            insights={insights}
            cityName={selectedCityData.location.city}
            timeRangeLabel={timeRangeLabels[timeRange]}
          />
        </div>
      )}

      {/* Tab: AQI Trends */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          <AQITrendChart
            data={historicalData}
            timeRange={timeRange}
            onTimeRangeChange={setTimeRange}
            trendDirection={summary.trendDirection}
            trendPercentageChange={summary.trendPercentageChange}
            cityName={selectedCityData.location.city}
          />
        </div>
      )}

      {/* Tab: Pollutants */}
      {activeTab === 'pollutants' && (
        <div className="space-y-6">
          <PollutantTrendChart
            data={historicalData}
            selectedPollutant={selectedPollutant}
            onPollutantChange={setSelectedPollutant}
            stats={pollutantStats}
            timeRangeLabel={timeRangeLabels[timeRange]}
          />
        </div>
      )}

      {/* Tab: Forecast */}
      {activeTab === 'forecast' && (
        <div className="space-y-6">
          <ForecastChart
            forecast={forecast}
            currentAQI={selectedCityData.aqi}
            cityName={selectedCityData.location.city}
            horizon={forecastHorizon}
            onHorizonChange={setForecastHorizon}
          />
        </div>
      )}

      {/* Tab: City Comparison */}
      {activeTab === 'comparison' && (
        <div className="space-y-6">
          <AnalyticsCityComparison
            comparisonCityIds={comparisonCityIds}
            allCities={allCities}
            onAddCity={addComparisonCity}
            onRemoveCity={removeComparisonCity}
            onClearAll={clearComparison}
            activeDashboardCityId={selectedCityId}
            onSelectForDashboard={setSelectedCityId}
          />
        </div>
      )}

      {/* Tab: Insights */}
      {activeTab === 'insights' && (
        <div className="space-y-6">
          <AnalyticsInsights
            insights={insights}
            cityName={selectedCityData.location.city}
            timeRangeLabel={timeRangeLabels[timeRange]}
          />
        </div>
      )}
    </div>
  );
}

