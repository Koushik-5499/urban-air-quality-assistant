import { Card } from '../ui/Card';
import { SearchX } from 'lucide-react';
import { Button } from '../ui/Button';

export interface MapEmptyStateProps {
  onReset: () => void;
}

export function MapEmptyState({ onReset }: MapEmptyStateProps) {
  return (
    <Card variant="standard" className="p-8 text-center space-y-3">
      <div className="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
        <SearchX className="w-6 h-6" />
      </div>
      <div>
        <h3 className="text-base font-bold text-slate-900 dark:text-white">
          No Monitoring Stations Match Filters
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto mt-1">
          No Indian demonstration cities matched your current category or search criteria.
        </p>
      </div>
      <Button variant="outline" size="sm" onClick={onReset} className="text-xs">
        Reset Map Filters
      </Button>
    </Card>
  );
}

