export interface LifestylePersonaOption {
  id: string;
  label: string;
  desc: string;
}

export const LIFESTYLE_PERSONAS: LifestylePersonaOption[] = [
  { id: 'family_with_children', label: 'Family with Children', desc: 'School commute, pediatric lung health, indoor hacks' },
  { id: 'daily_commuter', label: 'Daily Commuter', desc: 'Off-peak transit shifts, N95 routing, traffic corridors' },
  { id: 'elderly_caregiver', label: 'Elderly & Vulnerable', desc: 'Cardiopulmonary care, indoor air sealing, medication safety' },
  { id: 'outdoor_enthusiast', label: 'Outdoor Worker / Athlete', desc: 'Diurnal outdoor windows (1-4 PM), PM2.5 tracking' },
  { id: 'remote_worker', label: 'Work from Home', desc: 'Diurnal ventilation, DIY Corsi-Rosenthal filtration' },
  { id: 'community_leader', label: 'Community Action', desc: 'Neighborhood carpools, reporting waste burning, clean heating' },
];

