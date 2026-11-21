import { Loader2 } from 'lucide-react';

export function MapLoading() {
  return (
    <div
      className="w-full h-full min-h-[480px] rounded-2xl bg-slate-100 dark:bg-slate-850 flex flex-col items-center justify-center space-y-3 border border-slate-200 dark:border-slate-800 animate-pulse"
      role="status"
      aria-label="Loading geospatial map tiles"
    >
      <Loader2 className="w-8 h-8 text-emerald-600 animate-spin" />
      <div className="text-center">
        <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
          Initializing Geospatial Map
        </p>
        <p className="text-xs text-slate-400 mt-0.5">
          Loading OpenStreetMap tiles and atmospheric sensor telemetry...
        </p>
      </div>
    </div>
  );
}

