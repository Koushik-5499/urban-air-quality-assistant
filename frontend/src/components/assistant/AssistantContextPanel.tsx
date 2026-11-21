import {
  Activity,
  ShieldCheck,
  Wind,
  Heart,
  Flame,
  Info,
  MapPin,
  Clock,
} from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { getHealthRecommendationsForCity } from '../../services/assistantEngine';
import type { CityDashboardData } from '../../types/dashboard';

export interface AssistantContextPanelProps {
  cityData: CityDashboardData;
}

const iconMap: Record<string, typeof Activity> = {
  Activity: Activity,
  ShieldCheck: ShieldCheck,
  Wind: Wind,
  Heart: Heart,
};

export function AssistantContextPanel({ cityData }: AssistantContextPanelProps) {
  const { location, aqi, category, dominantPollutant, weather, pollutants, lastUpdated } = cityData;
  const pm25 = pollutants.find((p) => p.id === 'pm25')?.value ?? 25;
  const recommendations = getHealthRecommendationsForCity(cityData);

  const getBadgeVariant = (cat: string) => {
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
    <div className="space-y-4">
      {/* 1. Active City Atmospheric Card */}
      <Card variant="standard" className="p-4 space-y-3 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-500 to-amber-500" />

        <div className="flex items-start justify-between gap-2 pt-1">
          <div>
            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
              <MapPin className="w-3.5 h-3.5 text-emerald-600" />
              <span>Active City Context</span>
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white leading-tight mt-0.5">
              {location.city}, {location.state}
            </h3>
          </div>

          <Badge variant={getBadgeVariant(category)} size="sm">
            {category}
          </Badge>
        </div>

        {/* Primary Metrics Grid */}
        <div className="grid grid-cols-3 gap-2 py-2 border-y border-slate-100 dark:border-slate-800 text-center">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              AQI
            </span>
            <span className="text-xl font-black text-slate-900 dark:text-white">{aqi}</span>
          </div>

          <div className="border-x border-slate-100 dark:border-slate-800">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              PM2.5
            </span>
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
              {pm25.toFixed(1)} <span className="text-[9px] text-slate-400">µg</span>
            </span>
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
              Weather
            </span>
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
              {weather.temperature.toFixed(1)}°C
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-1">
            <Flame className="w-3 h-3 text-amber-500" />
            Dominant: {dominantPollutant}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {lastUpdated}
          </span>
        </div>
      </Card>

      {/* 2. Contextual Health Recommendations List */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
          <span>Active Recommendations for {category} Air</span>
          <span className="text-[10px] text-slate-400">WHO & CPCB</span>
        </div>

        <div className="space-y-2.5">
          {recommendations.map((rec) => {
            const Icon = iconMap[rec.iconName] || Activity;
            const isHigh = rec.severity === 'high';
            const isModerate = rec.severity === 'moderate';

            return (
              <div
                key={rec.id}
                className={`p-3.5 rounded-xl border transition-all text-xs space-y-1.5 ${
                  isHigh
                    ? 'bg-rose-50/60 dark:bg-rose-950/20 border-rose-200/80 dark:border-rose-900/40 text-slate-800 dark:text-slate-200'
                    : isModerate
                    ? 'bg-amber-50/60 dark:bg-amber-950/20 border-amber-200/80 dark:border-amber-900/40 text-slate-800 dark:text-slate-200'
                    : 'bg-white dark:bg-slate-900 border-slate-200/80 dark:border-slate-800 text-slate-800 dark:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`p-1.5 rounded-lg ${
                      isHigh
                        ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/60 dark:text-rose-300'
                        : isModerate
                        ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-300'
                        : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                  </span>
                  <span className="font-bold text-slate-900 dark:text-white leading-tight">
                    {rec.title}
                  </span>
                </div>

                <p className="text-slate-600 dark:text-slate-300 leading-relaxed text-[11px] pl-1">
                  {rec.description}
                </p>

                <ul className="space-y-0.5 text-[11px] text-slate-500 dark:text-slate-400 pl-3 list-disc">
                  {rec.bullets.map((b, bIdx) => (
                    <li key={bIdx}>{b}</li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Medical Disclaimer */}
      <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Educational Notice:</strong> The Urban Air Quality Health Assistant provides general environmental awareness and synthesized precautionary exposure advice based on public ambient guidelines. It does not provide clinical diagnosis or medical treatment. Consult licensed healthcare physicians for acute respiratory or cardiac symptoms.
        </p>
      </div>
    </div>
  );
}
