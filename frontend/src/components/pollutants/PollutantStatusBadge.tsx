import { Badge } from '../ui/Badge';
import type { AQICategory } from '../../types/dashboard';

export interface PollutantStatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
  showDot?: boolean;
}

export function PollutantStatusBadge({
  status,
  size = 'sm',
  showDot = true,
}: PollutantStatusBadgeProps) {
  const getVariant = (st: string) => {
    const s = st.toLowerCase();
    if (s.includes('good')) return 'success';
    if (s.includes('moderate')) return 'warning';
    if (s.includes('sensitive') || s.includes('unhealthy')) return 'danger';
    if (s.includes('hazardous')) return 'danger';
    return 'default';
  };

  return (
    <Badge
      variant={getVariant(status) as 'success' | 'warning' | 'danger' | 'default'}
      size={size}
      showDot={showDot}
    >
      {status as AQICategory}
    </Badge>
  );
}
