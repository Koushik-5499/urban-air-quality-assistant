import { useMemo } from 'react';
import type { AQICategory } from '../../types/dashboard';
import { Badge } from '../ui/Badge';

export interface AQIGaugeProps {
  aqi: number;
  category: AQICategory;
  className?: string;
}

export function AQIGauge({ aqi, category, className = '' }: AQIGaugeProps) {
  // Normalize AQI between 0 and 500
  const normalizedAQI = Math.min(Math.max(aqi, 0), 500);

  // Angle from 180 (left) to 0 (right) in radians
  const fraction = normalizedAQI / 500;
  const angleRad = Math.PI - fraction * Math.PI;

  // Gauge geometry
  const cx = 130;
  const cy = 130;
  const r = 90;

  // Needle tip coordinates
  const needleLength = 70;
  const needleX = cx + needleLength * Math.cos(angleRad);
  const needleY = cy - needleLength * Math.sin(angleRad);

  // Segment boundaries (values on 0-500 scale)
  const segments = useMemo(
    () => [
      { max: 50, color: '#16A34A', label: 'Good' },
      { max: 100, color: '#EAB308', label: 'Moderate' },
      { max: 150, color: '#F97316', label: 'Sensitive' },
      { max: 200, color: '#DC2626', label: 'Unhealthy' },
      { max: 300, color: '#9333EA', label: 'Very Unhealthy' },
      { max: 500, color: '#7F1D1D', label: 'Hazardous' },
    ],
    []
  );

  // Helper to calculate SVG arc path between two values (0-500)
  const createArc = (valStart: number, valEnd: number, radius: number) => {
    const aStart = Math.PI - (valStart / 500) * Math.PI;
    const aEnd = Math.PI - (valEnd / 500) * Math.PI;

    const x1 = cx + radius * Math.cos(aStart);
    const y1 = cy - radius * Math.sin(aStart);
    const x2 = cx + radius * Math.cos(aEnd);
    const y2 = cy - radius * Math.sin(aEnd);

    return `M ${x1} ${y1} A ${radius} ${radius} 0 0 1 ${x2} ${y2}`;
  };

  // Determine current badge variant
  const getBadgeVariant = (): 'success' | 'warning' | 'danger' => {
    if (aqi <= 50) return 'success';
    if (aqi <= 150) return 'warning';
    return 'danger';
  };

  return (
    <div
      className={`flex flex-col items-center justify-center ${className}`}
      role="img"
      aria-label={`Air Quality Index gauge showing ${aqi}, classified as ${category} on a 0 to 500 scale.`}
    >
      <div className="relative w-[260px] h-[155px]">
        <svg
          viewBox="0 0 260 155"
          className="w-full h-full overflow-visible"
          aria-hidden="true"
        >
          {/* Background Track Arc */}
          <path
            d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
            fill="none"
            stroke="currentColor"
            strokeWidth="16"
            className="text-slate-100 dark:text-slate-800"
            strokeLinecap="round"
          />

          {/* Segmented Color Arcs */}
          {segments.map((seg, idx) => {
            const prevMax = idx === 0 ? 0 : segments[idx - 1].max;
            return (
              <path
                key={seg.label}
                d={createArc(prevMax, seg.max, r)}
                fill="none"
                stroke={seg.color}
                strokeWidth="14"
                strokeLinecap="butt"
                opacity={0.9}
              />
            );
          })}

          {/* Inner tick marks & scale numbers */}
          <text
            x={cx - r + 4}
            y={cy + 18}
            className="text-[10px] font-semibold fill-slate-400 dark:fill-slate-500"
            textAnchor="middle"
          >
            0
          </text>
          <text
            x={cx}
            y={cy - r - 6}
            className="text-[10px] font-semibold fill-slate-400 dark:fill-slate-500"
            textAnchor="middle"
          >
            250
          </text>
          <text
            x={cx + r - 4}
            y={cy + 18}
            className="text-[10px] font-semibold fill-slate-400 dark:fill-slate-500"
            textAnchor="middle"
          >
            500
          </text>

          {/* Needle Indicator */}
          <line
            x1={cx}
            y1={cy}
            x2={needleX}
            y2={needleY}
            stroke="currentColor"
            strokeWidth="3.5"
            strokeLinecap="round"
            className="text-slate-800 dark:text-slate-100 transition-all duration-500 ease-out"
          />

          {/* Pivot Center Hub */}
          <circle
            cx={cx}
            cy={cy}
            r="7"
            className="fill-slate-900 dark:fill-white"
          />
          <circle
            cx={cx}
            cy={cy}
            r="3.5"
            className="fill-emerald-500"
          />
        </svg>

        {/* Center Display Overlay */}
        <div className="absolute inset-x-0 bottom-0 flex flex-col items-center justify-end text-center">
          <div className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-none">
            {aqi}
          </div>
          <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mt-1 uppercase tracking-wider">
            Air Quality Index
          </div>
        </div>
      </div>

      {/* Category Status Pill */}
      <div className="mt-2.5">
        <Badge variant={getBadgeVariant()} size="md" showDot>
          {category}
        </Badge>
      </div>
    </div>
  );
}
