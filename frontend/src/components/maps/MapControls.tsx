import { Plus, Minus, RotateCcw, Crosshair, Flame, MapPin } from 'lucide-react';

export interface MapControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView: () => void;
  onLocateSelected: () => void;
  showHeatmap: boolean;
  onToggleHeatmap: () => void;
  showMarkers: boolean;
  onToggleMarkers: () => void;
  hasSelectedCity: boolean;
}

export function MapControls({
  onZoomIn,
  onZoomOut,
  onResetView,
  onLocateSelected,
  showHeatmap,
  onToggleHeatmap,
  showMarkers,
  onToggleMarkers,
  hasSelectedCity,
}: MapControlsProps) {
  return (
    <div className="flex flex-col gap-2">
      {/* Zoom & View Reset Cluster */}
      <div className="flex flex-col rounded-xl bg-white/95 dark:bg-slate-900/95 backdrop-blur-xs border border-slate-200/80 dark:border-slate-800 shadow-md overflow-hidden">
        <button
          type="button"
          onClick={onZoomIn}
          className="p-2.5 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors border-b border-slate-100 dark:border-slate-800 cursor-pointer"
          aria-label="Zoom in on map"
        >
          <Plus className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={onZoomOut}
          className="p-2.5 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors border-b border-slate-100 dark:border-slate-800 cursor-pointer"
          aria-label="Zoom out on map"
        >
          <Minus className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={onResetView}
          className="p-2.5 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          title="Reset map to whole India view"
          aria-label="Reset map to national India view"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Focus & Layer Toggles Cluster */}
      <div className="flex flex-col rounded-xl bg-white/95 dark:bg-slate-900/95 backdrop-blur-xs border border-slate-200/80 dark:border-slate-800 shadow-md overflow-hidden">
        <button
          type="button"
          onClick={onLocateSelected}
          disabled={!hasSelectedCity}
          className="p-2.5 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 transition-colors border-b border-slate-100 dark:border-slate-800 cursor-pointer"
          title="Center on currently selected city"
          aria-label="Center on active selected city"
        >
          <Crosshair className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
        </button>

        <button
          type="button"
          onClick={onToggleHeatmap}
          className={`p-2.5 transition-colors border-b border-slate-100 dark:border-slate-800 cursor-pointer ${
            showHeatmap
              ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/60 dark:text-amber-400 font-bold'
              : 'text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
          title="Toggle atmospheric dispersion heatmap"
          aria-label="Toggle atmospheric dispersion heatmap"
        >
          <Flame className="w-4 h-4" />
        </button>

        <button
          type="button"
          onClick={onToggleMarkers}
          className={`p-2.5 transition-colors cursor-pointer ${
            showMarkers
              ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400 font-bold'
              : 'text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800'
          }`}
          title="Toggle AQI city pin markers"
          aria-label="Toggle AQI city pin markers"
        >
          <MapPin className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

