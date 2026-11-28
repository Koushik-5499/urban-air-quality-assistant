import React from 'react';
import type { BaseComponentProps, CardVariant } from '../../types/components';
import { cn } from '../../utils/cn';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement>, BaseComponentProps {
  variant?: CardVariant;
}

const cardVariantClasses: Record<CardVariant, string> = {
  standard:
    'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm',
  elevated:
    'bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-md hover:shadow-lg transition-shadow duration-200',
  interactive:
    'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-emerald-500/50 dark:hover:border-emerald-500/50 hover:shadow-md cursor-pointer transition-all duration-200 active:scale-[0.99]',
};

export function Card({
  className,
  variant = 'standard',
  children,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        'rounded-xl p-6 text-slate-900 dark:text-slate-100 transition-colors',
        cardVariantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, children, ...props }: CardProps) {
  return (
    <div className={cn('flex flex-col space-y-1.5 pb-4', className)} {...props}>
      {children}
    </div>
  );
}

export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  as?: 'h2' | 'h3' | 'h4';
}

export function CardTitle({
  as: Heading = 'h3',
  className,
  children,
  ...props
}: CardTitleProps) {
  return (
    <Heading
      className={cn(
        'text-lg font-semibold tracking-tight text-slate-900 dark:text-white',
        className
      )}
      {...props}
    >
      {children}
    </Heading>
  );
}

export function CardDescription({ className, children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn(
        'text-sm text-slate-600 dark:text-slate-300',
        className
      )}
      {...props}
    >
      {children}
    </p>
  );
}

export function CardContent({ className, children, ...props }: CardProps) {
  return (
    <div
      className={cn('pt-0 text-slate-700 dark:text-slate-300', className)}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardFooter({ className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'flex items-center pt-4 border-t border-slate-100 dark:border-slate-800/80',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
