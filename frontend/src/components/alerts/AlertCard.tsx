import {
  MapPin,
  Clock,
  Sparkles,
  Eye,
  Check,
  RotateCcw,
  Trash2,
  ShieldAlert,
} from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { AlertSeverityBadge } from './AlertSeverityBadge';
import { getAQIColor, getAQIBadgeVariant } from '../../data/mapData';
import type { AirAlert } from '../../types/alerts';

export interface AlertCardProps {
  alert: AirAlert;
  onToggleRead: (alertId: string) => void;
  onDismiss: (alertId: string) => void;
  onViewDetails: (alert: AirAlert) => void;
}

export function AlertCard({
  alert,
  onToggleRead,
  onDismiss,
  onViewDetails,
}: AlertCardProps) {
  const {
    id,
    city,
    state,
    station,
    aqi,
    category,
    severity,
    title,
    description,
    recommendedAction,
    timestamp,
    dateFormatted,
    isRead,
  } = alert;

  const aqiColor = getAQIColor(category);

  return (
    <Card
      variant="standard"
      className={`p-5 transition-all relative overflow-hidden flex flex-col justify-between ${
        isRead
          ? 'opacity-85 bg-slate-50/50 dark:bg-slate-900/40 border-slate-200/60 dark:border-slate-800/60'
          : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-xs ring-1 ring-emerald-500/10'
      }`}
    >
      {/* Top Accent Strip Colored by AQI Severity */}
      <div
        className="absolute top-0 left-0 right-0 h-1"
        style={{ backgroundColor: aqiColor }}
      />

      <div className="space-y-3">
        {/* Header: Title, Severity Badge, Unread Dot */}
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              {!isRead && (
                <span
                  className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"
                  title="Unread notification"
                />
              )}
              <h4 className="text-base font-bold text-slate-900 dark:text-white leading-tight">
                {title}
              </h4>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
              <MapPin className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span>
                {city}, {state} • Node: {station}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <AlertSeverityBadge severity={severity} size="sm" />
            <Badge variant={getAQIBadgeVariant(category)} size="sm">
              {aqi} AQI
            </Badge>
          </div>
        </div>

        {/* Short Description */}
        <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
          {description}
        </p>

        {/* Action Callout Box */}
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
          <ShieldAlert className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-slate-900 dark:text-white block">
              Recommended Precaution:
            </span>
            <span className="text-[11px] text-slate-600 dark:text-slate-300 leading-relaxed">
              {recommendedAction}
            </span>
          </div>
        </div>

        {/* Timestamp & Simulated Notice */}
        <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {dateFormatted} ({timestamp})
          </span>
          <span className="flex items-center gap-1 text-teal-600 font-medium">
            <Sparkles className="w-3 h-3" />
            Simulated Sensor Alert
          </span>
        </div>
      </div>

      {/* Action Footer */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onViewDetails(alert)}
          className="text-xs"
        >
          <Eye className="w-3.5 h-3.5 mr-1" />
          View Details
        </Button>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => onToggleRead(id)}
            className="px-2.5 py-1 rounded-lg text-xs font-medium text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex items-center gap-1 cursor-pointer"
            title={isRead ? 'Mark as unread' : 'Mark as read'}
            aria-label={isRead ? 'Mark as unread' : 'Mark as read'}
          >
            {isRead ? (
              <>
                <RotateCcw className="w-3 h-3" />
                <span className="hidden sm:inline">Mark Unread</span>
              </>
            ) : (
              <>
                <Check className="w-3 h-3 text-emerald-600" />
                <span className="hidden sm:inline">Mark Read</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={() => onDismiss(id)}
            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg transition-colors cursor-pointer"
            title="Dismiss alert"
            aria-label="Dismiss alert"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </Card>
  );
}
