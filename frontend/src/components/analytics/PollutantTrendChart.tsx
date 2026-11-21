import { useState } from 'react';
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
import { Wind, Shield, Bookmark } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { POLLUTANT_DETAILS } from '../../data/pollutantDetails';
import type { PollutantId } from '../../types/dashboard';
import type { HistoricalDataPoint, PollutantStats } from '../../types/analytics';

export interface PollutantTrendChartProps {
  data: HistoricalDataPoint[];
  selectedPollutant: PollutantId;
  onPollutantChange: (id: PollutantId) => void;
  stats: PollutantStats;
  timeRangeLabel: string;
}

interface CustomPollutantTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    payload: HistoricalDataPoint;
  }>;
  unit: string;
  whoLimit: number;
  naaqsLimit: number;
}

function CustomPollutantTooltip({
  active,
  payload,
  unit,
  whoLimit,
  naaqsLimit,
}: CustomPollutantTooltipProps) {
  if (active && payload && payload.length) {
    const point = payload[0].payload;
    const val = payload[0].value;
    const isOverNaaqs = val > naaqsLimit;
    const isOverWho = val > whoLimit;

    return (
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 shadow-lg text-xs space-y-1.5 min-w-[200px]">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-1">
          <span className="font-semibold text-slate-900 dark:text-white">{point.fullDate || point.time}</span>
          <span className="text-[10px] text-slate-400">Sample Interval</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">Concentration:</span>
          <span className="font-bold text-slate-900 dark:text-white text-sm">
            {val} {unit}
          </span>
        </div>
        <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-100 dark:border-slate-800">
          <span className="text-slate-400">vs WHO Target ({whoLimit} {unit}):</span>
          <span className={`font-semibold ${isOverWho ? 'text-amber-600 dark:text-amber-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
            {isOverWho ? 'Exceeded' : 'Within'}
          </span>
        </div>
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-slate-400">vs NAAQS Standard ({naaqsLimit} {unit}):</span>
          <span className={`font-semibold ${isOverNaaqs ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
            {isOverNaaqs ? 'Exceeded' : 'Compliant'}
          </span>
        </div>
      </div>
    );
  }
  return null;
}

export function PollutantTrendChart({
  data,
  selectedPollutant,
  onPollutantChange,
  stats,
  timeRangeLabel,
}: PollutantTrendChartProps) {
  const [showBenchmarks, setShowBenchmarks] = useState(true);

  const pollutantList: PollutantId[] = ['pm25', 'pm10', 'co', 'no2', 'so2', 'o3'];
  const currentMeta = POLLUTANT_DETAILS[selectedPollutant];

  // Chart data extraction
  const chartPoints = data.map((d) => ({
    time: d.time,
    fullDate: d.fullDate,
    value:
      selectedPollutant === 'pm25'
        ? d.pm25
        : selectedPollutant === 'pm10'
        ? d.pm10
        : selectedPollutant === 'co'
        ? d.co
        : selectedPollutant === 'no2'
        ? d.no2
        : selectedPollutant === 'so2'
        ? d.so2
        : d.o3,
  }));

  const maxVal = Math.max(...chartPoints.map((p) => p.value), currentMeta.naaqsLimit * 1.1);
  const isCo = selectedPollutant === 'co';
  const yAxisMax = isCo ? Math.ceil(maxVal * 1.2 * 10) / 10 : Math.ceil((maxVal * 1.15) / 10) * 10;

  return (
    <Card variant="standard" className="flex flex-col">
      <CardHeader className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Wind className="w-5 h-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <CardTitle className="text-lg">Individual Pollutant Historical Trajectory</CardTitle>
          </div>
          <CardDescription className="text-xs mt-0.5">
            Concentration trends across {timeRangeLabel} with WHO guidelines and National Ambient Air Quality Standards (NAAQS)
          </CardDescription>
        </div>

        {/* Pollutant Selector Pills */}
        <div className="flex flex-wrap items-center gap-1.5 self-start lg:self-auto">
          {pollutantList.map((id) => {
            const meta = POLLUTANT_DETAILS[id];
            const isSelected = selectedPollutant === id;
            return (
              <button
                key={id}
                type="button"
                onClick={() => onPollutantChange(id)}
                aria-pressed={isSelected}
                className={`px-3 py-1.5 text-xs font-bold rounded-lg border transition-all cursor-pointer flex items-center gap-1.5 ${
                  isSelected
                    ? 'border-emerald-600 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-300 shadow-xs'
                    : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: meta.color }}
                  aria-hidden="true"
                />
                <span>{meta.formula}</span>
                <span className="text-[10px] font-normal text-slate-400 hidden sm:inline">
                  ({meta.unit})
                </span>
              </button>
            );
          })}
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {/* Screen Reader Summary */}
        <p className="sr-only">
          Historical concentration trend chart for {currentMeta.fullName} ({currentMeta.formula}) measured in {stats.unit}. Current: {stats.current}, Average: {stats.average}, Minimum: {stats.min}, Maximum: {stats.max}.
        </p>

        {/* Metric Chips Row */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-2.5">
            <span className="text-[10px] font-semibold uppercase text-slate-400">Current</span>
            <p className="text-base font-bold text-slate-900 dark:text-white mt-0.5">
              {stats.current} <span className="text-xs font-normal text-slate-500">{stats.unit}</span>
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-2.5">
            <span className="text-[10px] font-semibold uppercase text-slate-400">Average</span>
            <p className="text-base font-bold text-slate-900 dark:text-white mt-0.5">
              {stats.average} <span className="text-xs font-normal text-slate-500">{stats.unit}</span>
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-2.5">
            <span className="text-[10px] font-semibold uppercase text-slate-400">Minimum</span>
            <p className="text-base font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
              {stats.min} <span className="text-xs font-normal text-slate-500">{stats.unit}</span>
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-2.5">
            <span className="text-[10px] font-semibold uppercase text-slate-400">Maximum</span>
            <p className="text-base font-bold text-rose-600 dark:text-rose-400 mt-0.5">
              {stats.max} <span className="text-xs font-normal text-slate-500">{stats.unit}</span>
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-2.5">
            <span className="text-[10px] font-semibold uppercase text-slate-400">WHO Target</span>
            <p className="text-base font-bold text-amber-600 dark:text-amber-400 mt-0.5">
              {stats.whoLimit} <span className="text-xs font-normal text-slate-500">{stats.unit}</span>
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-2.5">
            <span className="text-[10px] font-semibold uppercase text-slate-400">NAAQS Limit</span>
            <p className="text-base font-bold text-slate-700 dark:text-slate-300 mt-0.5">
              {stats.naaqsLimit} <span className="text-xs font-normal text-slate-500">{stats.unit}</span>
            </p>
          </div>
        </div>

        {/* Recharts Area Chart */}
        <div className="w-full h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartPoints} margin={{ top: 10, right: 15, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id={`pollutant-grad-${selectedPollutant}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={currentMeta.color} stopOpacity={0.4} />
                  <stop offset="95%" stopColor={currentMeta.color} stopOpacity={0.0} />
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

              <Tooltip
                content={
                  <CustomPollutantTooltip
                    unit={stats.unit}
                    whoLimit={stats.whoLimit}
                    naaqsLimit={stats.naaqsLimit}
                  />
                }
              />

              {/* Standard Threshold Reference Lines */}
              {showBenchmarks && (
                <>
                  <ReferenceLine
                    y={stats.whoLimit}
                    stroke="#D97706"
                    strokeDasharray="4 4"
                    label={{
                      value: `WHO (${stats.whoLimit} ${stats.unit})`,
                      fill: '#D97706',
                      fontSize: 10,
                      position: 'insideTopLeft',
                    }}
                  />
                  <ReferenceLine
                    y={stats.naaqsLimit}
                    stroke="#DC2626"
                    strokeDasharray="4 4"
                    label={{
                      value: `NAAQS (${stats.naaqsLimit} ${stats.unit})`,
                      fill: '#DC2626',
                      fontSize: 10,
                      position: 'insideTopLeft',
                    }}
                  />
                </>
              )}

              <Area
                type="monotone"
                dataKey="value"
                name={currentMeta.fullName}
                stroke={currentMeta.color}
                strokeWidth={2.5}
                fillOpacity={1}
                fill={`url(#pollutant-grad-${selectedPollutant})`}
                dot={{ r: 3, fill: currentMeta.color }}
                activeDot={{ r: 5, fill: currentMeta.accentColor }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Informational Context Banner */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/40 p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5 font-semibold text-slate-900 dark:text-white">
              <Shield className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>{currentMeta.fullName} ({currentMeta.classification})</span>
            </div>
            <p className="text-slate-500 dark:text-slate-400 text-[11px] line-clamp-1">
              Primary Sources: {currentMeta.primarySources.slice(0, 2).join(' • ')}
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowBenchmarks((prev) => !prev)}
            aria-pressed={showBenchmarks}
            className="text-emerald-700 dark:text-emerald-400 hover:underline flex items-center gap-1 text-[11px] font-semibold shrink-0 cursor-pointer"
          >
            <Bookmark className="w-3.5 h-3.5" />
            {showBenchmarks ? 'Hide Standards' : 'Show Standards'}
          </button>
        </div>
      </CardContent>
    </Card>
  );
}
