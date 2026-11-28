import type { PollutantId } from '../types/dashboard';
import type { PollutantDetailedInfo } from '../types/pollutants';

export type GaseousPollutantId = Exclude<PollutantId, 'pm25' | 'pm10'>;

export const GASEOUS_DETAILS: Record<GaseousPollutantId, PollutantDetailedInfo> = {
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
    color: '#DC2626',
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
    color: '#0284C7',
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
    color: '#9333EA',
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
    color: '#10B981',
    accentColor: '#059669',
  },
};

