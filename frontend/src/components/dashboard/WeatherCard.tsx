import { Thermometer, Droplets, Wind, CloudSun, Gauge, Sun } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import type { WeatherData } from '../../types/dashboard';

export interface WeatherCardProps {
  weather: WeatherData;
  locationName: string;
}

export function WeatherCard({ weather, locationName }: WeatherCardProps) {
  const {
    temperature,
    humidity,
    windSpeed,
    windDirection,
    condition,
    pressure,
    uvIndex,
  } = weather;

  return (
    <Card variant="standard" className="flex flex-col justify-between">
      <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-400 border border-teal-200/60 dark:border-teal-800/60">
              <CloudSun className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <CardTitle className="text-base">Atmospheric Weather</CardTitle>
              <CardDescription className="text-xs">
                Local meteorology for {locationName}
              </CardDescription>
            </div>
          </div>
          <span className="text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full">
            {condition}
          </span>
        </div>
      </CardHeader>

      <CardContent className="pt-4">
        {/* Main Temperature Display */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800/80">
          <div>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Ambient Temperature
            </span>
            <div className="text-3xl font-extrabold text-slate-900 dark:text-white mt-0.5 flex items-baseline gap-1">
              <span>{temperature.toFixed(1)}</span>
              <span className="text-lg font-medium text-slate-500">°C</span>
            </div>
          </div>
          <div className="p-3 rounded-full bg-slate-50 dark:bg-slate-800/60 text-emerald-600 dark:text-emerald-400">
            <Thermometer className="w-6 h-6" aria-hidden="true" />
          </div>
        </div>

        {/* 4 Meteorological Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 pt-3">
          {/* Humidity */}
          <div className="p-2.5 rounded-lg bg-slate-50/80 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
              <Droplets className="w-3.5 h-3.5 text-sky-500" aria-hidden="true" />
              <span>Humidity</span>
            </div>
            <div className="text-base font-bold text-slate-900 dark:text-slate-100 mt-1">
              {humidity}%
            </div>
          </div>

          {/* Wind Speed & Direction */}
          <div className="p-2.5 rounded-lg bg-slate-50/80 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
              <Wind className="w-3.5 h-3.5 text-teal-500" aria-hidden="true" />
              <span>Wind</span>
            </div>
            <div className="text-base font-bold text-slate-900 dark:text-slate-100 mt-1 flex items-center gap-1">
              <span>{windSpeed} km/h</span>
              <span className="text-xs font-normal text-slate-500">({windDirection})</span>
            </div>
          </div>

          {/* Atmospheric Pressure */}
          <div className="p-2.5 rounded-lg bg-slate-50/80 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
              <Gauge className="w-3.5 h-3.5 text-amber-500" aria-hidden="true" />
              <span>Pressure</span>
            </div>
            <div className="text-base font-bold text-slate-900 dark:text-slate-100 mt-1">
              {pressure} hPa
            </div>
          </div>

          {/* UV Index */}
          <div className="p-2.5 rounded-lg bg-slate-50/80 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
              <Sun className="w-3.5 h-3.5 text-orange-500" aria-hidden="true" />
              <span>UV Index</span>
            </div>
            <div className="text-base font-bold text-slate-900 dark:text-slate-100 mt-1">
              {uvIndex} (Moderate)
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
