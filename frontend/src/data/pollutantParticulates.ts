import type { PollutantId } from '../types/dashboard';
import type { PollutantDetailedInfo } from '../types/pollutants';

export const PARTICULATE_DETAILS: Record<'pm25' | 'pm10', PollutantDetailedInfo> = {
  pm25: {
    id: 'pm25',
    name: 'PM2.5',
    formula: 'PM₂.₅',
    fullName: 'Fine Inhalable Particulate Matter',
    classification: 'Particulate Matter',
    unit: 'µg/m³',
    whoLimit: 15,
    whoLimitText: '15 µg/m³ (24h Mean)',
    naaqsLimit: 60,
    naaqsLimitText: '60 µg/m³ (24h Standard)',
    description:
      'Atmospheric particulate matter with an aerodynamic diameter of 2.5 micrometers or smaller (approximately 3% the diameter of a human hair). Due to their minute scale, these particles remain suspended in ambient air for prolonged periods and can travel extensive distances.',
    primarySources: [
      'Internal combustion vehicular exhaust (primarily diesel emissions)',
      'Thermal coal power generation and metallurgical industries',
      'Seasonal agricultural residue and biomass combustion',
      'Construction dust, asphalt processing, and road surface wear',
    ],
    environmentalImpact:
      'Reduces regional visibility (creating dense regional haze), alters global radiation balances, deposits on foliage disrupting photosynthetic processes, and can acidify freshwater bodies upon precipitation.',
    healthEffects: {
      overview:
        'Fine particles bypass natural upper airway filtration (nasal hairs and cilia), penetrating deep into alveoli and crossing into systemic circulation.',
      sensitiveGroups: [
        {
          group: 'Children & Infants',
          description:
            'Developing lungs and higher ventilation rates per body weight heighten vulnerability to bronchial inflammation and impaired lung growth.',
        },
        {
          group: 'Older Adults',
          description:
            'Higher baseline prevalence of cardiovascular and cerebrovascular conditions elevates susceptibility to acute ischemic episodes.',
        },
        {
          group: 'Asthma & COPD Patients',
          description:
            'May provoke immediate bronchospasm, increase airway resistance, and trigger acute exacerbations requiring medical intervention.',
        },
        {
          group: 'Cardiovascular Patients',
          description:
            'Systemic microvascular inflammation may accelerate atherosclerotic plaque instability and trigger cardiac arrhythmias.',
        },
      ],
      symptoms: [
        'Shortness of breath and thoracic tightness',
        'Persistent coughing, throat irritation, and sneezing',
        'Aggravation of allergic rhinitis and sinusitis',
        'Elevated pulse rate during prolonged outdoor physical exertion',
      ],
    },
    protectiveMeasures: [
      'Employ certified N95 / FFP2 respirators during high-density exposure events',
      'Operate indoor True HEPA air filtration systems in closed living spaces',
      'Schedule strenuous outdoor exercise for early dawn or post-rainfall windows',
      'Keep windows sealed along high-traffic arterial road corridors during rush hours',
    ],
    color: '#F59E0B',
    accentColor: '#D97706',
  },

  pm10: {
    id: 'pm10',
    name: 'PM10',
    formula: 'PM₁₀',
    fullName: 'Coarse Inhalable Particulate Matter',
    classification: 'Particulate Matter',
    unit: 'µg/m³',
    whoLimit: 45,
    whoLimitText: '45 µg/m³ (24h Mean)',
    naaqsLimit: 100,
    naaqsLimitText: '100 µg/m³ (24h Standard)',
    description:
      'Coarse airborne particulate matter with an aerodynamic diameter between 2.5 and 10 micrometers. These particles are typically generated through mechanical abrasion, soil erosion, and industrial grinding activities.',
    primarySources: [
      'Resuspension of road dust from vehicular tire friction',
      'Uncovered civil construction, earth-moving, and demolition sites',
      'Open quarrying, aggregate crushing, and mining conveyor operations',
      'Dry soil erosion, agricultural plowing, and windblown mineral crust',
    ],
    environmentalImpact:
      'Deposits noticeable soot and dust films across urban surfaces, architectural monuments, and solar photovoltaic panels, reducing solar collection efficiency.',
    healthEffects: {
      overview:
        'Coarse particles deposit primarily within the nasopharyngeal and tracheobronchial regions of the human respiratory tract, causing mechanical irritation of epithelial tissues.',
      sensitiveGroups: [
        {
          group: 'Outdoor Workers',
          description:
            'Laborers, traffic enforcement personnel, and delivery riders face continuous, unmitigated exposure to mechanical dust clouds.',
        },
        {
          group: 'Chronic Bronchitis Patients',
          description:
            'Excessive dust deposition accelerates mucus hypersecretion and chronic airway obstruction.',
        },
        {
          group: 'Elderly Individuals',
          description:
            'Diminished mucociliary clearance mechanisms in aging airways impair particle expulsion.',
        },
      ],
      symptoms: [
        'Dry throat, persistent phlegm production, and coughing',
        'Ocular burning, conjunctive redness, and watering',
        'Nasal congestion and upper respiratory airway dryness',
      ],
    },
    protectiveMeasures: [
      'Wet-suppress dust around construction perimeter perimeters and unpaved pathways',
      'Wear protective face coverings in quarry, highway, or high-dust zones',
      'Wash face, eyes, and nasal passages thoroughly after prolonged outdoor exposure',
      'Utilize electrostatic or cyclonic pre-filters before fine HEPA filtration stages',
    ],
    color: '#EA580C',
    accentColor: '#C2410C',
  },
};

export type ParticulatePollutantId = Extract<PollutantId, 'pm25' | 'pm10'>;
