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
        disclaimer:
          'Educational environmental guidance based on simulated sensor readings. Not intended as clinical medical diagnosis.',
      };
  }
}

