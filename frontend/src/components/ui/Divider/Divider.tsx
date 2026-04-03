import styles from './Divider.module.css';

interface DividerProps {
  direction?: 'horizontal' | 'vertical';
  className?: string;
}

export function Divider({ direction = 'horizontal', className }: DividerProps) {
  return (
    <div
      role="separator"
      className={`${styles.divider} ${styles[direction]} ${className ?? ''}`}
    />
  );
}
