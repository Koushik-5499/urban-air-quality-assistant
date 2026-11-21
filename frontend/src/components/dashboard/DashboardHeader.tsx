import React from 'react';
import { MapPin, RefreshCw, Clock } from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { DEMO_LOCATIONS } from '../../data/dashboardData';
import type { LocationOption } from '../../types/dashboard';

export interface DashboardHeaderProps {
  selectedLocation: LocationOption;
  onLocationChange: (location: LocationOption) => void;
  lastUpdated: string;
  isRefreshing: boolean;
  onRefresh: () => void;
}

export function DashboardHeader({
  selectedLocation,
  onLocationChange,
  lastUpdated,
  isRefreshing,
  onRefresh,
}: DashboardHeaderProps) {
  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const loc = DEMO_LOCATIONS.find((l) => l.id === e.target.value);
    if (loc) {
      onLocationChange(loc);
    }
  };

  return (
    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
      {/* Title & Description */}
      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Air Quality Overview
          </h1>
          <Badge variant="neutral" size="sm" showDot>
            Simulated Data
          </Badge>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400 max-w-2xl">
          Real-time atmospheric telemetry and urban pollutant monitoring. Environmental index values are simulated for demonstration purposes.
        </p>
      </div>

      {/* Controls: Location Selector & Refresh Button */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Location Dropdown */}
        <div className="relative min-w-[240px] flex-1 sm:flex-initial">
          <label htmlFor="dashboard-location-select" className="sr-only">
            Select monitoring location
          </label>
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-emerald-600 dark:text-emerald-400">
            <MapPin className="h-4 w-4" aria-hidden="true" />
          </div>
          <select
            id="dashboard-location-select"
            value={selectedLocation.id}
            onChange={handleSelectChange}
            disabled={isRefreshing}
            className="w-full pl-9 pr-8 py-2 text-sm font-medium bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 rounded-lg border border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 shadow-sm transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {DEMO_LOCATIONS.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name}
              </option>
            ))}
          </select>
        </div>

        {/* Timestamp Indicator */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 text-xs text-slate-600 dark:text-slate-300">
          <Clock className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
          <span>{lastUpdated}</span>
        </div>

        {/* Refresh Action Button */}
        <Button
          variant="outline"
          size="md"
          onClick={onRefresh}
          disabled={isRefreshing}
          aria-label="Refresh telemetry readings"
          className="shrink-0"
        >
          <RefreshCw
            className={`w-4 h-4 mr-1.5 text-emerald-600 dark:text-emerald-400 ${
              isRefreshing ? 'animate-spin' : ''
            }`}
            aria-hidden="true"
          />
          <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
        </Button>
      </div>
    </div>
  );
}
