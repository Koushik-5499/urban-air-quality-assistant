import { useState } from 'react';
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
import { TrendingUp, Info } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { ChartDataTable } from '../common/ChartDataTable';
import type { ChartTimeRange, TrendDataPoint } from '../../types/dashboard';

export interface AirQualityChartProps {
  trends: Record<ChartTimeRange, TrendDataPoint[]>;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    dataKey: string;
  }>;
  label?: string;
}

function CustomChartTooltip({ active, payload, label }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 shadow-lg text-xs space-y-1.5">
        <p className="font-semibold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-1">
          Time: {label}
        </p>
        {payload.map((entry) => (
          <div key={entry.dataKey} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: entry.color }}
              />
              <span>{entry.name}:</span>
            </span>
            <span className="font-bold text-slate-900 dark:text-white">
              {entry.value} {entry.name === 'AQI' ? '' : 'µg/m³'}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
}

export function AirQualityChart({ trends }: AirQualityChartProps) {
  const [selectedRange, setSelectedRange] = useState<ChartTimeRange>('24h');

  const chartData = trends[selectedRange] || [];

  const rangeButtons: { key: ChartTimeRange; label: string }[] = [
    { key: '24h', label: '24 Hours' },
    { key: '7d', label: '7 Days' },
    { key: '30d', label: '30 Days' },
  ];

  return (
    <Card variant="standard" className="flex flex-col">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <CardTitle className="text-lg">Pollutant & AQI Telemetry Trends</CardTitle>
          </div>
          <CardDescription className="text-xs mt-0.5">
            Comparative temporal trends for overall AQI, PM2.5, and PM10
          </CardDescription>
        </div>

        {/* Time-Range Selector Buttons */}
        <div className="flex items-center gap-1.5 p-1 rounded-lg bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 self-start sm:self-auto">
          {rangeButtons.map((btn) => (
            <button
              key={btn.key}
              type="button"
              onClick={() => setSelectedRange(btn.key)}
              aria-pressed={selectedRange === btn.key}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                selectedRange === btn.key
                  ? 'bg-white dark:bg-slate-900 text-emerald-700 dark:text-emerald-300 shadow-xs border border-slate-200/60 dark:border-slate-700/60'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent className="pt-6">
        {/* Screen reader data summary */}
        <p className="sr-only">
          Line chart representing temporal trends for overall Air Quality Index, PM2.5, and PM10 across {selectedRange === '24h' ? 'the past 24 hours' : selectedRange === '7d' ? 'the past 7 days' : 'the past 30 days'}.
        </p>

        {/* Recharts Container */}
        <div className="w-full h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#94a3b8"
                opacity={0.15}
                vertical={false}
              />
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
              />
              <Tooltip content={<CustomChartTooltip />} />
              <Legend
                verticalAlign="top"
                align="right"
                iconType="circle"
                wrapperStyle={{ paddingBottom: '16px', fontSize: '12px' }}
              />
              <Line
                type="monotone"
                dataKey="aqi"
                name="AQI"
                stroke="#16A34A"
                strokeWidth={2.5}
                dot={{ r: 3, fill: '#16A34A' }}
                activeDot={{ r: 5 }}
              />
              <Line
                type="monotone"
                dataKey="pm25"
                name="PM2.5"
                stroke="#F59E0B"
                strokeWidth={2}
                dot={{ r: 2.5, fill: '#F59E0B' }}
                activeDot={{ r: 4 }}
              />
              <Line
                type="monotone"
                dataKey="pm10"
                name="PM10"
                stroke="#0F766E"
                strokeWidth={2}
                dot={{ r: 2.5, fill: '#0F766E' }}
                activeDot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
          <ChartDataTable
            caption="Hourly AQI, PM2.5, and PM10 air quality telemetry"
            columns={[
              { key: 'time', label: 'Time' },
              { key: 'aqi', label: 'AQI' },
              { key: 'pm25', label: 'PM2.5 (µg/m³)' },
              { key: 'pm10', label: 'PM10 (µg/m³)' },
            ]}
            rows={chartData}
          />
        </div>

        {/* Chart Disclaimer Notice */}
        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-600 dark:text-slate-300">
          <span className="flex items-center gap-1">
            <Info className="w-3.5 h-3.5" aria-hidden="true" />
            Showing simulated trend curves for {selectedRange === '24h' ? 'past 24 hours' : selectedRange === '7d' ? 'past 7 days' : 'past 30 days'}
          </span>
          <span>Sample Telemetry Model</span>
        </div>
      </CardContent>
    </Card>
  );
}
