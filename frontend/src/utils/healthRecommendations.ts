import type { AQICategory, HealthAdvice } from '../types/dashboard';

export function getHealthRecommendations(category: AQICategory, aqi: number): HealthAdvice {
  switch (category) {
    case 'Good':
      return {
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
        lowEmissionRoutines: [
          'Take advantage of clean air to walk, cycle, or use micromobility for local urban errands',
          'Coordinate community carpooling to maintain baseline clean ambient levels',
        ],
        indoorAirHacks: [
          'Freely open windows and cross-ventilate living spaces to replenish indoor air freshness',
          'Place indoor plants (Snake plant, Areca palm) in living areas for natural VOC absorption',
        ],
        sustainableAlternatives: [
          'Adopt solar rooftop charging and electric 2-wheelers for zero-emission neighborhood transport',
        ],
        impactExplanation: 'Active walking and cycling save ~160g CO2 per kilometer compared to private petrol car use.',
        disclaimer:
          'Educational environmental guidance based on simulated sensor readings. Not intended as clinical medical diagnosis.',
      };

    case 'Moderate':
      return {
        general:
          'Air quality is acceptable for most people. An AQI of ' +
          aqi +
          ' indicates low to moderate ambient particulate exposure in urban corridors.',
        sensitiveGroups:
          'Unusually sensitive individuals or individuals with severe asthma should monitor symptoms if spending extended hours outdoors.',
        outdoorActivity: 'Generally safe for outdoor sports; consider breaks during peak traffic hours.',
        protectiveMeasures: [
          'Ventilate rooms during early morning or late evening when traffic is lower',
          'Sensitive groups should carry rescue inhalers if prone to airway irritation',
          'Keep windows closed during peak industrial transit periods',
        ],
        winterSmogAdvice: 'Mild evening haze can develop; sensitive family members should conclude workouts before dusk.',
        lowEmissionRoutines: [
          'Reschedule commute departures away from peak congestion hours (e.g. before 8 AM or after 10 AM)',
          'Shift daily office commutes to electrified metro rail or express buses',
        ],
        indoorAirHacks: [
          'Practice wet mopping instead of dry brooming to prevent resuspending coarse dust particles',
          'Open windows during sunny midday hours (12:30 PM - 3:30 PM) for optimal natural ventilation',
        ],
        sustainableAlternatives: [
          'Avoid idling vehicle engines at traffic intersections or school drop-off zones',
        ],
        impactExplanation: 'Off-peak commuting cuts stop-and-go in-cabin toxic gas inhalation by up to 35%.',
        disclaimer:
          'Educational environmental guidance based on simulated sensor readings. Not intended as clinical medical diagnosis.',
      };

    case 'Unhealthy for Sensitive Groups':
      return {
        general:
          'General public is less likely to be affected, but sensitive individuals may experience throat irritation or shortness of breath.',
        sensitiveGroups:
          'Children, older adults, and individuals with heart or lung disease should reduce prolonged or heavy outdoor exertion.',
        outdoorActivity: 'Moderate intensity outdoor activities are suggested; take more frequent breaks.',
        protectiveMeasures: [
          'Sensitive individuals should wear well-fitting particulate masks (e.g. N95) outdoors',
          'Use indoor air purifiers with HEPA filtration if available',
          'Avoid exercising near congested highways and industrial nodes',
        ],
        winterSmogAdvice: 'Thermal inversion layers begin concentrating particulate matter near surface breathing levels during mornings.',
        lowEmissionRoutines: [
          'Shift outdoor runs and cardio to midday (1 PM - 4 PM) when solar warmth disperses surface smog',
          'Organize school carpools or take organized electric school buses to curtail drop-off congestion',
        ],
        indoorAirHacks: [
          'Keep windows firmly closed during morning and evening rush-hour pollution spikes',
          'Run DIY Corsi-Rosenthal boxes or true HEPA air cleaners in bedrooms for 8 hours of clean night air',
        ],
        sustainableAlternatives: [
          'Report neighborhood garbage or leaf fires via municipal grievance apps rather than letting smoke linger',
        ],
        impactExplanation: 'Shifting workouts to midday reduces inhaled particulate dose by 45–55% compared to dawn runs.',
        disclaimer:
          'Educational environmental guidance based on simulated sensor readings. Not intended as clinical medical diagnosis.',
      };

    case 'Unhealthy':
      return {
        general:
          'Everyone may begin to experience health effects such as eye irritation or coughing. Sensitive groups may experience more serious symptoms.',
        sensitiveGroups:
          'People with asthma, COPD, or heart disease should avoid outdoor exertion and remain in filtered indoor spaces.',
        outdoorActivity: 'Avoid strenuous outdoor activities; relocate workouts indoors.',
        protectiveMeasures: [
          'Wear N95/FFP2 protective masks when venturing outside',
          'Seal windows and utilize recirculating air conditioning',
          'Run indoor air purifiers in frequently occupied rooms',
        ],
        winterSmogAdvice: 'Winter thermal inversion traps vehicle exhaust and biomass smoke at surface levels; keep children indoors during early mornings.',
        lowEmissionRoutines: [
          'Take electrified metro transit for all urban movement to avoid toxic roadway micro-plumes',
          'Transition fitness workouts entirely to indoor HEPA-filtered fitness studios or home gyms',
        ],
        indoorAirHacks: [
          'Strictly seal window sills with draft stoppers; operate HEPA purifiers continuously in living areas',
          'Always use kitchen range hoods on maximum power during cooking and avoid dry sweeping',
        ],
        sustainableAlternatives: [
          'Use clean electric radiant space heaters instead of unvented solid-fuel/wood fires',
        ],
        impactExplanation: 'Wearing a sealed N95 respirator cuts personal PM2.5 inhalation by up to 95%.',
        disclaimer:
          'Educational environmental guidance based on simulated sensor readings. Not intended as clinical medical diagnosis.',
      };

    case 'Very Unhealthy':
    case 'Hazardous':
    default:
      return {
        general:
          'Health alert: Atmospheric pollution poses emergency health risks for all urban inhabitants.',
        sensitiveGroups:
          'All individuals must remain indoors. Vulnerable demographics should stay under close medical observation if symptoms emerge.',
        outdoorActivity: 'Prohibit all non-essential outdoor travel and activities.',
        protectiveMeasures: [
          'Strict indoor shelter with closed windows and HEPA filtration',
          'High-grade respirators required if mandatory outdoor transit is necessary',
          'Consult emergency health lines if experiencing severe respiratory distress',
        ],
        winterSmogAdvice: 'Severe winter smog emergency with stagnant ground inversion. Suspend all outdoor morning assemblies and physical education classes.',
        lowEmissionRoutines: [
          'Transition to remote work and virtual school to eliminate vehicular emissions during emergency stagnation',
          'Avoid all non-emergency vehicle trips; utilize zero-emission delivery when possible',
        ],
        indoorAirHacks: [
          'Deploy DIY Corsi-Rosenthal air cleaner boxes with MERV-13 filters to maintain safe indoor PM2.5 (<35 µg/m³)',
          'Strict wet mopping protocol; seal door bases with damp towels or silicone draft blockers',
        ],
        sustainableAlternatives: [
          'Mandate zero open fires in community compounds; provide electric space heating to security staff',
        ],
        impactExplanation: 'Indoor containment with DIY HEPA filtration prevents up to 85% of hazardous particulate exposure.',
        disclaimer:
          'Educational environmental guidance based on simulated sensor readings. Not intended as clinical medical diagnosis.',
      };
  }
}

