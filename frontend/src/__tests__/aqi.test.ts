import { describe, it, expect } from 'vitest';
import { getAQICategory, getAQICategoryColor } from '../services/analyticsService';
import { getAQIBadgeVariant } from '../data/mapData';

describe('AQI Category Breakpoints & Scales', () => {
  it('correctly maps values to the 6 EPA/CPCB AQI categories', () => {
    // 0 - 50: Good
    expect(getAQICategory(0)).toBe('Good');
    expect(getAQICategory(25)).toBe('Good');
    expect(getAQICategory(50)).toBe('Good');

    // 51 - 100: Moderate
    expect(getAQICategory(51)).toBe('Moderate');
    expect(getAQICategory(75)).toBe('Moderate');
    expect(getAQICategory(100)).toBe('Moderate');

    // 101 - 200: Unhealthy for Sensitive Groups
    expect(getAQICategory(101)).toBe('Unhealthy for Sensitive Groups');
    expect(getAQICategory(150)).toBe('Unhealthy for Sensitive Groups');
    expect(getAQICategory(200)).toBe('Unhealthy for Sensitive Groups');

    // 201 - 300: Unhealthy
    expect(getAQICategory(201)).toBe('Unhealthy');
    expect(getAQICategory(250)).toBe('Unhealthy');
    expect(getAQICategory(300)).toBe('Unhealthy');

    // 301 - 400: Very Unhealthy
    expect(getAQICategory(301)).toBe('Very Unhealthy');
    expect(getAQICategory(350)).toBe('Very Unhealthy');
    expect(getAQICategory(400)).toBe('Very Unhealthy');

    // 401+: Hazardous
    expect(getAQICategory(401)).toBe('Hazardous');
    expect(getAQICategory(500)).toBe('Hazardous');
  });

  it('provides distinct semantic colors for all AQI tiers', () => {
    const goodColor = getAQICategoryColor('Good');
    const moderateColor = getAQICategoryColor('Moderate');
    const sensitiveColor = getAQICategoryColor('Unhealthy for Sensitive Groups');
    const unhealthyColor = getAQICategoryColor('Unhealthy');
    const veryUnhealthyColor = getAQICategoryColor('Very Unhealthy');
    const hazardousColor = getAQICategoryColor('Hazardous');

    expect(goodColor).toMatch(/^#[0-9A-Fa-f]{6}$/);
    expect(moderateColor).toMatch(/^#[0-9A-Fa-f]{6}$/);
    expect(unhealthyColor).toMatch(/^#[0-9A-Fa-f]{6}$/);

    const colorSet = new Set([
      goodColor,
      moderateColor,
      sensitiveColor,
      unhealthyColor,
      veryUnhealthyColor,
      hazardousColor,
    ]);
    expect(colorSet.size).toBe(6);
  });

  it('maps categories to valid badge variants', () => {
    expect(getAQIBadgeVariant('Good')).toBe('success');
    expect(getAQIBadgeVariant('Moderate')).toBe('warning');
    expect(getAQIBadgeVariant('Unhealthy for Sensitive Groups')).toBe('danger');
    expect(getAQIBadgeVariant('Unhealthy')).toBe('danger');
    expect(getAQIBadgeVariant('Very Unhealthy')).toBe('danger');
    expect(getAQIBadgeVariant('Hazardous')).toBe('danger');
  });
});
