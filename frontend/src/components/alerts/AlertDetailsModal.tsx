import { useEffect } from 'react';
import {
  MapPin,
  Clock,
  Sparkles,
  Check,
  RotateCcw,
  Trash2,
  X,
  ShieldAlert,
  Flame,
  ExternalLink,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { AlertSeverityBadge } from './AlertSeverityBadge';
import { getAQIBadgeVariant } from '../../data/mapData';
import type { AirAlert } from '../../types/alerts';
import { Link } from 'react-router-dom';

export interface AlertDetailsModalProps {
  alert: AirAlert | null;
  isOpen: boolean;
  onClose: () => void;
  onToggleRead: (id: string) => void;
  onDismiss: (id: string) => void;
  onSelectForDashboard: (cityId: string) => void;
  isActiveDashboardCity: boolean;
}

export function AlertDetailsModal({
  alert,
  isOpen,
  onClose,
  onToggleRead,
  onDismiss,
  onSelectForDashboard,
  isActiveDashboardCity,
}: AlertDetailsModalProps) {
  // Close on ESC
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || !alert) return null;

  const {
    id,
    cityId,
    city,
    state,
    country,
    station,
    aqi,
    category,
    severity,
    title,
    description,
    recommendedAction,
    dominantPollutant,
    timestamp,
    dateFormatted,
    isRead,
  } = alert;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-labelledby="alert-details-title"
    >
      <div className="w-full max-w-xl rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-start justify-between gap-4 bg-slate-50/50 dark:bg-slate-850/50">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <AlertSeverityBadge severity={severity} size="md" />
              <Badge variant={getAQIBadgeVariant(category)} size="md">
                {aqi} AQI • {category}
              </Badge>
              {isRead ? (
                <span className="text-[11px] text-slate-400">Read</span>
              ) : (
                <span className="text-[11px] font-bold text-emerald-600">New / Unread</span>
              )}
            </div>

            <h3
              id="alert-details-title"
              className="text-xl font-bold text-slate-900 dark:text-white leading-tight"
            >
              {title}
            </h3>

            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
              <MapPin className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              <span>
                {city}, {state}, {country} • Node: {station}
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* Detailed Description */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Atmospheric Event Overview
            </h4>
            <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
              {description}
            </p>
          </div>

          {/* Recommended Precaution Banner */}
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850/80 border border-slate-200/80 dark:border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              <ShieldAlert className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span>Recommended Precautionary Action</span>
            </div>
            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed pl-6">
              {recommendedAction}
            </p>
          </div>

          {/* Telemetry Snapshot Cards */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850 border border-slate-200/60 dark:border-slate-800">
              <span className="text-[10px] font-bold uppercase text-slate-400 block">
                Dominant Contaminant
              </span>
              <div className="text-base font-bold text-amber-900 dark:text-amber-200 flex items-center gap-1.5 mt-0.5">
                <Flame className="w-4 h-4 text-amber-500" />
                <span>{dominantPollutant}</span>
              </div>
              <span className="text-[11px] text-slate-400">Primary active factor</span>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850 border border-slate-200/60 dark:border-slate-800">
              <span className="text-[10px] font-bold uppercase text-slate-400 block">
                Detection Timestamp
              </span>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5 mt-0.5">
                <Clock className="w-4 h-4 text-slate-400" />
                <span>{dateFormatted} ({timestamp})</span>
              </div>
              <span className="text-[11px] text-teal-600 font-medium flex items-center gap-1">
                <Sparkles className="w-3 h-3" /> Simulated Trigger
              </span>
            </div>
          </div>

          {/* Quick Cross-Navigation Links */}
          <div className="pt-2 flex items-center justify-between text-xs border-t border-slate-100 dark:border-slate-800">
            <span className="text-slate-400">Investigate city telemetry:</span>
            <div className="flex items-center gap-3">
              <Link
                to="/pollutants"
                className="text-emerald-600 dark:text-emerald-400 hover:underline font-medium inline-flex items-center gap-1"
              >
                Pollutant Trends <ExternalLink className="w-3 h-3" />
              </Link>
              <Link
                to="/map"
                className="text-teal-600 dark:text-teal-400 hover:underline font-medium inline-flex items-center gap-1"
              >
                Geospatial Map <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850/50 flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            {!isActiveDashboardCity && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => onSelectForDashboard(cityId)}
                className="text-xs"
              >
                <Check className="w-3.5 h-3.5 mr-1" />
                Set as Dashboard City
              </Button>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={() => onToggleRead(id)}
              className="text-xs"
            >
              {isRead ? (
                <>
                  <RotateCcw className="w-3.5 h-3.5 mr-1" />
                  Mark Unread
                </>
              ) : (
                <>
                  <Check className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                  Mark Read
                </>
              )}
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => {
                onDismiss(id);
                onClose();
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors flex items-center gap-1 cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Dismiss</span>
            </button>

            <Button variant="outline" size="sm" onClick={onClose} className="text-xs">
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

