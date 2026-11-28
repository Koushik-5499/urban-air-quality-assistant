import { useState } from 'react';
import {
  ShieldCheck,
  Heart,
  Activity,
  AlertTriangle,
  AlertCircle,
  Snowflake,
  Bike,
  Home,
  Leaf,
  TrendingDown,
  HelpCircle,
  ChevronDown,
  Cpu,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { HouseholdProfileBar } from './HouseholdProfileBar';
import {
  DEFAULT_HOUSEHOLD_PROFILE,
  getHealthRecommendations,
} from '../../utils/healthRecommendations';
import type { AQICategory, HouseholdProfile, QuantifiedActionItem } from '../../types/dashboard';

export interface HealthRecommendationProps {
  aqi: number;
  category: AQICategory;
  cityName?: string;
}

function ActionPlanSection({
  title,
  icon,
  items,
  containerClass,
  headingClass,
  bodyClass,
  badgeClass,
}: {
  title: string;
  icon: React.ReactNode;
  items: QuantifiedActionItem[];
  containerClass: string;
  headingClass: string;
  bodyClass: string;
  badgeClass: string;
}) {
  return (
    <div className={`p-3 rounded-xl border space-y-2 ${containerClass}`}>
      <div className={`flex items-center gap-1.5 text-xs font-semibold ${headingClass}`}>
        {icon}
        <span>{title}</span>
      </div>
      <ul className="space-y-2 pl-4">
        {items.map((item, idx) => (
          <li key={idx} className={`text-xs list-disc space-y-1 ${bodyClass}`}>
            <p className="font-medium">{item.text}</p>
            <div className="flex flex-wrap gap-1.5 text-[11px]">
              <span className={`px-2 py-0.5 rounded font-semibold ${badgeClass}`}>
                PM2.5 avoided: {item.pm25Avoided}
              </span>
              <span className={`px-2 py-0.5 rounded font-semibold ${badgeClass}`}>
                CO₂ saved: {item.co2SavedKg}
              </span>
            </div>
            <p className="text-[11px] opacity-90">
              <strong>Why this advice:</strong> {item.whyAdvice}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function HealthRecommendation({
  aqi,
  category,
  cityName = 'Delhi',
}: HealthRecommendationProps) {
  const [whyAdviceOpen, setWhyAdviceOpen] = useState(false);
  const [profile, setProfile] = useState<HouseholdProfile>(DEFAULT_HOUSEHOLD_PROFILE);
  const recommendations = getHealthRecommendations(category, aqi, profile, cityName);

  return (
    <Card variant="standard" className="flex flex-col justify-between">
      <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/60">
              <ShieldCheck className="w-4 h-4" aria-hidden="true" />
            </div>
            <div>
              <CardTitle className="text-base">Health Guidance &amp; Precautions</CardTitle>
              <CardDescription className="text-xs">
                {cityName} exposure plan for AQI {aqi} ({category})
              </CardDescription>
            </div>
          </div>
          <Badge variant={aqi <= 100 ? 'success' : 'warning'} size="sm">
            Current: {category}
          </Badge>
        </div>

        <div className="mt-2 inline-flex items-center gap-1.5 text-[11px] font-semibold text-teal-800 dark:text-teal-300 bg-teal-50 dark:bg-teal-950/50 border border-teal-200 dark:border-teal-800/70 px-2.5 py-1 rounded-lg self-start">
          <Cpu className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>Deterministic CPCB/WHO Fallback Ready (No Gemini Key Required)</span>
        </div>
      </CardHeader>

      <CardContent className="pt-4 space-y-4">
        <HouseholdProfileBar profile={profile} onChange={setProfile} idPrefix="dashboard-profile" />

        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 dark:text-slate-200">
            <Heart className="w-3.5 h-3.5 text-rose-500" aria-hidden="true" />
            <span>General Public Guidance</span>
          </div>
          <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed pl-5">
            {recommendations.general}
          </p>
        </div>

        <div className="p-3 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-900/40 space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-900 dark:text-amber-200">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" aria-hidden="true" />
            <span>Tailored Cohort Precautions</span>
          </div>
          <p className="text-xs text-amber-900 dark:text-amber-100 leading-relaxed pl-5">
            {recommendations.sensitiveGroups}
          </p>
        </div>

        {recommendations.winterSmogAdvice && (
          <div className="p-3 rounded-xl bg-cyan-50/70 dark:bg-cyan-950/30 border border-cyan-200/60 dark:border-cyan-900/40 space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-cyan-900 dark:text-cyan-200">
              <Snowflake className="w-3.5 h-3.5 text-cyan-700 dark:text-cyan-300" aria-hidden="true" />
              <span>Winter Smog &amp; Family Inversion Protocol</span>
            </div>
            <p className="text-xs text-cyan-900 dark:text-cyan-100 leading-relaxed pl-5">
              {recommendations.winterSmogAdvice}
            </p>
          </div>
        )}

        {recommendations.routineItems && (
          <ActionPlanSection
            title="1. Low-Emission Daily Routines"
            icon={<Bike className="w-3.5 h-3.5 text-blue-700 dark:text-blue-300" aria-hidden="true" />}
            items={recommendations.routineItems}
            containerClass="bg-blue-50/60 dark:bg-blue-950/30 border-blue-200/60 dark:border-blue-900/40"
            headingClass="text-blue-900 dark:text-blue-200"
            bodyClass="text-blue-900 dark:text-blue-100"
            badgeClass="bg-blue-100/80 dark:bg-blue-900/70 text-blue-900 dark:text-blue-100"
          />
        )}

        {recommendations.indoorHackItems && (
          <ActionPlanSection
            title="2. Indoor Air Quality Hacks"
            icon={<Home className="w-3.5 h-3.5 text-purple-700 dark:text-purple-300" aria-hidden="true" />}
            items={recommendations.indoorHackItems}
            containerClass="bg-purple-50/60 dark:bg-purple-950/30 border-purple-200/60 dark:border-purple-900/40"
            headingClass="text-purple-900 dark:text-purple-200"
            bodyClass="text-purple-900 dark:text-purple-100"
            badgeClass="bg-purple-100/80 dark:bg-purple-900/70 text-purple-900 dark:text-purple-100"
          />
        )}

        {recommendations.alternativeItems && (
          <ActionPlanSection
            title="3. Sustainable Alternatives"
            icon={<Leaf className="w-3.5 h-3.5 text-emerald-700 dark:text-emerald-300" aria-hidden="true" />}
            items={recommendations.alternativeItems}
            containerClass="bg-emerald-50/60 dark:bg-emerald-950/30 border-emerald-200/60 dark:border-emerald-900/40"
            headingClass="text-emerald-900 dark:text-emerald-200"
            bodyClass="text-emerald-900 dark:text-emerald-100"
            badgeClass="bg-emerald-100/80 dark:bg-emerald-900/70 text-emerald-900 dark:text-emerald-100"
          />
        )}

        {recommendations.impactExplanation && (
          <div className="p-3 rounded-xl bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200/60 dark:border-indigo-900/40 space-y-1">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-900 dark:text-indigo-200">
              <TrendingDown className="w-3.5 h-3.5 text-indigo-700 dark:text-indigo-300" aria-hidden="true" />
              <span>Combined Household Impact Summary</span>
            </div>
            <p className="text-xs font-medium text-indigo-900 dark:text-indigo-100 leading-relaxed pl-5">
              {recommendations.impactExplanation}
            </p>
          </div>
        )}

        <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 space-y-1">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 dark:text-slate-200">
            <Activity className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
            <span>Outdoor Activity Recommendation</span>
          </div>
          <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed pl-5">
            {recommendations.outdoorActivity}
          </p>
        </div>

        <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
          <button
            type="button"
            onClick={() => setWhyAdviceOpen(!whyAdviceOpen)}
            aria-expanded={whyAdviceOpen}
            aria-controls="dashboard-why-advice"
            className="min-h-[44px] flex items-center gap-1.5 text-xs font-semibold text-teal-700 dark:text-teal-300 hover:text-teal-800 dark:hover:text-teal-200 transition-colors cursor-pointer"
          >
            <HelpCircle className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Why this advice?</span>
            <ChevronDown
              className={`w-3.5 h-3.5 transition-transform duration-200 ${whyAdviceOpen ? 'rotate-180' : ''}`}
              aria-hidden="true"
            />
          </button>

          {whyAdviceOpen && (
            <div
              id="dashboard-why-advice"
              className="mt-2.5 p-3 rounded-xl bg-slate-50 dark:bg-slate-850/80 border border-slate-200/70 dark:border-slate-800 space-y-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-700 dark:text-slate-300">Priority Level:</span>
                <Badge
                  variant={aqi > 200 ? 'danger' : aqi > 100 ? 'warning' : 'success'}
                  size="sm"
                >
                  {aqi > 200
                    ? 'Critical / Health Alert'
                    : aqi > 100
                    ? 'Elevated Precaution'
                    : 'Satisfactory / Baseline'}
                </Badge>
              </div>
              <div>
                <span className="font-bold text-slate-700 dark:text-slate-300">
                  Epidemiological Reason:
                </span>{' '}
                <span className="text-slate-700 dark:text-slate-300">
                  {aqi > 150
                    ? 'Elevated fine particulates (PM2.5) bypass upper respiratory filtration to penetrate deep alveolar tissue, increasing cardiac workload and triggering bronchospasms.'
                    : 'Ambient concentrations remain within tolerable physiologic ranges; low-emission routines preserve clean urban air.'}
                </span>
              </div>
              <div className="pt-1.5 border-t border-slate-200/60 dark:border-slate-700/60 text-[11px] text-slate-600 dark:text-slate-300 flex items-center justify-between">
                <span className="font-semibold">Supporting Standards:</span>
                <span>CPCB NAQI Guidelines (2014) &amp; WHO Guidelines (2021)</span>
              </div>
            </div>
          )}
        </div>

        <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-600 dark:text-slate-300 leading-tight flex items-start gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-slate-500 dark:text-slate-400" aria-hidden="true" />
          <span>{recommendations.disclaimer}</span>
        </div>
      </CardContent>
    </Card>
  );
}
