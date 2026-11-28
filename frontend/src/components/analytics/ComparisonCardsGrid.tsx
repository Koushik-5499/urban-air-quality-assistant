import { X, Trophy, Check } from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import type { AQICategory, CityDashboardData } from '../../types/dashboard';

export interface ComparisonCardsGridProps {
  comparedCities: CityDashboardData[];
  cleanestCityId: string | null;
  activeDashboardCityId: string;
  onRemoveCity: (cityId: string) => void;
  onSelectForDashboard: (cityId: string) => void;
  getBadgeVariant: (cat: AQICategory) => 'success' | 'warning' | 'danger' | 'info' | 'default';
}

export function ComparisonCardsGrid({
  comparedCities,
  cleanestCityId,
  activeDashboardCityId,
  onRemoveCity,
  onSelectForDashboard,
  getBadgeVariant,
}: ComparisonCardsGridProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
      {comparedCities.map((city) => {
        const isCleanest = city.location.id === cleanestCityId;
        const isActive = city.location.id === activeDashboardCityId;
        const pm25 = city.pollutants.find((p) => p.id === 'pm25')?.value ?? 0;
        const pm10 = city.pollutants.find((p) => p.id === 'pm10')?.value ?? 0;

        return (
          <div
            key={city.location.id}
            className={`relative rounded-xl border p-4 space-y-3 flex flex-col justify-between transition-all ${
              isCleanest
                ? 'border-emerald-400 dark:border-emerald-700 bg-emerald-50/40 dark:bg-emerald-950/20 shadow-xs'
                : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60'
            }`}
          >
            <button
              type="button"
              onClick={() => onRemoveCity(city.location.id)}
              aria-label={`Remove ${city.location.city} from comparison`}
              className="absolute top-2 right-2 min-h-[44px] min-w-[44px] inline-flex items-center justify-center rounded-full text-slate-600 dark:text-slate-300 hover:text-rose-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <X className="w-3.5 h-3.5" aria-hidden="true" />
            </button>

            <div className="space-y-1 pr-10">
              {isCleanest && (
                <div className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-800 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-900/80 px-2 py-0.5 rounded-full mb-1">
                  <Trophy className="w-3 h-3 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                  Cleanest in Selection
                </div>
              )}

              <div className="flex items-center gap-1.5">
                <span className="font-bold text-slate-900 dark:text-white text-base">
                  {city.location.city}
                </span>
                {isActive && (
                  <span className="text-[10px] bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 px-1 rounded font-semibold">
                    Active
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 truncate">{city.location.state}</p>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
              <span className="text-2xl font-black text-slate-900 dark:text-white">
                {city.aqi}{' '}
                <span className="text-xs font-normal text-slate-600 dark:text-slate-300">AQI</span>
              </span>
              <Badge variant={getBadgeVariant(city.category)} size="sm">
                {city.category}
              </Badge>
            </div>

            <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300 pt-1">
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-300">PM2.5:</span>
                <span className="font-semibold">{pm25.toFixed(1)} µg/m³</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-300">PM10:</span>
                <span className="font-semibold">{pm10.toFixed(1)} µg/m³</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-300">Dominant:</span>
                <span className="font-semibold text-amber-700 dark:text-amber-300">
                  {city.dominantPollutant}
                </span>
              </div>
            </div>

            {!isActive ? (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onSelectForDashboard(city.location.id)}
                className="w-full text-xs mt-2 min-h-[44px]"
              >
                <Check className="w-3 h-3 mr-1" aria-hidden="true" />
                Set as Dashboard City
              </Button>
            ) : (
              <div className="w-full text-center py-2 text-xs text-emerald-800 dark:text-emerald-300 font-semibold bg-emerald-50 dark:bg-emerald-950/40 rounded-lg">
                Current Dashboard City
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
