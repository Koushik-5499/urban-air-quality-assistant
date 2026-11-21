import { Card } from '../ui/Card';

export function PollutantSkeleton() {
  return (
    <div className="space-y-6 animate-pulse" role="status" aria-label="Loading pollutant analytics">
      {/* Overview Skeleton */}
      <Card variant="standard" className="p-6">
        <div className="h-6 bg-slate-200 dark:bg-slate-800 rounded w-1/3 mb-4" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="h-16 bg-slate-200 dark:bg-slate-800 rounded" />
          <div className="h-16 bg-slate-200 dark:bg-slate-800 rounded" />
          <div className="h-16 bg-slate-200 dark:bg-slate-800 rounded" />
          <div className="h-16 bg-slate-200 dark:bg-slate-800 rounded" />
        </div>
      </Card>

      {/* Grid Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i} variant="standard" className="p-5 h-48">
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/2 mb-3" />
            <div className="h-8 bg-slate-200 dark:bg-slate-800 rounded w-1/3 mb-4" />
            <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-full mb-2" />
            <div className="h-3 bg-slate-200 dark:bg-slate-800 rounded w-2/3" />
          </Card>
        ))}
      </div>
    </div>
  );
}

