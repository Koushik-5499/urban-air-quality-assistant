import { useState } from 'react';
import { Layers, ChevronDown, ChevronUp } from 'lucide-react';

const AQI_SCALE = [
  { label: 'Good', range: '0–50', color: '#16A34A', text: 'Clean atmospheric air' },
  { label: 'Moderate', range: '51–100', color: '#EAB308', text: 'Acceptable ambient quality' },
  { label: 'Sensitive', range: '101–150', color: '#F97316', text: 'Unhealthy for sensitive groups' },
  { label: 'Unhealthy', range: '151–200', color: '#DC2626', text: 'Adverse effects on public' },
  { label: 'Very Unhealthy', range: '201–300', color: '#9333EA', text: 'Health alert conditions' },
  { label: 'Hazardous', range: '301–500', color: '#7F1D1D', text: 'Emergency conditions' },
];

export function MapLegend() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="rounded-2xl bg-white/95 dark:bg-slate-900/95 backdrop-blur-xs border border-slate-200/80 dark:border-slate-800 shadow-lg text-xs overflow-hidden transition-all duration-300">
      {/* Header Toggle */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-slate-800 dark:text-slate-200 font-bold hover:bg-slate-50 dark:hover:bg-slate-850 transition-colors cursor-pointer"
        aria-expanded={isOpen}
        aria-controls="map-legend-content"
      >
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          <span>AQI Scale & Map Legend</span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        )}
      </button>

      {/* Expandable Legend Content */}
      {isOpen && (
        <div id="map-legend-content" className="p-4 pt-1 space-y-3 border-t border-slate-100 dark:border-slate-800">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {AQI_SCALE.map((item) => (
              <div
                key={item.label}
                className="flex items-center gap-2 p-1.5 rounded-lg bg-slate-50 dark:bg-slate-850/60 border border-slate-100 dark:border-slate-800"
              >
                <span
                  className="w-3 h-3 rounded-full shrink-0 shadow-xs"
                  style={{ backgroundColor: item.color }}
                />
                <div className="leading-tight">
                  <span className="font-semibold text-slate-800 dark:text-slate-200 block text-[11px]">
                    {item.label}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">
                    {item.range}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Marker & Heatmap Visual Indicators */}
          <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between gap-3 text-[11px] text-slate-500 dark:text-slate-400 flex-wrap">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full border-2 border-emerald-500 bg-emerald-500 animate-pulse" />
              <span>Selected Active City</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-400 opacity-60" />
              <span>Simulated Dispersion Field</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
