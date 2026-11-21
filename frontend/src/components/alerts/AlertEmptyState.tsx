import { SearchX } from 'lucide-react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

export interface AlertEmptyStateProps {
  onResetFilters: () => void;
}

export function AlertEmptyState({ onResetFilters }: AlertEmptyStateProps) {
  return (
    <Card variant="standard" className="p-8 text-center space-y-3">
      <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
        <SearchX className="w-6 h-6" />
      </div>
      <div>
        <h3 className="text-base font-bold text-slate-900 dark:text-white">
          No Air Quality Alerts Match Filters
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto mt-1">
          No active atmospheric warnings or advisories match your current filter, severity, or search combination.
        </p>
      </div>
      <Button variant="outline" size="sm" onClick={onResetFilters} className="text-xs">
        Reset Alert Filters
      </Button>
    </Card>
  );
}

