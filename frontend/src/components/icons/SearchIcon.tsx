import type { IconProps } from './types';

export function SearchIcon({ size = 24, ...props }: IconProps) {
    return (
        <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
            <circle cx="8.5" cy="8.5" r="5.5" />
            <path d="M12.5 12.5l4 4" />
        </svg>
    );
}
