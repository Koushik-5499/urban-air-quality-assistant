import { ArrowUpRight, ArrowDownRight, Minus, Wind, CloudFog, Flame, Activity, Atom, Gauge } from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { PollutantMetric, PollutantId } from '../../types/dashboard';

export interface PollutantCardProps {
  pollutant: PollutantMetric;
}

const pollutantIcons: Record<PollutantId, typeof Wind> = {
  pm25: Wind,
  pm10: CloudFog,
  co: Flame,
  no2: Activity,
  so2: Atom,
  o3: Gauge,
};

export function PollutantCard({ pollutant }: PollutantCardProps) {
  const {
    id,
    name,
    formula,
    fullName,
    value,
    unit,
    status,
    badgeVariant,
    changePercent,
    isIncrease,
    period,
    standardLimit,
  } = pollutant;

  const IconComponent = pollutantIcons[id] || Wind;

  // Trend formatting
  const isNeutral = changePercent === 0;

  return (
    <Card
      variant="interactive"
      className="p-5 flex flex-col justify-between hover:shadow-md transition-all group"
    >
      <div>
        {/* Header: Chemical Formula & Full Name */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/60 group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/50 transition-colors">
              <IconComponent className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <span className="text-base font-bold text-slate-900 dark:text-white">
                {formula}
              </span>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                {name} • {fullName}
              </p>
            </div>
          </div>

          <Badge variant={badgeVariant} size="sm">
            {status}
          </Badge>
        </div>

        {/* Value & Measurement Unit */}
        <div className="mt-4 flex items-baseline gap-1.5">
          <span className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            {value.toFixed(1)}
          </span>
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
            {unit}
          </span>
        </div>
      </div>

      {/* Footer: Trend comparison and Reference limit */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs">
        <div className="flex items-center gap-1 font-medium">
          {isNeutral ? (
            <span className="text-slate-500 flex items-center gap-0.5">
              <Minus className="w-3 h-3" />
              <span>0% {period}</span>
            </span>
          ) : isIncrease ? (
            <span className="text-amber-600 dark:text-amber-400 flex items-center gap-0.5">
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span>+{changePercent}% {period}</span>
            </span>
          ) : (
            <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-0.5">
              <ArrowDownRight className="w-3.5 h-3.5" />
              <span>-{changePercent}% {period}</span>
            </span>
          )}
        </div>

        <span className="text-[10px] text-slate-400 dark:text-slate-500">
          {standardLimit}
        </span>
      </div>
    </Card>
  );
}

