import { useMemo } from 'react';
import { ChartDataTable } from '../common/ChartDataTable';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, Info } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { POLLUTANT_DETAILS } from '../../data/pollutantDetails';
import type { PollutantId, ChartTimeRange } from '../../types/dashboard';
import type { DetailedTrendPoint } from '../../types/pollutants';

export interface PollutantTrendChartProps {
  pollutantId: PollutantId;
  timeRange: ChartTimeRange;
  onTimeRangeChange: (range: ChartTimeRange) => void;
  trendData: DetailedTrendPoint[];
  locationCity: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  label?: string;
  unit: string;
}

function CustomTooltip({ active, payload, label, unit }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    const val = payload[0].value;
    return (
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 shadow-lg text-xs space-y-1">
        <p className="font-semibold text-slate-800 dark:text-slate-200 border-b border-slate-100 dark:border-slate-800 pb-1">
          Time: {label}
        </p>
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-500 dark:text-slate-400">Concentration:</span>
          <span className="font-bold text-slate-900 dark:text-white font-mono">
            {val} {unit}
          </span>
        </div>
      </div>
    );
  }
  return null;
}

export function PollutantTrendChart({
  pollutantId,
  timeRange,
  onTimeRangeChange,
  trendData,
  locationCity,
}: PollutantTrendChartProps) {
  const details = POLLUTANT_DETAILS[pollutantId];
  const unit = details?.unit || 'µg/m³';

  // Statistics: min, max, avg
  const stats = useMemo(() => {
    if (!trendData.length) return { min: 0, max: 0, avg: 0 };
    const values = trendData.map((d) => d[pollutantId]);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const avg = values.reduce((acc, curr) => acc + curr, 0) / values.length;
    return {
      min: Number(min.toFixed(1)),
      max: Number(max.toFixed(1)),
      avg: Number(avg.toFixed(1)),
    };
  }, [trendData, pollutantId]);

  return (
    <Card variant="standard" className="p-6">
      <CardHeader className="p-0 pb-5 border-b border-slate-100 dark:border-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/60">
                <TrendingUp className="w-5 h-5" aria-hidden="true" />
              </span>
              <CardTitle className="text-xl">
                {details?.formula} ({details?.fullName}) Trend Analysis
              </CardTitle>
            </div>
            <CardDescription className="text-xs sm:text-sm">
              Continuous atmospheric telemetry curve for {locationCity} ({unit})
            </CardDescription>
          </div>

          {/* Time Range Tabs */}
          <div className="inline-flex p-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 self-start sm:self-auto">
            {(['24h', '7d', '30d'] as ChartTimeRange[]).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => onTimeRangeChange(r)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  timeRange === r
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                    : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {r === '24h' ? '24 Hours' : r === '7d' ? '7 Days' : '30 Days'}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 pt-6 space-y-5">
        {/* Statistics Bar */}
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850 border border-slate-200/60 dark:border-slate-800 text-center">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Period Minimum
            </span>
            <div className="text-lg font-bold text-slate-800 dark:text-slate-200">
              {stats.min} <span className="text-xs font-normal text-slate-400">{unit}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850 border border-slate-200/60 dark:border-slate-800 text-center">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Period Average
            </span>
            <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400">
              {stats.avg} <span className="text-xs font-normal text-slate-400">{unit}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850 border border-slate-200/60 dark:border-slate-800 text-center">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Period Peak
            </span>
            <div className="text-lg font-bold text-rose-600 dark:text-rose-400">
              {stats.max} <span className="text-xs font-normal text-slate-400">{unit}</span>
            </div>
          </div>
        </div>

        {/* Recharts Line Chart */}
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#94a3b8" strokeOpacity={0.2} />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 11, fill: '#64748b' }}
                stroke="#cbd5e1"
                tickLine={false}
              />
              <YAxis
                unit={` ${unit}`}
                tick={{ fontSize: 11, fill: '#64748b' }}
                stroke="#cbd5e1"
                tickLine={false}
                domain={['auto', 'auto']}
              />
              <Tooltip content={<CustomTooltip unit={unit} />} />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />

              {/* Reference Lines for Standard Limits */}
              {details?.naaqsLimit && (
                <ReferenceLine
                  y={details.naaqsLimit}
                  label={{
                    value: `NAAQS Limit (${details.naaqsLimit} ${unit})`,
                    position: 'top',
                    fill: '#f97316',
                    fontSize: 10,
                  }}
                  stroke="#f97316"
                  strokeDasharray="4 4"
                />
              )}

              {details?.whoLimit && (
                <ReferenceLine
                  y={details.whoLimit}
                  label={{
                    value: `WHO Guideline (${details.whoLimit} ${unit})`,
                    position: 'bottom',
                    fill: '#10b981',
                    fontSize: 10,
                  }}
                  stroke="#10b981"
                  strokeDasharray="4 4"
                />
              )}

              <Line
                type="monotone"
                dataKey={pollutantId}
                name={`${details?.name || pollutantId} Concentration`}
                stroke={details?.color || '#10b981'}
                strokeWidth={3}
                dot={{ r: 4, strokeWidth: 2, fill: '#fff' }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
          <ChartDataTable
            caption={`24-hour ${pollutantId.toUpperCase()} concentration trend`}
            columns={[
              { key: 'time', label: 'Time' },
              { key: pollutantId, label: pollutantId.toUpperCase() },
            ]}
            rows={trendData}
          />
        </div>

        {/* Disclaimer / Unit note */}
        <p className="text-[11px] text-slate-400 flex items-center gap-1.5 pt-2">
          <Info className="w-3.5 h-3.5 text-teal-600 shrink-0" />
          <span>
            Measurement unit: <strong>{unit}</strong>. Reference guidelines indicate safe ambient human exposure thresholds according to WHO & Central Pollution Control Board (CPCB) standards.
          </span>
        </p>
      </CardContent>
    </Card>
  );
}
