import {
  ShieldAlert,
  Heart,
  Factory,
  Trees,
  AlertTriangle,
  CheckCircle2,
  Stethoscope,
  Info,
} from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { POLLUTANT_DETAILS } from '../../data/pollutantDetails';
import type { PollutantMetric } from '../../types/dashboard';

export interface PollutantDetailCardProps {
  pollutant: PollutantMetric;
}

export function PollutantDetailCard({ pollutant }: PollutantDetailCardProps) {
  const details = POLLUTANT_DETAILS[pollutant.id];

  if (!details) return null;

  return (
    <Card variant="standard" className="p-6 space-y-6 overflow-hidden">
      {/* Header */}
      <div className="pb-5 border-b border-slate-100 dark:border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="text-2xl font-black font-mono px-3 py-1 rounded-xl text-white"
              style={{ backgroundColor: details.color }}
            >
              {details.formula}
            </span>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
              {details.fullName}
            </h2>
            <Badge variant="neutral" size="sm">
              {details.classification}
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            Physical properties, environmental dispersion pathways, and physiological health thresholds.
          </p>
        </div>

        {/* Current Reading Snapshot */}
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-850 border border-slate-200/60 dark:border-slate-800 self-start md:self-auto min-w-[200px]">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            Active Sample Concentration
          </span>
          <div className="text-2xl font-black text-slate-900 dark:text-white mt-0.5">
            {pollutant.id === 'co' ? pollutant.value.toFixed(2) : pollutant.value.toFixed(1)}{' '}
            <span className="text-xs font-normal text-slate-400 font-mono">{pollutant.unit}</span>
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            Status: <strong className="text-emerald-600 dark:text-emerald-400">{pollutant.status}</strong>
          </div>
        </div>
      </div>

      {/* 1. What it is & Physical Description */}
      <div className="space-y-2">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider text-slate-500">
          What is {details.formula}?
        </h3>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
          {details.description}
        </p>
      </div>

      {/* 2. Sources & Environmental Impact */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Primary Sources */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
            <Factory className="w-4 h-4 text-emerald-600" />
            <span>Primary Emission Sources</span>
          </div>
          <ul className="space-y-2 text-xs text-slate-600 dark:text-slate-300">
            {details.primarySources.map((source, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                <span>{source}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Environmental Impact */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
            <Trees className="w-4 h-4 text-teal-600" />
            <span>Environmental & Ecological Impact</span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
            {details.environmentalImpact}
          </p>
          <div className="pt-2 border-t border-slate-200/60 dark:border-slate-800 text-[11px] text-slate-400">
            <span>Statutory Targets: {details.whoLimitText} • {details.naaqsLimitText}</span>
          </div>
        </div>
      </div>

      {/* 3. Potential Health Effects & Sensitive Populations */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Heart className="w-4 h-4 text-rose-500" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
            Potential Health Effects & Sensitive Populations
          </h3>
        </div>

        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
          {details.healthEffects.overview}
        </p>

        {/* Sensitive Groups Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {details.healthEffects.sensitiveGroups.map((sg, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 space-y-1"
            >
              <span className="text-xs font-bold text-amber-900 dark:text-amber-200 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                {sg.group}
              </span>
              <p className="text-xs text-amber-800/80 dark:text-amber-300/80 leading-relaxed">
                {sg.description}
              </p>
            </div>
          ))}
        </div>

        {/* Acute Symptoms Bar */}
        <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 space-y-1.5">
          <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
            <Stethoscope className="w-3.5 h-3.5 text-emerald-600" />
            Reported Symptoms Associated with Elevated Exposure:
          </span>
          <div className="flex flex-wrap gap-2 pt-1">
            {details.healthEffects.symptoms.map((symptom, idx) => (
              <span
                key={idx}
                className="px-2.5 py-1 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300"
              >
                {symptom}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* 4. Protective Recommendations */}
      <div className="p-4 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-900/30 space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold text-emerald-900 dark:text-emerald-300 uppercase tracking-wider">
          <ShieldAlert className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          <span>Recommended Protective Exposure-Reduction Measures</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-emerald-800 dark:text-emerald-300">
          {details.protectiveMeasures.map((pm, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 mt-0.5 shrink-0" />
              <span>{pm}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 5. Health Disclaimer */}
      <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[11px] text-slate-500 dark:text-slate-400 flex items-start gap-2">
        <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
        <p>
          <strong>Educational Reference Notice:</strong> This health impact information is compiled from public guidelines issued by the World Health Organization (WHO) and Central Pollution Control Board (CPCB) for general awareness. It does not constitute medical diagnosis, clinical treatment advice, or formal healthcare recommendations. Consult licensed medical physicians for individualized respiratory health guidance.
        </p>
      </div>
    </Card>
  );
}
