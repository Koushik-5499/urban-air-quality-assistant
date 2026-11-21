import {
  TrendingUp,
  Layers,
  Flame,
  Info,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { calculateAQISubIndices } from '../../data/pollutantDetails';
import type { PollutantMetric } from '../../types/dashboard';

export interface AQIContributionSectionProps {
  pollutants: PollutantMetric[];
  overallAQI: number;
  dominantPollutant: string;
}

export function AQIContributionSection({
  pollutants,
  overallAQI,
  dominantPollutant,
}: AQIContributionSectionProps) {
  const subIndices = calculateAQISubIndices(pollutants, overallAQI);

  return (
    <Card variant="standard" className="p-6">
      <CardHeader className="p-0 pb-5 border-b border-slate-100 dark:border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-400 border border-teal-200/60 dark:border-teal-800/60">
                <TrendingUp className="w-5 h-5" aria-hidden="true" />
              </span>
              <CardTitle className="text-xl">
                AQI Sub-Index Calculation & Dominant Driver
              </CardTitle>
            </div>
            <CardDescription className="text-xs sm:text-sm">
              Understanding why individual pollutant metrics determine the comprehensive Air Quality Index.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto">
            <Badge variant="warning" size="md">
              Dominant Driver: {dominantPollutant}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 pt-6 space-y-6">
        {/* Scientific Principle Explainer */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 dark:text-slate-200">
              <Layers className="w-4 h-4 text-emerald-600" />
              <span>Independent Sub-Indices</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Every pollutant is assigned a standardized sub-index based on epidemiological dose-response breakpoints published by the CPCB and WHO.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-900/40 space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900 dark:text-amber-200">
              <Flame className="w-4 h-4 text-amber-600" />
              <span>The Maximum Rule</span>
            </div>
            <p className="text-xs text-amber-800/80 dark:text-amber-300/80 leading-relaxed">
              AQI is <strong>not</strong> an average or sum. Overall AQI equals the <em>highest</em> individual sub-index, designated as the Dominant Pollutant.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 dark:text-slate-200">
              <Info className="w-4 h-4 text-teal-600" />
              <span>Incompatible Units</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Particulates are measured in µg/m³, while carbon monoxide is in mg/m³. Sub-indices mathematically normalize these into a comparable 0–500 scale.
            </p>
          </div>
        </div>

        {/* Visual Sub-Index Contribution Progress Bars */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-bold text-slate-700 dark:text-slate-300">
            <span>Current Pollutant Sub-Index Breakdown (0–500 scale)</span>
            <span className="text-slate-400 font-normal">Active City AQI: {overallAQI}</span>
          </div>

          <div className="space-y-3">
            {subIndices.map((item) => {
              const maxScale = 200; // Visual clamp for bar length
              const barWidthPercent = Math.min(Math.round((item.subIndex / maxScale) * 100), 100);

              return (
                <div
                  key={item.id}
                  className={`p-3.5 rounded-xl border transition-all ${
                    item.isDominant
                      ? 'bg-amber-50/60 dark:bg-amber-950/20 border-amber-300 dark:border-amber-800/80 shadow-xs ring-1 ring-amber-400/30'
                      : 'bg-white dark:bg-slate-900 border-slate-200/80 dark:border-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3 text-xs mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-slate-900 dark:text-white text-sm">
                        {item.formula}
                      </span>
                      <span className="text-slate-500 dark:text-slate-400">({item.name})</span>
                      {item.isDominant && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-200 text-amber-900 dark:bg-amber-900 dark:text-amber-200 flex items-center gap-1">
                          <Flame className="w-2.5 h-2.5" /> Dominant Driver
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3">
                      <span className="text-slate-500 dark:text-slate-400">
                        Reading: <strong className="text-slate-800 dark:text-slate-200">{item.concentration} {item.unit}</strong>
                      </span>
                      <span className="font-mono font-bold text-slate-900 dark:text-white bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                        Sub-Index: {item.subIndex}
                      </span>
                    </div>
                  </div>

                  {/* Visual Bar */}
                  <div className="w-full h-2.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${barWidthPercent}%`,
                        backgroundColor: item.color,
                      }}
                    />
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1.5">
                    <span>Benchmark: {item.benchmarkPercentage}% of 24h standard</span>
                    <span>Status: {item.category}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
