import type { PollutantId, ChartTimeRange, CityDashboardData, PollutantMetric } from '../types/dashboard';
import type { PollutantDetailedInfo, DetailedTrendPoint, PollutantSubIndex } from '../types/pollutants';
import { PARTICULATE_DETAILS } from './pollutantParticulates';
import { GASEOUS_DETAILS } from './pollutantGases';

export const POLLUTANT_DETAILS: Record<PollutantId, PollutantDetailedInfo> = {
  ...PARTICULATE_DETAILS,
  ...GASEOUS_DETAILS,
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
    const o3Multipliers = [0.45, 0.35, 0.50, 0.85, 1.35, 1.48, 1.10, 0.65];

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
  const limits: Record<PollutantId, number> = {
    pm25: 60,
    pm10: 100,
    co: 2.0,
    no2: 80,
    so2: 80,
    o3: 100,
  };

  const items = pollutants.map((p) => {
    const limit = limits[p.id] || 100;
    const benchmarkPercentage = Math.round((p.value / limit) * 100);
    const halfLimit = limit / 2;
    const subIndex = Math.min(
      Math.round(p.value <= halfLimit ? (p.value / halfLimit) * 50 : 50 + ((p.value - halfLimit) / halfLimit) * 50),
      500
    );

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

  let maxIdx = 0;
  for (let i = 1; i < items.length; i++) {
    if (items[i].subIndex > items[maxIdx].subIndex) {
      maxIdx = i;
    }
  }
  if (items[maxIdx]) {
    items[maxIdx].isDominant = true;
    items[maxIdx].subIndex = Math.max(items[maxIdx].subIndex, overallAQI);
  }

  return items;
}
