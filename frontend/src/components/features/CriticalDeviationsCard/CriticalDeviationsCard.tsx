import { useMemo } from 'react';
import { useApi } from '../../../api';
import type { CriticalStockItem } from '../../../api/types';
import { TargetIcon, ChevronRight } from '../../icons';
import styles from './CriticalDeviationsCard.module.css';

function pickTopByType(items: CriticalStockItem[], type: CriticalStockItem['deviation_type']) {
  return items
    .filter((i) => i.deviation_type === type)
    .sort((a, b) => b.deviation_qty - a.deviation_qty)[0];
}

interface RowProps {
  variant: 'deficit' | 'surplus';
  item: CriticalStockItem | undefined;
}

function DeviationRow({ variant, item }: RowProps) {
  const isDeficit = variant === 'deficit';
  const accentClass = isDeficit ? styles.accentDeficit : styles.accentSurplus;
  const headlineClass = isDeficit ? styles.headlineDeficit : styles.headlineSurplus;
  const iconColor = isDeficit ? 'var(--color-status-critical)' : 'var(--color-status-warning)';
  const headline = isDeficit
    ? `Дефицит ${item?.deviation_qty ?? '—'} шт. товара`
    : `Избыток ${item?.deviation_qty ?? '—'} шт. товара`;
  const subtitle = item ? `${item.product} — ${item.shop}` : 'Нет данных по сети';

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
        <button type="button" className={styles.action}>
          Перейти к списку
          <ChevronRight size={20} color="var(--color-icon-default)" />
        </button>
      </div>
    </div>
  );
}

export function CriticalDeviationsCard() {
  const { data, loading, error } = useApi<CriticalStockItem[]>('/dashboard/critical-stock/');

  const { deficit, surplus } = useMemo(() => {
    if (!data?.length) return { deficit: undefined, surplus: undefined };
    return {
      deficit: pickTopByType(data, 'deficit'),
      surplus: pickTopByType(data, 'surplus'),
    };
  }, [data]);

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
