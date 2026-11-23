import { useState, useMemo, useEffect } from 'react';
import {
  Map as MapIcon,
  Sparkles,
  ListFilter,
  MapPin,
  CheckCircle2,
} from 'lucide-react';
import { useLocation } from '../hooks/useLocation';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { DataProvenanceBadge } from '../components/common/DataProvenanceBadge';
import { PollutionMap } from '../components/maps/PollutionMap';
import { MapFilters } from '../components/maps/MapFilters';
import { MapCityDrawer } from '../components/maps/MapCityDrawer';
import { MapEmptyState } from '../components/maps/MapEmptyState';
import { MAP_CITIES, getAQIColor, getAQIBadgeVariant } from '../data/mapData';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { airQualityApi } from '../services/api/airQualityApi';
import type { MapCityData } from '../types/map';
import type { AQICategory } from '../types/dashboard';

export function MapPage() {
  useDocumentTitle('Pollution Map — Urban Air Quality Assistant');

  const { selectedCityId, setSelectedCityId, selectedCityData } = useLocation();

  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'all' | AQICategory>('all');
  const [selectedState, setSelectedState] = useState('all');
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showMarkers, setShowMarkers] = useState(true);
  const [viewMode, setViewMode] = useState<'map' | 'list'>('map');

  // Trigger states to command the map
  const [resetTrigger, setResetTrigger] = useState(0);
  const [focusTrigger, setFocusTrigger] = useState(0);
  const [stationsCount, setStationsCount] = useState<number | null>(null);

  // Query Backend for active monitoring stations on mount
  useEffect(() => {
    let isMounted = true;
    airQualityApi
      .getStations()
      .then((stations) => {
        if (isMounted && stations) {
          setStationsCount(stations.length);
        }
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, []);

  // Selected city object on map (defaults to the shared global selected city)
  const [activeMapCity, setActiveMapCity] = useState<MapCityData | null>(() => {
    return MAP_CITIES.find((c) => c.id === selectedCityId) || MAP_CITIES[0];
  });

  // Keep activeMapCity synced with global selectedCityId when it changes
  useEffect(() => {
    const found = MAP_CITIES.find((c) => c.id === selectedCityId);
    if (found) {
      setActiveMapCity(found);
    }
  }, [selectedCityId]);

  // List of distinct states
  const availableStates = useMemo(() => {
    const set = new Set(MAP_CITIES.map((c) => c.state));
    return Array.from(set).sort();
  }, []);

  // Filtered cities based on search, category, and state
  const filteredCities = useMemo(() => {
    return MAP_CITIES.filter((city) => {
      // Category filter
      if (selectedCategory !== 'all' && city.category !== selectedCategory) {
        return false;
      }

      // State filter
      if (selectedState !== 'all' && city.state !== selectedState) {
        return false;
      }

      // Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matches =
          city.city.toLowerCase().includes(q) ||
          city.state.toLowerCase().includes(q) ||
          city.station.toLowerCase().includes(q);
        if (!matches) return false;
      }

      return true;
    });
  }, [selectedCategory, selectedState, searchQuery]);

  // Handlers
  const handleSelectCity = (city: MapCityData) => {
    setActiveMapCity(city);
    setFocusTrigger((prev) => prev + 1);
  };

  const handleSelectForDashboard = (cityId: string) => {
    setSelectedCityId(cityId);
  };

  const handleResetFilters = () => {
    setSearchQuery('');
    setSelectedCategory('all');
    setSelectedState('all');
    setResetTrigger((prev) => prev + 1);
  };

  const handleResetView = () => {
    setResetTrigger((prev) => prev + 1);
  };

  const isFiltered =
    searchQuery.trim().length > 0 || selectedCategory !== 'all' || selectedState !== 'all';

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 animate-in fade-in duration-300">
      {/* 1. Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="p-2 rounded-xl bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-400 border border-teal-200/60 dark:border-teal-800/60">
              <MapIcon className="w-5 h-5" aria-hidden="true" />
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Interactive Pollution Map
            </h1>
            <DataProvenanceBadge />
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 max-w-3xl">
            Geospatial air quality monitoring across Indian metropolitan corridors. Track regional atmospheric dispersion zones, localized AQI hotspots, and sensor telemetry.
          </p>
        </div>

        {/* Active Dashboard City & View Switcher */}
        <div className="flex items-center gap-3 flex-wrap">
          {stationsCount !== null && (
            <Badge variant="success" size="sm" className="flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>{stationsCount} Active Stations</span>
            </Badge>
          )}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-850 border border-slate-200 dark:border-slate-700 text-xs font-medium">
            <span className="text-slate-500">Dashboard Active:</span>
            <span className="font-bold text-slate-900 dark:text-white flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              {selectedCityData.location.city} ({selectedCityData.aqi} AQI)
            </span>
          </div>

          <div className="inline-flex p-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold">
            <button
              type="button"
              onClick={() => setViewMode('map')}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
                viewMode === 'map'
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <MapIcon className="w-3.5 h-3.5" />
              <span>Map View</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
                viewMode === 'list'
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <ListFilter className="w-3.5 h-3.5" />
              <span>Accessible Table</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Map Filter Controls */}
      <MapFilters
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        selectedCategory={selectedCategory}
        onCategoryChange={setSelectedCategory}
        selectedState={selectedState}
        onStateChange={setSelectedState}
        availableStates={availableStates}
        totalCities={MAP_CITIES.length}
        filteredCount={filteredCities.length}
        onResetFilters={handleResetFilters}
        isFiltered={isFiltered}
      />

      {/* 3. Main Body */}
      {viewMode === 'map' ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Main Geospatial Leaflet Map */}
          <div className="lg:col-span-8 space-y-3">
            {filteredCities.length === 0 ? (
              <MapEmptyState onReset={handleResetFilters} />
            ) : (
              <PollutionMap
                cities={filteredCities}
                selectedCity={activeMapCity}
                activeDashboardCityId={selectedCityId}
                onSelectCity={handleSelectCity}
                onSelectForDashboard={handleSelectForDashboard}
                onViewDetails={handleSelectCity}
                showHeatmap={showHeatmap}
                onToggleHeatmap={() => setShowHeatmap(!showHeatmap)}
                showMarkers={showMarkers}
                onToggleMarkers={() => setShowMarkers(!showMarkers)}
                resetTrigger={resetTrigger}
                onResetView={handleResetView}
                focusTrigger={focusTrigger}
              />
            )}

            {/* Quick helper line below map */}
            <div className="flex items-center justify-between text-xs text-slate-400 px-1">
              <span className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                Click any city marker to inspect atmospheric metrics and center map
              </span>
              <span>OpenStreetMap Tiles • Leaflet v1.9</span>
            </div>
          </div>

          {/* Right Selected City Details Drawer */}
          <div className="lg:col-span-4">
            <MapCityDrawer
              city={activeMapCity}
              onClose={() => setActiveMapCity(null)}
              isActiveDashboardCity={activeMapCity?.id === selectedCityId}
              onSelectForDashboard={handleSelectForDashboard}
            />
          </div>
        </div>
      ) : (
        /* Accessible List & Table View Alternative */
        <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <MapPin className="w-4 h-4 text-emerald-600" />
                <span>Geographical Station Directory & Telemetry</span>
              </h3>
              <p className="text-xs text-slate-500">
                Accessible tabular alternative to the graphical map for screen readers and keyboard users.
              </p>
            </div>
            <Badge variant="neutral" size="sm">
              {filteredCities.length} Stations Available
            </Badge>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 dark:bg-slate-850 text-slate-500 uppercase tracking-wider text-[10px] border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">City & State</th>
                  <th className="py-2.5 px-3">Coordinates</th>
                  <th className="py-2.5 px-3">AQI Score</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">PM2.5</th>
                  <th className="py-2.5 px-3">PM10</th>
                  <th className="py-2.5 px-3">Weather</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredCities.map((city) => (
                  <tr
                    key={city.id}
                    className={`hover:bg-slate-50/60 dark:hover:bg-slate-850/60 transition-colors ${
                      city.id === selectedCityId ? 'bg-emerald-50/30 dark:bg-emerald-950/20' : ''
                    }`}
                  >
                    <td className="py-3 px-3">
                      <div className="font-bold text-slate-900 dark:text-white">{city.city}</div>
                      <div className="text-[11px] text-slate-400">
                        {city.state} • {city.station}
                      </div>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-500 text-[11px]">
                      {city.lat.toFixed(2)}°N, {city.lng.toFixed(2)}°E
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className="px-2 py-0.5 rounded-full font-mono font-bold text-white text-[11px]"
                        style={{ backgroundColor: getAQIColor(city.category) }}
                      >
                        {city.aqi}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <Badge variant={getAQIBadgeVariant(city.category)} size="sm">
                        {city.category}
                      </Badge>
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-slate-800 dark:text-slate-200">
                      {city.pm25.toFixed(1)} µg/m³
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-600 dark:text-slate-300">
                      {city.pm10.toFixed(1)} µg/m³
                    </td>
                    <td className="py-3 px-3 text-slate-600 dark:text-slate-300">
                      {city.temperature.toFixed(1)}°C ({city.humidity}%)
                    </td>
                    <td className="py-3 px-3 text-right space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          handleSelectCity(city);
                          setViewMode('map');
                        }}
                        className="text-xs"
                      >
                        View on Map
                      </Button>
                      {city.id !== selectedCityId && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleSelectForDashboard(city.id)}
                          className="text-xs text-emerald-700 dark:text-emerald-400"
                        >
                          Set Active
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 4. Bottom Simulated Data Notice */}
      <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850/60 border border-slate-200/60 dark:border-slate-800 flex items-start gap-3 text-xs text-slate-500 dark:text-slate-400">
        <Sparkles className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
        <p>
          <strong>Geospatial Telemetry Notice:</strong> Station locations and ambient AQI coordinates are calibrated to Indian metropolitan city centers for demonstration purposes. Atmospheric dispersion fields represent simulated Gaussian plume models and do not replace official regulatory sensor feeds from state pollution control boards.
        </p>
      </div>
    </div>
  );
}

export default MapPage;
