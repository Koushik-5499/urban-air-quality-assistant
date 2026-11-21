/**
 * Centralized Design Tokens for Urban Air Quality Assistant
 * Standardized across light & dark themes per Design System specifications.
 */

export const COLOR_TOKENS = {
  brand: {
    emerald: '#16A34A',
    darkEmerald: '#15803D',
    deepTeal: '#0F766E',
  },
  light: {
    background: '#F8FAFC',
    card: '#FFFFFF',
    cardElevated: '#FFFFFF',
    softGreen: '#F0FDF4',
    subtle: '#F1F5F9',
    textPrimary: '#111827',
    textSecondary: '#64748B',
    textMuted: '#94A3B8',
    border: '#E2E8F0',
  },
  dark: {
    background: '#0B0F19',
    card: '#131B2E',
    cardElevated: '#1A2338',
    softGreen: 'rgba(22, 163, 74, 0.15)',
    subtle: '#1A2338',
    textPrimary: '#F8FAFC',
    textSecondary: '#94A3B8',
    textMuted: '#64748B',
    border: '#1E293B',
  },
  aqi: {
    good: '#16A34A',
    moderate: '#EAB308',
    unhealthySensitive: '#F97316',
    unhealthy: '#DC2626',
    veryUnhealthy: '#9333EA',
    hazardous: '#7F1D1D',
  },
} as const;

export const SPACING_TOKENS = {
  1: '4px',
  2: '8px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
  8: '32px',
  10: '40px',
  12: '48px',
} as const;

export const TYPOGRAPHY_TOKENS = {
  fontFamily: {
    sans: "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    mono: "'JetBrains Mono', ui-monospace, SFMono-Regular, monospace",
  },
  fontSize: {
    xs: ['0.75rem', { lineHeight: '1rem' }],
    sm: ['0.875rem', { lineHeight: '1.25rem' }],
    base: ['1rem', { lineHeight: '1.5rem' }],
    lg: ['1.125rem', { lineHeight: '1.75rem' }],
    xl: ['1.25rem', { lineHeight: '1.75rem' }],
    '2xl': ['1.5rem', { lineHeight: '2rem' }],
    '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
  },
} as const;

export const RADIUS_TOKENS = {
  none: '0px',
  sm: '0.25rem',   // 4px
  md: '0.375rem',  // 6px
  lg: '0.5rem',    // 8px
  xl: '0.75rem',   // 12px
  '2xl': '1rem',   // 16px
  full: '9999px',
} as const;

export const SHADOW_TOKENS = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.08), 0 2px 4px -2px rgb(0 0 0 / 0.06)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.04)',
  card: '0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05)',
  elevated: '0 10px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
} as const;

export const TRANSITION_TOKENS = {
  fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
  normal: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
} as const;

export const Z_INDEX_TOKENS = {
  base: 0,
  dropdown: 10,
  sticky: 20,
  header: 40,
  mobileDrawer: 50,
  modalBackdrop: 60,
  modal: 70,
  tooltip: 80,
} as const;

export interface AQISemanticLevel {
  id: string;
  label: string;
  min: number;
  max: number;
  color: string;
  bgLight: string;
  textLight: string;
  bgDark: string;
  textDark: string;
  description: string;
}

export const AQI_LEVELS: Record<string, AQISemanticLevel> = {
  GOOD: {
    id: 'good',
    label: 'Good',
    min: 0,
    max: 50,
    color: COLOR_TOKENS.aqi.good,
    bgLight: 'bg-emerald-50 border-emerald-200',
    textLight: 'text-emerald-800',
    bgDark: 'dark:bg-emerald-950/60 dark:border-emerald-800/60',
    textDark: 'dark:text-emerald-300',
    description: 'Air quality is considered satisfactory, and air pollution poses little or no risk.',
  },
  MODERATE: {
    id: 'moderate',
    label: 'Moderate',
    min: 51,
    max: 100,
    color: COLOR_TOKENS.aqi.moderate,
    bgLight: 'bg-amber-50 border-amber-200',
    textLight: 'text-amber-800',
    bgDark: 'dark:bg-amber-950/60 dark:border-amber-800/60',
    textDark: 'dark:text-amber-300',
    description: 'Air quality is acceptable; however, some pollutants may be a moderate concern.',
  },
  UNHEALTHY_SENSITIVE: {
    id: 'unhealthy-sensitive',
    label: 'Unhealthy for Sensitive Groups',
    min: 101,
    max: 150,
    color: COLOR_TOKENS.aqi.unhealthySensitive,
    bgLight: 'bg-orange-50 border-orange-200',
    textLight: 'text-orange-800',
    bgDark: 'dark:bg-orange-950/60 dark:border-orange-800/60',
    textDark: 'dark:text-orange-300',
    description: 'Members of sensitive groups may experience health effects. General public not affected.',
  },
  UNHEALTHY: {
    id: 'unhealthy',
    label: 'Unhealthy',
    min: 151,
    max: 200,
    color: COLOR_TOKENS.aqi.unhealthy,
    bgLight: 'bg-red-50 border-red-200',
    textLight: 'text-red-800',
    bgDark: 'dark:bg-red-950/60 dark:border-red-800/60',
    textDark: 'dark:text-red-300',
    description: 'Everyone may begin to experience health effects; members of sensitive groups may experience more serious effects.',
  },
  VERY_UNHEALTHY: {
    id: 'very-unhealthy',
    label: 'Very Unhealthy',
    min: 201,
    max: 300,
    color: COLOR_TOKENS.aqi.veryUnhealthy,
    bgLight: 'bg-purple-50 border-purple-200',
    textLight: 'text-purple-800',
    bgDark: 'dark:bg-purple-950/60 dark:border-purple-800/60',
    textDark: 'dark:text-purple-300',
    description: 'Health alert: The risk of health effects is increased for everyone.',
  },
  HAZARDOUS: {
    id: 'hazardous',
    label: 'Hazardous',
    min: 301,
    max: 500,
    color: COLOR_TOKENS.aqi.hazardous,
    bgLight: 'bg-rose-950 border-rose-900',
    textLight: 'text-rose-100',
    bgDark: 'dark:bg-rose-950/90 dark:border-rose-900',
    textDark: 'dark:text-rose-200',
    description: 'Health warning of emergency conditions: Everyone is more likely to be affected.',
  },
};

