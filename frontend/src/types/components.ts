import type { ReactNode } from 'react';

export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

export type CardVariant = 'standard' | 'elevated' | 'interactive';

export type BadgeVariant =
  | 'default'
  | 'neutral'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'aqi-good'
  | 'aqi-moderate'
  | 'aqi-unhealthy-sensitive'
  | 'aqi-unhealthy'
  | 'aqi-very-unhealthy'
  | 'aqi-hazardous';

export type BadgeSize = 'sm' | 'md';
export type SpinnerSize = 'sm' | 'md' | 'lg';
export type SpinnerVariant = 'emerald' | 'slate' | 'white';

export interface BaseComponentProps {
  className?: string;
  children?: ReactNode;
}
