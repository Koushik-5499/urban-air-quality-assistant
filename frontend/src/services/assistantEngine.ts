import type { CityDashboardData } from '../types/dashboard';
import type { HealthRecommendationCard, SuggestedQuestion } from '../types/assistant';

export const SUGGESTED_QUESTIONS: SuggestedQuestion[] = [
  {
    id: 'sq-1',
    question: 'Is the air quality safe for my asthmatic child to play outdoors today?',
    category: 'Sensitive Groups',
  },
  {
    id: 'sq-2',
    question: 'Is it safe to exercise outdoors given the current AQI?',
    category: 'Outdoor Guidance',
  },
  {
    id: 'sq-3',
    question: 'What are the current PM2.5 levels and health risks for elderly residents?',
    category: 'Sensitive Groups',
  },
  {
    id: 'sq-4',
    question: 'Should outdoor workers take precautions given today\'s air quality forecast?',
    category: 'Outdoor Workers',
  },
  {
    id: 'sq-5',
    question: 'What indoor precautions should I take during Very Unhealthy air quality?',
    category: 'Protection',
  },
  {
    id: 'sq-6',
    question: 'How does today\'s AQI compare to safe WHO guidelines?',
    category: 'AQI Context',
  },
];

/**
 * Local rule-based AI Health Assistant response generator.
 * Analyzes query keywords and synthesizes tailored responses based on
 * the selected city's real-time simulated telemetry.
 */
export function generateAssistantResponse(
  query: string,
  cityData: CityDashboardData
): string {
  const q = query.toLowerCase().trim();
  const { location, aqi, category, dominantPollutant, pollutants, weather } = cityData;

  const pm25 = pollutants.find((p) => p.id === 'pm25')?.value ?? 25;
  const pm10 = pollutants.find((p) => p.id === 'pm10')?.value ?? 55;
  const co = pollutants.find((p) => p.id === 'co')?.value ?? 0.8;
  const no2 = pollutants.find((p) => p.id === 'no2')?.value ?? 30;
  const so2 = pollutants.find((p) => p.id === 'so2')?.value ?? 15;
  const o3 = pollutants.find((p) => p.id === 'o3')?.value ?? 40;

  // 1. Topic: What does today's AQI mean? / Explain AQI
  if (
    q.includes("today's aqi") ||
    q.includes('what does aqi mean') ||
    q.includes('what does today') ||
    q.includes('explain aqi') ||
    q.includes('current aqi') ||
    q.includes('air quality index mean')
  ) {
    let categoryExplanation = '';
    if (aqi <= 50) {
      categoryExplanation =
        'Air quality is considered satisfactory, and air pollution poses little or no risk. Ambient air is clean across urban sectors.';
    } else if (aqi <= 100) {
      categoryExplanation =
        'Air quality is acceptable. However, for some pollutants there may be a moderate health concern for a very small number of individuals who are unusually sensitive to air pollution.';
    } else if (aqi <= 150) {
      categoryExplanation =
        'Members of sensitive groups (children, elderly, and people with respiratory or cardiovascular disease) may experience health effects. The general public is less likely to be affected.';
    } else if (aqi <= 200) {
      categoryExplanation =
        'Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.';
    } else {
      categoryExplanation =
        'Health alert: The risk of adverse health effects is increased for everyone. Strenuous outdoor activities should be avoided.';
    }

    return `Currently in **${location.city}, ${location.state}**, the Air Quality Index is **${aqi}**, which falls into the **${category}** tier.\n\n` +
      `**What this means:**\n${categoryExplanation}\n\n` +
      `**Primary Influencing Factors:**\n` +
      `• **Dominant Contaminant:** ${dominantPollutant} is the primary driver governing today's sub-index.\n` +
      `• **Fine Particulates (PM2.5):** ${pm25.toFixed(1)} µg/m³ (WHO target: 15 µg/m³).\n` +
      `• **Coarse Particulates (PM10):** ${pm10.toFixed(1)} µg/m³ (NAAQS target: 100 µg/m³).\n` +
      `• **Local Meteorology:** ${weather.temperature.toFixed(1)}°C, ${weather.humidity}% humidity with ${weather.condition.toLowerCase()} skies.\n\n` +
      `*Educational disclaimer: This information is based on simulated atmospheric telemetry models and does not substitute for clinical medical advice.*`;
  }

  // 2. Topic: Is it safe to go outside? / Outdoor activity
  if (
    q.includes('safe to go outside') ||
    q.includes('can i go outside') ||
    q.includes('safe outside') ||
    q.includes('outdoor activity') ||
    q.includes('walk outside')
  ) {
    if (aqi <= 50) {
      return `Yes, outdoor conditions in **${location.city}** are **favorable and safe** today with an AQI of **${aqi} (Good)**.\n\n` +
        `• **General Public:** Ideal for outdoor walks, recreation, and open-air activities.\n` +
        `• **Sensitive Populations:** No restrictions necessary under current conditions.\n` +
        `• **Ventilation:** Good conditions for opening windows to refresh indoor air.\n\n` +
        `*Educational disclaimer: Values are simulated demonstration data.*`;
    }

    if (aqi <= 100) {
      return `In **${location.city}**, going outside is **generally safe for the healthy majority** (AQI is **${aqi} — Moderate**).\n\n` +
        `• **General Public:** You can engage in normal outdoor errands, commuting, and walking.\n` +
        `• **Sensitive Groups:** Individuals with chronic asthma, bronchitis, or heart disease should take occasional breaks during prolonged outdoor exertion.\n` +
        `• **Dominant Driver:** Watch for localized particulate spikes near heavy vehicular roads (current PM2.5: ${pm25.toFixed(1)} µg/m³).\n\n` +
        `*Educational disclaimer: Values are simulated demonstration data.*`;
    }

    return `In **${location.city}**, ambient air quality is currently **${category}** (AQI **${aqi}**). Caution is recommended:\n\n` +
      `• **General Public:** Reduce prolonged or vigorous outdoor physical exertion, particularly along major transit corridors.\n` +
      `• **Sensitive Groups (Children, Seniors, Asthmatics):** Limit outdoor activities and consider wearing an N95 respirator if spending extended periods outside.\n` +
      `• **Indoor Spaces:** Keep doors and windows closed during peak traffic hours to prevent outdoor soot ingress.\n\n` +
      `*Educational disclaimer: Educational guidance only. Consult a doctor for personal medical management.*`;
  }

  // 3. Topic: Outdoor exercise / Running / Jogging / Cycling / Workout
  if (
    q.includes('exercise') ||
    q.includes('running') ||
    q.includes('jogging') ||
    q.includes('cycling') ||
    q.includes('workout') ||
    q.includes('gym')
  ) {
    if (aqi <= 50) {
      return `Outdoor exercise in **${location.city}** is **fully recommended** today (AQI **${aqi} — Good**).\n\n` +
        `• **Cardiovascular Workouts:** Running, cycling, and outdoor team sports can proceed without pollution-related restrictions.\n` +
        `• **Weather Context:** Ambient temperature is ${weather.temperature.toFixed(1)}°C with ${weather.windSpeed} km/h breeze.\n` +
        `• **Hydration:** Maintain standard hydration during training.\n\n` +
        `*Educational disclaimer: Simulated demonstration data.*`;
    }

    if (aqi <= 100) {
      return `Outdoor workouts in **${location.city}** are **moderately safe** (AQI **${aqi} — Moderate**), but exercise timing matters:\n\n` +
        `• **Timing:** Schedule intense cardio workouts for early morning or late evening when vehicular traffic dispersion is lower.\n` +
        `• **Route Selection:** Avoid jogging or cycling along congested highways or construction corridors where localized PM2.5 can exceed ${pm25.toFixed(1)} µg/m³.\n` +
        `• **Symptom Awareness:** If you notice throat irritation, coughing, or unusual shortness of breath, reduce pace or shift indoors.\n\n` +
        `*Educational disclaimer: Educational guidance only.*`;
    }

    return `With an AQI of **${aqi} (${category})** in **${location.city}**, **strenuous outdoor exercise is not recommended** today.\n\n` +
      `• **Physiological Impact:** Heavy exercise increases your minute ventilation rate 5- to 10-fold, pulling deep particulate matter (${pm25.toFixed(1)} µg/m³ PM2.5) deep into pulmonary alveoli.\n` +
      `• **Recommended Alternative:** Shift cardio, running, or HIIT sessions indoors to an air-conditioned or HEPA-filtered fitness environment.\n` +
      `• **Outdoor Commuters:** Walk at a relaxed, steady pace rather than running.\n\n` +
      `*Educational disclaimer: Educational guidance only.*`;
  }

  // 4. Topic: Effects of PM2.5 / Fine Particulate Matter
  if (
    q.includes('pm2.5') ||
    q.includes('pm25') ||
    q.includes('fine particulate') ||
    q.includes('fine particles')
  ) {
    return `**Fine Particulate Matter (PM2.5)** consists of inhalable particles with an aerodynamic diameter under 2.5 micrometers (about 3% the width of a human hair).\n\n` +
      `**Current Reading in ${location.city}:** ${pm25.toFixed(1)} µg/m³ (Status: ${category}).\n\n` +
      `**Why PM2.5 is Significant:**\n` +
      `• **Deep Penetration:** Unlike coarse dust, PM2.5 evades upper nasal cilia and deposits deep inside the terminal alveoli of the lungs.\n` +
      `• **Bloodstream Entry:** Ultra-fine fractions can cross the alveolar-capillary barrier into systemic circulation.\n` +
      `• **Health Effects:** May trigger airway inflammation, exacerbate asthma and chronic bronchitis, increase cardiovascular workload, and reduce lung function development in children.\n` +
      `• **Regulatory Benchmarks:** WHO recommends a 24-hour mean limit of 15 µg/m³; Indian NAAQS sets the standard threshold at 60 µg/m³.\n\n` +
      `*Educational disclaimer: Compiled from WHO and CPCB public health guidelines for general awareness.*`;
  }

  // 5. Topic: Effects of other criteria pollutants (PM10, CO, NO2, SO2, O3)
  if (q.includes('pm10') || q.includes('coarse dust')) {
    return `**Respirable Coarse Particles (PM10)** have aerodynamic diameters between 2.5 and 10 micrometers.\n\n` +
      `• **Current ${location.city} Concentration:** ${pm10.toFixed(1)} µg/m³.\n` +
      `• **Primary Sources:** Resuspended road dust, civil demolition, aggregate stone crushing, and windblown agricultural soil.\n` +
      `• **Health Impacts:** Deposited primarily in the nasal cavity, throat, and upper bronchi. Can cause coughing, throat dryness, eye irritation, and aggravate allergic sinusitis.\n` +
      `• **Standard Limits:** WHO 24h: 45 µg/m³; Indian NAAQS: 100 µg/m³.\n\n` +
      `*Educational disclaimer: Simulated demonstration data.*`;
  }

  if (q.includes('carbon monoxide') || q.includes('co ') || q.endsWith('co')) {
    return `**Carbon Monoxide (CO)** is a colorless, odorless toxic gas generated by incomplete combustion of carbonaceous fuels.\n\n` +
      `• **Current ${location.city} Reading:** ${co.toFixed(2)} mg/m³.\n` +
      `• **Mechanism:** CO binds to hemoglobin with over 200× the affinity of oxygen, forming carboxyhemoglobin (COHb) and diminishing oxygen delivery to the heart and brain.\n` +
      `• **Symptoms:** Fatigue, headaches, and dizziness in enclosed or stagnant spaces.\n` +
      `• **Standard Limits:** Indian NAAQS 8-hour limit is 2.0 mg/m³.\n\n` +
      `*Educational disclaimer: Simulated demonstration data.*`;
  }

  if (q.includes('nitrogen dioxide') || q.includes('no2')) {
    return `**Nitrogen Dioxide (NO2)** is a reddish-brown, pungent combustion gas.\n\n` +
      `• **Current ${location.city} Reading:** ${no2.toFixed(1)} µg/m³.\n` +
      `• **Primary Sources:** Heavy diesel truck transit, industrial gas boilers, and thermal power generation.\n` +
      `• **Health Effects:** Potent respiratory oxidant. Inflames airway lining, increases bronchial hyperresponsiveness, and triggers allergic sensitivities.\n` +
      `• **Standard Limits:** WHO 24h: 25 µg/m³; Indian NAAQS: 80 µg/m³.\n\n` +
      `*Educational disclaimer: Simulated demonstration data.*`;
  }

  if (q.includes('sulfur dioxide') || q.includes('so2')) {
    return `**Sulfur Dioxide (SO2)** is a reactive choking gas released by burning sulfur-bearing coal and heavy bunker oils.\n\n` +
      `• **Current ${location.city} Reading:** ${so2.toFixed(1)} µg/m³.\n` +
      `• **Health Effects:** Highly water-soluble; rapidly triggers reflex bronchoconstriction, coughing, and chest tightness in individuals with asthma.\n` +
      `• **Standard Limits:** WHO 24h: 40 µg/m³; Indian NAAQS: 80 µg/m³.\n\n` +
      `*Educational disclaimer: Simulated demonstration data.*`;
  }

  if (q.includes('ozone') || q.includes('o3')) {
    return `**Ground-Level Ozone (O3)** is a secondary photochemical oxidant formed when vehicular NOx and VOCs react in the presence of strong solar ultraviolet radiation.\n\n` +
      `• **Current ${location.city} Reading:** ${o3.toFixed(1)} µg/m³.\n` +
      `• **Diurnal Cycle:** Typically peaks during warm, sunny mid-afternoon hours (13:00 to 17:00).\n` +
      `• **Health Effects:** Directly oxidizes respiratory epithelial cells, causing chest tightness, painful deep inhalation, and coughing in active outdoor individuals.\n` +
      `• **Standard Limits:** Indian NAAQS 8h threshold: 100 µg/m³.\n\n` +
      `*Educational disclaimer: Simulated demonstration data.*`;
  }

  // 6. Topic: How can I protect myself? / Masks / HEPA / Purifiers
  if (
    q.includes('protect myself') ||
    q.includes('how to protect') ||
    q.includes('mask') ||
    q.includes('purifier') ||
    q.includes('hepa') ||
    q.includes('protection')
  ) {
    return `Here is a comprehensive exposure-reduction strategy for **${location.city}** (current AQI: **${aqi}**):\n\n` +
      `**1. Personal Protective Masks:**\n` +
      `• Use certified **N95 or FFP2 respirators** fitted snugly over nose and mouth when spending time outdoors during elevated pollution.\n` +
      `• Note: Standard cloth and surgical masks filter coarse dust but do not seal against sub-micron PM2.5 particulates.\n\n` +
      `**2. Indoor Air Management:**\n` +
      `• Utilize air purifiers equipped with **True HEPA filters** (which capture 99.97% of particles down to 0.3 microns).\n` +
      `• Keep exterior doors and windows closed during morning and evening rush-hour traffic.\n` +
      `• Avoid indoor combustion sources like incense, unvented space heaters, or frying without an exhaust hood.\n\n` +
      `**3. Exposure Timing & Commute:**\n` +
      `• Select pedestrian paths set back at least 50 meters from high-density bus and truck corridors.\n` +
      `• Set car ventilation to "Recirculate" when driving in congested highway traffic.\n\n` +
      `*Educational disclaimer: Masks and purifiers reduce exposure but do not guarantee complete protection from all pollutants.*`;
  }

  // 7. Topic: Precautions for children
  if (
    q.includes('children') ||
    q.includes('kids') ||
    q.includes('school') ||
    q.includes('infants') ||
    q.includes('babies')
  ) {
    return `Children are particularly vulnerable to air pollution for biological and behavioral reasons:\n\n` +
      `**Why Children Face Higher Risk:**\n` +
      `• **Higher Respiratory Rate:** Children breathe more air per kilogram of body weight than adults.\n` +
      `• **Developing Airways:** Alveolar structures continue growing through late adolescence.\n` +
      `• **Mouth Breathing:** Active play encourages oral breathing, bypassing nasal particulate filtration.\n\n` +
      `**Recommended Precautions for ${location.city} (AQI ${aqi}):**\n` +
      `• ${aqi > 100 ? 'Restrict vigorous outdoor physical education and sports during midday.' : 'Outdoor school play is acceptable today; encourage frequent hydration.'}\n` +
      `• Keep school classrooms and play areas ventilated with filtered air where possible.\n` +
      `• Ensure children with diagnosed asthma have their quick-relief bronchodilator inhalers accessible.\n` +
      `• Wash hands, face, and eyes thoroughly after outdoor playtime.\n\n` +
      `*Educational disclaimer: Guidance is educational. Consult pediatricians for clinical child health plans.*`;
  }

  // 8. Topic: Precautions for elderly / seniors / cardiac
  if (
    q.includes('elderly') ||
    q.includes('seniors') ||
    q.includes('older adults') ||
    q.includes('heart') ||
    q.includes('cardiovascular')
  ) {
    return `Older adults and individuals with preexisting cardiovascular conditions should take specific precautions in **${location.city}** (AQI **${aqi}**):\n\n` +
      `**Vulnerability Factors:**\n` +
      `• Aging lung tissue exhibits diminished mucociliary particle clearance.\n` +
      `• Inhaled particulate matter (${pm25.toFixed(1)} µg/m³) can stimulate systemic vascular inflammation, potentially triggering myocardial ischemia or arrhythmias.\n\n` +
      `**Actionable Precautions:**\n` +
      `• Walk during late mornings after early-morning inversion layers have dissipated.\n` +
      `• Stay consistently hydrated and adhere strictly to prescribed cardiovascular medications.\n` +
      `• Seek prompt medical evaluation if you experience unusual chest discomfort, palpitations, or lightheadedness.\n\n` +
      `*Educational disclaimer: Educational information only, not clinical medical advice.*`;
  }

  // 9. Topic: Asthma / COPD / Respiratory
  if (
    q.includes('asthma') ||
    q.includes('copd') ||
    q.includes('respiratory') ||
    q.includes('bronchitis') ||
    q.includes('inhaler')
  ) {
    return `For individuals with **asthma, COPD, or chronic respiratory conditions** in **${location.city}** (AQI **${aqi} — ${category}**):\n\n` +
      `**Current Atmospheric Triggers:**\n` +
      `• **PM2.5:** ${pm25.toFixed(1)} µg/m³\n` +
      `• **Ozone:** ${o3.toFixed(1)} µg/m³\n` +
      `• **Nitrogen Dioxide:** ${no2.toFixed(1)} µg/m³\n\n` +
      `**Key Precautions:**\n` +
      `• Keep your prescribed rescue inhaler accessible at all times.\n` +
      `• Follow your personalized Asthma Action Plan developed with your pulmonologist.\n` +
      `• Stay indoors in HEPA-filtered rooms if you experience coughing or chest tightness.\n` +
      `• Avoid exposure to indoor triggers such as dust, pet dander, or cleaning chemical vapors.\n\n` +
      `*Educational disclaimer: Educational guidance only. Seek urgent medical care for acute breathing distress.*`;
  }

  // 10. Intelligent Fallback
  return `I'm analyzing the atmospheric telemetry for **${location.city}, ${location.state}**:\n\n` +
    `• **Current AQI Score:** **${aqi}** (${category})\n` +
    `• **Dominant Factor:** ${dominantPollutant}\n` +
    `• **Particulates:** PM2.5 at ${pm25.toFixed(1)} µg/m³ • PM10 at ${pm10.toFixed(1)} µg/m³\n` +
    `• **Meteorology:** ${weather.temperature.toFixed(1)}°C with ${weather.humidity}% humidity\n\n` +
    `You can ask me questions such as:\n` +
    `1. *"Is it safe to exercise outdoors today?"*\n` +
    `2. *"What does today's AQI score mean for health?"*\n` +
    `3. *"How can I protect my family from PM2.5?"*\n` +
    `4. *"What precautions should children and seniors take?"*\n\n` +
    `*Educational disclaimer: The Urban Air Quality Assistant provides general environmental health guidance for awareness purposes.*`;
}

/**
 * Generates 4-5 contextual health recommendation cards matching the selected city's current AQI.
 */
export function getHealthRecommendationsForCity(
  cityData: CityDashboardData
): HealthRecommendationCard[] {
  const { aqi } = cityData;

  const isGood = aqi <= 50;
  const isModerate = aqi > 50 && aqi <= 100;

  return [
    {
      id: 'rec-activity',
      category: 'activity',
      title: 'Outdoor Physical Activity',
      description: isGood
        ? 'Ideal conditions for all outdoor recreation, athletics, and commuting.'
        : isModerate
        ? 'Generally safe for most activities. Sensitive individuals should take breaks during strenuous workouts.'
        : 'Limit prolonged or heavy outdoor exertion. Shift strenuous cardio workouts indoors.',
      severity: isGood ? 'low' : isModerate ? 'moderate' : 'high',
      iconName: 'Activity',
      bullets: isGood
        ? ['Safe for all age groups', 'Unrestricted sports and running']
        : isModerate
        ? ['Avoid exercising near heavy traffic', 'Stay hydrated during workouts']
        : ['Shift workouts to indoor gyms', 'Walk at a relaxed pace outdoors'],
    },
    {
      id: 'rec-masks',
      category: 'masks',
      title: 'Personal Mask Precautions',
      description: isGood
        ? 'Face masks are not required for ambient air quality protection today.'
        : isModerate
        ? 'Masks optional for healthy adults; sensitive groups may consider N95 masks near traffic.'
        : 'Certified N95 or FFP2 respirators recommended for prolonged outdoor transit.',
      severity: isGood ? 'low' : isModerate ? 'moderate' : 'high',
      iconName: 'ShieldCheck',
      bullets: isGood
        ? ['No mask required outdoors', 'Standard breathing conditions']
        : isModerate
        ? ['Optional for sensitive individuals', 'Cloth masks do not stop PM2.5']
        : ['Use certified N95/FFP2 respirators', 'Ensure snug seal over nose & chin'],
    },
    {
      id: 'rec-ventilation',
      category: 'ventilation',
      title: 'Indoor Air & Ventilation',
      description: isGood
        ? 'Open windows freely to ventilate and replenish fresh indoor air.'
        : isModerate
        ? 'Natural ventilation is acceptable; close windows facing congested roadways.'
        : 'Keep doors and windows sealed. Operate True HEPA filtration in closed living areas.',
      severity: isGood ? 'low' : isModerate ? 'moderate' : 'high',
      iconName: 'Wind',
      bullets: isGood
        ? ['Open windows for cross-ventilation', 'Fresh ambient air flow']
        : isModerate
        ? ['Ventilate during low-traffic hours', 'Keep air purifier on auto mode']
        : ['Keep windows closed during rush hours', 'Run True HEPA air purifiers'],
    },
    {
      id: 'rec-vulnerable',
      category: 'vulnerable',
      title: 'Children & Older Adults',
      description: isGood
        ? 'Children and seniors can enjoy normal outdoor activities without restrictions.'
        : isModerate
        ? 'Normal outdoor playtime is safe; encourage regular hydration breaks.'
        : 'Restrict strenuous outdoor play for children. Seniors should stay in filtered indoor spaces.',
      severity: isGood ? 'low' : isModerate ? 'moderate' : 'high',
      iconName: 'Heart',
      bullets: isGood
        ? ['Unrestricted school playground sports', 'Normal senior walking routines']
        : isModerate
        ? ['Encourage hydration breaks', 'Monitor children with allergies']
        : ['Curtail intense outdoor school sports', 'Older adults should remain indoors'],
    },
  ];
}
