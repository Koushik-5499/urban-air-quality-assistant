import { AlertTriangle, AlertCircle, Info, Bell } from 'lucide-react';
import type { AlertSeverity } from '../../types/alerts';

export interface AlertSeverityBadgeProps {
  severity: AlertSeverity;
  size?: 'sm' | 'md';
}

export function AlertSeverityBadge({ severity, size = 'sm' }: AlertSeverityBadgeProps) {
  const getStyles = () => {
    switch (severity) {
      case 'severe':
      case 'critical':
        return {
          container:
            'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/70 dark:text-rose-300 dark:border-rose-900',
          dot: 'bg-rose-500',
          label: severity === 'severe' ? 'Severe Emergency' : 'Critical Alert',
          icon: AlertTriangle,
        };
      case 'warning':
        return {
          container:
            'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/70 dark:text-amber-300 dark:border-amber-900',
          dot: 'bg-amber-500',
          label: 'Health Warning',
          icon: AlertCircle,
        };
      case 'moderate':
        return {
          container:
            'bg-yellow-50 text-yellow-800 border-yellow-200 dark:bg-yellow-950/70 dark:text-yellow-300 dark:border-yellow-900',
          dot: 'bg-yellow-500',
          label: 'Moderate Advisory',
          icon: Info,
        };
      case 'info':
      default:
        return {
          container:
            'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/70 dark:text-emerald-300 dark:border-emerald-900',
          dot: 'bg-emerald-500',
          label: 'Clean Air Report',
          icon: Bell,
        };
    }
  };

  const { container, dot, label, icon: Icon } = getStyles();
  const padClass = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold border ${container} ${padClass}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dot} shrink-0 animate-pulse motion-reduce:animate-none`} />
      <Icon className="w-3 h-3" />
      <span>{label}</span>
    </span>
  );
}

