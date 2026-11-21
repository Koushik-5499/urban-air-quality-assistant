import { describe, it, expect } from 'vitest';
import { generateAssistantResponse, SUGGESTED_QUESTIONS } from '../services/assistantEngine';
import { DASHBOARD_DATA } from '../data/dashboardData';

describe('AI Assistant Simulated Health Engine', () => {
  const coimbatore = DASHBOARD_DATA['coimbatore'];
  const delhi = DASHBOARD_DATA['delhi'];

  it('includes pre-configured suggested questions', () => {
    expect(SUGGESTED_QUESTIONS.length).toBeGreaterThanOrEqual(4);
    expect(SUGGESTED_QUESTIONS[1].question).toContain('Is it safe');
    expect(SUGGESTED_QUESTIONS[0].id).toBeDefined();
  });

  it('generates context-aware responses incorporating active city data', () => {
    const responseCoimbatore = generateAssistantResponse('How is the air quality today?', coimbatore);
    expect(responseCoimbatore).toContain('Coimbatore');
    expect(responseCoimbatore).toContain(String(coimbatore.aqi));

    const responseDelhi = generateAssistantResponse('How is the air quality today?', delhi);
    expect(responseDelhi).toContain('Delhi');
    expect(responseDelhi).toContain(String(delhi.aqi));
  });

  it('provides safety precautions for outdoor exercise', () => {
    const response = generateAssistantResponse('Can I go for a run right now?', coimbatore);
    expect(response.toLowerCase()).toMatch(/outdoor|exercise|running|run/);
  });

  it('answers queries about specific pollutants (PM2.5, Ozone, etc.)', () => {
    const pmResponse = generateAssistantResponse('Tell me about PM2.5 levels', coimbatore);
    expect(pmResponse).toContain('PM2.5');

    const o3Response = generateAssistantResponse('What about ozone exposure?', coimbatore);
    expect(o3Response.toLowerCase()).toContain('ozone');
  });

  it('provides safe fallback response for general queries', () => {
    const fallbackResponse = generateAssistantResponse('What is quantum computing?', coimbatore);
    expect(fallbackResponse).toContain('Air Quality');
    expect(fallbackResponse).toContain(coimbatore.location.city);
  });
});
