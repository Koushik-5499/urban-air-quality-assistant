import { CheckCheck, Trash2 } from 'lucide-react';
import { AlertCard } from './AlertCard';
import { AlertEmptyState } from './AlertEmptyState';
import { Button } from '../ui/Button';
import type { AirAlert } from '../../types/alerts';

export interface AlertListProps {
  alerts: AirAlert[];
  unreadCount: number;
  onToggleRead: (id: string) => void;
  onDismiss: (id: string) => void;
  onViewDetails: (alert: AirAlert) => void;
  onMarkAllRead: () => void;
  onClearAll: () => void;
  onResetFilters: () => void;
}

export function AlertList({
  alerts,
  unreadCount,
  onToggleRead,
  onDismiss,
  onViewDetails,
  onMarkAllRead,
  onClearAll,
  onResetFilters,
}: AlertListProps) {
  if (alerts.length === 0) {
    return <AlertEmptyState onResetFilters={onResetFilters} />;
  }

  return (
    <div className="space-y-4">
      {/* Header Actions Bar */}
      <div className="flex items-center justify-between gap-3 text-xs">
        <span className="font-semibold text-slate-500 dark:text-slate-400">
          Showing <strong className="text-slate-900 dark:text-white">{alerts.length}</strong> active alerts
        </span>

        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={onMarkAllRead}
              className="text-xs py-1"
            >
              <CheckCheck className="w-3.5 h-3.5 mr-1 text-emerald-600" />
              Mark All Read
            </Button>
          )}

          <button
            type="button"
            onClick={onClearAll}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium text-slate-500 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Dismiss All</span>
          </button>
        </div>
      </div>

      {/* Grid of Alert Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {alerts.map((alert) => (
          <AlertCard
            key={alert.id}
            alert={alert}
            onToggleRead={onToggleRead}
            onDismiss={onDismiss}
            onViewDetails={onViewDetails}
          />
        ))}
      </div>
    </div>
  );
}

