import { Search, X, SlidersHorizontal } from 'lucide-react';
import type { AlertSeverity } from '../../types/alerts';

export interface AlertFiltersProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedSeverity: 'all' | AlertSeverity;
  onSeverityChange: (s: 'all' | AlertSeverity) => void;
  selectedCityId: string;
  onCityChange: (c: string) => void;
  selectedStatus: 'all' | 'unread' | 'read';
  onStatusChange: (st: 'all' | 'unread' | 'read') => void;
  sortBy: 'newest' | 'oldest' | 'severity';
  onSortByChange: (s: 'newest' | 'oldest' | 'severity') => void;
  availableCities: Array<{ id: string; name: string }>;
  onResetFilters: () => void;
  isFiltered: boolean;
  totalFilteredCount: number;
}

export function AlertFilters({
  searchQuery,
  onSearchChange,
  selectedSeverity,
  onSeverityChange,
  selectedCityId,
  onCityChange,
  selectedStatus,
  onStatusChange,
  sortBy,
  onSortByChange,
  availableCities,
  onResetFilters,
  isFiltered,
  totalFilteredCount,
}: AlertFiltersProps) {
  return (
    <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-3">
      {/* Row 1: Search, City Dropdown, Sort Dropdown */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
        {/* Search */}
        <div className="sm:col-span-6 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            id="alerts-search-input"
            name="alerts-search"
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search alerts by city, state, or title..."
            aria-label="Search air quality alerts"
            className="w-full pl-9 pr-8 py-2 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange('')}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer"
              aria-label="Clear search query"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* City Filter */}
        <div className="sm:col-span-3">
          <select
            id="alerts-city-filter"
            name="alerts-city"
            value={selectedCityId}
            onChange={(e) => onCityChange(e.target.value)}
            aria-label="Filter alerts by city"
            className="w-full py-2 px-3 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer font-medium"
          >
            <option value="all">All Cities ({availableCities.length})</option>
            {availableCities.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Sort By */}
        <div className="sm:col-span-3">
          <div className="relative">
            <select
              id="alerts-sort-filter"
              name="alerts-sort"
              value={sortBy}
              onChange={(e) =>
                onSortByChange(e.target.value as 'newest' | 'oldest' | 'severity')
              }
              aria-label="Sort alerts"
              className="w-full py-2 px-3 text-xs rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer font-medium"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="severity">Highest Severity</option>
            </select>
          </div>
        </div>
      </div>

      {/* Row 2: Severity Pills, Read/Unread Filter, Count */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] font-semibold text-slate-400 mr-1 flex items-center gap-1">
            <SlidersHorizontal className="w-3 h-3" /> Severity:
          </span>

          {(['all', 'critical', 'warning', 'moderate', 'info'] as const).map((sev) => (
            <button
              key={sev}
              type="button"
              onClick={() => onSeverityChange(sev)}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                selectedSeverity === sev
                  ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {sev === 'all'
                ? 'All Severities'
                : sev.charAt(0).toUpperCase() + sev.slice(1)}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3 self-end lg:self-auto flex-wrap">
          {/* Read / Unread Status Filter */}
          <div className="inline-flex p-0.5 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold">
            <button
              type="button"
              onClick={() => onStatusChange('all')}
              className={`px-2 py-0.5 rounded-md transition-all cursor-pointer ${
                selectedStatus === 'all'
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              All
            </button>
            <button
              type="button"
              onClick={() => onStatusChange('unread')}
              className={`px-2 py-0.5 rounded-md transition-all cursor-pointer ${
                selectedStatus === 'unread'
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Unread
            </button>
            <button
              type="button"
              onClick={() => onStatusChange('read')}
              className={`px-2 py-0.5 rounded-md transition-all cursor-pointer ${
                selectedStatus === 'read'
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-2xs'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Read
            </button>
          </div>

          <span className="text-xs text-slate-500 dark:text-slate-400">
            <strong>{totalFilteredCount}</strong> matching
          </span>

          {isFiltered && (
            <button
              type="button"
              onClick={onResetFilters}
              className="text-xs text-rose-600 dark:text-rose-400 hover:underline cursor-pointer font-medium"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
