import { MapPin, RotateCcw, Calendar, TrendingUp, Wind, Sparkles, Layers, Lightbulb, LayoutGrid } from 'lucide-react';
import { Button } from '../ui/Button';
import type { CityDashboardData } from '../../types/dashboard';
import type { AnalyticsTimeRange } from '../../types/analytics';

export type AnalyticsTab = 'overview' | 'trends' | 'pollutants' | 'forecast' | 'comparison' | 'insights';

export interface AnalyticsFiltersProps {
  selectedCityId: string;
  onCityChange: (cityId: string) => void;
  timeRange: AnalyticsTimeRange;
  onTimeRangeChange: (range: AnalyticsTimeRange) => void;
  allCities: CityDashboardData[];
  onResetFilters: () => void;
  activeTab: AnalyticsTab;
  onTabChange: (tab: AnalyticsTab) => void;
}

export function AnalyticsFilters({
  selectedCityId,
  onCityChange,
  timeRange,
  onTimeRangeChange,
  allCities,
  onResetFilters,
  activeTab,
  onTabChange,
}: AnalyticsFiltersProps) {
  const timeRanges: { key: AnalyticsTimeRange; label: string }[] = [
    { key: '24h', label: '24 Hours' },
    { key: '7d', label: '7 Days' },
    { key: '30d', label: '30 Days' },
    { key: '90d', label: '90 Days' },
  ];

  const tabs: { key: AnalyticsTab; label: string; icon: typeof TrendingUp }[] = [
    { key: 'overview', label: 'All Analytics', icon: LayoutGrid },
    { key: 'trends', label: 'AQI Trends', icon: TrendingUp },
    { key: 'pollutants', label: 'Pollutants', icon: Wind },
    { key: 'forecast', label: 'Forecast', icon: Sparkles },
    { key: 'comparison', label: 'City Compare', icon: Layers },
    { key: 'insights', label: 'Insights', icon: Lightbulb },
  ];

  return (
    <div className="space-y-4">
      {/* Primary Control Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-4 shadow-xs">
        {/* City Selector */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex items-center gap-2 text-slate-700 dark:text-slate-300">
            <MapPin className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" aria-hidden="true" />
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Location:</span>
          </div>
          <div className="relative">
            <label htmlFor="analytics-city-select" className="sr-only">
              Select City for Analytics
            </label>
            <select
              id="analytics-city-select"
              name="analyticsCity"
              aria-label="Select City for Analytics"
              value={selectedCityId}
              onChange={(e) => onCityChange(e.target.value)}
              className="w-full sm:w-64 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/80 px-3 py-1.5 text-xs font-semibold text-slate-900 dark:text-white focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer"
            >
              {allCities.map((c) => (
                <option key={c.location.id} value={c.location.id}>
                  {c.location.city}, {c.location.state} (AQI {c.aqi})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Time-Range Selector and Reset */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300">
            <Calendar className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" aria-hidden="true" />
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Range:</span>
          </div>

          <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800/80 p-0.5">
            {timeRanges.map((range) => {
              const isActive = timeRange === range.key;
              return (
                <button
                  key={range.key}
                  type="button"
                  onClick={() => onTimeRangeChange(range.key)}
                  aria-pressed={isActive}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                    isActive
                      ? 'bg-white dark:bg-slate-900 text-emerald-700 dark:text-emerald-300 shadow-xs border border-slate-200/60 dark:border-slate-700/60'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  {range.label}
                </button>
              );
            })}
          </div>

          <Button
            variant="ghost"
            size="sm"
            onClick={onResetFilters}
            className="text-xs text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white ml-auto sm:ml-0"
            title="Reset to default city and 24h window"
          >
            <RotateCcw className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
            Reset
          </Button>
        </div>
      </div>

      {/* Analytics Category Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none border-b border-slate-200 dark:border-slate-800">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => onTabChange(tab.key)}
              aria-pressed={isActive}
              className={`flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-all border-b-2 whitespace-nowrap cursor-pointer ${
                isActive
                  ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 bg-emerald-50/50 dark:bg-emerald-950/20'
                  : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:border-slate-300 dark:hover:border-slate-700'
              }`}
            >
              <Icon className="w-3.5 h-3.5" aria-hidden="true" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

