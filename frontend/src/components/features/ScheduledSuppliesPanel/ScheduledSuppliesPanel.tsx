import { useApi } from '../../../api';
import type { SuppliesScheduledResponse } from '../../../api/types';
import { InboxIcon } from '../../icons';
import styles from './ScheduledSuppliesPanel.module.css';

interface ScheduledSuppliesPanelProps {
  shopId?: string;
}

function positionsLabel(count: number): string {
  const n = Math.abs(count);
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return `${count} позиция`;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return `${count} позиции`;
  }
  return `${count} позиций`;
}

export function ScheduledSuppliesPanel({ shopId }: ScheduledSuppliesPanelProps) {
  const { data, loading, error } = useApi<SuppliesScheduledResponse>(
    '/supplies/scheduled/',
    { shop: shopId }
  );

  if (loading) {
    return <div className={styles.skeleton} />;
  }

  return (
    <section className={styles.root} aria-labelledby="scheduled-supplies-title">
      <h2 id="scheduled-supplies-title" className={styles.title}>
        К&nbsp;отгрузке&nbsp;завтра:
      </h2>

      {error ? (
        <p className={styles.empty}>Не удалось загрузить: {error}</p>
      ) : !data || data.rows.length === 0 ? (
        <p className={styles.empty}>Нет запланированных отгрузок на завтра</p>
      ) : (
        <div className={styles.scroll}>
          <ul className={styles.list}>
            {data.rows.map((row) => (
              <li key={row.shop_id} className={styles.item}>
                <span className={styles.icon} aria-hidden>
                  <InboxIcon size={20} />
                </span>
                <span className={styles.shopName}>{row.shop_name}</span>
                <span className={styles.dots} aria-hidden />
                <span className={styles.positions}>{positionsLabel(row.positions_count)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
