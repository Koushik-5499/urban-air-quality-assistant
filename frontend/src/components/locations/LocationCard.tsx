import { MapPin, Wind, Thermometer, Clock, Eye, Layers, Check } from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import type { CityDashboardData } from '../../types/dashboard';

export interface LocationCardProps {
  cityData: CityDashboardData;
  isSelectedForDashboard: boolean;
  isCompared: boolean;
  canCompare: boolean;
  onViewDetails: (city: CityDashboardData) => void;
  onSelectForDashboard: (city: CityDashboardData) => void;
  onToggleCompare: (cityId: string) => void;
}

export function LocationCard({
  cityData,
  isSelectedForDashboard,
  isCompared,
  canCompare,
  onViewDetails,
  onSelectForDashboard,
  onToggleCompare,
}: LocationCardProps) {
  const { location, aqi, category, pollutants, weather, lastUpdated } = cityData;
  const pm25 = pollutants.find((p) => p.id === 'pm25')?.value ?? 0;

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

  const getAQIColorClass = (cat: string) => {
    switch (cat) {
      case 'Good':
        return 'text-emerald-600 dark:text-emerald-400';
      case 'Moderate':
        return 'text-amber-600 dark:text-amber-400';
      case 'Unhealthy for Sensitive Groups':
        return 'text-orange-600 dark:text-orange-400';
      case 'Unhealthy':
        return 'text-rose-600 dark:text-rose-400';
      default:
        return 'text-slate-700 dark:text-slate-300';
    }
  };

  return (
    <Card
      variant="standard"
      className={`p-5 flex flex-col justify-between hover:shadow-md transition-all relative ${
        isSelectedForDashboard
          ? 'border-emerald-500/80 dark:border-emerald-500/80 ring-1 ring-emerald-500/20'
          : ''
      }`}
    >
      <div>
        {/* Top Header: City Name, State, Active Dashboard Pill */}
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-0.5">
            <div className="flex items-center gap-1.5">
              <MapPin className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" aria-hidden="true" />
              <h2 className="text-lg font-bold text-slate-900 dark:text-white leading-tight">
                {location.city}
              </h2>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 pl-5.5">
              {location.state}, {location.country}
            </p>
          </div>

          <div className="flex items-center gap-1.5">
            {isSelectedForDashboard && (
              <Badge variant="success" size="sm" showDot>
                Active
              </Badge>
            )}
            <Badge variant={getBadgeVariant(category)} size="sm">
              {category}
            </Badge>
          </div>
        </div>

        {/* Station Subtext */}
        <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-2 line-clamp-1">
          Node: {location.station}
        </p>

        {/* Primary Metrics: AQI, PM2.5, Temperature */}
        <div className="grid grid-cols-3 gap-2 py-4 my-3 border-y border-slate-100 dark:border-slate-800 text-center">
          {/* AQI */}
          <div className="space-y-0.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              AQI Score
            </span>
            <div className={`text-2xl font-black ${getAQIColorClass(category)}`}>
              {aqi}
            </div>
          </div>

          {/* PM2.5 */}
          <div className="space-y-0.5 border-x border-slate-100 dark:border-slate-800">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-center gap-1">
              <Wind className="w-2.5 h-2.5" aria-hidden="true" />
              PM2.5
            </span>
            <div className="text-base font-bold text-slate-800 dark:text-slate-200">
              {pm25.toFixed(1)}{' '}
              <span className="text-[10px] font-normal text-slate-400">µg/m³</span>
            </div>
          </div>

          {/* Temperature */}
          <div className="space-y-0.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-center gap-1">
              <Thermometer className="w-2.5 h-2.5" aria-hidden="true" />
              Weather
            </span>
            <div className="text-base font-bold text-slate-800 dark:text-slate-200">
              {weather.temperature.toFixed(1)}°C
            </div>
          </div>
        </div>

        {/* Telemetry Timestamp */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 mb-4">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" aria-hidden="true" />
            {lastUpdated}
          </span>
          <span>Simulated</span>
        </div>
      </div>

      {/* Action Buttons: View Details, Compare, Activate */}
      <div className="space-y-2 pt-1 border-t border-slate-100 dark:border-slate-800/80">
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewDetails(cityData)}
            className="w-full text-xs"
          >
            <Eye className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
            View Details
          </Button>

          <Button
            variant={isCompared ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => onToggleCompare(location.id)}
            disabled={!isCompared && !canCompare}
            className={`w-full text-xs ${
              isCompared
                ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800'
                : ''
            }`}
          >
            <Layers className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
            {isCompared ? 'Comparing' : '+ Compare'}
          </Button>
        </div>

        {!isSelectedForDashboard && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onSelectForDashboard(cityData)}
            className="w-full text-xs text-emerald-700 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/40"
          >
            <Check className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
            Set as Active Dashboard City
          </Button>
        )}
      </div>
    </Card>
  );
}
