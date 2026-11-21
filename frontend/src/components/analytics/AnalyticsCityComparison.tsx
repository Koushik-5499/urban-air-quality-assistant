import { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Layers, X, Trophy, Check, Plus, Info } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { DASHBOARD_DATA } from '../../data/dashboardData';
import type { CityDashboardData, AQICategory } from '../../types/dashboard';

export interface AnalyticsCityComparisonProps {
  comparisonCityIds: string[];
  allCities: CityDashboardData[];
  onAddCity: (cityId: string) => void;
  onRemoveCity: (cityId: string) => void;
  onClearAll: () => void;
  activeDashboardCityId: string;
  onSelectForDashboard: (cityId: string) => void;
}

type ComparisonMetricMode = 'aqi' | 'particulates' | 'gases';

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

interface CustomComparisonTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    dataKey: string;
  }>;
  label?: string;
  unit: string;
}

function CustomComparisonTooltip({ active, payload, label, unit }: CustomComparisonTooltipProps) {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 shadow-lg text-xs space-y-1.5 min-w-[170px]">
        <p className="font-semibold text-slate-900 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-1">
          City: {label}
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
              {entry.value} {entry.name === 'Air Quality Index' ? '' : unit}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
}

export function AnalyticsCityComparison({
  comparisonCityIds,
  allCities,
  onAddCity,
  onRemoveCity,
  onClearAll,
  activeDashboardCityId,
  onSelectForDashboard,
}: AnalyticsCityComparisonProps) {
  const [metricMode, setMetricMode] = useState<ComparisonMetricMode>('aqi');

  const comparedCities = useMemo(() => {
    return comparisonCityIds
      .map((id) => DASHBOARD_DATA[id])
      .filter((c): c is CityDashboardData => Boolean(c));
  }, [comparisonCityIds]);

  const availableCities = useMemo(() => {
    return allCities.filter((c) => !comparisonCityIds.includes(c.location.id));
  }, [allCities, comparisonCityIds]);

  // Identify city with lowest AQI (cleanest)
  const cleanestCityId = useMemo(() => {
    if (comparedCities.length === 0) return null;
    let minCity = comparedCities[0];
    for (const c of comparedCities) {
      if (c.aqi < minCity.aqi) minCity = c;
    }
    return minCity.location.id;
  }, [comparedCities]);

  // Prepare chart dataset depending on metricMode
  // Ensure NO INCOMPATIBLE UNITS ARE MIXED!
  // AQI: dimensionless
  // Particulates: PM2.5 (µg/m³), PM10 (µg/m³)
  // Gases: NO2 (µg/m³), SO2 (µg/m³), O3 (µg/m³)
  const chartData = useMemo(() => {
    return comparedCities.map((c) => {
      const pm25 = c.pollutants.find((p) => p.id === 'pm25')?.value ?? 0;
      const pm10 = c.pollutants.find((p) => p.id === 'pm10')?.value ?? 0;
      const no2 = c.pollutants.find((p) => p.id === 'no2')?.value ?? 0;
      const so2 = c.pollutants.find((p) => p.id === 'so2')?.value ?? 0;
      const o3 = c.pollutants.find((p) => p.id === 'o3')?.value ?? 0;

      return {
        name: c.location.city,
        aqi: c.aqi,
        pm25,
        pm10,
        no2,
        so2,
        o3,
      };
    });
  }, [comparedCities]);

  if (comparedCities.length === 0) {
    return (
      <Card variant="standard" className="p-8 text-center space-y-3">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
          <Layers className="h-6 w-6" aria-hidden="true" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            No Cities Selected for Cross-Comparison
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            Select up to 4 cities below to analyze atmospheric variations, particulate loads, and telemetry side by side.
          </p>
        </div>
        {availableCities.length > 0 && (
          <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
            {availableCities.slice(0, 4).map((c) => (
              <Button
                key={c.location.id}
                variant="outline"
                size="sm"
                onClick={() => onAddCity(c.location.id)}
                className="text-xs"
              >
                <Plus className="w-3.5 h-3.5 mr-1" />
                Add {c.location.city}
              </Button>
            ))}
          </div>
        )}
      </Card>
    );
  }

  return (
    <Card variant="standard" className="space-y-6">
      <CardHeader className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <CardTitle className="text-lg">Comparative Multi-City Analysis</CardTitle>
            <Badge variant="neutral" size="sm">
              {comparedCities.length} / 4 Cities
            </Badge>
          </div>
          <CardDescription className="text-xs mt-0.5">
            Direct atmospheric benchmarking across up to 4 monitored Indian urban centres
          </CardDescription>
        </div>

        {/* Controls: Add city dropdown + Clear All */}
        <div className="flex items-center gap-2 self-start md:self-auto">
          {comparedCities.length < 4 && availableCities.length > 0 && (
            <div className="relative">
              <label htmlFor="analytics-add-comparison-city" className="sr-only">
                Add city to comparison
              </label>
              <select
                id="analytics-add-comparison-city"
                aria-label="Add city to comparison"
                onChange={(e) => {
                  if (e.target.value) {
                    onAddCity(e.target.value);
                    e.target.value = '';
                  }
                }}
                className="text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 rounded-lg px-2.5 py-1.5 focus:outline-none cursor-pointer"
                defaultValue=""
              >
                <option value="" disabled>
                  + Add City ({4 - comparedCities.length} slots left)
                </option>
                {availableCities.map((c) => (
                  <option key={c.location.id} value={c.location.id}>
                    {c.location.city} (AQI {c.aqi})
                  </option>
                ))}
              </select>
            </div>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={onClearAll}
            className="text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/40"
          >
            Clear All
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* City Comparison Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {comparedCities.map((city) => {
            const isCleanest = city.location.id === cleanestCityId;
            const isActive = city.location.id === activeDashboardCityId;
            const pm25 = city.pollutants.find((p) => p.id === 'pm25')?.value ?? 0;
            const pm10 = city.pollutants.find((p) => p.id === 'pm10')?.value ?? 0;

            return (
              <div
                key={city.location.id}
                className={`relative rounded-xl border p-4 space-y-3 flex flex-col justify-between transition-all ${
                  isCleanest
                    ? 'border-emerald-400 dark:border-emerald-700 bg-emerald-50/40 dark:bg-emerald-950/20 shadow-xs'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60'
                }`}
              >
                {/* Remove button */}
                <button
                  type="button"
                  onClick={() => onRemoveCity(city.location.id)}
                  aria-label={`Remove ${city.location.city} from comparison`}
                  className="absolute top-3 right-3 p-1 rounded-full text-slate-400 hover:text-rose-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" aria-hidden="true" />
                </button>

                {/* Header & Cleanest Badge */}
                <div className="space-y-1 pr-6">
                  {isCleanest && (
                    <div className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-800 dark:text-emerald-300 bg-emerald-100 dark:bg-emerald-900/80 px-2 py-0.5 rounded-full mb-1">
                      <Trophy className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                      Cleanest in Selection
                    </div>
                  )}

                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-slate-900 dark:text-white text-base">
                      {city.location.city}
                    </span>
                    {isActive && (
                      <span className="text-[10px] bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 px-1 rounded font-semibold">
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 truncate">{city.location.state}</p>
                </div>

                {/* AQI Score */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
                  <span className="text-2xl font-black text-slate-900 dark:text-white">
                    {city.aqi}{' '}
                    <span className="text-xs font-normal text-slate-400">AQI</span>
                  </span>
                  <Badge variant={getBadgeVariant(city.category)} size="sm">
                    {city.category}
                  </Badge>
                </div>

                {/* Metrics Breakdown */}
                <div className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300 pt-1">
                  <div className="flex justify-between">
                    <span className="text-slate-400">PM2.5:</span>
                    <span className="font-semibold">{pm25.toFixed(1)} µg/m³</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">PM10:</span>
                    <span className="font-semibold">{pm10.toFixed(1)} µg/m³</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Dominant:</span>
                    <span className="font-semibold text-amber-600 dark:text-amber-400">
                      {city.dominantPollutant}
                    </span>
                  </div>
                </div>

                {/* Activate on Dashboard */}
                {!isActive ? (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onSelectForDashboard(city.location.id)}
                    className="w-full text-xs mt-2"
                  >
                    <Check className="w-3 h-3 mr-1" aria-hidden="true" />
                    Set as Dashboard City
                  </Button>
                ) : (
                  <div className="w-full text-center py-1 text-xs text-emerald-700 dark:text-emerald-400 font-semibold bg-emerald-50 dark:bg-emerald-950/40 rounded-lg">
                    Current Dashboard City
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Comparative Bar Chart Section with Unit Compatibility Guards */}
        <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
                Comparative Bar Visualization
              </h4>
              <p className="text-xs text-slate-500">
                {metricMode === 'aqi'
                  ? 'Normalized Air Quality Index values across compared stations'
                  : metricMode === 'particulates'
                  ? 'Particulate concentrations (all values standardized in µg/m³)'
                  : 'Gaseous pollutant concentrations (all values standardized in µg/m³)'}
              </p>
            </div>

            {/* Mode Selector Buttons */}
            <div className="inline-flex rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800/80 p-0.5 self-start sm:self-auto">
              <button
                type="button"
                onClick={() => setMetricMode('aqi')}
                aria-pressed={metricMode === 'aqi'}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                  metricMode === 'aqi'
                    ? 'bg-white dark:bg-slate-900 text-emerald-700 dark:text-emerald-300 shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                Overall AQI
              </button>
              <button
                type="button"
                onClick={() => setMetricMode('particulates')}
                aria-pressed={metricMode === 'particulates'}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                  metricMode === 'particulates'
                    ? 'bg-white dark:bg-slate-900 text-emerald-700 dark:text-emerald-300 shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                Particulates (µg/m³)
              </button>
              <button
                type="button"
                onClick={() => setMetricMode('gases')}
                aria-pressed={metricMode === 'gases'}
                className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-all cursor-pointer ${
                  metricMode === 'gases'
                    ? 'bg-white dark:bg-slate-900 text-emerald-700 dark:text-emerald-300 shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                Gases (µg/m³)
              </button>
            </div>
          </div>

          <div className="w-full h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#94a3b8" opacity={0.15} vertical={false} />
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  content={
                    <CustomComparisonTooltip
                      unit={metricMode === 'aqi' ? 'AQI' : 'µg/m³'}
                    />
                  }
                />
                <Legend
                  verticalAlign="top"
                  align="right"
                  iconType="circle"
                  wrapperStyle={{ paddingBottom: '12px', fontSize: '11px' }}
                />

                {metricMode === 'aqi' && (
                  <Bar
                    dataKey="aqi"
                    name="Air Quality Index"
                    fill="#16A34A"
                    radius={[4, 4, 0, 0]}
                  />
                )}

                {metricMode === 'particulates' && (
                  <>
                    <Bar
                      dataKey="pm25"
                      name="PM2.5 (µg/m³)"
                      fill="#F59E0B"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="pm10"
                      name="PM10 (µg/m³)"
                      fill="#0F766E"
                      radius={[4, 4, 0, 0]}
                    />
                  </>
                )}

                {metricMode === 'gases' && (
                  <>
                    <Bar
                      dataKey="no2"
                      name="NO2 (µg/m³)"
                      fill="#0284C7"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="so2"
                      name="SO2 (µg/m³)"
                      fill="#9333EA"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="o3"
                      name="O3 (µg/m³)"
                      fill="#10B981"
                      radius={[4, 4, 0, 0]}
                    />
                  </>
                )}
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="pt-2 flex items-center justify-between text-[11px] text-slate-400">
            <span className="flex items-center gap-1">
              <Info className="w-3.5 h-3.5" aria-hidden="true" />
              Units strictly partitioned: particulate & gaseous charts preserve homogeneous µg/m³ metrics
            </span>
            <span>Simulated Multi-Station Dataset</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
