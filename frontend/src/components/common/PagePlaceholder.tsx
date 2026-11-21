import type { LucideIcon } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { cn } from '../../utils/cn';

export interface PagePlaceholderProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  routePath?: string;
  className?: string;
}

export function PagePlaceholder({
  title,
  description,
  icon: Icon,
  routePath,
  className,
}: PagePlaceholderProps) {
  return (
    <div className={cn('max-w-5xl mx-auto space-y-6', className)}>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-3.5">
          {Icon && (
            <div className="p-2.5 rounded-xl bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60 shadow-sm">
              <Icon className="w-6 h-6" aria-hidden="true" />
            </div>
          )}
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {title}
              </h1>
              <Badge variant="success" size="sm" showDot>
                Active
              </Badge>
            </div>
            {routePath && (
              <p className="text-xs font-mono text-slate-500 dark:text-slate-400 mt-1">
                Route: {routePath}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="neutral" size="sm">
            Design System Phase 2
          </Badge>
        </div>
      </div>

      {/* Main Status Card */}
      <Card variant="standard">
        <CardHeader>
          <CardTitle>Architecture & Design Verification</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-xl border border-dashed border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/40 p-8 text-center space-y-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-950/70 text-emerald-600 dark:text-emerald-400">
              {Icon ? (
                <Icon className="h-6 w-6" aria-hidden="true" />
              ) : (
                <span className="text-lg font-bold">AQ</span>
              )}
            </div>

            <div className="space-y-1">
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                {title} Route Initialized
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
                This view inherits all design system tokens, typography scales, accessibility
                standards, and dual light/dark themes. Core feature logic and telemetry will be
                layered in future phases.
              </p>
            </div>

            <div className="inline-flex items-center gap-2 text-xs text-emerald-700 dark:text-emerald-400 font-medium bg-emerald-50 dark:bg-emerald-950/50 px-3 py-1.5 rounded-full border border-emerald-200 dark:border-emerald-800/60">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>Theme-Aware Design System Ready</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
