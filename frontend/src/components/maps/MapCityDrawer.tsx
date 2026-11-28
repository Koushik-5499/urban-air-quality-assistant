import {
  MapPin,
  Wind,
  Thermometer,
  Droplets,
  Clock,
  Sparkles,
  Check,
  ChevronRight,
  X,
  ExternalLink,
  Flame,
} from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { getAQIBadgeVariant } from '../../data/mapData';
import type { MapCityData } from '../../types/map';
import { Link } from 'react-router-dom';

export interface MapCityDrawerProps {
  city: MapCityData | null;
  onClose: () => void;
  isActiveDashboardCity: boolean;
  onSelectForDashboard: (cityId: string) => void;
}

export function MapCityDrawer({
  city,
  onClose,
  isActiveDashboardCity,
  onSelectForDashboard,
}: MapCityDrawerProps) {
  if (!city) return null;

  const { fullData } = city;

  return (
    <Card
      variant="standard"
      className="p-5 flex flex-col justify-between h-full space-y-5 animate-in slide-in-from-right-2 duration-300 relative overflow-hidden"
    >
      {/* Top Banner */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-500 to-amber-500" />

      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400">
                <MapPin className="w-4 h-4" />
              </span>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white leading-tight">
                {city.city}
              </h2>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 pl-8">
              {city.state}, {city.country}
            </p>
          </div>

          <div className="flex items-center gap-1.5">
            <Badge variant={getAQIBadgeVariant(city.category)} size="md">
              {city.category}
            </Badge>
            <button
              type="button"
              onClick={onClose}
              className="min-h-[44px] min-w-[44px] flex items-center justify-center p-2 text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              aria-label="Close details drawer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Node Station & Coordinates */}
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 text-xs space-y-1">
          <p className="text-slate-700 dark:text-slate-300 font-semibold truncate">
            Station: {city.station}
          </p>
          <p className="text-[11px] text-slate-600 dark:text-slate-300 font-mono">
            Coordinates: {city.lat != null ? city.lat.toFixed(4) : '—'}° N, {city.lng != null ? city.lng.toFixed(4) : '—'}° E
          </p>
        </div>

        {/* Main AQI Score & Dominant Pollutant */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 text-center space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-600 dark:text-slate-300 block tracking-wider">
              AQI Score
            </span>
            <div className="text-3xl font-black text-slate-900 dark:text-white">
              {city.aqi}
            </div>
            <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 block">
              {city.category}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 text-center space-y-1">
            <span className="text-[10px] uppercase font-bold text-amber-700 dark:text-amber-400 flex items-center justify-center gap-1 tracking-wider">
              <Flame className="w-3 h-3" /> Dominant Driver
            </span>
            <div className="text-2xl font-black text-amber-900 dark:text-amber-200">
              {city.dominantPollutant}
            </div>
            <span className="text-[11px] text-amber-700/80 dark:text-amber-400/80 block">
              Primary active factor
            </span>
          </div>
        </div>

        {/* Key Pollutant Readings */}
        <div className="space-y-2">
          <span className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider block">
            Criteria Pollutant Telemetry
          </span>
          <div className="grid grid-cols-3 gap-2">
            {fullData.pollutants.slice(0, 6).map((p) => (
              <div
                key={p.id}
                className="p-2 rounded-lg bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 text-center"
              >
                <span className="text-[10px] font-bold font-mono text-slate-500 block">
                  {p.formula}
                </span>
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  {p.id === 'co' ? p.value.toFixed(2) : p.value.toFixed(1)}
                </span>
                <span className="text-[9px] text-slate-400 block">{p.unit}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Atmospheric Weather Snapshot */}
        <div className="p-3 rounded-xl bg-teal-50/50 dark:bg-teal-950/20 border border-teal-100 dark:border-teal-900/30 flex items-center justify-around text-xs text-teal-900 dark:text-teal-200">
          <div className="flex items-center gap-1.5">
            <Thermometer className="w-3.5 h-3.5 text-teal-600" />
            <span>{city.temperature.toFixed(1)}°C Ambient</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Droplets className="w-3.5 h-3.5 text-teal-600" />
            <span>{city.humidity}% Humidity</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Wind className="w-3.5 h-3.5 text-teal-600" />
            <span>{fullData.weather.windSpeed} km/h</span>
          </div>
        </div>

        {/* Timestamp */}
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {city.lastUpdated}
          </span>
          <span className="flex items-center gap-1 text-teal-600 font-medium">
            <Sparkles className="w-3 h-3" />
            Simulated Node
          </span>
        </div>
      </div>

      {/* Actions Footer */}
      <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800">
        {!isActiveDashboardCity ? (
          <Button
            variant="primary"
            size="sm"
            onClick={() => onSelectForDashboard(city.id)}
            className="w-full text-xs"
          >
            <Check className="w-3.5 h-3.5 mr-1" />
            Set as Active Dashboard City
          </Button>
        ) : (
          <div className="w-full text-center py-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 rounded-xl border border-emerald-200/60 dark:border-emerald-800">
            Current Active Dashboard City
          </div>
        )}

        <div className="grid grid-cols-2 gap-2">
          <Link
            to="/pollutants"
            className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            Pollutants View
            <ChevronRight className="w-3 h-3 ml-1" />
          </Link>
          <Link
            to="/locations"
            className="inline-flex items-center justify-center px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
          >
            Compare View
            <ExternalLink className="w-3 h-3 ml-1" />
          </Link>
        </div>
      </div>
    </Card>
  );
}

