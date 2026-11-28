import type { CommuteMode, HeatingType, HouseholdProfile } from '../../types/dashboard';

export interface HouseholdProfileBarProps {
  profile: HouseholdProfile;
  onChange: (next: HouseholdProfile) => void;
  idPrefix?: string;
}

const COHORT_FLAGS: Array<{ key: 'children' | 'elderly' | 'asthma' | 'outdoorWorker'; label: string }> = [
  { key: 'children', label: 'Children' },
  { key: 'elderly', label: 'Elderly' },
  { key: 'asthma', label: 'Asthma / COPD' },
  { key: 'outdoorWorker', label: 'Outdoor worker' },
];

export function HouseholdProfileBar({
  profile,
  onChange,
  idPrefix = 'household',
}: HouseholdProfileBarProps) {
  const toggleFlag = (key: 'children' | 'elderly' | 'asthma' | 'outdoorWorker') => {
    onChange({ ...profile, [key]: !profile[key] });
  };

  return (
    <section
      aria-label="Household profile customization"
      className="p-3 rounded-xl bg-slate-50 dark:bg-slate-850/70 border border-slate-200 dark:border-slate-800 space-y-2.5"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-bold text-slate-800 dark:text-slate-100">
          Household Profile (Tailors Routines, Hacks & Impact)
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5" role="group" aria-label="Household vulnerability groups">
        {COHORT_FLAGS.map((flag) => {
          const checked = profile[flag.key];
          return (
            <label
              key={flag.key}
              className={`min-h-[44px] px-2.5 py-1.5 rounded-lg border text-xs font-medium inline-flex items-center gap-1.5 cursor-pointer select-none transition-colors ${
                checked
                  ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-400 dark:border-emerald-700 text-emerald-900 dark:text-emerald-200'
                  : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300'
              }`}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => toggleFlag(flag.key)}
                className="rounded border-slate-400 text-emerald-600 focus:ring-emerald-500"
              />
              <span>{flag.label}</span>
            </label>
          );
        })}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <div className="space-y-1">
          <label
            htmlFor={`${idPrefix}-commute-select`}
            className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300"
          >
            Commute Mode
          </label>
          <select
            id={`${idPrefix}-commute-select`}
            value={profile.commuteMode}
            onChange={(e) => onChange({ ...profile, commuteMode: e.target.value as CommuteMode })}
            className="w-full min-h-[44px] px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-900 dark:text-slate-100 cursor-pointer"
          >
            <option value="car">Private Car</option>
            <option value="two_wheeler">Two-Wheeler</option>
            <option value="public_transit">Public Transit / Metro</option>
            <option value="walk_cycle">Walk / Cycle</option>
            <option value="remote">Work from Home</option>
          </select>
        </div>

        <div className="space-y-1">
          <label
            htmlFor={`${idPrefix}-heating-select`}
            className="block text-[11px] font-semibold text-slate-700 dark:text-slate-300"
          >
            Home Heating Type
          </label>
          <select
            id={`${idPrefix}-heating-select`}
            value={profile.heatingType}
            onChange={(e) => onChange({ ...profile, heatingType: e.target.value as HeatingType })}
            className="w-full min-h-[44px] px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-900 dark:text-slate-100 cursor-pointer"
          >
            <option value="electric">Electric / Heat Pump</option>
            <option value="gas">Gas Heater</option>
            <option value="biomass">Wood / Biomass</option>
            <option value="none">None</option>
          </select>
        </div>
      </div>
    </section>
  );
}

