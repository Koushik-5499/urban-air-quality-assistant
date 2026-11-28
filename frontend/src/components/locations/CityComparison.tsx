import { useMemo } from 'react';
import { ChartDataTable } from '../common/ChartDataTable';
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
import { Layers, X, Info, Check } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { DASHBOARD_DATA } from '../../data/dashboardData';
import type { CityDashboardData } from '../../types/dashboard';

export interface CityComparisonProps {
  comparisonCityIds: string[];
  allCities: CityDashboardData[];
  onRemoveCity: (cityId: string) => void;
  onAddCity: (cityId: string) => void;
  onClearAll: () => void;
  onSelectForDashboard: (city: CityDashboardData) => void;
  activeDashboardCityId: string;
}

interface CustomBarTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    dataKey: string;
  }>;
  label?: string;
}

function CustomBarTooltip({ active, payload, label }: CustomBarTooltipProps) {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 shadow-lg text-xs space-y-1.5">
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
              {entry.value} {entry.name === 'AQI' ? '' : 'µg/m³'}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
}

export function CityComparison({
  comparisonCityIds,
  allCities,
  onRemoveCity,
  onAddCity,
  onClearAll,
  onSelectForDashboard,
  activeDashboardCityId,
}: CityComparisonProps) {
  // Retrieve data objects for selected comparison cities
  const comparedCities = useMemo(() => {
    return comparisonCityIds
      .map((id) => DASHBOARD_DATA[id])
      .filter((c): c is CityDashboardData => Boolean(c));
  }, [comparisonCityIds]);

  // Cities available to be added (not currently in comparison)
  const availableToAdd = useMemo(() => {
    return allCities.filter((c) => !comparisonCityIds.includes(c.location.id));
  }, [allCities, comparisonCityIds]);

  // Chart dataset
  const chartData = useMemo(() => {
    return comparedCities.map((city) => {
      const pm25 = city.pollutants.find((p) => p.id === 'pm25')?.value ?? 0;
      const pm10 = city.pollutants.find((p) => p.id === 'pm10')?.value ?? 0;
      return {
        name: city.location.city,
        AQI: city.aqi,
        'PM2.5': pm25,
        'PM10': pm10,
      };
    });
  }, [comparedCities]);

  const getBadgeVariant = (cat: string) => {
    switch (cat) {
      case 'Good':
        return 'success';
      case 'Moderate':
        return 'warning';
      case 'Unhealthy for Sensitive Groups':
      case 'Unhealthy':
        return 'danger';
      default:
        return 'default';
    }
  };

  if (comparedCities.length === 0) {
    return (
      <Card variant="standard" className="text-center p-8 space-y-3">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
          <Layers className="h-6 w-6" aria-hidden="true" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-white">
            No cities selected for comparison
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            Click "+ Compare" on any city cards above to contrast AQI and particulate metrics side by side.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card variant="standard" className="space-y-6">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <CardTitle className="text-lg">Multi-City Environmental Comparison</CardTitle>
            <Badge variant="neutral" size="sm">
              {comparedCities.length} of 4 Cities
            </Badge>
          </div>
          <CardDescription className="text-xs mt-0.5">
            Side-by-side particulate evaluation and atmospheric metrics (Simulated Demonstration)
          </CardDescription>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {/* Add City quick dropdown if under 4 cities */}
          {comparedCities.length < 4 && availableToAdd.length > 0 && (
            <div className="relative">
              <label htmlFor="quick-add-comparison-city" className="sr-only">
                Add city to comparison
              </label>
              <select
                id="quick-add-comparison-city"
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
                {availableToAdd.map((c) => (
                  <option key={c.location.id} value={c.location.id}>
                    {c.location.city} (AQI {c.aqi})
                  </option>
                ))}
              </select>
            </div>
          )}

          <Button variant="ghost" size="sm" onClick={onClearAll} className="text-xs text-rose-600 hover:text-rose-700">
            Clear All
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Comparison Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {comparedCities.map((city) => {
            const pm25 = city.pollutants.find((p) => p.id === 'pm25')?.value ?? 0;
            const pm10 = city.pollutants.find((p) => p.id === 'pm10')?.value ?? 0;
            const isActive = activeDashboardCityId === city.location.id;

            return (
              <div
                key={city.location.id}
                className="relative rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/60 p-4 space-y-3 flex flex-col justify-between"
              >
                {/* Remove button */}
                <button
                  type="button"
                  onClick={() => onRemoveCity(city.location.id)}
                  aria-label={`Remove ${city.location.city} from comparison`}
                  className="absolute top-3 right-3 p-1 rounded-full text-slate-400 hover:text-rose-600 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" aria-hidden="true" />
                </button>

                <div className="space-y-1 pr-6">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-slate-900 dark:text-white text-base">
                      {city.location.city}
                    </span>
                    {isActive && (
                      <span className="text-[10px] bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 px-1 rounded font-semibold">
                        Dashboard
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">
                    {city.location.state}
                  </p>
                </div>

                {/* Score & Category */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-200/60 dark:border-slate-800">
                  <span className="text-2xl font-black text-slate-900 dark:text-white">
                    {city.aqi}{' '}
                    <span className="text-xs font-normal text-slate-400">AQI</span>
                  </span>
                  <Badge variant={getBadgeVariant(city.category)} size="sm">
                    {city.category}
                  </Badge>
                </div>

                {/* Detailed Row breakdown */}
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
                    <span className="text-slate-400">Temp:</span>
                    <span className="font-semibold">{city.weather.temperature.toFixed(1)}°C</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Humidity:</span>
                    <span className="font-semibold">{city.weather.humidity}%</span>
                  </div>
                </div>

                {/* Activate on Dashboard */}
                {!isActive && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onSelectForDashboard(city)}
                    className="w-full text-xs mt-2"
                  >
                    <Check className="w-3 h-3 mr-1" aria-hidden="true" />
                    Set on Dashboard
                  </Button>
                )}
              </div>
            );
          })}
        </div>

        {/* Recharts Comparison Chart */}
        <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
              Comparative Metric Curves
            </h4>
            <span className="text-xs text-slate-400 flex items-center gap-1">
              <Info className="w-3 h-3" />
              Simulated cross-city bar analysis
            </span>
          </div>

          <div className="w-full h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
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
                  dataKey="name"
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
                <Tooltip content={<CustomBarTooltip />} />
                <Legend
                  verticalAlign="top"
                  align="right"
                  iconType="circle"
                  wrapperStyle={{ paddingBottom: '12px', fontSize: '11px' }}
                />
                <Bar dataKey="AQI" fill="#16A34A" radius={[4, 4, 0, 0]} />
                <Bar dataKey="PM2.5" fill="#F59E0B" radius={[4, 4, 0, 0]} />
                <Bar dataKey="PM10" fill="#0F766E" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <ChartDataTable
              caption="Monitored cities AQI, PM2.5, and PM10 comparison"
              columns={[
                { key: 'name', label: 'City' },
                { key: 'AQI', label: 'AQI' },
                { key: 'PM2.5', label: 'PM2.5 (µg/m³)' },
                { key: 'PM10', label: 'PM10 (µg/m³)' },
              ]}
              rows={chartData}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
