import { MapPin, Wind, Thermometer, Clock, Sparkles, Check, ExternalLink } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { getAQIBadgeVariant } from '../../data/mapData';
import type { MapCityData } from '../../types/map';

export interface AQIPopupProps {
  city: MapCityData;
  isActiveDashboardCity: boolean;
  onSelectForDashboard: (cityId: string) => void;
  onViewDetails: (city: MapCityData) => void;
}

export function AQIPopup({
  city,
  isActiveDashboardCity,
  onSelectForDashboard,
  onViewDetails,
}: AQIPopupProps) {
  return (
    <div className="p-1 min-w-[240px] max-w-[280px] text-slate-800 dark:text-slate-100 font-sans">
      {/* Header */}
      <div className="flex items-start justify-between gap-2 border-b border-slate-100 dark:border-slate-800 pb-2.5 mb-2.5">
        <div>
          <div className="flex items-center gap-1.5">
            <MapPin className="w-4 h-4 text-emerald-600 shrink-0" />
            <h4 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">
              {city.city}
            </h4>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 pl-5">
            {city.state}, {city.country}
          </p>
        </div>

        <Badge variant={getAQIBadgeVariant(city.category)} size="sm">
          {city.category}
        </Badge>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-3 gap-1.5 py-2 px-1.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 text-center mb-2.5">
        <div>
          <span className="text-[9px] uppercase font-bold text-slate-400 block">AQI</span>
          <span className="text-lg font-black text-slate-900 dark:text-white">{city.aqi}</span>
        </div>

        <div className="border-x border-slate-200/60 dark:border-slate-700">
          <span className="text-[9px] uppercase font-bold text-slate-400 flex items-center justify-center gap-0.5">
            <Wind className="w-2.5 h-2.5" /> PM2.5
          </span>
          <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
            {city.pm25.toFixed(1)}
          </span>
          <span className="text-[8px] text-slate-400 block -mt-0.5">µg/m³</span>
        </div>

        <div>
          <span className="text-[9px] uppercase font-bold text-slate-400 flex items-center justify-center gap-0.5">
            <Thermometer className="w-2.5 h-2.5" /> Temp
          </span>
          <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
            {city.temperature.toFixed(1)}°C
          </span>
        </div>
      </div>

      {/* Node Station & Time */}
      <div className="space-y-1 text-[10px] text-slate-400 mb-3 px-0.5">
        <p className="truncate">Node: {city.station}</p>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {city.lastUpdated}
          </span>
          <span className="flex items-center gap-0.5 text-teal-600 font-medium">
            <Sparkles className="w-2.5 h-2.5" /> Simulated
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-1.5 pt-1 border-t border-slate-100 dark:border-slate-800">
        {!isActiveDashboardCity ? (
          <Button
            variant="primary"
            size="sm"
            onClick={() => onSelectForDashboard(city.id)}
            className="w-full text-xs py-1"
          >
            <Check className="w-3 h-3 mr-1" />
            Set as Active Dashboard City
          </Button>
        ) : (
          <div className="w-full text-center py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 rounded-lg">
            Active Dashboard City
          </div>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={() => onViewDetails(city)}
          className="w-full text-xs py-1"
        >
          <ExternalLink className="w-3 h-3 mr-1" />
          View Full Telemetry
        </Button>
      </div>
    </div>
  );
}

