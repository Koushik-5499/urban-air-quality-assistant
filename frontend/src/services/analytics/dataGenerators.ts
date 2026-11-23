import { DASHBOARD_DATA } from '../../data/dashboardData';
import type {
  AnalyticsTimeRange,
  ForecastHorizon,
  HistoricalDataPoint,
  ForecastDataPoint,
  ForecastReport,
} from '../../types/analytics';
import { getAQICategory } from './metricsCalculator';

/**
 * Deterministic pseudo-random multiplier function based on cityId and index seed.
 * Produces smooth, natural, reproducible variations between 0.75 and 1.28.
 */
export function getDeterministicFactor(cityId: string, index: number, seedOffset = 0): number {
  let hash = 0;
  for (let i = 0; i < cityId.length; i++) {
    hash = (hash << 5) - hash + cityId.charCodeAt(i);
    hash |= 0;
  }
  const x = Math.sin(Math.abs(hash) + index * 1.618 + seedOffset) * 10000;
  const raw = x - Math.floor(x); // 0 to 1
  return 0.75 + raw * 0.50; // 0.75 to 1.25
}

/**
 * Generates reproducible historical sample series anchored to the city's actual simulated reading.
 */
export function generateHistoricalData(
  cityId: string,
  timeRange: AnalyticsTimeRange
): HistoricalDataPoint[] {
  const city = DASHBOARD_DATA[cityId] || DASHBOARD_DATA['coimbatore'];
  const baseAQI = city.aqi;

  const pm25Base = city.pollutants.find((p) => p.id === 'pm25')?.value ?? 28;
  const pm10Base = city.pollutants.find((p) => p.id === 'pm10')?.value ?? 55;
  const coBase = city.pollutants.find((p) => p.id === 'co')?.value ?? 0.8;
  const no2Base = city.pollutants.find((p) => p.id === 'no2')?.value ?? 32;
  const so2Base = city.pollutants.find((p) => p.id === 'so2')?.value ?? 14;
  const o3Base = city.pollutants.find((p) => p.id === 'o3')?.value ?? 38;

  let intervals: { time: string; fullDate: string; diurnalModifier: number }[] = [];

  if (timeRange === '24h') {
    const hours = [
      '00:00', '02:00', '04:00', '06:00', '08:00', '10:00',
      '12:00', '14:00', '16:00', '18:00', '20:00', '22:00',
    ];
    const diurnals = [0.85, 0.80, 0.78, 0.95, 1.22, 1.15, 1.05, 0.98, 1.10, 1.28, 1.18, 1.02];
    intervals = hours.map((h, i) => ({
      time: h,
      fullDate: `Today at ${h} hrs`,
      diurnalModifier: diurnals[i],
    }));
  } else if (timeRange === '7d') {
    const days = ['Day -6', 'Day -5', 'Day -4', 'Day -3', 'Day -2', 'Yesterday', 'Today'];
    const diurnals = [0.92, 1.05, 1.12, 0.98, 1.02, 1.18, 1.0];
    intervals = days.map((d, i) => ({
      time: d,
      fullDate: `Sample Window: ${d}`,
      diurnalModifier: diurnals[i],
    }));
  } else if (timeRange === '30d') {
    intervals = Array.from({ length: 15 }, (_, i) => {
      const dayNum = (i + 1) * 2;
      return {
        time: `Day ${dayNum}`,
        fullDate: `30-Day Series: Day ${dayNum}`,
        diurnalModifier: 0.90 + Math.sin(i * 0.7) * 0.22,
      };
    });
  } else {
    intervals = Array.from({ length: 12 }, (_, i) => {
      const weekNum = i + 1;
      return {
        time: `Wk ${weekNum}`,
        fullDate: `Quarterly Series: Week ${weekNum}`,
        diurnalModifier: 0.88 + Math.cos(i * 0.55) * 0.24,
      };
    });
  }

  return intervals.map((interval, idx) => {
    const factor = getDeterministicFactor(cityId, idx, 42);
    const combinedFactor = 0.5 * interval.diurnalModifier + 0.5 * factor;

    const rawAQI = Math.round(baseAQI * combinedFactor);
    const aqi = Math.max(15, Math.min(495, rawAQI));
    const category = getAQICategory(aqi);

    const o3Factor = timeRange === '24h' && (idx >= 5 && idx <= 8) ? 1.35 : 0.95;

    const pm25 = Number((pm25Base * combinedFactor).toFixed(1));
    const pm10 = Number((pm10Base * combinedFactor).toFixed(1));
    const co = Number((coBase * (0.85 + combinedFactor * 0.15)).toFixed(2));
    const no2 = Number((no2Base * combinedFactor).toFixed(1));
    const so2 = Number((so2Base * (0.9 + (idx % 3) * 0.1)).toFixed(1));
    const o3 = Number((o3Base * combinedFactor * o3Factor).toFixed(1));

    const ratios = [
      { id: 'PM2.5', ratio: pm25 / 60 },
      { id: 'PM10', ratio: pm10 / 100 },
      { id: 'NO2', ratio: no2 / 80 },
      { id: 'SO2', ratio: so2 / 80 },
      { id: 'O3', ratio: o3 / 100 },
      { id: 'CO', ratio: co / 2.0 },
    ];
    ratios.sort((a, b) => b.ratio - a.ratio);
    const dominantPollutant = ratios[0].id;

    return {
      time: interval.time,
      fullDate: interval.fullDate,
      timestamp: idx,
      aqi,
      category,
      pm25,
      pm10,
      co,
      no2,
      so2,
      o3,
      dominantPollutant,
    };
  });
}

/**
 * Generates deterministic short-term simulated forecasts with uncertainty bands.
 */
export function generateSimulatedForecast(
  cityId: string,
  horizon: ForecastHorizon
): ForecastReport {
  const city = DASHBOARD_DATA[cityId] || DASHBOARD_DATA['coimbatore'];
  const baseAQI = city.aqi;

  let intervals: { time: string; label: string; trendCurve: number; uncertainty: number }[] = [];

  if (horizon === '6h') {
    intervals = [
      { time: '+1h', label: 'In 1 Hour', trendCurve: 1.02, uncertainty: 8 },
      { time: '+2h', label: 'In 2 Hours', trendCurve: 1.05, uncertainty: 12 },
      { time: '+3h', label: 'In 3 Hours', trendCurve: 1.03, uncertainty: 15 },
      { time: '+4h', label: 'In 4 Hours', trendCurve: 0.98, uncertainty: 18 },
      { time: '+5h', label: 'In 5 Hours', trendCurve: 0.94, uncertainty: 22 },
      { time: '+6h', label: 'In 6 Hours', trendCurve: 0.92, uncertainty: 25 },
    ];
  } else if (horizon === '12h') {
    intervals = [
      { time: '+2h', label: 'In 2 Hours', trendCurve: 1.04, uncertainty: 12 },
      { time: '+4h', label: 'In 4 Hours', trendCurve: 1.07, uncertainty: 18 },
      { time: '+6h', label: 'In 6 Hours', trendCurve: 0.98, uncertainty: 24 },
      { time: '+8h', label: 'In 8 Hours', trendCurve: 0.93, uncertainty: 28 },
      { time: '+10h', label: 'In 10 Hours', trendCurve: 1.02, uncertainty: 32 },
      { time: '+12h', label: 'In 12 Hours', trendCurve: 1.06, uncertainty: 36 },
    ];
  } else if (horizon === '24h') {
    intervals = [
      { time: '+3h', label: 'Afternoon (+3h)', trendCurve: 1.05, uncertainty: 15 },
      { time: '+6h', label: 'Late Afternoon (+6h)', trendCurve: 1.09, uncertainty: 22 },
      { time: '+9h', label: 'Evening Peak (+9h)', trendCurve: 1.15, uncertainty: 28 },
      { time: '+12h', label: 'Midnight (+12h)', trendCurve: 1.04, uncertainty: 34 },
      { time: '+15h', label: 'Dawn (+15h)', trendCurve: 0.96, uncertainty: 38 },
      { time: '+18h', label: 'Morning Commute (+18h)', trendCurve: 1.12, uncertainty: 42 },
      { time: '+21h', label: 'Mid-Morning (+21h)', trendCurve: 1.06, uncertainty: 45 },
      { time: '+24h', label: 'Tomorrow Noon (+24h)', trendCurve: 0.98, uncertainty: 48 },
    ];
  } else {
    intervals = [
      { time: 'Day 1 AM', label: 'Tomorrow Morning', trendCurve: 1.08, uncertainty: 30 },
      { time: 'Day 1 PM', label: 'Tomorrow Afternoon', trendCurve: 0.96, uncertainty: 38 },
      { time: 'Day 2 AM', label: 'Day 2 Morning', trendCurve: 1.14, uncertainty: 46 },
      { time: 'Day 2 PM', label: 'Day 2 Afternoon', trendCurve: 1.02, uncertainty: 54 },
      { time: 'Day 3 AM', label: 'Day 3 Morning', trendCurve: 1.07, uncertainty: 60 },
      { time: 'Day 3 PM', label: 'Day 3 Afternoon', trendCurve: 0.94, uncertainty: 65 },
    ];
  }

  const dataPoints: ForecastDataPoint[] = intervals.map((interval, idx) => {
    const citySeedModifier = 1 + (getDeterministicFactor(cityId, idx, 99) - 1) * 0.15;
    const predictedAQI = Math.round(
      Math.max(15, Math.min(480, baseAQI * interval.trendCurve * citySeedModifier))
    );
    const predictedCategory = getAQICategory(predictedAQI);
    const lower = Math.max(10, predictedAQI - interval.uncertainty);
    const upper = Math.min(500, predictedAQI + interval.uncertainty);

    const pm25Estimate = Number((predictedAQI * 0.38).toFixed(1));
    const pm10Estimate = Number((predictedAQI * 0.72).toFixed(1));

    return {
      time: interval.time,
      label: interval.label,
      timestamp: idx,
      predictedAQI,
      predictedCategory,
      confidenceLower: lower,
      confidenceUpper: upper,
      pm25Estimate,
      pm10Estimate,
    };
  });

  const sumAqi = dataPoints.reduce((acc, p) => acc + p.predictedAQI, 0);
  const averagePredictedAQI = Math.round(sumAqi / dataPoints.length);
  const peakPredictedAQI = Math.max(...dataPoints.map((p) => p.predictedAQI));
  const overallCategory = getAQICategory(averagePredictedAQI);

  const delta = dataPoints[dataPoints.length - 1].predictedAQI - baseAQI;
  let direction: 'improving' | 'worsening' | 'stable' = 'stable';
  if (delta > 5) direction = 'worsening';
  else if (delta < -5) direction = 'improving';

  const peakCat = getAQICategory(peakPredictedAQI);
  let precautions: string[] = [];

  switch (peakCat) {
    case 'Good':
      precautions = [
        'Conditions are projected to remain favorable for all outdoor sports and physical recreation.',
        'Natural home ventilation and open windows are recommended throughout this horizon.',
      ];
      break;
    case 'Moderate':
      precautions = [
        'Air quality is generally acceptable; unusually sensitive individuals should observe mild symptoms.',
        'Plan intense workouts during early morning or post-rain periods for optimal clean air.',
      ];
      break;
    case 'Unhealthy for Sensitive Groups':
      precautions = [
        'Sensitive groups (children, elderly, asthmatics) should limit extended outdoor exertion.',
        'Run indoor air purifiers with HEPA filtration if sensitive family members are present.',
        'Keep vehicle windows closed when driving along dense transit corridors during peak hours.',
      ];
      break;
    case 'Unhealthy':
      precautions = [
        'Everyone may begin to experience health effects; sensitive groups should avoid outdoor activities.',
        'Wear certified N95 / FFP2 respirators if outdoor transit is unavoidable.',
        'Seal doors and windows; maintain continuous indoor air filtration.',
      ];
      break;
    case 'Very Unhealthy':
    case 'Hazardous':
      precautions = [
        'Health alert: serious risk of respiratory symptoms across the general public.',
        'Avoid all non-essential outdoor physical activity.',
        'Maintain sealed indoor clean-air refuges with certified HEPA filtration.',
      ];
      break;
  }

  const horizonNameMap: Record<ForecastHorizon, string> = {
    '6h': 'next 6 hours',
    '12h': 'next 12 hours',
    '24h': 'next 24 hours',
    '3d': 'next 3 days',
  };

  const summary = `Simulated projections for ${city.location.city} over the ${horizonNameMap[horizon]} indicate an average AQI of ${averagePredictedAQI} (${overallCategory}), with peak expected concentration reaching ${peakPredictedAQI}. The anticipated general trajectory is ${direction}.`;

  const minConf = Math.min(...dataPoints.map((p) => p.confidenceLower));
  const maxConf = Math.max(...dataPoints.map((p) => p.confidenceUpper));

  return {
    horizon,
    dataPoints,
    overallCategory,
    direction,
    summary,
    precautions,
    averagePredictedAQI,
    peakPredictedAQI,
    confidenceRangeText: `Estimated confidence interval: ${minConf} – ${maxConf} AQI`,
  };
}

