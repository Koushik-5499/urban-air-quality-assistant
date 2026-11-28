import { Layers, Plus } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import type { CityDashboardData } from '../../types/dashboard';

export interface ComparisonEmptyStateProps {
  availableCities: CityDashboardData[];
  onAddCity: (cityId: string) => void;
}

export function ComparisonEmptyState({ availableCities, onAddCity }: ComparisonEmptyStateProps) {
  return (
    <Card variant="standard" className="p-8 text-center space-y-3">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
        <Layers className="h-6 w-6" aria-hidden="true" />
      </div>
      <div>
        <h3 className="text-base font-semibold text-slate-900 dark:text-white">
          No Cities Selected for Cross-Comparison
        </h3>
        <p className="text-xs text-slate-600 dark:text-slate-300 max-w-sm mx-auto mt-1">
          Select up to 4 cities below to analyze atmospheric variations, particulate loads, and telemetry side by side.
        </p>
      </div>
      {availableCities.length > 0 && (
        <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
          {availableCities.slice(0, 4).map((c) => (
            <Button
              key={c.location.id}
              variant="outline"
              size="sm"
              onClick={() => onAddCity(c.location.id)}
              className="text-xs min-h-[44px]"
            >
              <Plus className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
              Add {c.location.city}
            </Button>
          ))}
        </div>
      )}
    </Card>
  );
}

