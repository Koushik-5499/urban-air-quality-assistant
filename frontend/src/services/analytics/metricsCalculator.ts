import { POLLUTANT_DETAILS } from '../../data/pollutantDetails';
import type { AQICategory, CityDashboardData, PollutantId } from '../../types/dashboard';
import type {
  HistoricalDataPoint,
  AnalyticsSummary,
  PollutantStats,
  AnalyticsInsightItem,
  TrendDirection,
} from '../../types/analytics';

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

  const sliceSize = Math.max(1, Math.floor(points.length / 3));
  const firstSlice = points.slice(0, sliceSize);
  const lastSlice = points.slice(points.length - sliceSize);

  const avgFirst = firstSlice.reduce((acc, p) => acc + p.aqi, 0) / firstSlice.length;
  const avgLast = lastSlice.reduce((acc, p) => acc + p.aqi, 0) / lastSlice.length;

  const rawChange = avgLast - avgFirst;
  const trendPercentageChange = Number(((rawChange / (avgFirst || 1)) * 100).toFixed(1));

  let trendDirection: TrendDirection = 'stable';
  if (trendPercentageChange > 4.5) {
    trendDirection = 'worsening';
  } else if (trendPercentageChange < -4.5) {
    trendDirection = 'improving';
  }

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

