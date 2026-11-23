import { Radio, Database } from 'lucide-react';
import { Badge } from '../ui/Badge';
import { useLocation } from '../../hooks/useLocation';

export interface DataProvenanceBadgeProps {
  className?: string;
  forceProvenance?: 'live' | 'demo';
}

export function DataProvenanceBadge({ className = '', forceProvenance }: DataProvenanceBadgeProps) {
  const { isLiveBackend, isSimulated } = useLocation();

  const isLive = forceProvenance ? forceProvenance === 'live' : isLiveBackend && !isSimulated;

  return (
    <div className={`inline-flex items-center gap-1.5 ${className}`}>
      {isLive ? (
        <Badge variant="success" size="sm" className="flex items-center gap-1.5 font-medium">
          <Database className="w-3 h-3 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
          <span>Live CPCB data</span>
        </Badge>
      ) : (
        <Badge variant="neutral" size="sm" className="flex items-center gap-1.5 font-medium text-slate-600 dark:text-slate-300">
          <Radio className="w-3 h-3 text-slate-500 animate-pulse" aria-hidden="true" />
          <span>Demo data (live CPCB unavailable)</span>
        </Badge>
      )}
    </div>
  );
}
