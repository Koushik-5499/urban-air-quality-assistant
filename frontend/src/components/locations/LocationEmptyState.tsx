import { SearchX, RotateCcw } from 'lucide-react';
import { Button } from '../ui/Button';

export interface LocationEmptyStateProps {
  query?: string;
  onReset?: () => void;
  message?: string;
}

export function LocationEmptyState({
  query,
  onReset,
  message,
}: LocationEmptyStateProps) {
  return (
    <div
      role="status"
      className="rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/40 p-8 text-center space-y-3"
    >
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500">
        <SearchX className="h-6 w-6" aria-hidden="true" />
      </div>
      <div>
        <h3 className="text-base font-semibold text-slate-800 dark:text-slate-200">
          No demonstration locations found
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
          {message ||
            (query
              ? `No cities matching "${query}" were found in the current demonstration telemetry index.`
              : 'Try searching for an Indian city, state, or regional node.')}
        </p>
      </div>
      {onReset && (
        <Button variant="outline" size="sm" onClick={onReset} className="mt-2">
          <RotateCcw className="w-3.5 h-3.5 mr-1.5" aria-hidden="true" />
          Reset Search Filters
        </Button>
      )}
    </div>
  );
}

