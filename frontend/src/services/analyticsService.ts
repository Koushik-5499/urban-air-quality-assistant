/**
 * Analytics Service Facade
 * Delegates generation of historical & simulated forecasts and metrics calculation to sub-modules.
 */
export {
  getAQICategory,
  getAQICategoryColor,
  calculateAnalyticsSummary,
  calculatePollutantStats,
  generateAnalyticsInsights,
} from './analytics/metricsCalculator';

export {
  getDeterministicFactor,
  generateHistoricalData,
  generateSimulatedForecast,
} from './analytics/dataGenerators';
