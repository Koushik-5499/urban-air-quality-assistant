import type { PollutantId, ChartTimeRange } from './dashboard';

export type PollutantCategoryType = 'all' | 'particulate' | 'gaseous';

export interface SensitiveGroupInfo {
  group: string;
  description: string;
}

export interface PollutantDetailedInfo {
  id: PollutantId;
  name: string;
  formula: string;
  fullName: string;
  classification: 'Particulate Matter' | 'Gaseous Combustion' | 'Photochemical Oxidant';
  unit: string;
  whoLimit: number;
  whoLimitText: string;
  naaqsLimit: number;
  naaqsLimitText: string;
  description: string;
  primarySources: string[];
  environmentalImpact: string;
  healthEffects: {
    overview: string;
    sensitiveGroups: SensitiveGroupInfo[];
    symptoms: string[];
  };
  protectiveMeasures: string[];
  color: string;
  accentColor: string;
}

export interface DetailedTrendPoint {
  time: string;
  pm25: number;
  pm10: number;
  co: number; // in mg/m³
  no2: number;
  so2: number;
  o3: number;
  aqi: number;
}

export interface PollutantSubIndex {
  id: PollutantId;
  name: string;
  formula: string;
  concentration: number;
  unit: string;
  subIndex: number;
  isDominant: boolean;
  benchmarkPercentage: number;
  category: string;
  color: string;
}

export interface PollutantFilterState {
  searchQuery: string;
  category: PollutantCategoryType;
  selectedPollutantId: PollutantId;
  comparisonPollutants: PollutantId[];
  timeRange: ChartTimeRange;
  comparisonMode: 'normalized' | 'individual';
}

