import styles from './StatCard.module.css';

interface StatCardProps {
  icon?: React.ReactNode;
  title: string;
  title_additional?: string;
  value: string;
  unit?: string;
  changePct?: number | null;
  footer_additional?: string;
  loading?: boolean;
}
  
export function StatCard({ icon, title, title_additional, value, unit, changePct, footer_additional, loading }: StatCardProps) {
  if (loading) {
    return <div className={styles.skeleton} />;
  }

  const changeClass =
    changePct === null || changePct === undefined || changePct === 0
      ? styles.neutral
      : changePct > 0
        ? styles.negative
        : styles.positive;

  const changeText =
    changePct === null || changePct === undefined
      ? null
      : `${changePct > 0 ? '+' : ''}${changePct}%`;

  return (
    <div className={styles.card}>
      <div className={styles.header}> 
        {icon && <span className={styles.icon}>{icon}</span>}
        <span className={styles.title}>{title}</span>
        {title_additional && <span className={styles.title_additional}>{title_additional}</span>}
      </div>
      <div className={styles.footer}>
        <span className={styles.value}>
          {value}{unit ? ` ${unit}` : ''}
        </span>
        {changeText && <span className={`${styles.change} ${changeClass}`}>{changeText}</span>}
        {footer_additional && <span className={styles.footer_additional}>{footer_additional}</span>}
      </div>
    </div>
  );
}
