import { MapPin } from 'lucide-react';
import { Badge } from '../ui/Badge';
import type { CityDashboardData } from '../../types/dashboard';

export interface LocationSuggestionsProps {
  suggestions: CityDashboardData[];
  searchTerm: string;
  selectedIndex: number;
  onSelect: (city: CityDashboardData) => void;
  isOpen: boolean;
}

// Helper to highlight matching text
function HighlightMatch({ text, query }: { text: string; query: string }) {
  if (!query.trim()) return <span>{text}</span>;

  const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const regex = new RegExp(`(${escaped})`, 'gi');
  const parts = text.split(regex);

  return (
    <span>
      {parts.map((part, i) =>
        regex.test(part) ? (
          <mark
            key={i}
            className="bg-emerald-100 dark:bg-emerald-950/80 text-emerald-900 dark:text-emerald-200 font-semibold px-0.5 rounded"
          >
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </span>
  );
}

export function LocationSuggestions({
  suggestions,
  searchTerm,
  selectedIndex,
  onSelect,
  isOpen,
}: LocationSuggestionsProps) {
  if (!isOpen || suggestions.length === 0) return null;

  const getBadgeVariant = (category: string) => {
    switch (category) {
      case 'Good':
        return 'success';
      case 'Moderate':
        return 'warning';
      case 'Unhealthy for Sensitive Groups':
      case 'Unhealthy':
        return 'danger';
      default:
        return 'default';
    }
  };

  return (
    <ul
      id="location-suggestions-list"
      role="listbox"
      aria-label="Location suggestions"
      className="absolute top-full left-0 right-0 z-50 mt-1 max-h-64 overflow-y-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-1.5 shadow-xl transition-all"
    >
      {suggestions.map((cityData, index) => {
        const isSelected = index === selectedIndex;
        const { city, state, country } = cityData.location;

        return (
          <li
            key={cityData.location.id}
            id={`suggestion-item-${index}`}
            role="option"
            aria-selected={isSelected}
            onClick={() => onSelect(cityData)}
            onMouseEnter={() => {}}
            className={`flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-lg text-sm cursor-pointer transition-colors ${
              isSelected
                ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-950 dark:text-emerald-100 font-medium'
                : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-850'
            }`}
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <MapPin
                className={`w-4 h-4 shrink-0 ${
                  isSelected
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-slate-400 dark:text-slate-500'
                }`}
                aria-hidden="true"
              />
              <div className="truncate">
                <span className="font-semibold text-slate-900 dark:text-white">
                  <HighlightMatch text={city} query={searchTerm} />
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 ml-1.5">
                  <HighlightMatch text={`${state}, ${country}`} query={searchTerm} />
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs font-bold text-slate-900 dark:text-white">
                AQI {cityData.aqi}
              </span>
              <Badge variant={getBadgeVariant(cityData.category)} size="sm">
                {cityData.category}
              </Badge>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
