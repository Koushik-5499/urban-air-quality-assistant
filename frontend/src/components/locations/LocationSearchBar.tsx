import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { Search, X } from 'lucide-react';
import { LocationSuggestions } from './LocationSuggestions';
import type { CityDashboardData } from '../../types/dashboard';

export interface LocationSearchBarProps {
  cities: CityDashboardData[];
  onSelectCity: (city: CityDashboardData) => void;
  searchTerm: string;
  onSearchChange: (value: string) => void;
  placeholder?: string;
}

export function LocationSearchBar({
  cities,
  onSelectCity,
  searchTerm,
  onSearchChange,
  placeholder = 'Search cities by name, state, or country (e.g. Coimbatore, Tamil Nadu, Kerala)...',
}: LocationSearchBarProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter cities matching search term (city, state, or country)
  const filteredCities = useMemo(() => {
    if (!searchTerm.trim()) return [];
    const q = searchTerm.toLowerCase().trim();
    return cities.filter(
      (c) =>
        c.location.city.toLowerCase().includes(q) ||
        c.location.state.toLowerCase().includes(q) ||
        c.location.country.toLowerCase().includes(q) ||
        c.location.name.toLowerCase().includes(q)
    );
  }, [cities, searchTerm]);

  // Click outside to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleClear = useCallback(() => {
    onSearchChange('');
    setIsOpen(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  }, [onSearchChange]);

  const handleSelect = useCallback(
    (city: CityDashboardData) => {
      onSelectCity(city);
      onSearchChange(city.location.city);
      setIsOpen(false);
      setSelectedIndex(-1);
    },
    [onSelectCity, onSearchChange]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || filteredCities.length === 0) {
      if (e.key === 'ArrowDown' && filteredCities.length > 0) {
        setIsOpen(true);
        setSelectedIndex(0);
        e.preventDefault();
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) =>
        prev < filteredCities.length - 1 ? prev + 1 : 0
      );
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) =>
        prev > 0 ? prev - 1 : filteredCities.length - 1
      );
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < filteredCities.length) {
        handleSelect(filteredCities[selectedIndex]);
      } else if (filteredCities.length > 0) {
        handleSelect(filteredCities[0]);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      setSelectedIndex(-1);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    onSearchChange(val);
    setIsOpen(val.trim().length > 0);
    setSelectedIndex(-1);
  };

  return (
    <div ref={containerRef} className="relative w-full">
      <div className="relative flex items-center">
        <label htmlFor="location-search-input" className="sr-only">
          Search cities
        </label>
        <div className="absolute left-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
          <Search className="h-5 w-5" aria-hidden="true" />
        </div>

        <input
          ref={inputRef}
          id="location-search-input"
          type="text"
          value={searchTerm}
          onChange={handleChange}
          onFocus={() => {
            if (searchTerm.trim().length > 0) setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          role="combobox"
          aria-expanded={isOpen && filteredCities.length > 0}
          aria-autocomplete="list"
          aria-controls="location-suggestions-list"
          aria-activedescendant={
            selectedIndex >= 0 ? `suggestion-item-${selectedIndex}` : undefined
          }
          className="w-full pl-11 pr-10 py-3 text-sm font-medium bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 rounded-xl border border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 shadow-sm transition-colors"
        />

        {searchTerm && (
          <button
            type="button"
            onClick={handleClear}
            aria-label="Clear search query"
            className="absolute right-3 p-1 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* Dynamic Suggestions List */}
      <LocationSuggestions
        suggestions={filteredCities}
        searchTerm={searchTerm}
        selectedIndex={selectedIndex}
        onSelect={handleSelect}
        isOpen={isOpen}
      />
    </div>
  );
}
