import { useState, useMemo, useEffect } from 'react';
import {
  MapPin,
  Layers,
  Sparkles,
  SlidersHorizontal,
  ExternalLink,
  CheckCircle2,
} from 'lucide-react';
import { useLocation } from '../hooks/useLocation';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { DataProvenanceBadge } from '../components/common/DataProvenanceBadge';
import { LocationSearchBar } from '../components/locations/LocationSearchBar';
import { RecentLocations } from '../components/locations/RecentLocations';
import { LocationGrid } from '../components/locations/LocationGrid';
import { CityComparison } from '../components/locations/CityComparison';
import { CityDetailsPanel } from '../components/locations/CityDetailsPanel';
import { Badge } from '../components/ui/Badge';
import { airQualityApi } from '../services/api/airQualityApi';
import type { CityAvailabilitySummary } from '../services/api/types';
import type { CityDashboardData } from '../types/dashboard';
import { Link } from 'react-router-dom';

function Locations() {
  useDocumentTitle('Locations — Urban Air Quality Assistant');

  const {
    allCities,
    selectedCityId,
    selectedCityData,
    setSelectedCityId,
    recentCityIds,
    clearRecentCities,
    comparisonCityIds,
    toggleComparisonCity,
    addComparisonCity,
    removeComparisonCity,
    clearComparison,
  } = useLocation();

  // Search state
  const [searchTerm, setSearchTerm] = useState('');

  // Active view tab: 'grid' (All Cities) or 'compare' (Comparison Mode)
  const [activeTab, setActiveTab] = useState<'grid' | 'compare'>('grid');

  // Detailed city drawer state
  const [detailsCity, setDetailsCity] = useState<CityDashboardData | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [backendCities, setBackendCities] = useState<CityAvailabilitySummary[]>([]);

  // Fetch registered cities availability from FastAPI backend
  useEffect(() => {
    let isMounted = true;
    airQualityApi
      .getCities()
      .then((data) => {
        if (isMounted && data) {
          setBackendCities(data);
        }
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, []);

  // Filtered cities based on search
  const searchedCities = useMemo(() => {
    if (!searchTerm.trim()) return allCities;
    const q = searchTerm.toLowerCase().trim();
    return allCities.filter(
      (c) =>
        c.location.city.toLowerCase().includes(q) ||
        c.location.state.toLowerCase().includes(q) ||
        c.location.country.toLowerCase().includes(q) ||
        c.location.name.toLowerCase().includes(q)
    );
  }, [allCities, searchTerm]);

  // Handlers
  const handleOpenDetails = (city: CityDashboardData) => {
    setDetailsCity(city);
    setIsDetailsOpen(true);
  };

  const handleCloseDetails = () => {
    setIsDetailsOpen(false);
  };

  const handleSelectForDashboard = (city: CityDashboardData) => {
    setSelectedCityId(city.location.id);
  };

  const handleSearchSelectCity = (city: CityDashboardData) => {
    setSearchTerm('');
    handleOpenDetails(city);
  };

  const handleResetSearch = () => {
    setSearchTerm('');
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 animate-in fade-in duration-300">
      {/* 1. Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="p-2 rounded-xl bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/60">
              <MapPin className="w-5 h-5" aria-hidden="true" />
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              Explore Air Quality by Location
            </h1>
            <DataProvenanceBadge />
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 max-w-2xl">
            Discover and compare air quality conditions across cities. Inspect microclimate telemetry, ambient pollutant levels, and historical health thresholds.
          </p>
        </div>

        {/* Active Dashboard City Status Pill */}
        <div className="flex flex-wrap items-center gap-3">
          {backendCities.length > 0 && (
            <Badge variant="success" size="sm" className="flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>{backendCities.length} Cities Active in Backend</span>
            </Badge>
          )}
          <div className="flex items-center gap-2.5 px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
            <span className="text-slate-500 dark:text-slate-400">Dashboard Active:</span>
            <span className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              {selectedCityData.location.city} ({selectedCityData.aqi} AQI)
            </span>
            <Link
              to="/"
              className="text-emerald-600 dark:text-emerald-400 hover:underline font-medium inline-flex items-center gap-0.5 ml-1"
            >
              <span>View Dashboard</span>
              <ExternalLink className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* 2. Search & Filter Bar */}
      <div className="space-y-4">
        <LocationSearchBar
          cities={allCities}
          onSelectCity={handleSearchSelectCity}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          placeholder="Search 10 Indian cities by name, state, or country (e.g., Coimbatore, Delhi, Kochi)..."
        />

        {/* Recently Searched Locations */}
        <RecentLocations
          recentCityIds={recentCityIds}
          onSelectCity={handleOpenDetails}
          onClear={clearRecentCities}
        />
      </div>

      {/* 3. View Switcher Tabs (All Cities vs Comparison) */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2">
        <div className="inline-flex p-1 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 self-start">
          <button
            type="button"
            onClick={() => setActiveTab('grid')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'grid'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" aria-hidden="true" />
            <span>All Monitoring Stations ({allCities.length})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('compare')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === 'compare'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Multi-City Comparison</span>
            <Badge
              variant={comparisonCityIds.length > 0 ? 'info' : 'default'}
              size="sm"
            >
              {comparisonCityIds.length}/4
            </Badge>
          </button>
        </div>

        {/* Quick status message */}
        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <Sparkles className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          <span>All 10 monitoring locations updated with simulated atmospheric telemetry</span>
        </div>
      </div>

      {/* 4. Tab Content */}
      {activeTab === 'grid' ? (
        <LocationGrid
          cities={searchedCities}
          selectedCityId={selectedCityId}
          comparisonCityIds={comparisonCityIds}
          onViewDetails={handleOpenDetails}
          onSelectForDashboard={handleSelectForDashboard}
          onToggleCompare={toggleComparisonCity}
          onResetSearch={handleResetSearch}
          isSearchActive={searchTerm.trim().length > 0}
        />
      ) : (
        <CityComparison
          comparisonCityIds={comparisonCityIds}
          allCities={allCities}
          onRemoveCity={removeComparisonCity}
          onAddCity={addComparisonCity}
          onClearAll={clearComparison}
          onSelectForDashboard={handleSelectForDashboard}
          activeDashboardCityId={selectedCityId}
        />
      )}

      {/* 5. City Details Drawer / Slide-Over Modal */}
      <CityDetailsPanel
        city={detailsCity}
        isOpen={isDetailsOpen}
        onClose={handleCloseDetails}
        onSelectForDashboard={handleSelectForDashboard}
        isActiveCity={detailsCity?.location.id === selectedCityId}
        onToggleCompare={toggleComparisonCity}
        isComparing={Boolean(detailsCity && comparisonCityIds.includes(detailsCity.location.id))}
        canCompare={comparisonCityIds.length < 4}
      />
    </div>
  );
}

export { Locations, Locations as LocationsPage };
export default Locations;
