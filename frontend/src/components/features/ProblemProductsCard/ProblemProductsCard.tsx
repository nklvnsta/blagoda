import { useMemo } from 'react';
import { useApi } from '../../../api';
import type { ProblemProductItem } from '../../../api/types';
import styles from './ProblemProductsCard.module.css';

const PREVIEW_COUNT = 3;

function shopsLabel(count: number): string {
  const n = Math.abs(count);
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return `В ${count} магазине`;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return `В ${count} магазинах`;
  }
  return `В ${count} магазинах`;
}

export function ProblemProductsCard() {
  const { data, loading, error } = useApi<ProblemProductItem[]>('/dashboard/problem-products/');

  const items = useMemo(() => (data?.length ? data.slice(0, PREVIEW_COUNT) : []), [data]);

  if (loading) {
    return <div className={styles.skeleton} />;
  }

  if (error) {
    return (
      <section className={styles.root} aria-labelledby="problem-products-title">
        <h2 id="problem-products-title" className={styles.title}>
          Проблемные товары:
        </h2>
        <p className={styles.empty}>Не удалось загрузить: {error}</p>
      </section>
    );
  }

  return (
    <section className={styles.root} aria-labelledby="problem-products-title">
      <h2 id="problem-products-title" className={styles.title}>
        Проблемные товары:
      </h2>

      {items.length === 0 ? (
        <p className={styles.empty}>Сейчас нет проблемных товаров по выбранным правилам</p>
      ) : (
        <ul className={styles.list}>
          {items.map((item) => (
            <li key={item.product_id} className={styles.item}>
              <span className={styles.bullet} aria-hidden />
              <div className={styles.text}>
                <span className={styles.productName}>{item.product}</span>
                <span className={styles.shopLine}>{shopsLabel(item.affected_shops)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}

      <button type="button" className={styles.moreLink}>
        Подробнее
      </button>
    </section>
  );
}
