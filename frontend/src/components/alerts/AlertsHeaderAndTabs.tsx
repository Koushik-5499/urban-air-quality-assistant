import { Link } from 'react-router-dom';
import { Bell, Sliders, Building2, Sparkles, ExternalLink } from 'lucide-react';
import { DataProvenanceBadge } from '../common/DataProvenanceBadge';

export type AlertsTab = 'feed' | 'preferences' | 'cities';

export interface AlertsHeaderAndTabsProps {
  activeCityName: string;
  activeTab: AlertsTab;
  onTabChange: (tab: AlertsTab) => void;
  unreadCount: number;
  monitoredCount: number;
  totalCitiesCount: number;
}

export function AlertsHeaderAndTabs({
  activeCityName,
  activeTab,
  onTabChange,
  unreadCount,
  monitoredCount,
  totalCitiesCount,
}: AlertsHeaderAndTabsProps) {
  return (
    <>
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="p-2 rounded-xl bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-400 border border-teal-200/60 dark:border-teal-800/60">
              <Bell className="w-5 h-5" aria-hidden="true" />
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Air Quality Alerts & Advisories
            </h1>
            <DataProvenanceBadge />
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-300 max-w-3xl">
            Real-time environmental threshold notifications, rapid deterioration warnings, and sensitive group advisories for monitored urban regions across India.
          </p>
        </div>

        <div className="text-xs text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800/60 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700/60 flex items-center gap-1.5 self-start md:self-auto">
          <span>Active City:</span>
          <span className="font-semibold text-slate-800 dark:text-slate-200">{activeCityName}</span>
          <span className="text-slate-400 dark:text-slate-500">•</span>
          <Link
            to="/dashboard"
            className="text-teal-700 dark:text-teal-300 hover:underline inline-flex items-center gap-0.5 min-h-[44px]"
          >
            Dashboard
            <ExternalLink className="w-3 h-3" aria-hidden="true" />
          </Link>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-2">
        <div
          role="tablist"
          aria-label="Alerts view switcher"
          className="inline-flex p-1 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-xs font-semibold self-start"
        >
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'feed'}
            onClick={() => onTabChange('feed')}
            className={`px-3.5 py-2 min-h-[44px] rounded-lg transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'feed'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Bell className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Alert Feed</span>
            {unreadCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-rose-600 text-white text-[10px] font-bold">
                {unreadCount}
              </span>
            )}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'preferences'}
            onClick={() => onTabChange('preferences')}
            className={`px-3.5 py-2 min-h-[44px] rounded-lg transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'preferences'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Threshold Preferences</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'cities'}
            onClick={() => onTabChange('cities')}
            className={`px-3.5 py-2 min-h-[44px] rounded-lg transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'cities'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" aria-hidden="true" />
            <span>
              Monitored Cities ({monitoredCount}/{totalCitiesCount})
            </span>
          </button>
        </div>

        <span className="text-xs text-slate-600 dark:text-slate-300 flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" aria-hidden="true" />
          Synchronized with FastAPI Alert & Notification Engine
        </span>
      </div>
    </>
  );
}
