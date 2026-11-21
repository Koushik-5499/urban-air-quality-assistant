import { useState, useMemo } from 'react';
import { SlidersHorizontal, ArrowUpDown } from 'lucide-react';
import { LocationCard } from './LocationCard';
import { LocationEmptyState } from './LocationEmptyState';
import type { CityDashboardData } from '../../types/dashboard';
import type { LocationFilter, LocationSort } from '../../types/locations';

export interface LocationGridProps {
  cities: CityDashboardData[];
  selectedCityId: string;
  comparisonCityIds: string[];
  onViewDetails: (city: CityDashboardData) => void;
  onSelectForDashboard: (city: CityDashboardData) => void;
  onToggleCompare: (cityId: string) => void;
  onResetSearch?: () => void;
  isSearchActive: boolean;
}

export function LocationGrid({
  cities,
  selectedCityId,
  comparisonCityIds,
  onViewDetails,
  onSelectForDashboard,
  onToggleCompare,
  onResetSearch,
  isSearchActive,
}: LocationGridProps) {
  const [filter, setFilter] = useState<LocationFilter>('all');
  const [sortBy, setSortBy] = useState<LocationSort>('name');

  // Filter logic
  const filteredCities = useMemo(() => {
    return cities.filter((city) => {
      if (filter === 'good') return city.category === 'Good';
      if (filter === 'moderate') return city.category === 'Moderate';
      if (filter === 'unhealthy')
        return (
          city.category === 'Unhealthy for Sensitive Groups' ||
          city.category === 'Unhealthy' ||
          city.category === 'Very Unhealthy' ||
          city.category === 'Hazardous'
        );
      return true;
    });
  }, [cities, filter]);

  // Sort logic
  const sortedCities = useMemo(() => {
    const list = [...filteredCities];
    list.sort((a, b) => {
      if (sortBy === 'aqi-asc') return a.aqi - b.aqi;
      if (sortBy === 'aqi-desc') return b.aqi - a.aqi;
      if (sortBy === 'pm25-desc') {
        const aPm25 = a.pollutants.find((p) => p.id === 'pm25')?.value ?? 0;
        const bPm25 = b.pollutants.find((p) => p.id === 'pm25')?.value ?? 0;
        return bPm25 - aPm25;
      }
      // 'name' sort
      return a.location.city.localeCompare(b.location.city);
    });
    return list;
  }, [filteredCities, sortBy]);

  const canAddMoreToCompare = comparisonCityIds.length < 4;

  return (
    <div className="space-y-4">
      {/* Filters & Sorting Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
        {/* Category Filters */}
        <div className="flex flex-wrap items-center gap-1.5" role="radiogroup" aria-label="Filter locations by air quality">
          <span className="text-xs font-semibold text-slate-500 mr-1 flex items-center gap-1">
            <SlidersHorizontal className="w-3.5 h-3.5" aria-hidden="true" />
            Filter:
          </span>
          <button
            type="button"
            onClick={() => setFilter('all')}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors cursor-pointer ${
              filter === 'all'
                ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 font-semibold'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:hover:bg-slate-700'
            }`}
          >
            All Cities ({cities.length})
          </button>
          <button
            type="button"
            onClick={() => setFilter('good')}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors cursor-pointer ${
              filter === 'good'
                ? 'bg-emerald-600 text-white font-semibold'
                : 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 hover:bg-emerald-100'
            }`}
          >
            Good (AQI ≤ 50)
          </button>
          <button
            type="button"
            onClick={() => setFilter('moderate')}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors cursor-pointer ${
              filter === 'moderate'
                ? 'bg-amber-600 text-white font-semibold'
                : 'bg-amber-50 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 hover:bg-amber-100'
            }`}
          >
            Moderate (51–100)
          </button>
          <button
            type="button"
            onClick={() => setFilter('unhealthy')}
            className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors cursor-pointer ${
              filter === 'unhealthy'
                ? 'bg-rose-600 text-white font-semibold'
                : 'bg-rose-50 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 hover:bg-rose-100'
            }`}
          >
            Sensitive & Unhealthy (101+)
          </button>
        </div>

        {/* Sort Dropdown */}
        <div className="flex items-center gap-2 self-end sm:self-auto">
          <label htmlFor="location-sort-select" className="text-xs text-slate-500 font-medium flex items-center gap-1">
            <ArrowUpDown className="w-3 h-3" aria-hidden="true" />
            Sort:
          </label>
          <select
            id="location-sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as LocationSort)}
            className="text-xs font-medium bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer"
          >
            <option value="name">City Name (A–Z)</option>
            <option value="aqi-asc">Lowest AQI First</option>
            <option value="aqi-desc">Highest AQI First</option>
            <option value="pm25-desc">Highest PM2.5 First</option>
          </select>
        </div>
      </div>

      {/* Grid of City Cards */}
      {sortedCities.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {sortedCities.map((cityData) => (
            <LocationCard
              key={cityData.location.id}
              cityData={cityData}
              isSelectedForDashboard={selectedCityId === cityData.location.id}
              isCompared={comparisonCityIds.includes(cityData.location.id)}
              canCompare={canAddMoreToCompare}
              onViewDetails={onViewDetails}
              onSelectForDashboard={onSelectForDashboard}
              onToggleCompare={onToggleCompare}
            />
          ))}
        </div>
      ) : (
        <LocationEmptyState
          onReset={() => {
            setFilter('all');
            if (onResetSearch) onResetSearch();
          }}
          message={
            isSearchActive
              ? 'No cities matched your search query or filter combination.'
              : 'No cities found for the selected category filter.'
          }
        />
      )}
    </div>
  );
}
