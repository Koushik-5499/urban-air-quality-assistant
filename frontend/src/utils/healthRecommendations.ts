import type {
  AQICategory,
  HealthAdvice,
  HouseholdProfile,
  QuantifiedActionItem,
} from '../types/dashboard';

export const DEFAULT_HOUSEHOLD_PROFILE: HouseholdProfile = {
  children: true,
  elderly: false,
  asthma: false,
  outdoorWorker: false,
  commuteMode: 'car',
  heatingType: 'electric',
};

function buildRoutineItems(
  category: AQICategory,
  aqi: number,
  profile: HouseholdProfile,
  cityLabel: string
): QuantifiedActionItem[] {
  const highPollution = aqi > 150 || category === 'Unhealthy' || category === 'Very Unhealthy' || category === 'Hazardous';
  const items: QuantifiedActionItem[] = [];

  if (profile.commuteMode === 'car' || profile.commuteMode === 'two_wheeler') {
    items.push({
      text: `Shift ${cityLabel} commute away from peak inversion traffic (before 8:00 AM or after 10:15 AM) or take electrified metro/bus`,
      pm25Avoided: highPollution ? '28 µg/m³ peak avoided (-45% inhaled)' : '12 µg/m³ avoided (-35% inhaled)',
      co2SavedKg: profile.commuteMode === 'car' ? '3.2 kg CO₂/day' : '1.4 kg CO₂/day',
      whyAdvice: 'Stop-and-go congestion concentrates in-cabin PM2.5 and NO2 3–5× above sidewalk baselines (CPCB 2023).',
    });
  } else {
    items.push({
      text: `Keep outdoor errands in ${cityLabel} within the sunny midday dispersion window (12:00 PM – 3:30 PM)`,
      pm25Avoided: highPollution ? '34 µg/m³ peak avoided (-52% inhaled)' : '10 µg/m³ avoided (-30% inhaled)',
      co2SavedKg: '0.8 kg CO₂/trip vs motor vehicle',
      whyAdvice: 'Solar convective mixing breaks the winter radiation inversion ceiling around midday (CPCB/WHO).',
    });
  }

  if (profile.children || profile.elderly || profile.asthma) {
    items.push({
      text: profile.asthma
        ? 'Keep prescribed bronchodilator accessible; shift school sports and sensitive-cohort walks indoors'
        : 'Reschedule children’s outdoor play and senior walks after 11:30 AM and avoid arterial roads',
      pm25Avoided: highPollution ? '42 µg/m³ avoided (-58% lung load)' : '14 µg/m³ avoided (-40%)',
      co2SavedKg: '1.1 kg CO₂/day (school carpool vs solo drop-off)',
      whyAdvice: 'Developing pediatric lungs, aging cilia, and reactive airways experience bronchospasm at lower PM2.5 doses (WHO 2021).',
    });
  }

  if (profile.outdoorWorker) {
    items.push({
      text: 'Wear a snugly fitted certified N95/FFP2 respirator during outdoor shifts and rotate heavy tasks to midday',
      pm25Avoided: 'Up to 95% fine PM2.5 filtered (~65 µg/m³ avoided)',
      co2SavedKg: '0.4 kg CO₂/day (planned consolidated site trips)',
      whyAdvice: 'Outdoor workers face continuous high-ventilation inhalation where cloth masks fail sub-micron filtration (MoHFW).',
    });
  }

  if (items.length < 2) {
    items.push({
      text: highPollution
        ? 'Consolidate errands remotely or shift cardio workouts to indoor filtered spaces'
        : 'Choose walking or cycling on tree-lined streets for trips under 2 km',
      pm25Avoided: highPollution ? '38 µg/m³ workout spike avoided' : '6 µg/m³ avoided',
      co2SavedKg: '1.6 kg CO₂/day saved',
      whyAdvice: 'Aerobic exercise increases breathing rate 5–10×, driving surface soot deep into lung alveoli (WHO).',
    });
  }

  return items;
}

function buildIndoorHackItems(
  aqi: number,
  profile: HouseholdProfile
): QuantifiedActionItem[] {
  const highPollution = aqi > 150;
  return [
    {
      text: highPollution
        ? 'Seal dawn/nighttime window drafts; ventilate strictly 12:30 PM – 3:30 PM on clear afternoons'
        : 'Cross-ventilate rooms during midday low-traffic hours and keep roadside vents filtered',
      pm25Avoided: highPollution ? '45 µg/m³ indoor ingress prevented (-75%)' : '10 µg/m³ avoided (-60%)',
      co2SavedKg: '0.5 kg CO₂/day vs heavy AC compressor cycling',
      whyAdvice: 'Timed diurnal ventilation flushes indoor CO2 without admitting early-morning thermal inversion plumes (CPCB).',
    },
    {
      text:
        profile.asthma || profile.children
          ? 'Run bedroom HEPA purifier or 4-filter MERV-13 DIY Corsi-Rosenthal box overnight'
          : 'Build a low-cost MERV-13 Corsi-Rosenthal box fan filter for shared living rooms',
      pm25Avoided: highPollution ? '120+ µg/m³ cleared (-80% in 45 min)' : '18 µg/m³ reduced (-75%)',
      co2SavedKg: '0.3 kg CO₂/day (60W fan vs dual-compressor AC)',
      whyAdvice: 'High surface-area MERV-13 cubes deliver >250 CFM CADR at under 20% the energy and hardware cost of branded purifiers (EPA).',
    },
    {
      text: 'Replace dry sweeping with damp microfiber mopping and run kitchen range hood on high while cooking',
      pm25Avoided: '16 µg/m³ PM2.5 + 65% settled PM10 prevented',
      co2SavedKg: '0.2 kg CO₂/day (avoided vacuum draw)',
      whyAdvice: 'Dry brooming re-aerosolizes settled coarse dust and cooking soot back into family breathing zones (IIT Delhi / WHO).',
    },
  ];
}

function buildAlternativeItems(profile: HouseholdProfile): QuantifiedActionItem[] {
  const items: QuantifiedActionItem[] = [];

  if (profile.heatingType === 'biomass') {
    items.push({
      text: 'Replace open wood, coal, or biomass heating with an oil-filled electric radiant heater and heavy curtains',
      pm25Avoided: '>800 µg/m³ point spike eliminated (-90% indoor soot)',
      co2SavedKg: '3.6 kg CO₂/evening avoided',
      whyAdvice: 'Unvented biomass combustion produces severe black carbon, CO, and carcinogenic PAHs directly indoors (CPCB/BEE).',
    });
  } else if (profile.heatingType === 'gas') {
    items.push({
      text: 'Service gas heaters with external chimney flues or supplement with electric heat-pump/radiant warmth',
      pm25Avoided: '22 µg/m³ NO2/soot peak avoided',
      co2SavedKg: '1.9 kg CO₂/day saved',
      whyAdvice: 'Unvented gas space heaters release concentrated nitrogen dioxide that triggers pediatric and asthmatic airway inflammation (WHO).',
    });
  } else {
    items.push({
      text: 'Pair electric/solar heating with silicone door draft stoppers and thermal window drapes to retain warmth',
      pm25Avoided: 'Zero point-source soot; blocks 40% cold smog leaks',
      co2SavedKg: '1.5 kg CO₂/day reduced thermal draw',
      whyAdvice: 'Passive insulation eliminates combustion heating demand while physically blocking cold outdoor smog infiltration (BEE).',
    });
  }

  items.push({
    text: 'Organize RWA leaf composting instead of burning garden waste and join neighborhood EV carpools',
    pm25Avoided: '60+ µg/m³ neighborhood smoke plume prevented',
    co2SavedKg: '2.8 kg CO₂/day per household',
    whyAdvice: 'Preventing open biomass and leaf fires stops toxic community-wide PM2.5 spikes trapped under winter inversions (CPCB GRAP).',
  });

  return items;
}

export function getHealthRecommendations(
  category: AQICategory,
  aqi: number,
  profile: HouseholdProfile = DEFAULT_HOUSEHOLD_PROFILE,
  cityName = 'your city'
): HealthAdvice {
  const routineItems = buildRoutineItems(category, aqi, profile, cityName);
  const indoorHackItems = buildIndoorHackItems(aqi, profile);
  const alternativeItems = buildAlternativeItems(profile);

  const disclaimerText =
    'Deterministic CPCB/WHO guidance based on simulated or live sensor readings. Not intended as clinical medical advice.';
  const profileTags: string[] = [];
  if (profile.children) profileTags.push('children');
  if (profile.elderly) profileTags.push('elderly adults');
  if (profile.asthma) profileTags.push('asthma/COPD');
  if (profile.outdoorWorker) profileTags.push('outdoor workers');
  const sensitiveLine = profileTags.length > 0
    ? `Tailored precautions active for ${profileTags.join(', ')} in ${cityName} (${profile.commuteMode.replace('_', ' ')} commute, ${profile.heatingType} heating).`
    : 'Individuals with respiratory or cardiovascular sensitivity should monitor symptoms closely.';

  let base: HealthAdvice;
  switch (category) {
    case 'Good':
      base = {
        general:
          'Air quality is ideal for all outdoor leisure, exercise, and activities. Atmospheric particulate levels are well within safe environmental ranges.',
        sensitiveGroups:
          'Individuals with pre-existing respiratory or cardiovascular conditions can enjoy outdoor activities without special precautions.',
        outdoorActivity: 'Optimal conditions for running, cycling, and outdoor recreation.',
        protectiveMeasures: [
          'Natural home and office ventilation recommended',
          'Standard physical activities encouraged without restriction',
          'No specialized masks or filtration required',
        ],
        winterSmogAdvice: 'Clear conditions with no atmospheric trapping. Ideal for outdoor community sports and family walks.',
        impactExplanation: 'Active walking and cycling save ~160g CO2 per kilometer compared to private petrol car use.',
        disclaimer: disclaimerText,
      };
      break;

    case 'Moderate':
      base = {
        general:
          `Air quality is acceptable for most people. An AQI of ${aqi} indicates moderate ambient particulate exposure in urban corridors.`,
        sensitiveGroups: sensitiveLine,
        outdoorActivity: 'Generally safe for outdoor sports; consider breaks during peak traffic hours.',
        protectiveMeasures: [
          'Ventilate rooms during midday low-traffic windows',
          'Keep rescue inhalers accessible if prone to airway irritation',
          'Keep windows closed during peak industrial transit periods',
        ],
        winterSmogAdvice: 'Mild evening haze can develop; sensitive family members should conclude workouts before dusk.',
        impactExplanation: 'Off-peak commuting cuts stop-and-go in-cabin toxic gas inhalation by up to 35% and saves ~1.4–3.2 kg CO2/day.',
        disclaimer: disclaimerText,
      };
      break;

    case 'Unhealthy for Sensitive Groups':
      base = {
        general:
          'General public is less likely to be affected, but sensitive individuals may experience throat irritation or shortness of breath.',
        sensitiveGroups: sensitiveLine,
        outdoorActivity: 'Moderate intensity outdoor activities suggested during midday only; avoid dawn congestion.',
        protectiveMeasures: [
          'Sensitive individuals should wear well-fitting certified N95 masks outdoors',
          'Use indoor air purifiers or Corsi-Rosenthal HEPA filtration boxes',
          'Avoid exercising near congested highways and open waste burning',
        ],
        winterSmogAdvice: 'Thermal inversion layers concentrate particulate matter near surface breathing height during mornings.',
        impactExplanation: 'Shifting routines to midday avoids 45–55% peak PM2.5 inhalation and cuts commute CO2 by up to 3.2 kg/day.',
        disclaimer: disclaimerText,
      };
      break;

    case 'Unhealthy':
      base = {
        general:
          'Everyone may begin to experience health effects such as eye irritation or coughing. Sensitive groups face higher acute risk.',
        sensitiveGroups: sensitiveLine,
        outdoorActivity: 'Avoid strenuous outdoor activities; relocate workouts indoors.',
        protectiveMeasures: [
          'Wear certified N95/FFP2 respirators when venturing outside',
          'Seal windows during morning inversion and use HEPA air filtration',
          'Switch away from solid-fuel/wood heaters and dry sweeping',
        ],
        winterSmogAdvice: 'Winter thermal inversion traps vehicle exhaust and biomass smoke at ground level; keep children indoors at dawn.',
        impactExplanation: 'Combining N95 protection (-95% inhaled PM2.5), HEPA filtration (-80%), and metro transit (-3.2 kg CO2/day) sharply cuts exposure.',
        disclaimer: disclaimerText,
      };
      break;

    case 'Very Unhealthy':
    case 'Hazardous':
    default:
      base = {
        general:
          'Health alert: Atmospheric pollution poses emergency health risks for all urban inhabitants.',
        sensitiveGroups: sensitiveLine,
        outdoorActivity: 'Prohibit all non-essential outdoor travel and vigorous dawn activities.',
        protectiveMeasures: [
          'Strict indoor shelter with closed windows and continuous HEPA/MERV-13 filtration',
          'Certified N95/FFP2 respirators required for mandatory outdoor transit',
          'Consult medical lines promptly for acute respiratory distress',
        ],
        winterSmogAdvice: 'Severe winter smog emergency with stagnant ground inversion. Suspend outdoor morning assemblies and school PE.',
        impactExplanation: 'Indoor HEPA containment avoids up to 85% hazardous PM2.5 exposure; eliminating biomass fires saves ~3.6 kg CO2/evening.',
        disclaimer: disclaimerText,
      };
      break;
  }

  return {
    ...base,
    lowEmissionRoutines: routineItems.map((i) => i.text),
    indoorAirHacks: indoorHackItems.map((i) => i.text),
    sustainableAlternatives: alternativeItems.map((i) => i.text),
    routineItems,
    indoorHackItems,
    alternativeItems,
  };
}
