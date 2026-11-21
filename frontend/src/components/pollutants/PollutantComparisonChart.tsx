import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Layers, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { POLLUTANT_DETAILS } from '../../data/pollutantDetails';
import type { PollutantId, ChartTimeRange } from '../../types/dashboard';
import type { DetailedTrendPoint } from '../../types/pollutants';

export interface PollutantComparisonChartProps {
  selectedPollutants: PollutantId[];
  onTogglePollutant: (id: PollutantId) => void;
  onClearComparison: () => void;
  timeRange: ChartTimeRange;
  onTimeRangeChange: (range: ChartTimeRange) => void;
  trendData: DetailedTrendPoint[];
  comparisonMode: 'normalized' | 'individual';
  onComparisonModeChange: (mode: 'normalized' | 'individual') => void;
}

interface CustomComparisonTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    dataKey: string;
  }>;
  label?: string;
  mode: 'normalized' | 'individual';
}

function CustomComparisonTooltip({
  active,
  payload,
  label,
  mode,
}: CustomComparisonTooltipProps) {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 shadow-lg text-xs space-y-2 min-w-[200px]">
        <p className="font-semibold text-slate-800 dark:text-slate-200 border-b border-slate-100 dark:border-slate-800 pb-1">
          Time: {label}
        </p>
        <div className="space-y-1">
          {payload.map((entry) => {
            const pId = entry.dataKey as PollutantId;
            const details = POLLUTANT_DETAILS[pId];
            return (
              <div key={entry.dataKey} className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-1.5 font-medium text-slate-600 dark:text-slate-300">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ backgroundColor: entry.color }}
                  />
                  <span>{details?.formula || entry.name}:</span>
                </span>
                <span className="font-bold text-slate-900 dark:text-white font-mono">
                  {mode === 'normalized'
                    ? `${entry.value}% of limit`
                    : `${entry.value} ${details?.unit || ''}`}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  return null;
}

export function PollutantComparisonChart({
  selectedPollutants,
  onTogglePollutant,
  onClearComparison,
  timeRange,
  onTimeRangeChange,
  trendData,
  comparisonMode,
  onComparisonModeChange,
}: PollutantComparisonChartProps) {
  const allPollutantIds: PollutantId[] = ['pm25', 'pm10', 'co', 'no2', 'so2', 'o3'];

  // Calculate normalized data if in normalized benchmark mode
  const normalizedData: DetailedTrendPoint[] = trendData.map((d) => {
    return {
      time: d.time,
      pm25: Number(((d.pm25 / (POLLUTANT_DETAILS.pm25.naaqsLimit || 60)) * 100).toFixed(1)),
      pm10: Number(((d.pm10 / (POLLUTANT_DETAILS.pm10.naaqsLimit || 100)) * 100).toFixed(1)),
      co: Number(((d.co / (POLLUTANT_DETAILS.co.naaqsLimit || 2)) * 100).toFixed(1)),
      no2: Number(((d.no2 / (POLLUTANT_DETAILS.no2.naaqsLimit || 80)) * 100).toFixed(1)),
      so2: Number(((d.so2 / (POLLUTANT_DETAILS.so2.naaqsLimit || 80)) * 100).toFixed(1)),
      o3: Number(((d.o3 / (POLLUTANT_DETAILS.o3.naaqsLimit || 100)) * 100).toFixed(1)),
      aqi: d.aqi,
    };
  });

  const chartData: DetailedTrendPoint[] = comparisonMode === 'normalized' ? normalizedData : trendData;

  return (
    <Card variant="standard" className="p-6">
      <CardHeader className="p-0 pb-5 border-b border-slate-100 dark:border-slate-800">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-400 border border-teal-200/60 dark:border-teal-800/60">
                <Layers className="w-5 h-5" aria-hidden="true" />
              </span>
              <CardTitle className="text-xl">
                Multi-Pollutant Comparative Dynamics
              </CardTitle>
            </div>
            <CardDescription className="text-xs sm:text-sm">
              Cross-pollutant correlation analysis. Normalized by statutory limit benchmarks to avoid deceptive multi-unit axes.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Mode Switcher */}
            <div className="inline-flex p-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold">
              <button
                type="button"
                onClick={() => onComparisonModeChange('normalized')}
                className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  comparisonMode === 'normalized'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                % of Standard Limit (Recommended)
              </button>
              <button
                type="button"
                onClick={() => onComparisonModeChange('individual')}
                className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  comparisonMode === 'individual'
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                Raw Concentration
              </button>
            </div>

            {/* Time Range Tabs */}
            <div className="inline-flex p-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold">
              {(['24h', '7d', '30d'] as ChartTimeRange[]).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => onTimeRangeChange(r)}
                  className={`px-2.5 py-1.5 rounded-lg transition-all cursor-pointer ${
                    timeRange === r
                      ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                      : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 pt-6 space-y-6">
        {/* Selection Chips */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-slate-500 mr-1">
            Compare Pollutants:
          </span>
          {allPollutantIds.map((id) => {
            const isChecked = selectedPollutants.includes(id);
            const details = POLLUTANT_DETAILS[id];
            return (
              <button
                key={id}
                type="button"
                onClick={() => onTogglePollutant(id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all flex items-center gap-1.5 cursor-pointer ${
                  isChecked
                    ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800 shadow-xs'
                    : 'bg-white dark:bg-slate-850 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-slate-300'
                }`}
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: details?.color }}
                />
                <span>{details?.formula}</span>
                <span className="text-[10px] text-slate-400 font-mono">({details?.unit})</span>
              </button>
            );
          })}

          {selectedPollutants.length > 0 && (
            <button
              type="button"
              onClick={onClearComparison}
              className="text-xs text-slate-400 hover:text-rose-500 transition-colors ml-auto cursor-pointer"
            >
              Reset Comparison
            </button>
          )}
        </div>

        {/* Incompatible unit warning when in raw concentration mode and CO is selected */}
        {comparisonMode === 'individual' && selectedPollutants.includes('co') && selectedPollutants.length > 1 && (
          <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 flex items-start gap-2.5 text-xs text-amber-900 dark:text-amber-200">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <p>
              <strong>Scientific Notice:</strong> CO is measured in <strong>mg/m³</strong>, whereas particulates and oxides are measured in <strong>µg/m³</strong> (a 1000× scale difference). We strongly recommend switching to <strong>"% of Standard Limit"</strong> mode above for valid comparative curves.
            </p>
          </div>
        )}

        {/* Chart View */}
        {selectedPollutants.length === 0 ? (
          <div className="p-12 text-center rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800">
            <Layers className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No pollutants selected for comparison
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Select at least two pollutants from the chips above to view comparative dynamics.
            </p>
          </div>
        ) : (
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#94a3b8" strokeOpacity={0.2} />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  stroke="#cbd5e1"
                  tickLine={false}
                />
                <YAxis
                  unit={comparisonMode === 'normalized' ? '%' : ''}
                  tick={{ fontSize: 11, fill: '#64748b' }}
                  stroke="#cbd5e1"
                  tickLine={false}
                />
                <Tooltip content={<CustomComparisonTooltip mode={comparisonMode} />} />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />

                {selectedPollutants.map((id) => {
                  const details = POLLUTANT_DETAILS[id];
                  return (
                    <Line
                      key={id}
                      type="monotone"
                      dataKey={id}
                      name={
                        comparisonMode === 'normalized'
                          ? `${details?.formula} (% limit)`
                          : `${details?.formula} (${details?.unit})`
                      }
                      stroke={details?.color || '#10b981'}
                      strokeWidth={2.5}
                      dot={{ r: 3 }}
                    />
                  );
                })}
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
