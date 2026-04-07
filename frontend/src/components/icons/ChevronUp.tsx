import type { IconProps } from './types';

export function ChevronUp({ size = 24, ...props }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
            <path d="M15 12.5L10 7.5L5 12.5" />
        </svg>
    );
}
