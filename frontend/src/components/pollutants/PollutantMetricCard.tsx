import {
  Wind,
  CloudFog,
  Flame,
  Activity,
  Atom,
  Gauge,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Layers,
  ChevronRight,
} from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { POLLUTANT_DETAILS } from '../../data/pollutantDetails';
import type { PollutantMetric, PollutantId } from '../../types/dashboard';

export interface PollutantMetricCardProps {
  pollutant: PollutantMetric;
  isSelected: boolean;
  isCompared: boolean;
  canCompare: boolean;
  onSelect: (id: PollutantId) => void;
  onToggleCompare: (id: PollutantId) => void;
}

const pollutantIcons: Record<PollutantId, typeof Wind> = {
  pm25: Wind,
  pm10: CloudFog,
  co: Flame,
  no2: Activity,
  so2: Atom,
  o3: Gauge,
};

export function PollutantMetricCard({
  pollutant,
  isSelected,
  isCompared,
  canCompare,
  onSelect,
  onToggleCompare,
}: PollutantMetricCardProps) {
  const { id, name, formula, fullName, value, unit, status, changePercent, isIncrease, period } = pollutant;
  const details = POLLUTANT_DETAILS[id];
  const IconComponent = pollutantIcons[id] || Wind;

  const isNeutral = changePercent === 0;

  const getStatusBadgeVariant = (st: string) => {
    switch (st.toLowerCase()) {
      case 'good':
        return 'success';
      case 'moderate':
        return 'warning';
      case 'sensitive':
      case 'unhealthy':
      case 'very unhealthy':
      case 'hazardous':
        return 'danger';
      default:
        return 'default';
    }
  };

  return (
    <Card
      variant="interactive"
      className={`p-5 flex flex-col justify-between transition-all relative group ${
        isSelected
          ? 'ring-2 ring-emerald-500 border-emerald-500/80 shadow-md'
          : 'hover:shadow-md'
      }`}
      onClick={() => onSelect(id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(id);
        }
      }}
      aria-label={`Inspect ${name} (${fullName}) air pollutant telemetry`}
    >
      {/* Top Accent Strip */}
      <div
        className="absolute top-0 left-0 right-0 h-1 rounded-t-xl"
        style={{ backgroundColor: details?.color || '#10B981' }}
      />

      <div>
        {/* Header: Chemical Formula & Badges */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2.5">
            <div
              className="p-2.5 rounded-xl border transition-colors"
              style={{
                backgroundColor: `${details?.color}15`,
                borderColor: `${details?.color}40`,
                color: details?.color,
              }}
            >
              <IconComponent className="w-5 h-5" aria-hidden="true" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-extrabold text-slate-900 dark:text-white font-mono">
                  {formula}
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                  {details?.classification || 'Pollutant'}
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                {fullName}
              </p>
            </div>
          </div>

          <Badge variant={getStatusBadgeVariant(status)} size="sm">
            {status}
          </Badge>
        </div>

        {/* Primary Reading Display */}
        <div className="mt-5 pb-4 border-b border-slate-100 dark:border-slate-800 flex items-baseline justify-between">
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">
                {id === 'co' ? value.toFixed(2) : value.toFixed(1)}
              </span>
              <span className="text-sm font-semibold text-slate-500 dark:text-slate-400 font-mono">
                {unit}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              NAAQS Limit: {details?.naaqsLimitText || 'N/A'}
            </p>
          </div>

          {/* Trend Indicator */}
          <div
            className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-lg ${
              isNeutral
                ? 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
                : isIncrease
                ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400'
                : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400'
            }`}
          >
            {isNeutral ? (
              <Minus className="w-3.5 h-3.5" aria-hidden="true" />
            ) : isIncrease ? (
              <ArrowUpRight className="w-3.5 h-3.5" aria-hidden="true" />
            ) : (
              <ArrowDownRight className="w-3.5 h-3.5" aria-hidden="true" />
            )}
            <span>
              {isIncrease ? '+' : '-'}
              {changePercent}%
            </span>
            <span className="text-[10px] opacity-75 font-normal ml-0.5">{period}</span>
          </div>
        </div>

        {/* Short Summary Description */}
        <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 mt-3 leading-relaxed">
          {details?.description || 'Atmospheric pollutant measured via automated gas chromatography.'}
        </p>
      </div>

      {/* Action Footer */}
      <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2">
        <Button
          variant={isSelected ? 'secondary' : 'outline'}
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onSelect(id);
          }}
          className={`text-xs ${
            isSelected
              ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-300'
              : ''
          }`}
        >
          {isSelected ? 'Active Selection' : 'View Analysis'}
          <ChevronRight className="w-3.5 h-3.5 ml-1" />
        </Button>

        <Button
          variant={isCompared ? 'secondary' : 'ghost'}
          size="sm"
          onClick={(e) => {
            e.stopPropagation();
            onToggleCompare(id);
          }}
          disabled={!isCompared && !canCompare}
          className={`text-xs ${
            isCompared
              ? 'bg-teal-50 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300 border border-teal-300'
              : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
          }`}
        >
          <Layers className="w-3.5 h-3.5 mr-1" />
          {isCompared ? 'In Compare' : '+ Compare'}
        </Button>
      </div>
    </Card>
  );
}
