import {
  Lightbulb,
  Flame,
  ShieldCheck,
  Wind,
  TrendingUp,
  Layers,
  Clock,
  Sparkles,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import type { AnalyticsInsightItem } from '../../types/analytics';

export interface AnalyticsInsightsProps {
  insights: AnalyticsInsightItem[];
  cityName: string;
  timeRangeLabel: string;
}

export function AnalyticsInsights({
  insights,
  cityName,
  timeRangeLabel,
}: AnalyticsInsightsProps) {
  const getInsightIcon = (type: AnalyticsInsightItem['type']) => {
    switch (type) {
      case 'peak':
        return <Flame className="w-4 h-4 text-rose-500" />;
      case 'trough':
        return <ShieldCheck className="w-4 h-4 text-emerald-500" />;
      case 'dominant':
        return <Wind className="w-4 h-4 text-amber-500" />;
      case 'trend':
        return <TrendingUp className="w-4 h-4 text-teal-500" />;
      case 'comparison':
        return <Layers className="w-4 h-4 text-indigo-500" />;
      case 'pattern':
        return <Clock className="w-4 h-4 text-sky-500" />;
      default:
        return <Lightbulb className="w-4 h-4 text-emerald-500" />;
    }
  };

  const getSeverityBadgeVariant = (
    severity: AnalyticsInsightItem['severity']
  ): 'success' | 'warning' | 'danger' | 'info' | 'default' => {
    switch (severity) {
      case 'positive':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'danger';
      case 'info':
      default:
        return 'info';
    }
  };

  return (
    <Card variant="standard" className="space-y-6">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-100 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-amber-500" aria-hidden="true" />
            <CardTitle className="text-lg">Calculated Historical & Telemetry Insights</CardTitle>
          </div>
          <CardDescription className="text-xs mt-0.5">
            Empirical observations calculated directly from sampled telemetry for {cityName} ({timeRangeLabel})
          </CardDescription>
        </div>

        <Badge variant="neutral" size="sm" className="self-start sm:self-auto">
          {insights.length} Data Insights
        </Badge>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {insights.map((item) => (
            <div
              key={item.id}
              className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-4 space-y-3 flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 shrink-0">
                      {getInsightIcon(item.type)}
                    </div>
                    <span className="text-xs font-bold text-slate-900 dark:text-white leading-tight">
                      {item.title}
                    </span>
                  </div>

                  {item.metricValue && (
                    <Badge variant={getSeverityBadgeVariant(item.severity)} size="sm">
                      {item.metricValue}
                    </Badge>
                  )}
                </div>

                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  {item.description}
                </p>
              </div>

              {item.recommendation && (
                <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 text-[11px] text-slate-500 dark:text-slate-400 flex items-start gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <span>
                    <strong className="text-slate-700 dark:text-slate-300">Action: </strong>
                    {item.recommendation}
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Analytical Integrity Guardrail Notice */}
        <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
          <span>
            Strict Data Guardrail: Insights are computed solely from telemetry datasets without unverified external causality claims.
          </span>
          <span>Sample Analytics Engine</span>
        </div>
      </CardContent>
    </Card>
  );
}
