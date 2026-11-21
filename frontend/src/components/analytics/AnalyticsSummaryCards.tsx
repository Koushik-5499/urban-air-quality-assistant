import { Activity, Gauge, ArrowUpRight, ArrowDownRight, MoveRight, Flame, ShieldCheck, Wind } from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { AnalyticsSummary } from '../../types/analytics';
import type { AQICategory } from '../../types/dashboard';

export interface AnalyticsSummaryCardsProps {
  summary: AnalyticsSummary;
  cityName: string;
  timeRangeLabel: string;
}

function getCategoryBadgeVariant(cat: AQICategory): 'success' | 'warning' | 'danger' | 'info' | 'default' {
  switch (cat) {
    case 'Good':
      return 'success';
    case 'Moderate':
      return 'warning';
    case 'Unhealthy for Sensitive Groups':
    case 'Unhealthy':
    case 'Very Unhealthy':
    case 'Hazardous':
      return 'danger';
    default:
      return 'default';
  }
}

export function AnalyticsSummaryCards({
  summary,
  cityName,
  timeRangeLabel,
}: AnalyticsSummaryCardsProps) {
  // Trend styling
  const isImproving = summary.trendDirection === 'improving';
  const isWorsening = summary.trendDirection === 'worsening';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3.5">
      {/* 1. Current AQI */}
      <Card variant="standard" className="p-4 flex flex-col justify-between space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span className="font-semibold uppercase tracking-wider text-[10px]">Current AQI</span>
          <Activity className="w-4 h-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
        </div>
        <div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">
              {summary.currentAQI}
            </span>
            <span className="text-xs font-semibold text-slate-400">index</span>
          </div>
          <p className="text-xs text-slate-500 truncate mt-0.5">{cityName} station</p>
        </div>
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
          <Badge variant={getCategoryBadgeVariant(summary.currentCategory)} size="sm">
            {summary.currentCategory}
          </Badge>
        </div>
      </Card>

      {/* 2. Historical Average AQI */}
      <Card variant="standard" className="p-4 flex flex-col justify-between space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span className="font-semibold uppercase tracking-wider text-[10px]">Sample Average</span>
          <Gauge className="w-4 h-4 text-teal-600 dark:text-teal-400" aria-hidden="true" />
        </div>
        <div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">
              {summary.historicalAverageAQI}
            </span>
            <span className="text-xs font-semibold text-slate-400">avg</span>
          </div>
          <p className="text-xs text-slate-500 truncate mt-0.5">Across {timeRangeLabel}</p>
        </div>
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
          <Badge variant={getCategoryBadgeVariant(summary.averageCategory)} size="sm">
            {summary.averageCategory}
          </Badge>
        </div>
      </Card>

      {/* 3. Highest Recorded Sample AQI */}
      <Card variant="standard" className="p-4 flex flex-col justify-between space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span className="font-semibold uppercase tracking-wider text-[10px]">Peak Sample</span>
          <Flame className="w-4 h-4 text-rose-500" aria-hidden="true" />
        </div>
        <div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-black text-rose-600 dark:text-rose-400 tracking-tight">
              {summary.highestAQI}
            </span>
            <span className="text-xs font-semibold text-slate-400">max</span>
          </div>
          <p className="text-xs text-slate-500 truncate mt-0.5">At {summary.highestAQITime}</p>
        </div>
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
          <span>Highest reading</span>
          <span className="font-semibold text-rose-600 dark:text-rose-400">Peak load</span>
        </div>
      </Card>

      {/* 4. Lowest Recorded Sample AQI */}
      <Card variant="standard" className="p-4 flex flex-col justify-between space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span className="font-semibold uppercase tracking-wider text-[10px]">Cleanest Sample</span>
          <ShieldCheck className="w-4 h-4 text-emerald-500" aria-hidden="true" />
        </div>
        <div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-3xl font-black text-emerald-600 dark:text-emerald-400 tracking-tight">
              {summary.lowestAQI}
            </span>
            <span className="text-xs font-semibold text-slate-400">min</span>
          </div>
          <p className="text-xs text-slate-500 truncate mt-0.5">At {summary.lowestAQITime}</p>
        </div>
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
          <span>Cleanest window</span>
          <span className="font-semibold text-emerald-600 dark:text-emerald-400">Baseline</span>
        </div>
      </Card>

      {/* 5. Overall Trend Direction */}
      <Card variant="standard" className="p-4 flex flex-col justify-between space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span className="font-semibold uppercase tracking-wider text-[10px]">Trend Direction</span>
          {isImproving ? (
            <ArrowDownRight className="w-4 h-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
          ) : isWorsening ? (
            <ArrowUpRight className="w-4 h-4 text-rose-500" aria-hidden="true" />
          ) : (
            <MoveRight className="w-4 h-4 text-sky-500" aria-hidden="true" />
          )}
        </div>
        <div>
          <div className="flex items-baseline gap-1.5">
            <span
              className={`text-2xl font-black tracking-tight ${
                isImproving
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : isWorsening
                  ? 'text-rose-600 dark:text-rose-400'
                  : 'text-sky-600 dark:text-sky-400'
              }`}
            >
              {isImproving ? 'Improving' : isWorsening ? 'Worsening' : 'Stable'}
            </span>
          </div>
          <p className="text-xs text-slate-500 truncate mt-0.5">
            {summary.trendPercentageChange > 0 ? '+' : ''}
            {summary.trendPercentageChange}% net change
          </p>
        </div>
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
          <span>Telemetry shift</span>
          <span className="font-semibold text-slate-700 dark:text-slate-300">
            {isImproving ? 'Air cleaner' : isWorsening ? 'Air dirtier' : 'No major shift'}
          </span>
        </div>
      </Card>

      {/* 6. Dominant Pollutant */}
      <Card variant="standard" className="p-4 flex flex-col justify-between space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span className="font-semibold uppercase tracking-wider text-[10px]">Dominant Driver</span>
          <Wind className="w-4 h-4 text-amber-500" aria-hidden="true" />
        </div>
        <div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              {summary.dominantPollutantFormula}
            </span>
            <span className="text-xs font-semibold text-slate-400">{summary.mostDominantPollutant}</span>
          </div>
          <p className="text-xs text-slate-500 truncate mt-0.5">{summary.dominantPollutantFrequency}% of samples</p>
        </div>
        <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
          <span>Primary factor</span>
          <span className="font-semibold text-amber-600 dark:text-amber-400">Governs AQI</span>
        </div>
      </Card>
    </div>
  );
}
