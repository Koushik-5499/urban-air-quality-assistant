import { MapPin, Bell, BellOff, Check } from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { DEMO_LOCATIONS, DASHBOARD_DATA } from '../../data/dashboardData';
import { getAQIBadgeVariant, getAQIColor } from '../../data/mapData';
import { saveMonitoredCities } from '../../services/alertService';
import { useState } from 'react';

export interface MonitoredCitiesProps {
  monitoredCityIds: string[];
  onMonitoredCityChange: (cityIds: string[]) => void;
  activeDashboardCityId: string;
  onSelectForDashboard: (cityId: string) => void;
  latestAlerts: Record<string, string>;
}

export function MonitoredCities({
  monitoredCityIds,
  onMonitoredCityChange,
  activeDashboardCityId,
  onSelectForDashboard,
  latestAlerts,
}: MonitoredCitiesProps) {
  const [monitored, setMonitored] = useState<string[]>(monitoredCityIds);

  const handleToggle = (cityId: string) => {
    let updated: string[];
    if (monitored.includes(cityId)) {
      updated = monitored.filter((id) => id !== cityId);
    } else {
      updated = [...monitored, cityId];
    }
    setMonitored(updated);
    saveMonitoredCities(updated);
    onMonitoredCityChange(updated);
  };

  return (
    <Card variant="standard" className="p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Bell className="w-4 h-4 text-emerald-600" />
            <span>Monitored Cities Air Watch</span>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Toggle notifications and surveillance feeds across the 10 supported Indian metropolitan nodes.
          </p>
        </div>

        <Badge variant="neutral" size="sm">
          {monitored.length} of {DEMO_LOCATIONS.length} Cities Active
        </Badge>
      </div>

      {/* Table / List */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left">
          <thead className="bg-slate-50 dark:bg-slate-850 text-slate-500 uppercase tracking-wider text-[10px] border-b border-slate-200 dark:border-slate-800">
            <tr>
              <th className="py-2.5 px-3">City & State</th>
              <th className="py-2.5 px-3">Current AQI</th>
              <th className="py-2.5 px-3">Category</th>
              <th className="py-2.5 px-3">Latest Alert Notice</th>
              <th className="py-2.5 px-3 text-center">Alert Watch</th>
              <th className="py-2.5 px-3 text-right">Dashboard</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {DEMO_LOCATIONS.map((loc) => {
              const dash = DASHBOARD_DATA[loc.id] || DASHBOARD_DATA['coimbatore'];
              const isWatching = monitored.includes(loc.id);
              const isActive = loc.id === activeDashboardCityId;
              const alertSnippet = latestAlerts[loc.id] || 'No active warnings';

              return (
                <tr
                  key={loc.id}
                  className={`hover:bg-slate-50/60 dark:hover:bg-slate-850/60 transition-colors ${
                    isActive ? 'bg-emerald-50/30 dark:bg-emerald-950/20' : ''
                  }`}
                >
                  <td className="py-3 px-3">
                    <div className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      <span>{loc.city}</span>
                    </div>
                    <div className="text-[11px] text-slate-400 pl-5">
                      {loc.state} • {loc.station}
                    </div>
                  </td>

                  <td className="py-3 px-3">
                    <span
                      className="px-2 py-0.5 rounded-full font-mono font-bold text-white text-[11px]"
                      style={{ backgroundColor: getAQIColor(dash.category) }}
                    >
                      {dash.aqi}
                    </span>
                  </td>

                  <td className="py-3 px-3">
                    <Badge variant={getAQIBadgeVariant(dash.category)} size="sm">
                      {dash.category}
                    </Badge>
                  </td>

                  <td className="py-3 px-3 text-slate-600 dark:text-slate-300 max-w-[220px] truncate">
                    {alertSnippet}
                  </td>

                  <td className="py-3 px-3 text-center">
                    <button
                      type="button"
                      onClick={() => handleToggle(loc.id)}
                      className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-semibold border transition-all cursor-pointer ${
                        isWatching
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800 shadow-2xs'
                          : 'bg-slate-100 text-slate-500 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700'
                      }`}
                      aria-label={`${isWatching ? 'Disable' : 'Enable'} alert watch for ${loc.city}`}
                    >
                      {isWatching ? (
                        <>
                          <Bell className="w-3 h-3 text-emerald-600" />
                          <span>Watching</span>
                        </>
                      ) : (
                        <>
                          <BellOff className="w-3 h-3 text-slate-400" />
                          <span>Muted</span>
                        </>
                      )}
                    </button>
                  </td>

                  <td className="py-3 px-3 text-right">
                    {isActive ? (
                      <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 flex items-center justify-end gap-1">
                        <Check className="w-3.5 h-3.5" /> Active
                      </span>
                    ) : (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onSelectForDashboard(loc.id)}
                        className="text-xs text-slate-600 dark:text-slate-300 hover:text-emerald-700"
                      >
                        Set Active
                      </Button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
