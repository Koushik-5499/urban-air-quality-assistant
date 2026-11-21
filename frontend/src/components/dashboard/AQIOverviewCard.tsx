import { MapPin, Clock, Info, Wind } from 'lucide-react';
import { Card } from '../ui/Card';
import { AQIGauge } from './AQIGauge';
import type { CityDashboardData } from '../../types/dashboard';

export interface AQIOverviewCardProps {
  data: CityDashboardData;
}

export function AQIOverviewCard({ data }: AQIOverviewCardProps) {
  const { aqi, category, dominantPollutant, summary, location, lastUpdated } = data;

  // Scale levels for the horizontal scale bar
  const scaleLevels = [
    { label: 'Good', range: '0-50', color: 'bg-emerald-500', active: aqi <= 50 },
    { label: 'Moderate', range: '51-100', color: 'bg-amber-500', active: aqi > 50 && aqi <= 100 },
    { label: 'Sensitive', range: '101-150', color: 'bg-orange-500', active: aqi > 100 && aqi <= 150 },
    { label: 'Unhealthy', range: '151-200', color: 'bg-red-500', active: aqi > 150 && aqi <= 200 },
    { label: 'Very Unhealthy', range: '201-300', color: 'bg-purple-500', active: aqi > 200 && aqi <= 300 },
    { label: 'Hazardous', range: '301-500', color: 'bg-rose-900', active: aqi > 300 },
  ];

  return (
    <Card variant="standard" className="relative overflow-hidden">
      {/* Top Banner with station metadata & simulation warning */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <MapPin className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" aria-hidden="true" />
          <span className="font-semibold text-slate-700 dark:text-slate-200">{location.name}</span>
          <span className="hidden md:inline">• {location.station}</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-[11px] text-slate-400 dark:text-slate-500 flex items-center gap-1">
            <Clock className="w-3 h-3" aria-hidden="true" />
            {lastUpdated}
          </span>
          <span className="inline-flex items-center gap-1 rounded bg-amber-50 dark:bg-amber-950/60 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60">
            <Info className="w-2.5 h-2.5" aria-hidden="true" />
            Simulated Sample
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Left Column: Gauge Visualization */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center p-2 rounded-xl bg-slate-50/60 dark:bg-slate-950/40 border border-slate-100 dark:border-slate-800/80">
          <AQIGauge aqi={aqi} category={category} />
        </div>

        {/* Right Column: Metric Breakdown & Health Status */}
        <div className="lg:col-span-7 space-y-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                Primary Air Quality Metric
              </span>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
              AQI {aqi} — {category}
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-300 mt-2 leading-relaxed">
              {summary}
            </p>
          </div>

          {/* Dominant Pollutant highlight pill */}
          <div className="inline-flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200/80 dark:border-emerald-800/60 text-xs text-emerald-900 dark:text-emerald-200 font-medium">
            <Wind className="w-4 h-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <span>Dominant Pollutant: <strong className="font-semibold text-emerald-700 dark:text-emerald-300">{dominantPollutant}</strong></span>
          </div>

          {/* Horizontal AQI Scale Bar */}
          <div className="space-y-1.5 pt-2">
            <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-medium">
              <span>AQI Measurement Scale</span>
              <span>0 to 500 Index Range</span>
            </div>
            <div className="grid grid-cols-6 gap-1 h-3 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800 p-0.5" role="progressbar" aria-valuenow={aqi} aria-valuemin={0} aria-valuemax={500}>
              {scaleLevels.map((lvl) => (
                <div
                  key={lvl.label}
                  className={`h-full rounded-sm transition-all ${lvl.color} ${
                    lvl.active ? 'ring-2 ring-slate-900 dark:ring-white scale-y-110' : 'opacity-40'
                  }`}
                  title={`${lvl.label} (${lvl.range})`}
                />
              ))}
            </div>
            <div className="grid grid-cols-6 gap-1 text-[10px] text-slate-400 dark:text-slate-500 text-center font-medium">
              <span>0-50</span>
              <span>51-100</span>
              <span>101-150</span>
              <span>151-200</span>
              <span>201-300</span>
              <span>301+</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
