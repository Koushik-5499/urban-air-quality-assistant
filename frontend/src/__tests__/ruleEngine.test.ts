import { describe, it, expect } from 'vitest';
import {
  generateAssistantResponse,
  getHealthRecommendationsForCity,
} from '../services/assistant/ruleEngine';
import { getHealthRecommendations } from '../utils/healthRecommendations';
import { DASHBOARD_DATA } from '../data/dashboardData';
import type { AQICategory, CityDashboardData } from '../types/dashboard';

function makeCityWithAqi(aqi: number, category: AQICategory): CityDashboardData {
  const base = DASHBOARD_DATA['delhi'];
  return {
    ...base,
    aqi,
    category,
  };
}

describe('Rule Engine Exhaustive Topic & AQI Coverage', () => {
  const goodCity = makeCityWithAqi(35, 'Good');
  const modCity = makeCityWithAqi(82, 'Moderate');
  const sensitiveCity = makeCityWithAqi(135, 'Unhealthy for Sensitive Groups');
  const unhealthyCity = makeCityWithAqi(180, 'Unhealthy');
  const hazardousCity = makeCityWithAqi(340, 'Hazardous');

  it('handles aqi_meaning across all 5 AQI tiers', () => {
    expect(generateAssistantResponse('what does today aqi score mean', goodCity)).toContain('satisfactory');
    expect(generateAssistantResponse('what does today aqi score mean', modCity)).toContain('acceptable');
    expect(generateAssistantResponse('what does today aqi score mean', sensitiveCity)).toContain('sensitive groups');
    expect(generateAssistantResponse('what does today aqi score mean', unhealthyCity)).toContain('serious health effects');
    expect(generateAssistantResponse('what does today aqi score mean', hazardousCity)).toContain('Health alert');
  });

  it('handles safe_outside across Good, Moderate, and High AQI tiers', () => {
    expect(generateAssistantResponse('is it safe outside today', goodCity)).toContain('favorable and safe');
    expect(generateAssistantResponse('is it safe outside today', modCity)).toContain('generally safe');
    expect(generateAssistantResponse('is it safe outside today', unhealthyCity)).toContain('Caution is recommended');
  });

  it('handles exercise queries across Good, Moderate, and High AQI tiers', () => {
    expect(generateAssistantResponse('can I exercise outdoors', goodCity)).toContain('fully recommended');
    expect(generateAssistantResponse('can I exercise outdoors', modCity)).toContain('moderately safe');
    expect(generateAssistantResponse('can I exercise outdoors', unhealthyCity)).toContain('not recommended');
  });

  it('covers all 6 criteria pollutant topics', () => {
    expect(generateAssistantResponse('explain pm2.5 health risk', unhealthyCity)).toContain('Fine Particulate Matter');
    expect(generateAssistantResponse('what is pm10 dust', unhealthyCity)).toContain('Respirable Coarse Particles');
    expect(generateAssistantResponse('carbon monoxide co effects', unhealthyCity)).toContain('Carbon Monoxide');
    expect(generateAssistantResponse('nitrogen dioxide no2 sources', unhealthyCity)).toContain('Nitrogen Dioxide');
    expect(generateAssistantResponse('sulfur dioxide so2 levels', unhealthyCity)).toContain('Sulfur Dioxide');
    expect(generateAssistantResponse('ground level ozone o3 warning', unhealthyCity)).toContain('Ground-Level Ozone');
  });

  it('covers Challenge 6 topics: winter smog, impact, routines, indoor hacks, sustainable alternatives', () => {
    expect(generateAssistantResponse('winter smog thermal inversion protocol', unhealthyCity)).toContain('nocturnal radiation inversion');
    expect(generateAssistantResponse('quantified impact of choices co2', unhealthyCity)).toContain('Direct Quantified Impact');
    expect(generateAssistantResponse('low-emission commute routine metro', unhealthyCity)).toContain('Smart Departure Scheduling');
    expect(generateAssistantResponse('indoor air quality hacks ventilation', unhealthyCity)).toContain('Corsi-Rosenthal');
    expect(generateAssistantResponse('sustainable heating alternatives biomass', unhealthyCity)).toContain('Clean Space Heating');
  });

  it('covers personal protection and vulnerable demographic cohorts', () => {
    expect(generateAssistantResponse('which n95 mask or hepa purifier protection', unhealthyCity)).toContain('True HEPA filters');
    expect(generateAssistantResponse('precautions for children at school', goodCity)).toContain('acceptable today');
    expect(generateAssistantResponse('precautions for children at school', unhealthyCity)).toContain('Restrict vigorous outdoor');
    expect(generateAssistantResponse('advice for elderly seniors heart', unhealthyCity)).toContain('Older adults');
    expect(generateAssistantResponse('advice for pregnant women pregnancy', unhealthyCity)).toContain('Pregnant Women');
    expect(generateAssistantResponse('asthma copd breathing trigger', unhealthyCity)).toContain('Asthma Action Plan');
  });

  it('returns general fallback with educational disclaimer for unknown prompts', () => {
    const out = generateAssistantResponse('random unrelated question', modCity);
    expect(out).toContain('analyzing the atmospheric telemetry');
    expect(out).toContain('Educational disclaimer');
  });

  it('generates contextual cards with getHealthRecommendationsForCity for Good, Moderate, and High AQI', () => {
    const goodCards = getHealthRecommendationsForCity(goodCity);
    expect(goodCards).toHaveLength(5);
    expect(goodCards[0].severity).toBe('low');

    const modCards = getHealthRecommendationsForCity(modCity);
    expect(modCards).toHaveLength(5);
    expect(modCards[0].severity).toBe('moderate');

    const highCards = getHealthRecommendationsForCity(unhealthyCity);
    expect(highCards).toHaveLength(5);
    expect(highCards[0].severity).toBe('high');
    expect(highCards[4].impactExplanation).toContain('52%');
  });
});

describe('HealthRecommendations utility covers all 6 NAQI categories', () => {
  const categories: AQICategory[] = [
    'Good',
    'Moderate',
    'Unhealthy for Sensitive Groups',
    'Unhealthy',
    'Very Unhealthy',
    'Hazardous',
  ];

  it('returns populated general, sensitive, winter smog, routines, hacks, alternatives, and disclaimer per category', () => {
    categories.forEach((cat, idx) => {
      const advice = getHealthRecommendations(cat, (idx + 1) * 50);
      expect(advice.general.length).toBeGreaterThan(10);
      expect(advice.sensitiveGroups.length).toBeGreaterThan(10);
      expect(advice.outdoorActivity.length).toBeGreaterThan(10);
      expect(advice.protectiveMeasures.length).toBeGreaterThanOrEqual(2);
      expect(advice.winterSmogAdvice?.length).toBeGreaterThan(10);
      expect(advice.lowEmissionRoutines?.length).toBeGreaterThanOrEqual(2);
      expect(advice.indoorAirHacks?.length).toBeGreaterThanOrEqual(2);
      expect(advice.sustainableAlternatives?.length).toBeGreaterThanOrEqual(1);
      expect(advice.impactExplanation?.length).toBeGreaterThan(10);
      expect(advice.disclaimer).toContain('Not intended as clinical');
    });
  });
});

