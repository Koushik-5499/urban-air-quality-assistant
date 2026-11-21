import {
  Activity,
  Wind,
  Flame,
  Clock,
  Sparkles,
  MapPin,
  ChevronDown,
} from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { CityDashboardData, LocationOption } from '../../types/dashboard';

export interface PollutantOverviewProps {
  cityData: CityDashboardData;
  allLocations: LocationOption[];
  onSelectCity: (cityId: string) => void;
}

export function PollutantOverview({
  cityData,
  allLocations,
  onSelectCity,
}: PollutantOverviewProps) {
  const { location, aqi, category, dominantPollutant, pollutants, lastUpdated } = cityData;

  const pm25 = pollutants.find((p) => p.id === 'pm25')?.value ?? 0;
  const pm10 = pollutants.find((p) => p.id === 'pm10')?.value ?? 0;

  const getAQIBadgeVariant = (cat: string) => {
    switch (cat) {
      case 'Good':
        return 'success';
      case 'Moderate':
        return 'warning';
      case 'Unhealthy for Sensitive Groups':
      case 'Unhealthy':
        return 'danger';
      default:
        return 'default';
    }
  };

  return (
    <Card variant="standard" className="p-6 overflow-hidden relative">
      {/* Decorative top accent gradient */}
      <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-emerald-500 via-teal-500 to-amber-500" />

      {/* Main Header Row */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-6 border-b border-slate-200/80 dark:border-slate-800">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/60">
              <Activity className="w-5 h-5" aria-hidden="true" />
            </span>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
              Ambient Air Pollutant Overview
            </h2>
            <Badge variant="neutral" size="sm">
              6 Criteria Pollutants
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
            Real-time atmospheric analysis of primary inhalable particulates, combustion gases, and secondary oxidants.
          </p>
        </div>

        {/* City Selector & Simulated Badge */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative inline-block">
            <label htmlFor="pollutants-city-select" className="sr-only">
              Select City for Pollutant Analysis
            </label>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-850 border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200 font-medium">
              <MapPin className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <select
                id="pollutants-city-select"
                value={location.id}
                onChange={(e) => onSelectCity(e.target.value)}
                className="bg-transparent pr-4 font-semibold text-slate-900 dark:text-white focus:outline-none cursor-pointer appearance-none"
              >
                {allLocations.map((loc) => (
                  <option key={loc.id} value={loc.id} className="dark:bg-slate-900 text-slate-900 dark:text-white">
                    {loc.city}, {loc.state}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 pointer-events-none" />
            </div>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-teal-50 dark:bg-teal-950/50 border border-teal-200/60 dark:border-teal-800/60 text-[11px] font-medium text-teal-800 dark:text-teal-300">
            <Sparkles className="w-3 h-3 text-teal-600 dark:text-teal-400" />
            <span>Simulated Telemetry</span>
          </div>
        </div>
      </div>

      {/* 5-Column Key Metric Overview Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 pt-6">
        {/* Metric 1: Selected City & Station */}
        <div className="space-y-1 p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Active Station
          </span>
          <div className="text-sm font-bold text-slate-900 dark:text-white truncate">
            {location.city}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
            {location.station}
          </div>
        </div>

        {/* Metric 2: Overall AQI */}
        <div className="space-y-1 p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Overall AQI Score
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900 dark:text-white">{aqi}</span>
            <Badge variant={getAQIBadgeVariant(category)} size="sm">
              {category}
            </Badge>
          </div>
        </div>

        {/* Metric 3: Dominant Pollutant */}
        <div className="space-y-1 p-3 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-900/40">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-700 dark:text-amber-400 flex items-center gap-1">
            <Flame className="w-3 h-3" />
            Dominant Driver
          </span>
          <div className="text-xl font-black text-amber-900 dark:text-amber-200">
            {dominantPollutant}
          </div>
          <div className="text-[11px] text-amber-700/80 dark:text-amber-400/80">
            Sets governing sub-index
          </div>
        </div>

        {/* Metric 4: PM2.5 Concentration */}
        <div className="space-y-1 p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <Wind className="w-3 h-3" />
            Fine PM₂.₅
          </span>
          <div className="text-xl font-black text-slate-900 dark:text-white">
            {pm25.toFixed(1)}{' '}
            <span className="text-xs font-normal text-slate-500 dark:text-slate-400">µg/m³</span>
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            WHO Limit: 15 µg/m³
          </div>
        </div>

        {/* Metric 5: PM10 Concentration */}
        <div className="space-y-1 p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <Wind className="w-3 h-3" />
            Coarse PM₁₀
          </span>
          <div className="text-xl font-black text-slate-900 dark:text-white">
            {pm10.toFixed(1)}{' '}
            <span className="text-xs font-normal text-slate-500 dark:text-slate-400">µg/m³</span>
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            NAAQS: 100 µg/m³
          </div>
        </div>
      </div>

      {/* Bottom Sub-info: timestamp and notice */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <span className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          Last telemetry sync: {lastUpdated}
        </span>
        <span>6 of 6 regulatory parameters actively measured</span>
      </div>
    </Card>
  );
}
