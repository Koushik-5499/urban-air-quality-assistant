import React from 'react';
import type { BadgeSize, BadgeVariant, BaseComponentProps } from '../../types/components';
import { cn } from '../../utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, BaseComponentProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  showDot?: boolean;
}

const variantClasses: Record<BadgeVariant, { container: string; dot: string }> = {
  default: {
    container: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
    dot: 'bg-slate-400 dark:bg-slate-500',
  },
  neutral: {
    container: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
    dot: 'bg-slate-400 dark:bg-slate-500',
  },
  success: {
    container: 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/70 dark:text-emerald-300 dark:border-emerald-800/60',
    dot: 'bg-emerald-500',
  },
  warning: {
    container: 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/70 dark:text-amber-300 dark:border-amber-800/60',
    dot: 'bg-amber-500',
  },
  danger: {
    container: 'bg-rose-50 text-rose-800 border-rose-200 dark:bg-rose-950/70 dark:text-rose-300 dark:border-rose-800/60',
    dot: 'bg-rose-500',
  },
  info: {
    container: 'bg-teal-50 text-teal-800 border-teal-200 dark:bg-teal-950/70 dark:text-teal-300 dark:border-teal-800/60',
    dot: 'bg-teal-500',
  },
  'aqi-good': {
    container: 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-300 dark:border-emerald-800',
    dot: 'bg-[#16A34A]',
  },
  'aqi-moderate': {
    container: 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/80 dark:text-amber-300 dark:border-amber-800',
    dot: 'bg-[#EAB308]',
  },
  'aqi-unhealthy-sensitive': {
    container: 'bg-orange-50 text-orange-800 border-orange-200 dark:bg-orange-950/80 dark:text-orange-300 dark:border-orange-800',
    dot: 'bg-[#F97316]',
  },
  'aqi-unhealthy': {
    container: 'bg-red-50 text-red-800 border-red-200 dark:bg-red-950/80 dark:text-red-300 dark:border-red-800',
    dot: 'bg-[#DC2626]',
  },
  'aqi-very-unhealthy': {
    container: 'bg-purple-50 text-purple-800 border-purple-200 dark:bg-purple-950/80 dark:text-purple-300 dark:border-purple-800',
    dot: 'bg-[#9333EA]',
  },
  'aqi-hazardous': {
    container: 'bg-rose-950 text-rose-100 border-rose-900 dark:bg-rose-950 dark:text-rose-200 dark:border-rose-900',
    dot: 'bg-[#7F1D1D]',
  },
};

const sizeClasses: Record<BadgeSize, string> = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs font-semibold',
};

export function Badge({
  className,
  variant = 'default',
  size = 'sm',
  showDot = false,
  children,
  ...props
}: BadgeProps) {
  const currentVariant = variantClasses[variant] || variantClasses.default;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 font-medium rounded-full border tracking-wide select-none',
        currentVariant.container,
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {showDot && (
        <span
          className={cn('inline-block w-1.5 h-1.5 rounded-full shrink-0', currentVariant.dot)}
          aria-hidden="true"
        />
      )}
      <span>{children}</span>
    </span>
  );
}
