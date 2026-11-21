import { Search, X, Layers, Activity } from 'lucide-react';
import type { PollutantCategoryType } from '../../types/pollutants';

export interface PollutantFilterProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  category: PollutantCategoryType;
  onCategoryChange: (category: PollutantCategoryType) => void;
  activeView: 'grid' | 'comparison';
  onActiveViewChange: (view: 'grid' | 'comparison') => void;
  onClearFilters: () => void;
  isFiltered: boolean;
}

export function PollutantFilter({
  searchQuery,
  onSearchChange,
  category,
  onCategoryChange,
  activeView,
  onActiveViewChange,
  onClearFilters,
  isFiltered,
}: PollutantFilterProps) {
  return (
    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs">
      {/* Search Input & Category Pills */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 flex-1">
        {/* Search */}
        <div className="relative min-w-[240px] max-w-sm">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            id="pollutant-search-input"
            name="pollutant-search"
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search pollutant (e.g. PM2.5, Ozone, CO)..."
            aria-label="Search criteria pollutants by chemical formula or name"
            className="w-full pl-9 pr-8 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer"
              aria-label="Clear search text"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Category Pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            type="button"
            onClick={() => onCategoryChange('all')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              category === 'all'
                ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-xs'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            All Pollutants (6)
          </button>

          <button
            type="button"
            onClick={() => onCategoryChange('particulate')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              category === 'particulate'
                ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-xs'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Particulates (PM2.5, PM10)
          </button>

          <button
            type="button"
            onClick={() => onCategoryChange('gaseous')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              category === 'gaseous'
                ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-xs'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Gaseous & Oxidants (CO, NO2, SO2, O3)
          </button>

          {isFiltered && (
            <button
              type="button"
              onClick={onClearFilters}
              className="text-xs text-rose-600 dark:text-rose-400 hover:underline px-2 cursor-pointer font-medium"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Active View Switcher */}
      <div className="inline-flex p-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 self-start lg:self-auto text-xs font-semibold">
        <button
          type="button"
          onClick={() => onActiveViewChange('grid')}
          className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
            activeView === 'grid'
              ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Metric Cards & Trends</span>
        </button>

        <button
          type="button"
          onClick={() => onActiveViewChange('comparison')}
          className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
            activeView === 'comparison'
              ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Multi-Pollutant Compare</span>
        </button>
      </div>
    </div>
  );
}
