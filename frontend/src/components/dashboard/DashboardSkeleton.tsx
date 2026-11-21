import { Card } from '../ui/Card';

export function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse" role="status" aria-label="Loading air quality dashboard telemetry">
      {/* Top Banner Skeleton */}
      <div className="h-10 w-2/3 bg-slate-200 dark:bg-slate-800 rounded-lg"></div>

      {/* Main AQI Overview Skeleton */}
      <Card className="h-64 bg-slate-100 dark:bg-slate-800/60 border-slate-200 dark:border-slate-700/60">
        <div className="flex flex-col lg:flex-row gap-6 h-full items-center justify-around p-4">
          <div className="w-48 h-48 rounded-full bg-slate-200 dark:bg-slate-700/60"></div>
          <div className="flex-1 space-y-4 w-full">
            <div className="h-6 w-1/3 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-4 w-2/3 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-4 w-1/2 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-8 w-full bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        </div>
      </Card>

      {/* 6 Pollutants Skeleton Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="h-32 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 p-4 space-y-3"
          >
            <div className="h-4 w-1/2 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-8 w-3/4 bg-slate-200 dark:bg-slate-700 rounded"></div>
            <div className="h-3 w-full bg-slate-200 dark:bg-slate-700 rounded"></div>
          </div>
        ))}
      </div>

      {/* Middle Section: Chart & Health Recommendation */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8 h-80 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 p-6 space-y-4">
          <div className="h-6 w-1/4 bg-slate-200 dark:bg-slate-700 rounded"></div>
          <div className="h-56 w-full bg-slate-200 dark:bg-slate-700 rounded"></div>
        </div>
        <div className="lg:col-span-4 h-80 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 p-6 space-y-3">
          <div className="h-6 w-1/2 bg-slate-200 dark:bg-slate-700 rounded"></div>
          <div className="h-20 w-full bg-slate-200 dark:bg-slate-700 rounded"></div>
          <div className="h-20 w-full bg-slate-200 dark:bg-slate-700 rounded"></div>
        </div>
      </div>
      <span className="sr-only">Refreshing dashboard telemetry...</span>
    </div>
  );
}

