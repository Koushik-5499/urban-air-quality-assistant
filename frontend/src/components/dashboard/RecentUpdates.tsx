import { History, MapPin, Activity } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { RecentUpdateItem } from '../../types/dashboard';

export interface RecentUpdatesProps {
  updates: RecentUpdateItem[];
}

export function RecentUpdates({ updates }: RecentUpdatesProps) {
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
    <Card variant="standard">
      <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/60">
              <History className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <CardTitle className="text-base">Recent Telemetry Recordings</CardTitle>
              <CardDescription className="text-xs">
                Sequential sample readings logged across regional sensor nodes
              </CardDescription>
            </div>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            Simulated Log
          </span>
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        <div className="space-y-3">
          {updates.map((item) => (
            <div
              key={item.id}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-xl bg-slate-50/70 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 hover:border-emerald-500/40 dark:hover:border-emerald-500/40 transition-colors"
            >
              {/* Left: Time and Station info */}
              <div className="flex items-center gap-3">
                <div className="flex flex-col items-center justify-center w-12 h-12 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white font-bold text-sm shrink-0 shadow-xs">
                  <span>{item.aqi}</span>
                  <span className="text-[9px] font-medium text-slate-400">AQI</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                      {item.time}
                    </span>
                    <Badge variant={getBadgeVariant(item.category)} size="sm">
                      {item.category}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    <MapPin className="w-3 h-3 text-slate-400" aria-hidden="true" />
                    <span>{item.station}</span>
                  </div>
                </div>
              </div>

              {/* Right: Dominant pollutant tag */}
              <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 pl-15 sm:pl-0">
                <Activity className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                <span>Primary: {item.dominantPollutant}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
