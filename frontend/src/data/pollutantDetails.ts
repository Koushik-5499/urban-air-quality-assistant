import type { PollutantId, ChartTimeRange, CityDashboardData, PollutantMetric } from '../types/dashboard';
import type { PollutantDetailedInfo, DetailedTrendPoint, PollutantSubIndex } from '../types/pollutants';

export const POLLUTANT_DETAILS: Record<PollutantId, PollutantDetailedInfo> = {
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
    color: '#F59E0B', // Amber
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
    color: '#EA580C', // Orange
    accentColor: '#C2410C',
  },

  co: {
    id: 'co',
    name: 'CO',
    formula: 'CO',
    fullName: 'Carbon Monoxide',
    classification: 'Gaseous Combustion',
    unit: 'mg/m³',
    whoLimit: 4,
    whoLimitText: '4 mg/m³ (24h Guideline)',
    naaqsLimit: 2,
    naaqsLimitText: '2 mg/m³ (8h Standard)',
    description:
      'A colorless, odorless, and non-irritating toxic gas formed by the incomplete combustion of carbon-based fuels (gasoline, diesel, natural gas, wood, and coal) in oxygen-deficient environments.',
    primarySources: [
      'Vehicular internal combustion engines operating at idle or low speeds',
      'Decentralized diesel generators and small commercial engines',
      'Residential biomass burning, solid fuel cookstoves, and charcoal heaters',
      'Industrial smelting furnaces and refinery flare processes',
    ],
    environmentalImpact:
      'While not a direct greenhouse gas, CO reacts with atmospheric hydroxyl radicals (OH), depleting the atmosphere’s self-cleansing capacity and indirectly prolonging methane lifetime.',
    healthEffects: {
      overview:
        'CO exhibits a binding affinity for hemoglobin approximately 200–250 times greater than that of oxygen, forming carboxyhemoglobin (COHb) and severely impairing tissue oxygenation.',
      sensitiveGroups: [
        {
          group: 'Cardiovascular Patients',
          description:
            'Patients with coronary artery disease may experience premature myocardial ischemia and angina at COHb levels as low as 2–4%.',
        },
        {
          group: 'Pregnant Women & Fetuses',
          description:
            'Fetal hemoglobin binds CO eagerly; reduced transplacental oxygen delivery can impair fetal neurodevelopment.',
        },
        {
          group: 'Older Adults',
          description:
            'Pre-existing vascular calcification magnifies the impact of acute arterial hypoxia.',
        },
      ],
      symptoms: [
        'Dull frontal headache and visual fatigue',
        'Dizziness, lightheadedness, and mild disorientation',
        'Generalized muscular weakness and diminished reaction times',
        'Exertional chest discomfort in individuals with coronary insufficiency',
      ],
    },
    protectiveMeasures: [
      'Install UL-certified electrochemical CO alarms in enclosed structures near combustion appliances',
      'Prohibit vehicle idling inside attached basements, garages, or enclosed driveways',
      'Ensure chimney flues, exhausts, and combustion room ventilation remain unobstructed',
      'Avoid unvented kerosene or charcoal space heaters in bedrooms',
    ],
    color: '#DC2626', // Red
    accentColor: '#B91C1C',
  },

  no2: {
    id: 'no2',
    name: 'NO2',
    formula: 'NO₂',
    fullName: 'Nitrogen Dioxide',
    classification: 'Gaseous Combustion',
    unit: 'µg/m³',
    whoLimit: 25,
    whoLimitText: '25 µg/m³ (24h Guideline)',
    naaqsLimit: 80,
    naaqsLimitText: '80 µg/m³ (24h Standard)',
    description:
      'A pungent, brownish gas formed at high temperatures when atmospheric nitrogen reacts with oxygen during combustion. It serves as a primary precursor for photochemical ground-level ozone and nitrate aerosols.',
    primarySources: [
      'Heavy-duty diesel trucks, buses, and marine transit corridors',
      'Coal and natural gas thermal power generation facilities',
      'Industrial furnaces, kilns, and chemical nitric acid synthesis plants',
      'Unvented indoor gas stoves, kerosene heaters, and boilers',
    ],
    environmentalImpact:
      'Undergoes photochemical reactions leading to acid deposition (nitric acid rain), accelerating structural corrosion, depleting soil calcium, and causing aquatic acidification and nutrient eutrophication.',
    healthEffects: {
      overview:
        'A potent oxidant gas that inflames the mucous membranes of the lungs, damages bronchial epithelial cells, and amplifies allergic sensitivities.',
      sensitiveGroups: [
        {
          group: 'Children',
          description:
            'Chronic exposure is statistically linked with higher incidence of childhood asthma and diminished forced expiratory volume.',
        },
        {
          group: 'Asthmatic Individuals',
          description:
            'Increases bronchial reactivity to common airborne allergens such as pollen, house dust mites, and animal dander.',
        },
        {
          group: 'Elderly with COPD',
          description:
            'Can precipitate acute respiratory failure and hospital re-admissions.',
        },
      ],
      symptoms: [
        'Irritating dry cough and pharyngeal inflammation',
        'Wheezing and rapid shallow breathing',
        'Increased vulnerability to secondary bacterial and viral airway infections',
      ],
    },
    protectiveMeasures: [
      'Use high-flow exhaust range hoods vented outdoors when cooking with natural gas',
      'Choose pedestrian paths situated at least 50 meters back from congested arterial roads',
      'Equip indoor air purification with activated carbon adsorption stages to capture gaseous oxides',
      'Maintain adequate cross-ventilation in rooms with combustion heating systems',
    ],
    color: '#0284C7', // Sky Blue
    accentColor: '#0369A1',
  },

  so2: {
    id: 'so2',
    name: 'SO2',
    formula: 'SO₂',
    fullName: 'Sulfur Dioxide',
    classification: 'Gaseous Combustion',
    unit: 'µg/m³',
    whoLimit: 40,
    whoLimitText: '40 µg/m³ (24h Guideline)',
    naaqsLimit: 80,
    naaqsLimitText: '80 µg/m³ (24h Standard)',
    description:
      'A colorless, reactive gas with an intensely sharp, choking odor. It is primarily released through the thermal combustion of sulfur-rich raw fossil fuels (coal and heavy fuel oil) and mineral ore smelting.',
    primarySources: [
      'Thermal power plants burning sulfur-containing bituminous or lignite coal',
      'Metal refining, copper/zinc smelters, and petroleum cracking units',
      'Commercial maritime vessels burning heavy bunker fuel oil',
      'Chemical paper pulping and sulfuric acid manufacturing facilities',
    ],
    environmentalImpact:
      'The principal causative agent of sulfuric acid rain. Causes severe foliar necrosis on agricultural crops, dissolves calcareous stone in heritage architecture, and acidifies pristine catchment waterways.',
    healthEffects: {
      overview:
        'Being highly water-soluble, SO2 rapidly dissolves into the moist mucous membranes of the upper respiratory tract, triggering immediate reflex bronchoconstriction within minutes.',
      sensitiveGroups: [
        {
          group: 'Asthmatic Children & Adults',
          description:
            'Can trigger severe bronchospastic attacks within 5 to 10 minutes of moderate exercise in ambient SO2 atmospheres.',
        },
        {
          group: 'Chronic Bronchitis Sufferers',
          description:
            'Aggravates persistent bronchial wall swelling and hampers alveolar gas exchange.',
        },
      ],
      symptoms: [
        'Immediate throat tightness, choking sensation, and stinging coughing',
        'Burning sensation in eyes and nasal passages',
        'Severe acute wheezing in hyper-reactive airways',
      ],
    },
    protectiveMeasures: [
      'Avoid high-intensity outdoor cardiovascular exercise downwind of industrial thermal clusters',
      'Individuals with asthma should verify their rescue bronchodilators are on hand when SO2 levels spike',
      'Ensure HVAC air handlers incorporate impregnated chemical adsorption media',
    ],
    color: '#9333EA', // Purple
    accentColor: '#7E22CE',
  },

  o3: {
    id: 'o3',
    name: 'O3',
    formula: 'O₃',
    fullName: 'Ground-Level Ozone (Tropospheric)',
    classification: 'Photochemical Oxidant',
    unit: 'µg/m³',
    whoLimit: 100,
    whoLimitText: '100 µg/m³ (8h Guideline)',
    naaqsLimit: 100,
    naaqsLimitText: '100 µg/m³ (8h Standard)',
    description:
      'A secondary photochemical pollutant formed when precursor gases—principally Nitrogen Oxides (NOx) and Volatile Organic Compounds (VOCs)—chemically interact in the presence of strong solar ultraviolet radiation and warm ambient temperatures.',
    primarySources: [
      'Secondary reaction: Vehicle exhaust NOx + Industrial VOC solvents under sunlight',
      'Evaporative fuel emissions from retail petrol filling stations',
      'Chemical solvent manufacturing, printing presses, and spray painting',
      'Biogenic hydrocarbon emissions from certain urban tree canopies under intense heat',
    ],
    environmentalImpact:
      'A fierce biological oxidant. Enters plant stomata to destroy mesophyll cells, reducing photosynthetic efficiency and stunting growth in key agricultural staple crops like wheat, rice, and cotton.',
    healthEffects: {
      overview:
        'Ozone literally oxidizes delicate biological tissues, triggering severe cellular necrosis across respiratory alveolar membranes, reducing lung elasticity and functional vital capacity.',
      sensitiveGroups: [
        {
          group: 'Active Outdoor Children',
          description:
            'Longer duration of vigorous afternoon outdoor play exposes smaller developing airways to peak photochemical concentrations.',
        },
        {
          group: 'Outdoor Athletes',
          description:
            'High minute ventilation rates pull large volumes of ozone deep into terminal bronchioles.',
        },
        {
          group: 'Asthma & Allergy Patients',
          description:
            'Ozone heightens airway hyperreactivity and triggers sudden bronchial contractions.',
        },
      ],
      symptoms: [
        'Deep chest pain upon taking a full breath',
        'Dry, painful spasmodic coughing',
        'Throat irritation and airway burning',
        'Premature exhaustion during routine cardiovascular tasks',
      ],
    },
    protectiveMeasures: [
      'Shift strenuous physical recreation and workouts to early mornings before photochemical reaction peaks',
      'Remain indoors in air-conditioned or well-filtered rooms during peak sunny afternoon hours (13:00–17:00)',
      'Refuel vehicles and handle chemical solvents during late evening hours to curb VOC evaporation',
    ],
    color: '#10B981', // Emerald
    accentColor: '#059669',
  },
};

/**
 * Generates continuous trend series for all 6 pollutants anchored to the city's actual simulated readings.
 */
export function generatePollutantTrends(
  cityData: CityDashboardData,
  timeRange: ChartTimeRange
): DetailedTrendPoint[] {
  const pm25Base = cityData.pollutants.find((p) => p.id === 'pm25')?.value ?? 25;
  const pm10Base = cityData.pollutants.find((p) => p.id === 'pm10')?.value ?? 55;
  const coBase = cityData.pollutants.find((p) => p.id === 'co')?.value ?? 0.8;
  const no2Base = cityData.pollutants.find((p) => p.id === 'no2')?.value ?? 32;
  const so2Base = cityData.pollutants.find((p) => p.id === 'so2')?.value ?? 14;
  const o3Base = cityData.pollutants.find((p) => p.id === 'o3')?.value ?? 40;
  const aqiBase = cityData.aqi;

  if (timeRange === '24h') {
    const times = ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'];
    const multipliers = [0.82, 0.74, 0.90, 1.25, 1.05, 0.98, 1.22, 1.08];
    const o3Multipliers = [0.45, 0.35, 0.50, 0.85, 1.35, 1.48, 1.10, 0.65]; // Ozone peaks in afternoon!

    return times.map((t, idx) => {
      const m = multipliers[idx];
      const o3m = o3Multipliers[idx];
      return {
        time: t,
        pm25: Number((pm25Base * m).toFixed(1)),
        pm10: Number((pm10Base * m).toFixed(1)),
        co: Number((coBase * (0.85 + m * 0.15)).toFixed(2)),
        no2: Number((no2Base * (0.8 + m * 0.2)).toFixed(1)),
        so2: Number((so2Base * (0.9 + (idx % 3) * 0.1)).toFixed(1)),
        o3: Number((o3Base * o3m).toFixed(1)),
        aqi: Math.round(aqiBase * m),
      };
    });
  }

  if (timeRange === '7d') {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const multipliers = [0.95, 0.90, 1.10, 1.02, 1.18, 0.85, 0.92];

    return days.map((day, idx) => {
      const m = multipliers[idx];
      return {
        time: day,
        pm25: Number((pm25Base * m).toFixed(1)),
        pm10: Number((pm10Base * m).toFixed(1)),
        co: Number((coBase * (0.9 + m * 0.1)).toFixed(2)),
        no2: Number((no2Base * m).toFixed(1)),
        so2: Number((so2Base * (0.92 + (idx % 2) * 0.12)).toFixed(1)),
        o3: Number((o3Base * (0.95 + (idx % 4) * 0.08)).toFixed(1)),
        aqi: Math.round(aqiBase * m),
      };
    });
  }

  // 30 Days (sample intervals every 3-4 days)
  const intervals = [
    'Day 1', 'Day 4', 'Day 8', 'Day 12', 'Day 16',
    'Day 20', 'Day 24', 'Day 28', 'Day 30',
  ];
  const multipliers = [0.88, 0.94, 1.12, 0.96, 1.24, 1.02, 0.90, 1.08, 1.0];

  return intervals.map((day, idx) => {
    const m = multipliers[idx];
    return {
      time: day,
      pm25: Number((pm25Base * m).toFixed(1)),
      pm10: Number((pm10Base * m).toFixed(1)),
      co: Number((coBase * (0.9 + m * 0.1)).toFixed(2)),
      no2: Number((no2Base * m).toFixed(1)),
      so2: Number((so2Base * (0.95 + (idx % 3) * 0.06)).toFixed(1)),
      o3: Number((o3Base * (0.9 + (idx % 3) * 0.1)).toFixed(1)),
      aqi: Math.round(aqiBase * m),
    };
  });
}

/**
 * Calculates scientifically grounded AQI sub-indices for the 6 pollutants based on
 * the Indian CPCB / EPA breakpoint methodology, showing how the dominant pollutant governs the AQI.
 */
export function calculateAQISubIndices(
  pollutants: PollutantMetric[],
  overallAQI: number
): PollutantSubIndex[] {
  // Approximate standard limits for benchmark ratio (WHO/NAAQS)
  const limits: Record<PollutantId, number> = {
    pm25: 60, // NAAQS 24h
    pm10: 100, // NAAQS 24h
    co: 2.0, // NAAQS 8h (mg/m³)
    no2: 80, // NAAQS 24h
    so2: 80, // NAAQS 24h
    o3: 100, // NAAQS 8h
  };

  const items = pollutants.map((p) => {
    const limit = limits[p.id] || 100;
    const benchmarkPercentage = Math.round((p.value / limit) * 100);

    // Approximate sub-index calculation based on linear piecewise scale
    let subIndex = 0;
    if (p.id === 'pm25') {
      subIndex = p.value <= 30 ? (p.value / 30) * 50 : 50 + ((p.value - 30) / 30) * 50;
    } else if (p.id === 'pm10') {
      subIndex = p.value <= 50 ? (p.value / 50) * 50 : 50 + ((p.value - 50) / 50) * 50;
    } else if (p.id === 'co') {
      subIndex = p.value <= 1.0 ? (p.value / 1.0) * 50 : 50 + ((p.value - 1.0) / 1.0) * 50;
    } else if (p.id === 'no2') {
      subIndex = p.value <= 40 ? (p.value / 40) * 50 : 50 + ((p.value - 40) / 40) * 50;
    } else if (p.id === 'so2') {
      subIndex = p.value <= 40 ? (p.value / 40) * 50 : 50 + ((p.value - 40) / 40) * 50;
    } else if (p.id === 'o3') {
      subIndex = p.value <= 50 ? (p.value / 50) * 50 : 50 + ((p.value - 50) / 50) * 50;
    }
    subIndex = Math.min(Math.round(subIndex), 500);

    return {
      id: p.id,
      name: p.name,
      formula: p.formula,
      concentration: p.value,
      unit: p.unit,
      subIndex,
      isDominant: false,
      benchmarkPercentage,
      category: p.status,
      color: POLLUTANT_DETAILS[p.id]?.color || '#10B981',
    };
  });

  // Find dominant (highest sub-index)
  let maxIdx = 0;
  for (let i = 1; i < items.length; i++) {
    if (items[i].subIndex > items[maxIdx].subIndex) {
      maxIdx = i;
    }
  }
  if (items[maxIdx]) {
    items[maxIdx].isDominant = true;
    // Tie dominant sub-index closely to the city's calculated AQI
    items[maxIdx].subIndex = Math.max(items[maxIdx].subIndex, overallAQI);
  }

  return items;
}

