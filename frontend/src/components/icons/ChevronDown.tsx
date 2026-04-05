import type { IconProps } from './types';

export function ChevronDown({ size = 24, ...props }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
            <path d="M5 7.5L10 12.5L15 7.5" />
        </svg>
    );
}