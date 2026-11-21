import { History, Trash2, MapPin } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { DASHBOARD_DATA } from '../../data/dashboardData';
import type { CityDashboardData } from '../../types/dashboard';

export interface RecentLocationsProps {
  recentCityIds: string[];
  onSelectCity: (city: CityDashboardData) => void;
  onClear: () => void;
}

export function RecentLocations({
  recentCityIds,
  onSelectCity,
  onClear,
}: RecentLocationsProps) {
  if (recentCityIds.length === 0) return null;

  const getBadgeVariant = (category: string) => {
    switch (category) {
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
    <div className="space-y-2.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
          <History className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
          <span>Recently Viewed Cities</span>
        </div>
        <button
          type="button"
          onClick={onClear}
          className="text-xs text-slate-400 hover:text-rose-500 transition-colors flex items-center gap-1 cursor-pointer"
        >
          <Trash2 className="w-3 h-3" aria-hidden="true" />
          <span>Clear History</span>
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {recentCityIds.map((id) => {
          const cityData = DASHBOARD_DATA[id];
          if (!cityData) return null;

          return (
            <button
              key={id}
              type="button"
              onClick={() => onSelectCity(cityData)}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-emerald-500/60 dark:hover:border-emerald-500/60 shadow-xs text-xs font-medium text-slate-800 dark:text-slate-200 transition-all cursor-pointer group"
            >
              <MapPin className="w-3 h-3 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
              <span className="group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                {cityData.location.city}
              </span>
              <span className="font-bold">AQI {cityData.aqi}</span>
              <Badge variant={getBadgeVariant(cityData.category)} size="sm">
                {cityData.category}
              </Badge>
            </button>
          );
        })}
      </div>
    </div>
  );
}
