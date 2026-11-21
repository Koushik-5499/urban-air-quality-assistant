import { createContext } from 'react';
import type { CityDashboardData } from '../types/dashboard';
import type { AQICalculationResponse, CityAirQualityResponse } from '../services/api/types';

export interface LocationContextType {
  selectedCityId: string;
  selectedCityData: CityDashboardData;
  setSelectedCityId: (id: string) => void;
  recentCityIds: string[];
  addRecentCity: (id: string) => void;
  clearRecentCities: () => void;
  comparisonCityIds: string[];
  toggleComparisonCity: (id: string) => void;
  addComparisonCity: (id: string) => void;
  removeComparisonCity: (id: string) => void;
  clearComparison: () => void;
  allCities: CityDashboardData[];

  // Phase 9 Live Backend State
  isLiveBackend: boolean;
  isLoadingLive: boolean;
  liveError: string | null;
  isSimulated: boolean;
  isStale: boolean;
  dataAgeSeconds: number | null;
  backendAqiData: AQICalculationResponse | null;
  backendCityData: CityAirQualityResponse | null;
  refreshLiveData: () => Promise<void>;
}

export const LocationContext = createContext<LocationContextType | undefined>(undefined);
