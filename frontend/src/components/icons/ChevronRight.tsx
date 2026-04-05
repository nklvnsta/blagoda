import type { IconProps } from './types';

export function ChevronRight({ size = 24, color = 'currentColor', ...props }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" aria-hidden {...props}>
      <path
        d="M7.5 5L12.5 10L7.5 15"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
