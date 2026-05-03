import { useApi } from '../../../api';
import type { CriticalStockItem } from '../../../api/types';
import { TargetIcon } from '../../icons';
import styles from './CriticalDeviationsCard.module.css';

interface RowProps {
  variant: 'deficit' | 'surplus';
  item: CriticalStockItem | undefined;
}

function DeviationRow({ variant, item }: RowProps) {
  if (!item) return null;

  const isDeficit = variant === 'deficit';
  const accentClass = isDeficit ? styles.accentDeficit : styles.accentSurplus;
  const headlineClass = isDeficit ? styles.headlineDeficit : styles.headlineSurplus;
  const iconColor = isDeficit ? 'var(--color-status-critical)' : 'var(--color-status-warning)';
  const headline = isDeficit
    ? `Дефицит ${item.deviation_qty} шт. товара`
    : `Избыток ${item.deviation_qty} шт. товара`;
  const subtitle = `${item.product} — ${item.shop}`;

  return (
    <div className={styles.row}>
      <div className={styles.left}>
        <div className={`${styles.accent} ${accentClass}`} aria-hidden />
        <TargetIcon size={22} color={iconColor} />
      </div>
      <div className={styles.rowMain}>
        <div className={styles.textBlock}>
          <p className={`${styles.headline} ${headlineClass}`}>{headline}</p>
          <p className={styles.subtitle}>{subtitle}</p>
        </div>
      </div>
    </div>
  );
}

export function CriticalDeviationsCard() {
  const deficitQuery = useApi<CriticalStockItem[]>(
    '/dashboard/critical-stock/',
    { deviation_type: 'deficit', limit: '1' }
  );
  const surplusQuery = useApi<CriticalStockItem[]>(
    '/dashboard/critical-stock/',
    { deviation_type: 'surplus', limit: '1' }
  );

  const loading = deficitQuery.loading || surplusQuery.loading;
  const error = deficitQuery.error || surplusQuery.error;

  const deficit = deficitQuery.data?.[0];
  const surplus = surplusQuery.data?.[0];

  if (loading) {
    return <div className={styles.skeleton} />;
  }

  if (error) {
    return (
      <div className={styles.root}>
        <h2 className={styles.title}>Критические отклонения</h2>
        <p className={styles.empty}>Не удалось загрузить: {error}</p>
      </div>
    );
  }

  if (!deficit && !surplus) {
    return null;
  }

  return (
    <section className={styles.root} aria-labelledby="critical-deviations-title">
      <h2 id="critical-deviations-title" className={styles.title}>
        Критические отклонения
      </h2>
      <DeviationRow variant="deficit" item={deficit} />
      <DeviationRow variant="surplus" item={surplus} />
    </section>
  );
}
