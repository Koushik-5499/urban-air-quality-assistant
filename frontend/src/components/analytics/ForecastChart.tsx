import {
  ResponsiveContainer,
  AreaChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import {
  Sparkles,
  AlertTriangle,
  ArrowUpRight,
  ArrowDownRight,
  MoveRight,
  Info,
  ShieldAlert,
  Clock,
  HeartPulse,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { ForecastHorizon, ForecastReport, ForecastDataPoint } from '../../types/analytics';
import type { AQICategory } from '../../types/dashboard';

export interface ForecastChartProps {
  forecast: ForecastReport;
  currentAQI: number;
  cityName: string;
  horizon: ForecastHorizon;
  onHorizonChange: (horizon: ForecastHorizon) => void;
}

function getBadgeVariant(cat: AQICategory): 'success' | 'warning' | 'danger' | 'info' | 'default' {
  switch (cat) {
    case 'Good':
      return 'success';
    case 'Moderate':
      return 'warning';
    case 'Unhealthy for Sensitive Groups':
    case 'Unhealthy':
    case 'Very Unhealthy':
    case 'Hazardous':
      return 'danger';
    default:
      return 'default';
  }
}

interface CustomForecastTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    payload: ForecastDataPoint;
  }>;
}

function CustomForecastTooltip({ active, payload }: CustomForecastTooltipProps) {
  if (active && payload && payload.length) {
    const pt = payload[0].payload;
    return (
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 shadow-lg text-xs space-y-1.5 min-w-[200px]">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-1">
          <span className="font-semibold text-slate-900 dark:text-white">{pt.label}</span>
          <span className="text-[10px] text-teal-600 dark:text-teal-400 font-semibold">{pt.time}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">Projected AQI:</span>
          <span className="font-black text-teal-600 dark:text-teal-400 text-sm">
            {pt.predictedAQI} AQI
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">Predicted Category:</span>
          <span className="font-semibold text-slate-800 dark:text-slate-200">{pt.predictedCategory}</span>
        </div>
        <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-100 dark:border-slate-800">
          <span className="text-slate-400">Confidence Band:</span>
          <span className="font-medium text-slate-600 dark:text-slate-300">
            {pt.confidenceLower} – {pt.confidenceUpper} AQI
          </span>
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span>Est. PM2.5 / PM10:</span>
          <span>{pt.pm25Estimate} / {pt.pm10Estimate} µg/m³</span>
        </div>
      </div>
    );
  }
  return null;
}

export function ForecastChart({
  forecast,
  currentAQI,
  cityName,
  horizon,
  onHorizonChange,
}: ForecastChartProps) {
  const horizons: { key: ForecastHorizon; label: string }[] = [
    { key: '6h', label: 'Next 6 Hours' },
    { key: '12h', label: 'Next 12 Hours' },
    { key: '24h', label: 'Next 24 Hours' },
    { key: '3d', label: 'Next 3 Days' },
  ];

  const isImproving = forecast.direction === 'improving';
  const isWorsening = forecast.direction === 'worsening';

  // Y-axis range
  const allValues = [
    ...forecast.dataPoints.map((p) => p.confidenceUpper),
    ...forecast.dataPoints.map((p) => p.predictedAQI),
    currentAQI,
  ];
  const maxVal = Math.max(...allValues);
  const yAxisMax = Math.min(500, Math.ceil((maxVal + 30) / 20) * 20);

  return (
    <Card variant="standard" className="space-y-6">
      {/* Prominent Required Simulation Disclaimer Notice */}
      <div className="rounded-xl border border-amber-300 dark:border-amber-800/80 bg-amber-50 dark:bg-amber-950/40 p-3.5 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
        <div className="space-y-0.5">
          <h4 className="text-xs font-bold text-amber-900 dark:text-amber-200">
            Simulated Demonstration Projection
          </h4>
          <p className="text-xs text-amber-800 dark:text-amber-300">
            Forecasts are simulated for demonstration purposes and are not real-world AQI predictions.
          </p>
        </div>
      </div>

      <CardHeader className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-teal-600 dark:text-teal-400" aria-hidden="true" />
            <CardTitle className="text-lg">Predictive Air Quality Forecast Model</CardTitle>
            <Badge variant={getBadgeVariant(forecast.overallCategory)} size="sm">
              Exp: {forecast.overallCategory}
            </Badge>
          </div>
          <CardDescription className="text-xs mt-0.5">
            Atmospheric dispersion and diurnal variation modeling for {cityName}
          </CardDescription>
        </div>

        {/* Horizon selector buttons */}
        <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800/80 p-0.5 self-start lg:self-auto">
          {horizons.map((h) => (
            <button
              key={h.key}
              type="button"
              onClick={() => onHorizonChange(h.key)}
              aria-pressed={horizon === h.key}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                horizon === h.key
                  ? 'bg-white dark:bg-slate-900 text-teal-700 dark:text-teal-300 shadow-xs border border-slate-200/60 dark:border-slate-700/60'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {h.label}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Forecast Summary Card Header */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-3.5 space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="font-semibold uppercase text-[10px]">Average Expected</span>
              <Clock className="w-3.5 h-3.5" />
            </div>
            <div className="text-2xl font-black text-slate-900 dark:text-white">
              {forecast.averagePredictedAQI} <span className="text-xs font-normal text-slate-400">AQI</span>
            </div>
            <p className="text-[11px] text-slate-500">{forecast.overallCategory} tier</p>
          </div>

          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-3.5 space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="font-semibold uppercase text-[10px]">Peak Anticipated</span>
              <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
            </div>
            <div className="text-2xl font-black text-rose-600 dark:text-rose-400">
              {forecast.peakPredictedAQI} <span className="text-xs font-normal text-slate-400">AQI</span>
            </div>
            <p className="text-[11px] text-slate-500">Worst interval in horizon</p>
          </div>

          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-3.5 space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="font-semibold uppercase text-[10px]">Projected Trajectory</span>
              {isImproving ? (
                <ArrowDownRight className="w-3.5 h-3.5 text-emerald-500" />
              ) : isWorsening ? (
                <ArrowUpRight className="w-3.5 h-3.5 text-rose-500" />
              ) : (
                <MoveRight className="w-3.5 h-3.5 text-sky-500" />
              )}
            </div>
            <div
              className={`text-2xl font-black capitalize ${
                isImproving
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : isWorsening
                  ? 'text-rose-600 dark:text-rose-400'
                  : 'text-sky-600 dark:text-sky-400'
              }`}
            >
              {forecast.direction}
            </div>
            <p className="text-[11px] text-slate-500">Compared to current {currentAQI} AQI</p>
          </div>

          <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60 p-3.5 space-y-1">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="font-semibold uppercase text-[10px]">Uncertainty Band</span>
              <Info className="w-3.5 h-3.5 text-slate-400" />
            </div>
            <div className="text-xs font-bold text-slate-800 dark:text-slate-200 pt-1">
              {forecast.confidenceRangeText}
            </div>
            <p className="text-[11px] text-slate-500">95% statistical envelope</p>
          </div>
        </div>

        {/* Forecast Recharts Chart */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              Predicted Curve & Uncertainty Envelope
            </span>
            <span className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1">
                <span className="w-3 h-0.5 bg-teal-600 inline-block" /> Mean Forecast
              </span>
              <span className="inline-flex items-center gap-1">
                <span className="w-3 h-3 bg-teal-100 dark:bg-teal-950/60 border border-teal-300 dark:border-teal-700 inline-block rounded-xs" />{' '}
                Uncertainty Range
              </span>
            </span>
          </div>

          <div className="w-full h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={forecast.dataPoints}
                margin={{ top: 10, right: 15, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="forecastBandGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0F766E" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#0F766E" stopOpacity={0.05} />
                  </linearGradient>
                </defs>

                <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.15} vertical={false} />

                <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} domain={[0, yAxisMax]} />

                <Tooltip content={<CustomForecastTooltip />} />

                {/* Current AQI baseline reference line */}
                <ReferenceLine
                  y={currentAQI}
                  stroke="#64748B"
                  strokeDasharray="3 3"
                  label={{
                    value: `Current (${currentAQI})`,
                    fill: '#64748B',
                    fontSize: 10,
                    position: 'insideTopLeft',
                  }}
                />

                {/* Upper Confidence Band */}
                <Area
                  type="monotone"
                  dataKey="confidenceUpper"
                  stroke="#0F766E"
                  strokeWidth={1}
                  strokeDasharray="2 2"
                  fill="url(#forecastBandGrad)"
                />

                {/* Mean Projected AQI Line */}
                <Line
                  type="monotone"
                  dataKey="predictedAQI"
                  name="Mean Predicted AQI"
                  stroke="#0F766E"
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#0F766E' }}
                  activeDot={{ r: 6, fill: '#115E59' }}
                />

                {/* Lower Confidence Band */}
                <Area
                  type="monotone"
                  dataKey="confidenceLower"
                  stroke="#0F766E"
                  strokeWidth={1}
                  strokeDasharray="2 2"
                  fill="transparent"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Forecast Narrative Summary */}
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/40 p-4 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
            <Info className="w-4 h-4 text-teal-600 dark:text-teal-400" />
            <span>Forecasting Narrative</span>
          </div>
          <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
            {forecast.summary}
          </p>
        </div>

        {/* Health Precautions Suggestions based on forecast */}
        <div className="space-y-3 pt-2 border-t border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <HeartPulse className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Anticipated Health Precautions & Protective Measures
            </h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {forecast.precautions.map((precaution, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-3 text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2.5"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-teal-500 mt-1.5 shrink-0" />
                <span className="leading-relaxed">{precaution}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

