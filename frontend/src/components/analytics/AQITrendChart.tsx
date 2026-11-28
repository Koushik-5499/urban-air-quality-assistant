import { useState } from 'react';
import { ChartDataTable } from '../common/ChartDataTable';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, ArrowDownRight, ArrowUpRight, MoveRight, Info, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { HistoricalDataPoint, AnalyticsTimeRange, TrendDirection } from '../../types/analytics';

export interface AQITrendChartProps {
  data: HistoricalDataPoint[];
  timeRange: AnalyticsTimeRange;
  onTimeRangeChange: (range: AnalyticsTimeRange) => void;
  trendDirection: TrendDirection;
  trendPercentageChange: number;
  cityName: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    payload: HistoricalDataPoint;
  }>;
  label?: string;
}

function CustomAQITooltip({ active, payload }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    const point = payload[0].payload;
    return (
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 shadow-lg text-xs space-y-1.5 min-w-[180px]">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-1">
          <span className="font-semibold text-slate-900 dark:text-white">{point.fullDate || point.time}</span>
          <span className="text-[10px] text-slate-400">Sample Point</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">Air Quality Index:</span>
          <span className="font-black text-emerald-600 dark:text-emerald-400 text-sm">
            {point.aqi} AQI
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">Category:</span>
          <span className="font-semibold text-slate-800 dark:text-slate-200">{point.category}</span>
        </div>
        <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-100 dark:border-slate-800">
          <span className="text-slate-400">Dominant Driver:</span>
          <span className="font-medium text-amber-600 dark:text-amber-400">{point.dominantPollutant}</span>
        </div>
      </div>
    );
  }
  return null;
}

export function AQITrendChart({
  data,
  timeRange,
  onTimeRangeChange,
  trendDirection,
  trendPercentageChange,
  cityName,
}: AQITrendChartProps) {
  const [showReferenceLines, setShowReferenceLines] = useState(true);

  const timeRanges: { key: AnalyticsTimeRange; label: string }[] = [
    { key: '24h', label: '24 Hours' },
    { key: '7d', label: '7 Days' },
    { key: '30d', label: '30 Days' },
    { key: '90d', label: '90 Days' },
  ];

  const isImproving = trendDirection === 'improving';
  const isWorsening = trendDirection === 'worsening';

  if (!data || data.length === 0) {
    return (
      <Card variant="standard" className="p-8 text-center">
        <AlertCircle className="w-8 h-8 text-slate-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">No historical telemetry points</h3>
        <p className="text-xs text-slate-500 mt-1">Sample data is currently being generated.</p>
      </Card>
    );
  }

  // Calculate dynamic Y-axis maximum
  const maxAQI = Math.max(...data.map((d) => d.aqi));
  const yAxisMax = Math.min(500, Math.ceil((maxAQI + 40) / 50) * 50);

  return (
    <Card variant="standard" className="flex flex-col">
      <CardHeader className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <CardTitle as="h2" className="text-lg">Air Quality Index Trajectory</CardTitle>
            <Badge
              variant={isImproving ? 'success' : isWorsening ? 'danger' : 'neutral'}
              size="sm"
              className="flex items-center gap-1"
            >
              {isImproving ? (
                <ArrowDownRight className="w-3 h-3" />
              ) : isWorsening ? (
                <ArrowUpRight className="w-3 h-3" />
              ) : (
                <MoveRight className="w-3 h-3" />
              )}
              <span>
                {isImproving ? 'Improving' : isWorsening ? 'Worsening' : 'Stable'} ({trendPercentageChange > 0 ? '+' : ''}
                {trendPercentageChange}%)
              </span>
            </Badge>
          </div>
          <CardDescription className="text-xs mt-0.5">
            Temporal telemetry variations for {cityName} with EPA/CPCB AQI category thresholds
          </CardDescription>
        </div>

        {/* Chart Action Controls */}
        <div className="flex flex-wrap items-center gap-2 self-start md:self-auto">
          {/* Reference Line Toggle */}
          <button
            type="button"
            onClick={() => setShowReferenceLines((prev) => !prev)}
            aria-pressed={showReferenceLines}
            className={`px-2.5 py-1 text-xs font-medium rounded-lg border transition-all cursor-pointer ${
              showReferenceLines
                ? 'border-emerald-300 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300'
                : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-500'
            }`}
          >
            {showReferenceLines ? 'Hide Thresholds' : 'Show Thresholds'}
          </button>

          {/* Time Range Pills */}
          <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800/80 p-0.5">
            {timeRanges.map((r) => (
              <button
                key={r.key}
                type="button"
                onClick={() => onTimeRangeChange(r.key)}
                aria-pressed={timeRange === r.key}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                  timeRange === r.key
                    ? 'bg-white dark:bg-slate-900 text-emerald-700 dark:text-emerald-300 shadow-xs border border-slate-200/60 dark:border-slate-700/60'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {/* Screen Reader Summary */}
        <p className="sr-only">
          Trajectory area chart displaying historical Air Quality Index points for {cityName} across {timeRange}. Current overall trend is {trendDirection} with {trendPercentageChange}% change.
        </p>

        {/* Recharts Area Chart */}
        <div className="w-full h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 15, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="aqiAreaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#16A34A" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#16A34A" stopOpacity={0.0} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.15} vertical={false} />

              <XAxis
                dataKey="time"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                domain={[0, yAxisMax]}
              />

              <Tooltip content={<CustomAQITooltip />} />

              {/* Standard AQI Boundary Reference Lines */}
              {showReferenceLines && (
                <>
                  <ReferenceLine
                    y={50}
                    stroke="#16A34A"
                    strokeDasharray="4 4"
                    label={{ value: 'Good (50)', fill: '#16A34A', fontSize: 10, position: 'insideTopLeft' }}
                  />
                  <ReferenceLine
                    y={100}
                    stroke="#EAB308"
                    strokeDasharray="4 4"
                    label={{ value: 'Moderate (100)', fill: '#CA8A04', fontSize: 10, position: 'insideTopLeft' }}
                  />
                  {yAxisMax >= 200 && (
                    <ReferenceLine
                      y={200}
                      stroke="#F97316"
                      strokeDasharray="4 4"
                      label={{ value: 'Sensitive (200)', fill: '#EA580C', fontSize: 10, position: 'insideTopLeft' }}
                    />
                  )}
                  {yAxisMax >= 300 && (
                    <ReferenceLine
                      y={300}
                      stroke="#EF4444"
                      strokeDasharray="4 4"
                      label={{ value: 'Unhealthy (300)', fill: '#DC2626', fontSize: 10, position: 'insideTopLeft' }}
                    />
                  )}
                </>
              )}

              <Area
                type="monotone"
                dataKey="aqi"
                name="AQI"
                stroke="#16A34A"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#aqiAreaGradient)"
                dot={{ r: 3, fill: '#16A34A' }}
                activeDot={{ r: 6, fill: '#15803D' }}
              />
            </AreaChart>
          </ResponsiveContainer>
          <ChartDataTable
            caption="Historical AQI trend over selected period"
            columns={[
              { key: 'time', label: 'Time' },
              { key: 'aqi', label: 'AQI' },
            ]}
            rows={data}
          />
        </div>

        {/* Threshold Category Legend / Footer */}
        <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-semibold text-slate-700 dark:text-slate-300">Category Bands:</span>
            <span className="inline-flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> 0-50 Good
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-yellow-500" /> 51-100 Moderate
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-orange-500" /> 101-200 Sensitive
            </span>
            <span className="inline-flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> 201-300 Unhealthy
            </span>
          </div>

          <div className="flex items-center gap-1 text-[11px] text-slate-400">
            <Info className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Simulated Telemetry Model ({data.length} Sample Intervals)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

