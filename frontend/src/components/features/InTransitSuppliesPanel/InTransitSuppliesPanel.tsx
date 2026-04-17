import { useApi } from '../../../api';
import type { SuppliesInTransitResponse } from '../../../api/types';
import { InboxIcon } from '../../icons';
import styles from './InTransitSuppliesPanel.module.css';

interface InTransitSuppliesPanelProps {
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

export function InTransitSuppliesPanel({ shopId }: InTransitSuppliesPanelProps) {
  const { data, loading, error } = useApi<SuppliesInTransitResponse>(
    '/supplies/in-transit/',
    { shop: shopId }
  );

  if (loading) {
    return <div className={styles.skeleton} />;
  }

  return (
    <section className={styles.root} aria-labelledby="in-transit-supplies-title">
      <h2 id="in-transit-supplies-title" className={styles.title}>
        В&nbsp;пути:
      </h2>

      {error ? (
        <p className={styles.empty}>Не удалось загрузить: {error}</p>
      ) : !data || data.rows.length === 0 ? (
        <p className={styles.empty}>Сейчас ничего не в пути</p>
      ) : (
        <div className={styles.scroll}>
          <ul className={styles.list}>
            {data.rows.map((row) => (
              <li key={`${row.shop_id}-${row.dispatch_date}`} className={styles.item}>
                <span className={styles.icon} aria-hidden>
                  <InboxIcon size={20} />
                </span>
                <span className={styles.shopName}>{row.shop_name}</span>
                <span className={styles.dots} aria-hidden />
                <span className={styles.positions}>{positionsLabel(row.positions_count)}</span>
                <span className={styles.pill}>в пути</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
