import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { LocationContext } from './location-context-def';
import { DASHBOARD_DATA, DEMO_LOCATIONS } from '../data/dashboardData';
import { airQualityApi } from '../services/api/airQualityApi';
import { formatApiErrorMessage } from '../services/api/errors';
import type { AQICalculationResponse, CityAirQualityResponse } from '../services/api/types';
import type { AQICategory, CityDashboardData } from '../types/dashboard';

const STORAGE_KEY_SELECTED = 'uaqa_selected_city';
const STORAGE_KEY_RECENTS = 'uaqa_recent_cities';
const MAX_RECENTS = 6;
const MAX_COMPARISON = 4;

function mapNaqiToFrontendCategory(naqiCategory: string | null | undefined): AQICategory {
  if (!naqiCategory) return 'Moderate';
  const norm = naqiCategory.toLowerCase();
  if (norm.includes('good')) return 'Good';
  if (norm.includes('satisfactory')) return 'Moderate';
  if (norm.includes('moderate')) return 'Unhealthy for Sensitive Groups';
  if (norm.includes('very poor')) return 'Very Unhealthy';
  if (norm.includes('poor')) return 'Unhealthy';
  if (norm.includes('severe') || norm.includes('hazardous')) return 'Hazardous';
  return 'Moderate';
}

export function LocationProvider({ children }: { children: React.ReactNode }) {
  // 1. Selected City ID state (persisted)
  const [selectedCityId, setSelectedCityIdState] = useState<string>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY_SELECTED);
      if (stored && DASHBOARD_DATA[stored]) return stored;
      return 'delhi';
    } catch {
      return 'delhi';
    }
  });

  // 2. Recent City IDs state (persisted)
  const [recentCityIds, setRecentCityIds] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY_RECENTS);
      if (stored) {
        const parsed: string[] = JSON.parse(stored);
        return parsed.filter((id) => Boolean(DASHBOARD_DATA[id]));
      }
      return ['delhi', 'mumbai', 'bengaluru'];
    } catch {
      return ['delhi', 'mumbai', 'bengaluru'];
    }
  });

  // 3. Comparison City IDs (up to 4 cities)
  const [comparisonCityIds, setComparisonCityIds] = useState<string[]>([
    'delhi',
    'mumbai',
    'bengaluru',
  ]);

  // 4. Live Backend State
  const [isLiveBackend, setIsLiveBackend] = useState<boolean>(false);
  const [isLoadingLive, setIsLoadingLive] = useState<boolean>(false);
  const [liveError, setLiveError] = useState<string | null>(null);
  const [backendAqiData, setBackendAqiData] = useState<AQICalculationResponse | null>(null);
  const [backendCityData, setBackendCityData] = useState<CityAirQualityResponse | null>(null);

  // Active request controller ref for race-condition prevention
  const activeAbortControllerRef = useRef<AbortController | null>(null);

  // Persist selected city
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_SELECTED, selectedCityId);
    } catch {
      // storage unavailable
    }
  }, [selectedCityId]);

  // Persist recent cities
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_RECENTS, JSON.stringify(recentCityIds));
    } catch {
      // storage unavailable
    }
  }, [recentCityIds]);

  // Add to recents
  const addRecentCity = useCallback((id: string) => {
    if (!DASHBOARD_DATA[id]) return;
    setRecentCityIds((prev) => {
      const filtered = prev.filter((item) => item !== id);
      return [id, ...filtered].slice(0, MAX_RECENTS);
    });
  }, []);

  const setSelectedCityId = useCallback(
    (id: string) => {
      const cleanId = id === 'new-delhi' ? 'delhi' : id;
      if (DASHBOARD_DATA[cleanId]) {
        setSelectedCityIdState(cleanId);
        addRecentCity(cleanId);
      }
    },
    [addRecentCity]
  );

  const clearRecentCities = useCallback(() => {
    setRecentCityIds([]);
    try {
      localStorage.removeItem(STORAGE_KEY_RECENTS);
    } catch {
      // storage unavailable
    }
  }, []);

  // Comparison actions
  const addComparisonCity = useCallback((id: string) => {
    const cleanId = id === 'new-delhi' ? 'delhi' : id;
    if (!DASHBOARD_DATA[cleanId]) return;
    setComparisonCityIds((prev) => {
      if (prev.includes(cleanId)) return prev;
      if (prev.length >= MAX_COMPARISON) return prev;
      return [...prev, cleanId];
    });
  }, []);

  const removeComparisonCity = useCallback((id: string) => {
    setComparisonCityIds((prev) => prev.filter((item) => item !== id));
  }, []);

  const toggleComparisonCity = useCallback((id: string) => {
    const cleanId = id === 'new-delhi' ? 'delhi' : id;
    setComparisonCityIds((prev) => {
      if (prev.includes(cleanId)) {
        return prev.filter((item) => item !== cleanId);
      }
      if (prev.length >= MAX_COMPARISON) {
        return prev;
      }
      return [...prev, cleanId];
    });
  }, []);

  const clearComparison = useCallback(() => {
    setComparisonCityIds([]);
  }, []);

  // Live Data Fetcher with AbortController for race condition protection
  const fetchLiveData = useCallback(async (cityId: string) => {
    // Abort previous pending in-flight request
    if (activeAbortControllerRef.current) {
      activeAbortControllerRef.current.abort();
    }

    const controller = new AbortController();
    activeAbortControllerRef.current = controller;

    setIsLoadingLive(true);
    setLiveError(null);

    const baseData = DASHBOARD_DATA[cityId] || DASHBOARD_DATA['delhi'];
    const cityName = baseData.location.city;

    try {
      const [cityResponse, aqiResponse] = await Promise.all([
        airQualityApi.getCityAirQuality(cityName, controller.signal).catch((err) => {
          if (controller.signal.aborted) throw err;
          return null;
        }),
        airQualityApi.calculateAqi({ city: cityName }, controller.signal).catch((err) => {
          if (controller.signal.aborted) throw err;
          return null;
        }),
      ]);

      if (controller.signal.aborted) return;

      if (cityResponse || aqiResponse) {
        setBackendCityData(cityResponse);
        setBackendAqiData(aqiResponse);
        setIsLiveBackend(true);
        setLiveError(null);
      } else {
        setIsLiveBackend(false);
        setBackendCityData(null);
        setBackendAqiData(null);
      }
    } catch (err: unknown) {
      if (controller.signal.aborted) return;
      setIsLiveBackend(false);
      setBackendCityData(null);
      setBackendAqiData(null);
      setLiveError(formatApiErrorMessage(err));
    } finally {
      if (!controller.signal.aborted) {
        setIsLoadingLive(false);
      }
    }
  }, []);

  // Trigger live fetch on selectedCityId change
  useEffect(() => {
    fetchLiveData(selectedCityId);
    return () => {
      if (activeAbortControllerRef.current) {
        activeAbortControllerRef.current.abort();
      }
    };
  }, [selectedCityId, fetchLiveData]);

  const refreshLiveData = useCallback(async () => {
    await fetchLiveData(selectedCityId);
  }, [fetchLiveData, selectedCityId]);

  // Derived metadata
  const isSimulated = useMemo(() => {
    return Boolean(backendCityData?.is_simulated || backendAqiData?.is_simulated);
  }, [backendCityData, backendAqiData]);

  const isStale = useMemo(() => {
    return Boolean(backendCityData?.is_stale);
  }, [backendCityData]);

  const dataAgeSeconds = useMemo(() => {
    return backendCityData?.data_age_seconds ?? null;
  }, [backendCityData]);

  // Merge live backend data into selected city data
  const selectedCityData = useMemo<CityDashboardData>(() => {
    const base = DASHBOARD_DATA[selectedCityId] || DASHBOARD_DATA['delhi'];

    if (!isLiveBackend || (!backendAqiData && !backendCityData)) {
      return base;
    }

    const calculatedAqi = backendAqiData?.aqi ?? base.aqi;
    const category = backendAqiData?.category
      ? mapNaqiToFrontendCategory(backendAqiData.category)
      : base.category;
    const dominant = backendAqiData?.dominant_pollutant ?? base.dominantPollutant;
    const summary = backendAqiData?.explanation || base.summary;

    // Update pollutant concentrations from backend if available
    const updatedPollutants = base.pollutants.map((pollutant) => {
      const match = backendCityData?.pollutants.find(
        (p) => p.code.toLowerCase() === pollutant.id.toLowerCase()
      );
      if (!match) return pollutant;

      const subIndexInfo = backendAqiData?.pollutant_subindices?.[match.code];
      return {
        ...pollutant,
        value: Math.round(match.concentration * 10) / 10,
        status: subIndexInfo?.category || pollutant.status,
      };
    });

    // Format last updated
    const timestampStr =
      backendAqiData?.calculated_at ||
      backendCityData?.measured_at ||
      backendCityData?.fetched_at;
    let formattedLastUpdated = base.lastUpdated;
    if (timestampStr) {
      try {
        const date = new Date(timestampStr);
        formattedLastUpdated = `Updated ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      } catch {
        // keep base
      }
    }

    return {
      ...base,
      aqi: calculatedAqi,
      category,
      dominantPollutant: dominant,
      summary,
      pollutants: updatedPollutants,
      lastUpdated: formattedLastUpdated,
    };
  }, [selectedCityId, isLiveBackend, backendAqiData, backendCityData]);

  // List of all 10 cities
  const allCities = useMemo(() => {
    return DEMO_LOCATIONS.map((loc) => DASHBOARD_DATA[loc.id] || DASHBOARD_DATA['delhi']);
  }, []);

  const value = useMemo(
    () => ({
      selectedCityId,
      selectedCityData,
      setSelectedCityId,
      recentCityIds,
      addRecentCity,
      clearRecentCities,
      comparisonCityIds,
      toggleComparisonCity,
      addComparisonCity,
      removeComparisonCity,
      clearComparison,
      allCities,
      isLiveBackend,
      isLoadingLive,
      liveError,
      isSimulated,
      isStale,
      dataAgeSeconds,
      backendAqiData,
      backendCityData,
      refreshLiveData,
    }),
    [
      selectedCityId,
      selectedCityData,
      setSelectedCityId,
      recentCityIds,
      addRecentCity,
      clearRecentCities,
      comparisonCityIds,
      toggleComparisonCity,
      addComparisonCity,
      removeComparisonCity,
      clearComparison,
      allCities,
      isLiveBackend,
      isLoadingLive,
      liveError,
      isSimulated,
      isStale,
      dataAgeSeconds,
      backendAqiData,
      backendCityData,
      refreshLiveData,
    ]
  );

  return <LocationContext.Provider value={value}>{children}</LocationContext.Provider>;
}
