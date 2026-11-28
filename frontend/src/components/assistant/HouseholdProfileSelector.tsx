import { HouseholdProfileBar } from '../dashboard/HouseholdProfileBar';
import { LIFESTYLE_PERSONAS } from '../../constants/personas';
import type { HouseholdProfile } from '../../types/dashboard';

export interface HouseholdProfileSelectorProps {
  selectedLifestyle: string;
  onSelectLifestyle: (id: string) => void;
  householdProfile: HouseholdProfile;
  onChangeProfile: (profile: HouseholdProfile) => void;
}

export function HouseholdProfileSelector({
  selectedLifestyle,
  onSelectLifestyle,
  householdProfile,
  onChangeProfile,
}: HouseholdProfileSelectorProps) {
  return (
    <div className="p-3.5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
          Tailor Advisory to Your Lifestyle &amp; Household Profile:
        </span>
        <span className="text-xs text-teal-700 dark:text-teal-300 font-semibold">
          Active: {LIFESTYLE_PERSONAS.find((p) => p.id === selectedLifestyle)?.label}
        </span>
      </div>

      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
        {LIFESTYLE_PERSONAS.map((persona) => {
          const isActive = selectedLifestyle === persona.id;
          return (
            <button
              key={persona.id}
              type="button"
              onClick={() => onSelectLifestyle(persona.id)}
              aria-pressed={isActive}
              className={`min-h-[44px] px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1 ${
                isActive
                  ? 'bg-teal-700 text-white shadow-xs dark:bg-teal-500 dark:text-slate-950'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-200'
              }`}
            >
              <span>{persona.label}</span>
            </button>
          );
        })}
      </div>

      <HouseholdProfileBar
        profile={householdProfile}
        onChange={onChangeProfile}
        idPrefix="assistant-profile"
      />
    </div>
  );
}
