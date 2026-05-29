import type { IconProps } from './types';

export function ChartTrendIcon({ size = 48, ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <polyline points="23.5 22.5 1.5 22.5 1.5 0.5" />
      <polyline points="1.5 16.76 8.2 10.06 11.06 12.94 22.54 1.46" />
      <polyline points="17.76 1.46 22.54 1.46 22.54 6.24" />
      <line x1="7.24" y1="14.85" x2="7.24" y2="22.5" />
      <line x1="12.98" y1="16.76" x2="12.98" y2="22.5" />
      <line x1="18.72" y1="9.11" x2="18.72" y2="22.5" />
    </svg>
  );
}
