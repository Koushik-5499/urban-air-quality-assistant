import { useEffect, useRef } from 'react';
import {
  X,
  MapPin,
  Clock,
  Radio,
  Check,
  Layers,
  Sparkles,
  Info,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';
import { AQIGauge } from '../dashboard/AQIGauge';
import { PollutantCard } from '../dashboard/PollutantCard';
import { WeatherCard } from '../dashboard/WeatherCard';
import { HealthRecommendation } from '../dashboard/HealthRecommendation';
import type { CityDashboardData } from '../../types/dashboard';

export interface CityDetailsPanelProps {
  city: CityDashboardData | null;
  isOpen: boolean;
  onClose: () => void;
  onSelectForDashboard: (city: CityDashboardData) => void;
  isActiveCity: boolean;
  onToggleCompare: (cityId: string) => void;
  isComparing: boolean;
  canCompare: boolean;
}

export function CityDetailsPanel({
  city,
  isOpen,
  onClose,
  onSelectForDashboard,
  isActiveCity,
  onToggleCompare,
  isComparing,
  canCompare,
}: CityDetailsPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  // Close on ESC key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Lock body scroll when panel is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen || !city) return null;

  const { location, aqi, category, summary, pollutants, weather, lastUpdated } = city;

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
    <div
      className="fixed inset-0 z-50 overflow-hidden"
      role="dialog"
      aria-modal="true"
      aria-labelledby="city-details-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity duration-300"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer Container (Slide-over from right on desktop, modal-like on mobile) */}
      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div
          ref={panelRef}
          className="w-screen max-w-2xl bg-white dark:bg-slate-900 shadow-2xl flex flex-col h-full border-l border-slate-200 dark:border-slate-800 animate-in slide-in-from-right duration-300"
        >
          {/* Header */}
          <div className="p-6 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex items-start justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="p-1.5 rounded-lg bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                  <MapPin className="w-5 h-5" aria-hidden="true" />
                </span>
                <h2
                  id="city-details-title"
                  className="text-2xl font-bold text-slate-900 dark:text-white"
                >
                  {location.city}
                </h2>
                <Badge variant={getBadgeVariant(category)} size="md">
                  {category}
                </Badge>
                {isActiveCity && (
                  <Badge variant="success" size="md" showDot>
                    Active Dashboard City
                  </Badge>
                )}
              </div>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {location.state}, {location.country} • Node: {location.station}
              </p>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
              aria-label="Close city details panel"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>

          {/* Action Bar (Set as active city, compare) */}
          <div className="px-6 py-3 bg-emerald-50/50 dark:bg-emerald-950/20 border-b border-emerald-100 dark:border-emerald-900/30 flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2 text-xs text-emerald-800 dark:text-emerald-300">
              <Sparkles className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
              <span>Simulated telemetry node • 100% demonstration data</span>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant={isComparing ? 'secondary' : 'outline'}
                size="sm"
                onClick={() => onToggleCompare(location.id)}
                disabled={!isComparing && !canCompare}
                className="text-xs"
              >
                <Layers className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
                {isComparing ? 'In Comparison' : '+ Add to Compare'}
              </Button>

              {!isActiveCity ? (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onSelectForDashboard(city)}
                  className="text-xs"
                >
                  <Check className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
                  Set as Dashboard City
                </Button>
              ) : (
                <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-100/60 dark:bg-emerald-900/40">
                  <Check className="w-3.5 h-3.5" aria-hidden="true" /> Current City
                </span>
              )}
            </div>
          </div>

          {/* Scrollable Content Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* AQI Overview & Gauge */}
            <Card variant="standard" className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Air Quality Index (AQI)
                    </span>
                    <Badge variant={getBadgeVariant(category)} size="sm">
                      {category}
                    </Badge>
                  </div>

                  <div className="flex items-baseline gap-2">
                    <span className="text-5xl font-black text-slate-900 dark:text-white">
                      {aqi}
                    </span>
                    <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
                      / 500 AQI
                    </span>
                  </div>

                  <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                    {summary}
                  </p>

                  <div className="pt-2 flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400 border-t border-slate-100 dark:border-slate-800">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" aria-hidden="true" />
                      {lastUpdated}
                    </span>
                    <span className="flex items-center gap-1">
                      <Radio className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" />
                      Continuous Feed
                    </span>
                  </div>
                </div>

                <div className="flex justify-center items-center">
                  <AQIGauge aqi={aqi} category={category} className="w-full max-w-[260px]" />
                </div>
              </div>
            </Card>

            {/* 6 Pollutants Grid */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>Major Ambient Pollutants</span>
                  <span className="text-xs font-normal text-slate-500 dark:text-slate-400">
                    (6 monitored criteria)
                  </span>
                </h3>
                <span className="text-xs text-slate-400">CPCB & WHO Standards</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {pollutants.map((pollutant) => (
                  <PollutantCard key={pollutant.id} pollutant={pollutant} />
                ))}
              </div>
            </div>

            {/* Weather & Health Recommendations */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <WeatherCard weather={weather} locationName={location.city} />
              <HealthRecommendation aqi={aqi} category={category} />
            </div>

            {/* Notice Footer */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 flex items-start gap-3 text-xs text-slate-500 dark:text-slate-400">
              <Info className="w-4 h-4 text-teal-600 dark:text-teal-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="font-semibold text-slate-700 dark:text-slate-300">
                  Demonstration Dataset Notice
                </p>
                <p>
                  This air quality breakdown is synthesized using standard Indian atmospheric dispersion models for academic and evaluation purposes. Values are simulated and do not reflect official regulatory enforcement feeds.
                </p>
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/80 flex items-center justify-end gap-3">
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
            {!isActiveCity ? (
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  onSelectForDashboard(city);
                  onClose();
                }}
              >
                <Check className="w-4 h-4 mr-1.5" aria-hidden="true" />
                Activate for Dashboard
              </Button>
            ) : (
              <Button variant="secondary" size="sm" onClick={onClose}>
                Done (Active)
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

