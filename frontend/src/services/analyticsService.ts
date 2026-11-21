import { DASHBOARD_DATA } from '../data/dashboardData';
import { POLLUTANT_DETAILS } from '../data/pollutantDetails';
import type { AQICategory, CityDashboardData, PollutantId } from '../types/dashboard';
import type {
  AnalyticsTimeRange,
  ForecastHorizon,
  HistoricalDataPoint,
  ForecastDataPoint,
  AnalyticsSummary,
  PollutantStats,
  AnalyticsInsightItem,
  ForecastReport,
  TrendDirection,
} from '../types/analytics';

export function getAQICategory(aqi: number): AQICategory {
  if (aqi <= 50) return 'Good';
  if (aqi <= 100) return 'Moderate';
  if (aqi <= 200) return 'Unhealthy for Sensitive Groups';
  if (aqi <= 300) return 'Unhealthy';
  if (aqi <= 400) return 'Very Unhealthy';
  return 'Hazardous';
}

export function getAQICategoryColor(cat: AQICategory): string {
  switch (cat) {
    case 'Good':
      return '#16A34A'; // emerald-600
    case 'Moderate':
      return '#EAB308'; // yellow-500
    case 'Unhealthy for Sensitive Groups':
      return '#F97316'; // orange-500
    case 'Unhealthy':
      return '#EF4444'; // red-500
    case 'Very Unhealthy':
      return '#A855F7'; // purple-500
    case 'Hazardous':
      return '#881337'; // rose-900
    default:
      return '#64748B';
  }
}

/**
 * Deterministic pseudo-random multiplier function based on cityId and index seed.
 * Produces smooth, natural, reproducible variations between 0.75 and 1.28.
 */
function getDeterministicFactor(cityId: string, index: number, seedOffset = 0): number {
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
    // 12 points (every 2 hours)
    const hours = [
      '00:00', '02:00', '04:00', '06:00', '08:00', '10:00',
      '12:00', '14:00', '16:00', '18:00', '20:00', '22:00',
    ];
    // Inversions early morning and rush hour evenings produce higher readings
    const diurnals = [0.85, 0.80, 0.78, 0.95, 1.22, 1.15, 1.05, 0.98, 1.10, 1.28, 1.18, 1.02];
    intervals = hours.map((h, i) => ({
      time: h,
      fullDate: `Today at ${h} hrs`,
      diurnalModifier: diurnals[i],
    }));
  } else if (timeRange === '7d') {
    // 7 points (past 7 days)
    const days = ['Day -6', 'Day -5', 'Day -4', 'Day -3', 'Day -2', 'Yesterday', 'Today'];
    const diurnals = [0.92, 1.05, 1.12, 0.98, 1.02, 1.18, 1.0];
    intervals = days.map((d, i) => ({
      time: d,
      fullDate: `Sample Window: ${d}`,
      diurnalModifier: diurnals[i],
    }));
  } else if (timeRange === '30d') {
    // 15 sample intervals (every 2 days)
    intervals = Array.from({ length: 15 }, (_, i) => {
      const dayNum = (i + 1) * 2;
      return {
        time: `Day ${dayNum}`,
        fullDate: `30-Day Series: Day ${dayNum}`,
        diurnalModifier: 0.90 + Math.sin(i * 0.7) * 0.22,
      };
    });
  } else {
    // 90d: 12 weekly intervals
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
    // Combine baseline with diurnal wave and deterministic perturbation
    const combinedFactor = 0.5 * interval.diurnalModifier + 0.5 * factor;

    // Calculate AQI
    const rawAQI = Math.round(baseAQI * combinedFactor);
    const aqi = Math.max(15, Math.min(495, rawAQI));
    const category = getAQICategory(aqi);

    // Ozone typically peaks in warm afternoons (index 5-7 in 24h)
    const o3Factor = timeRange === '24h' && (idx >= 5 && idx <= 8) ? 1.35 : 0.95;

    const pm25 = Number((pm25Base * combinedFactor).toFixed(1));
    const pm10 = Number((pm10Base * combinedFactor).toFixed(1));
    const co = Number((coBase * (0.85 + combinedFactor * 0.15)).toFixed(2));
    const no2 = Number((no2Base * combinedFactor).toFixed(1));
    const so2 = Number((so2Base * (0.9 + (idx % 3) * 0.1)).toFixed(1));
    const o3 = Number((o3Base * combinedFactor * o3Factor).toFixed(1));

    // Determine dominant pollutant dynamically based on benchmark ratios
    // PM2.5 benchmark = 60, PM10 = 100, NO2 = 80, SO2 = 80, O3 = 100, CO = 2.0
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
 * Calculates summary metrics across the selected historical series.
 */
export function calculateAnalyticsSummary(
  points: HistoricalDataPoint[],
  currentCityData: CityDashboardData
): AnalyticsSummary {
  if (points.length === 0) {
    return {
      currentAQI: currentCityData.aqi,
      currentCategory: currentCityData.category,
      historicalAverageAQI: currentCityData.aqi,
      averageCategory: currentCityData.category,
      highestAQI: currentCityData.aqi,
      highestAQITime: 'Current Reading',
      lowestAQI: currentCityData.aqi,
      lowestAQITime: 'Current Reading',
      trendDirection: 'stable',
      trendPercentageChange: 0,
      mostDominantPollutant: currentCityData.dominantPollutant,
      dominantPollutantFormula: 'PM₂.₅',
      dominantPollutantFrequency: 100,
    };
  }

  let totalAqi = 0;
  let highest = points[0];
  let lowest = points[0];
  const dominantCounts: Record<string, number> = {};

  for (const pt of points) {
    totalAqi += pt.aqi;
    if (pt.aqi > highest.aqi) highest = pt;
    if (pt.aqi < lowest.aqi) lowest = pt;

    dominantCounts[pt.dominantPollutant] = (dominantCounts[pt.dominantPollutant] || 0) + 1;
  }

  const averageAqi = Math.round(totalAqi / points.length);

  // Calculate trend direction by comparing first third of points vs last third
  const sliceSize = Math.max(1, Math.floor(points.length / 3));
  const firstSlice = points.slice(0, sliceSize);
  const lastSlice = points.slice(points.length - sliceSize);

  const avgFirst = firstSlice.reduce((acc, p) => acc + p.aqi, 0) / firstSlice.length;
  const avgLast = lastSlice.reduce((acc, p) => acc + p.aqi, 0) / lastSlice.length;

  const rawChange = avgLast - avgFirst;
  const trendPercentageChange = Number(((rawChange / (avgFirst || 1)) * 100).toFixed(1));

  let trendDirection: TrendDirection = 'stable';
  if (trendPercentageChange > 4.5) {
    trendDirection = 'worsening'; // AQI rose (dirtier)
  } else if (trendPercentageChange < -4.5) {
    trendDirection = 'improving'; // AQI declined (cleaner)
  }

  // Find most frequent dominant pollutant
  let topDominant = currentCityData.dominantPollutant;
  let maxCount = 0;
  for (const [pollutant, count] of Object.entries(dominantCounts)) {
    if (count > maxCount) {
      maxCount = count;
      topDominant = pollutant;
    }
  }

  const frequency = Math.round((maxCount / points.length) * 100);

  const formulaMap: Record<string, string> = {
    'PM2.5': 'PM₂.₅',
    PM10: 'PM₁₀',
    CO: 'CO',
    NO2: 'NO₂',
    SO2: 'SO₂',
    O3: 'O₃',
  };

  return {
    currentAQI: currentCityData.aqi,
    currentCategory: currentCityData.category,
    historicalAverageAQI: averageAqi,
    averageCategory: getAQICategory(averageAqi),
    highestAQI: highest.aqi,
    highestAQITime: highest.time,
    lowestAQI: lowest.aqi,
    lowestAQITime: lowest.time,
    trendDirection,
    trendPercentageChange,
    mostDominantPollutant: topDominant,
    dominantPollutantFormula: formulaMap[topDominant] || topDominant,
    dominantPollutantFrequency: frequency,
  };
}

/**
 * Calculates pollutant-specific historical statistics.
 */
export function calculatePollutantStats(
  points: HistoricalDataPoint[],
  pollutantId: PollutantId,
  currentCityData: CityDashboardData
): PollutantStats {
  const meta = POLLUTANT_DETAILS[pollutantId];
  const currentMetric = currentCityData.pollutants.find((p) => p.id === pollutantId);
  const current = currentMetric?.value ?? 0;

  if (points.length === 0) {
    return {
      pollutantId,
      name: meta.name,
      formula: meta.formula,
      current,
      average: current,
      min: current,
      max: current,
      unit: meta.unit,
      trendDirection: 'stable',
      changePercentage: 0,
      whoLimit: meta.whoLimit,
      naaqsLimit: meta.naaqsLimit,
    };
  }

  const values = points.map((p) => {
    switch (pollutantId) {
      case 'pm25':
        return p.pm25;
      case 'pm10':
        return p.pm10;
      case 'co':
        return p.co;
      case 'no2':
        return p.no2;
      case 'so2':
        return p.so2;
      case 'o3':
        return p.o3;
    }
  });

  const min = Math.min(...values);
  const max = Math.max(...values);
  const sum = values.reduce((acc, v) => acc + v, 0);
  const isCo = pollutantId === 'co';
  const average = isCo
    ? Number((sum / values.length).toFixed(2))
    : Number((sum / values.length).toFixed(1));

  const firstVal = values[0] || 0.1;
  const lastVal = values[values.length - 1];
  const changePercentage = Number((((lastVal - firstVal) / firstVal) * 100).toFixed(1));

  let trendDirection: TrendDirection = 'stable';
  if (changePercentage > 5) trendDirection = 'worsening';
  else if (changePercentage < -5) trendDirection = 'improving';

  return {
    pollutantId,
    name: meta.name,
    formula: meta.formula,
    current,
    average,
    min,
    max,
    unit: meta.unit,
    trendDirection,
    changePercentage,
    whoLimit: meta.whoLimit,
    naaqsLimit: meta.naaqsLimit,
  };
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
    // 3d horizon
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
    // City-seeded modifier to avoid identical curves across cities
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

  // Precautions based on the peak anticipated condition
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

/**
 * Derives calculated observational insights strictly from the mock sample dataset.
 * Does NOT invent external causes like traffic or factory fires.
 */
export function generateAnalyticsInsights(
  cityData: CityDashboardData,
  points: HistoricalDataPoint[],
  summary: AnalyticsSummary,
  allCities: CityDashboardData[]
): AnalyticsInsightItem[] {
  const insights: AnalyticsInsightItem[] = [];

  // 1. Peak period observation
  insights.push({
    id: 'peak-period',
    type: 'peak',
    title: 'Peak Pollution Concentration Interval',
    description: `The highest sampled air quality index occurred at ${summary.highestAQITime}, reaching ${summary.highestAQI} AQI (${getAQICategory(summary.highestAQI)}).`,
    severity: summary.highestAQI > 200 ? 'critical' : summary.highestAQI > 100 ? 'warning' : 'info',
    metricValue: `${summary.highestAQI} AQI`,
    recommendation: 'Target high-intensity outdoor tasks outside this peak window.',
  });

  // 2. Cleanest period observation
  insights.push({
    id: 'cleanest-period',
    type: 'trough',
    title: 'Optimal Ambient Air Window',
    description: `The lowest sampled pollution reading was recorded at ${summary.lowestAQITime} at ${summary.lowestAQI} AQI (${getAQICategory(summary.lowestAQI)}).`,
    severity: 'positive',
    metricValue: `${summary.lowestAQI} AQI`,
    recommendation: 'Optimal window for natural building ventilation and outdoor exercise.',
  });

  // 3. Dominant pollutant driver
  insights.push({
    id: 'dominant-pollutant',
    type: 'dominant',
    title: 'Primary Contaminant Driver',
    description: `${summary.mostDominantPollutant} (${summary.dominantPollutantFormula}) determined the governing air quality rating in ${summary.dominantPollutantFrequency}% of all sample intervals in this period.`,
    severity: summary.mostDominantPollutant.includes('PM') ? 'warning' : 'info',
    metricValue: `${summary.dominantPollutantFrequency}% Dominance`,
    recommendation: `Focus mitigation on particulate filtration targeting ${summary.dominantPollutantFormula}.`,
  });

  // 4. Trend trajectory insight
  const absChange = Math.abs(summary.trendPercentageChange);
  const trendDesc =
    summary.trendDirection === 'improving'
      ? `Simulated sample values demonstrate a ${absChange}% improvement (decline in AQI) from the initial interval to the latest interval.`
      : summary.trendDirection === 'worsening'
      ? `Simulated sample values indicate a ${absChange}% elevation in AQI across the measured sample sequence.`
      : `Pollution measurements remained relatively stable across the sample series, with net variation within ±4.5%.`;

  insights.push({
    id: 'trend-trajectory',
    type: 'trend',
    title: 'Observed Trajectory Across Time Range',
    description: trendDesc,
    severity: summary.trendDirection === 'worsening' ? 'warning' : summary.trendDirection === 'improving' ? 'positive' : 'info',
    metricValue: `${summary.trendPercentageChange > 0 ? '+' : ''}${summary.trendPercentageChange}%`,
  });

  // 5. Cross-city standing among the 10 monitored stations
  const sortedCities = [...allCities].sort((a, b) => a.aqi - b.aqi);
  const rank = sortedCities.findIndex((c) => c.location.id === cityData.location.id) + 1;
  const isCleanest = rank === 1;
  const isMostPolluted = rank === sortedCities.length;

  insights.push({
    id: 'city-standing',
    type: 'comparison',
    title: 'Comparative Standing Among Monitored Stations',
    description: isCleanest
      ? `${cityData.location.city} currently records the lowest AQI (${cityData.aqi}) among all 10 monitored urban locations in the telemetry network.`
      : isMostPolluted
      ? `${cityData.location.city} currently records the highest AQI (${cityData.aqi}) across the 10 monitored stations in this demonstration network.`
      : `${cityData.location.city} ranks #${rank} of 10 monitored urban stations (with #1 being cleanest: ${sortedCities[0].location.city} at ${sortedCities[0].aqi} AQI).`,
    severity: isCleanest ? 'positive' : isMostPolluted ? 'critical' : 'info',
    metricValue: `Rank ${rank} of ${sortedCities.length}`,
  });

  // 6. Diurnal Pattern
  const morningPeak = points.find((p) => p.time === '08:00' || p.time === '10:00' || p.time === 'Day 2 AM');
  const eveningPeak = points.find((p) => p.time === '18:00' || p.time === '20:00');
  if (morningPeak || eveningPeak) {
    insights.push({
      id: 'cyclical-pattern',
      type: 'pattern',
      title: 'Cyclical Concentration Variation',
      description:
        'Telemetry curves exhibit recurring elevation during morning (08:00–10:00) and evening (18:00–21:00) transition hours, aligning with ambient thermal patterns and lower boundary layer heights.',
      severity: 'info',
      metricValue: 'Bimodal Curve',
      recommendation: 'Prioritize indoor HEPA air cleaning during transition windows.',
    });
  }

  return insights;
}

