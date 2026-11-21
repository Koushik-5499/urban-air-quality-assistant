import { Loader2 } from 'lucide-react';
import type { SpinnerSize, SpinnerVariant } from '../../types/components';
import { cn } from '../../utils/cn';

export interface LoadingSpinnerProps {
  size?: SpinnerSize;
  variant?: SpinnerVariant;
  className?: string;
  label?: string;
}

const sizeClasses: Record<SpinnerSize, string> = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
};

const variantClasses: Record<SpinnerVariant, string> = {
  emerald: 'text-emerald-600 dark:text-emerald-400',
  slate: 'text-slate-500 dark:text-slate-400',
  white: 'text-white',
};

export function LoadingSpinner({
  size = 'md',
  variant = 'emerald',
  className,
  label = 'Loading...',
}: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-label={label}
      className="inline-flex items-center justify-center gap-2"
    >
      <Loader2
        className={cn('animate-spin', sizeClasses[size], variantClasses[variant], className)}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
    </div>
  );
}
