import { Search, X, SlidersHorizontal, MapPin } from 'lucide-react';
import type { AQICategory } from '../../types/dashboard';

export interface MapFiltersProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedCategory: 'all' | AQICategory;
  onCategoryChange: (cat: 'all' | AQICategory) => void;
  selectedState: string;
  onStateChange: (state: string) => void;
  availableStates: string[];
  totalCities: number;
  filteredCount: number;
  onResetFilters: () => void;
  isFiltered: boolean;
}

export function MapFilters({
  searchQuery,
  onSearchChange,
  selectedCategory,
  onCategoryChange,
  selectedState,
  onStateChange,
  availableStates,
  totalCities,
  filteredCount,
  onResetFilters,
  isFiltered,
}: MapFiltersProps) {
  return (
    <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-3">
      {/* Search Input & State Selector */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            id="map-city-search"
            name="map-city-search"
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search city, state or station..."
            aria-label="Search city, state or station on map"
            className="w-full pl-9 pr-8 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer"
              aria-label="Clear search input"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* State Selector */}
        <div className="relative min-w-[160px]">
          <select
            id="map-state-filter"
            name="map-state-filter"
            value={selectedState}
            onChange={(e) => onStateChange(e.target.value)}
            aria-label="Filter stations by Indian state"
            className="w-full py-2 px-3 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer font-medium"
          >
            <option value="all">All States ({availableStates.length})</option>
            {availableStates.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Category Pills & Count */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1 border-t border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] font-semibold text-slate-400 mr-1 flex items-center gap-1">
            <SlidersHorizontal className="w-3 h-3" /> AQI Filter:
          </span>

          {(['all', 'Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy'] as const).map(
            (cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => onCategoryChange(cat)}
                className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  selectedCategory === cat
                    ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-xs'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {cat === 'all'
                  ? 'All Categories'
                  : cat === 'Unhealthy for Sensitive Groups'
                  ? 'Sensitive'
                  : cat}
              </button>
            )
          )}

          {isFiltered && (
            <button
              type="button"
              onClick={onResetFilters}
              className="text-xs text-rose-600 dark:text-rose-400 hover:underline px-2 cursor-pointer font-medium"
            >
              Reset
            </button>
          )}
        </div>

        {/* Count indicator */}
        <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5 self-end sm:self-auto">
          <MapPin className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          <span>
            Showing <strong className="text-slate-900 dark:text-white">{filteredCount}</strong> of {totalCities} monitoring nodes
          </span>
        </div>
      </div>
    </div>
  );
}

