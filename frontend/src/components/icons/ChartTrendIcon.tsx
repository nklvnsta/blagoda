import type { IconProps } from './types';

export function ChartTrendIcon({ size = 48, ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M8 36V20" />
      <path d="M20 36V12" />
      <path d="M32 36V24" />
      <path d="M44 36V8" />
      <path d="M6 14l14 10 10-8 16 12" />
    </svg>
  );
}
