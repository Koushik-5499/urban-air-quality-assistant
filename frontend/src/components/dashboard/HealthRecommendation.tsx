import {
  ShieldCheck,
  Heart,
  Activity,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Snowflake,
  Bike,
  Home,
  Leaf,
  TrendingDown,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { getHealthRecommendations } from '../../utils/healthRecommendations';
import type { AQICategory } from '../../types/dashboard';

export interface HealthRecommendationProps {
  aqi: number;
  category: AQICategory;
}

export function HealthRecommendation({ aqi, category }: HealthRecommendationProps) {
  const recommendations = getHealthRecommendations(category, aqi);

  return (
    <Card variant="standard" className="flex flex-col justify-between">
      <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/60">
              <ShieldCheck className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <CardTitle className="text-base">Health Guidance & Precautions</CardTitle>
              <CardDescription className="text-xs">
                Atmospheric exposure guidance for AQI {aqi} ({category})
              </CardDescription>
            </div>
          </div>
          <Badge variant={aqi <= 100 ? 'success' : 'warning'} size="sm">
            Current: {category}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        {/* General Public Recommendation */}
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 dark:text-slate-200">
            <Heart className="w-3.5 h-3.5 text-rose-500" aria-hidden="true" />
            <span>General Public Guidance</span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed pl-5">
            {recommendations.general}
          </p>
        </div>

        {/* Sensitive Groups Advice */}
        <div className="p-3 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-900/40 space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-900 dark:text-amber-300">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" aria-hidden="true" />
            <span>Sensitive & Vulnerable Groups</span>
          </div>
          <p className="text-xs text-amber-800 dark:text-amber-200/90 leading-relaxed pl-5">
            {recommendations.sensitiveGroups}
          </p>
        </div>

        {/* Outdoor Activity Suggestion */}
        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 dark:text-slate-200">
            <Activity className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <span>Outdoor Activity Recommendation</span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed pl-5">
            {recommendations.outdoorActivity}
          </p>
        </div>

        {/* Winter Smog & Thermal Inversion Guidance */}
        {recommendations.winterSmogAdvice && (
          <div className="p-3 rounded-xl bg-cyan-50/70 dark:bg-cyan-950/30 border border-cyan-200/60 dark:border-cyan-900/40 space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-cyan-900 dark:text-cyan-300">
              <Snowflake className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400" aria-hidden="true" />
              <span>Winter Smog & Family Inversion Protocol</span>
            </div>
            <p className="text-xs text-cyan-800 dark:text-cyan-200/90 leading-relaxed pl-5">
              {recommendations.winterSmogAdvice}
            </p>
          </div>
        )}

        {/* Low-Emission Daily Routines */}
        {recommendations.lowEmissionRoutines && recommendations.lowEmissionRoutines.length > 0 && (
          <div className="p-3 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200/60 dark:border-blue-900/40 space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-900 dark:text-blue-300">
              <Bike className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" aria-hidden="true" />
              <span>Low-Emission Daily Routines</span>
            </div>
            <ul className="space-y-1 pl-5">
              {recommendations.lowEmissionRoutines.map((routine, idx) => (
                <li key={idx} className="text-xs text-blue-800 dark:text-blue-200/90 list-disc">
                  {routine}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Indoor Air Quality Hacks */}
        {recommendations.indoorAirHacks && recommendations.indoorAirHacks.length > 0 && (
          <div className="p-3 rounded-xl bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200/60 dark:border-purple-900/40 space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-purple-900 dark:text-purple-300">
              <Home className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" aria-hidden="true" />
              <span>Indoor Air Quality Hacks</span>
            </div>
            <ul className="space-y-1 pl-5">
              {recommendations.indoorAirHacks.map((hack, idx) => (
                <li key={idx} className="text-xs text-purple-800 dark:text-purple-200/90 list-disc">
                  {hack}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Sustainable Alternatives */}
        {recommendations.sustainableAlternatives && recommendations.sustainableAlternatives.length > 0 && (
          <div className="p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-900/40 space-y-1.5">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-900 dark:text-emerald-300">
              <Leaf className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
              <span>Sustainable Community Alternatives</span>
            </div>
            <ul className="space-y-1 pl-5">
              {recommendations.sustainableAlternatives.map((alt, idx) => (
                <li key={idx} className="text-xs text-emerald-800 dark:text-emerald-200/90 list-disc">
                  {alt}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Direct Quantified Impact */}
        {recommendations.impactExplanation && (
          <div className="p-3 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200/60 dark:border-indigo-900/40 space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-900 dark:text-indigo-300">
              <TrendingDown className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" aria-hidden="true" />
              <span>Direct Quantified Impact of Choices</span>
            </div>
            <p className="text-xs font-medium text-indigo-800 dark:text-indigo-200/90 leading-relaxed pl-5">
              {recommendations.impactExplanation}
            </p>
          </div>
        )}

        {/* Protective Measures Checklist */}
        <div className="space-y-2 pt-1">
          <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
            Recommended Protective Measures:
          </span>
          <ul className="space-y-1.5" aria-label="Protective measures list">
            {recommendations.protectiveMeasures.map((measure, idx) => (
              <li
                key={idx}
                className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" aria-hidden="true" />
                <span>{measure}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Mandatory Medical Disclaimer Notice */}
        <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-400 dark:text-slate-500 leading-tight flex items-start gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-slate-400" aria-hidden="true" />
          <span>{recommendations.disclaimer}</span>
        </div>
      </CardContent>
    </Card>
  );
}

