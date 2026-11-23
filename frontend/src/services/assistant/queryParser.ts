import type { SuggestedQuestion } from '../../types/assistant';

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
    id: 'sq-winter',
    question: 'How can our family navigate severe winter smog and protect children from inversion layers?',
    category: 'Winter Smog',
  },
  {
    id: 'sq-routine',
    question: 'What low-emission daily routines and commute times cut our pollution exposure?',
    category: 'Low-Emission Routines',
  },
  {
    id: 'sq-indoor',
    question: 'What are practical indoor air quality hacks and DIY air filtration tips for our home?',
    category: 'Indoor Hacks',
  },
  {
    id: 'sq-sustain',
    question: 'What sustainable heating and clean transport alternatives can our community adopt?',
    category: 'Sustainable Alternatives',
  },
  {
    id: 'sq-impact',
    question: 'What is the direct health and emission impact of switching our commute to public transit?',
    category: 'Direct Impact',
  },
  {
    id: 'sq-pregnant',
    question: 'What specific precautions should pregnant women, infants, and seniors follow today?',
    category: 'Vulnerable Groups',
  },
  {
    id: 'sq-5',
    question: 'What indoor precautions should I take during Very Unhealthy air quality?',
    category: 'Protection',
  },
];

export type AssistantTopic =
  | 'aqi_meaning'
  | 'safe_outside'
  | 'exercise'
  | 'pm25'
  | 'pm10'
  | 'co'
  | 'no2'
  | 'so2'
  | 'o3'
  | 'winter_smog'
  | 'quantified_impact'
  | 'low_emission_routines'
  | 'indoor_hacks'
  | 'sustainable_alternatives'
  | 'protection'
  | 'children'
  | 'elderly'
  | 'pregnant'
  | 'asthma'
  | 'general_fallback';

export function detectQueryTopic(query: string): AssistantTopic {
  const q = query.toLowerCase().trim();

  if (
    q.includes("today's aqi") ||
    q.includes('what does aqi mean') ||
    q.includes('what does today') ||
    q.includes('explain aqi') ||
    q.includes('current aqi') ||
    q.includes('air quality index mean')
  ) {
    return 'aqi_meaning';
  }

  if (
    q.includes('safe to go outside') ||
    q.includes('can i go outside') ||
    q.includes('safe outside') ||
    q.includes('outdoor activity') ||
    q.includes('walk outside')
  ) {
    return 'safe_outside';
  }

  if (
    q.includes('exercise') ||
    q.includes('running') ||
    q.includes('jogging') ||
    q.includes('cycling') ||
    q.includes('workout') ||
    q.includes('gym')
  ) {
    return 'exercise';
  }

  if (
    q.includes('pm2.5') ||
    q.includes('pm25') ||
    q.includes('fine particulate') ||
    q.includes('fine particles')
  ) {
    return 'pm25';
  }

  if (q.includes('pm10') || q.includes('coarse dust')) {
    return 'pm10';
  }

  if (q.includes('carbon monoxide') || q.includes('co ') || q.endsWith('co')) {
    return 'co';
  }

  if (q.includes('nitrogen dioxide') || q.includes('no2')) {
    return 'no2';
  }

  if (q.includes('sulfur dioxide') || q.includes('so2')) {
    return 'so2';
  }

  if (q.includes('ozone') || q.includes('o3')) {
    return 'o3';
  }

  if (
    q.includes('winter') ||
    q.includes('smog') ||
    q.includes('inversion') ||
    q.includes('fog') ||
    q.includes('cold air')
  ) {
    return 'winter_smog';
  }

  if (
    q.includes('impact') ||
    q.includes('choice') ||
    q.includes('quantif') ||
    q.includes('reduction') ||
    q.includes('how much') ||
    q.includes('benefit')
  ) {
    return 'quantified_impact';
  }

  if (
    q.includes('low-emission') ||
    q.includes('routine') ||
    q.includes('commute') ||
    q.includes('traffic') ||
    q.includes('transit') ||
    q.includes('carpool') ||
    q.includes('metro')
  ) {
    return 'low_emission_routines';
  }

  if (
    q.includes('indoor hack') ||
    q.includes('hacks') ||
    q.includes('diy') ||
    q.includes('corsi') ||
    q.includes('rosenthal') ||
    q.includes('ventilation timing') ||
    q.includes('plants') ||
    q.includes('plant') ||
    q.includes('dusting') ||
    q.includes('mopping')
  ) {
    return 'indoor_hacks';
  }

  if (
    q.includes('sustainable') ||
    q.includes('alternatives') ||
    q.includes('heating') ||
    q.includes('burning') ||
    q.includes('solar') ||
    q.includes('community action')
  ) {
    return 'sustainable_alternatives';
  }

  if (
    q.includes('protect myself') ||
    q.includes('how to protect') ||
    q.includes('mask') ||
    q.includes('purifier') ||
    q.includes('hepa') ||
    q.includes('protection')
  ) {
    return 'protection';
  }

  if (
    q.includes('children') ||
    q.includes('kids') ||
    q.includes('school') ||
    q.includes('infants') ||
    q.includes('babies')
  ) {
    return 'children';
  }

  if (
    q.includes('pregnant') ||
    q.includes('pregnancy') ||
    q.includes('expecting') ||
    q.includes('maternal')
  ) {
    return 'pregnant';
  }

  if (
    q.includes('elderly') ||
    q.includes('seniors') ||
    q.includes('older adults') ||
    q.includes('heart') ||
    q.includes('cardiovascular')
  ) {
    return 'elderly';
  }

  if (
    q.includes('asthma') ||
    q.includes('copd') ||
    q.includes('respiratory') ||
    q.includes('bronchitis') ||
    q.includes('inhaler')
  ) {
    return 'asthma';
  }

  return 'general_fallback';
}

