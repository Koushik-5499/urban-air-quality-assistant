import { Bell, AlertTriangle, Mail, Building2 } from 'lucide-react';
import { Card } from '../ui/Card';

export interface AlertSummaryCardsProps {
  totalAlerts: number;
  unreadAlerts: number;
  criticalAlerts: number;
  monitoredCitiesCount: number;
  totalCitiesCount: number;
}

export function AlertSummaryCards({
  totalAlerts,
  unreadAlerts,
  criticalAlerts,
  monitoredCitiesCount,
  totalCitiesCount,
}: AlertSummaryCardsProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Total Alerts */}
      <Card variant="standard" className="p-4 flex items-center justify-between">
        <div className="space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Total Active Alerts
          </span>
          <div className="text-2xl font-black text-slate-900 dark:text-white">
            {totalAlerts}
          </div>
          <span className="text-[11px] text-slate-500">Across monitored nodes</span>
        </div>
        <div className="p-3 rounded-2xl bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-400 border border-teal-200/60 dark:border-teal-800/60">
          <Bell className="w-5 h-5" />
        </div>
      </Card>

      {/* 2. Unread Alerts */}
      <Card variant="standard" className="p-4 flex items-center justify-between">
        <div className="space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Unread Notifications
          </span>
          <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
            {unreadAlerts}
          </div>
          <span className="text-[11px] text-slate-500">Awaiting user review</span>
        </div>
        <div className="p-3 rounded-2xl bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/60">
          <Mail className="w-5 h-5" />
        </div>
      </Card>

      {/* 3. Critical Alerts */}
      <Card
        variant="standard"
        className={`p-4 flex items-center justify-between ${
          criticalAlerts > 0
            ? 'border-rose-300 dark:border-rose-900/60 ring-1 ring-rose-500/20'
            : ''
        }`}
      >
        <div className="space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Critical Warnings
          </span>
          <div className="text-2xl font-black text-rose-600 dark:text-rose-400">
            {criticalAlerts}
          </div>
          <span className="text-[11px] text-rose-600/80 dark:text-rose-400/80 font-medium">
            AQI &gt; 150 (Unhealthy)
          </span>
        </div>
        <div className="p-3 rounded-2xl bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border border-rose-200/60 dark:border-rose-800/60">
          <AlertTriangle className="w-5 h-5" />
        </div>
      </Card>

      {/* 4. Monitored Cities */}
      <Card variant="standard" className="p-4 flex items-center justify-between">
        <div className="space-y-1">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Monitored Cities
          </span>
          <div className="text-2xl font-black text-slate-900 dark:text-white">
            {monitoredCitiesCount}{' '}
            <span className="text-xs font-normal text-slate-400">/ {totalCitiesCount}</span>
          </div>
          <span className="text-[11px] text-slate-500">Active regional telemetry</span>
        </div>
        <div className="p-3 rounded-2xl bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
          <Building2 className="w-5 h-5" />
        </div>
      </Card>
    </div>
  );
}

