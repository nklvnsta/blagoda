import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { apiMutate, useApi } from '../../api';
import type {
  PickingBulkSavePayload,
  PickingBulkSaveResponse,
  PickingDetailResponse,
  PickingDispatchResponse,
  PickingItem,
  RowPickStatus,
} from '../../api/types';
import { Button } from '../../components/ui/Button';
import { PickStatusPill } from '../../components/features/PickStatusPill';
import styles from './PickingDetailPage.module.css';

function formatNumber(value: number): string {
  return new Intl.NumberFormat('ru-RU').format(value);
}

function deriveRowStatus(picked: number, ordered: number): RowPickStatus {
  if (picked <= 0) return 'not_started';
  if (picked >= ordered) return 'picked';
  return 'partial';
}

interface QuantityCounterProps {
  value: number;
  onChange: (next: number) => void;
  disabled?: boolean;
}

function QuantityCounter({ value, onChange, disabled }: QuantityCounterProps) {
  const handleDecrement = () => {
    if (disabled) return;
    onChange(Math.max(0, value - 1));
  };
  const handleIncrement = () => {
    if (disabled) return;
    onChange(value + 1);
  };
  const handleManual = (raw: string) => {
    if (disabled) return;
    if (raw === '') {
      onChange(0);
      return;
    }
    const parsed = Number.parseInt(raw, 10);
    if (Number.isFinite(parsed) && parsed >= 0) {
      onChange(parsed);
    }
  };

  return (
    <div className={styles.counter}>
      <button
        type="button"
        className={styles.counterButton}
        onClick={handleDecrement}
        disabled={disabled || value <= 0}
        aria-label="Уменьшить"
      >
        −
      </button>
      <input
        type="number"
        className={styles.counterInput}
        value={value}
        min={0}
        onChange={(e) => handleManual(e.target.value)}
        disabled={disabled}
      />
      <button
        type="button"
        className={styles.counterButton}
        onClick={handleIncrement}
        disabled={disabled}
        aria-label="Увеличить"
      >
        +
      </button>
    </div>
  );
}

function buildDraft(items: PickingItem[]): Record<string, number> {
  const next: Record<string, number> = {};
  for (const it of items) {
    next[it.id] = it.picked_quantity;
  }
  return next;
}

export function PickingDetailPage() {
  const { shopId } = useParams<{ shopId: string }>();
  const navigate = useNavigate();

  const [bumpKey, setBumpKey] = useState<number>(0);
  const [draft, setDraft] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState<boolean>(false);
  const [dispatching, setDispatching] = useState<boolean>(false);

  const { data, loading, error } = useApi<PickingDetailResponse>(
    shopId ? `/picking/${shopId}/` : '/picking/__missing__/',
    { _: String(bumpKey) },
  );

  useEffect(() => {
    if (data?.items) {
      setDraft(buildDraft(data.items));
    }
  }, [data?.shop.id, bumpKey]);

  const items = data?.items ?? [];
  const orderedTotal = data?.totals.ordered_units ?? 0;
  const pickedTotal = useMemo(() => {
    return items.reduce((acc, it) => acc + (draft[it.id] ?? it.picked_quantity), 0);
  }, [items, draft]);

  const buildPayload = (): PickingBulkSavePayload => ({
    items: items.map((it) => ({
      id: it.id,
      picked_quantity: draft[it.id] ?? it.picked_quantity,
    })),
  });

  const handleSave = async () => {
    if (!shopId) return;
    setSaving(true);
    try {
      await apiMutate<PickingBulkSaveResponse, PickingBulkSavePayload>(
        `/picking/${shopId}/save/`,
        'POST',
        buildPayload(),
      );
      setBumpKey((k) => k + 1);
    } catch (err) {
      window.alert(`Не удалось сохранить: ${(err as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleDispatch = async () => {
    if (!shopId) return;
    const ok = window.confirm(
      'Отправить собранное на выгрузку? Несобранные позиции будут отменены.',
    );
    if (!ok) return;

    setDispatching(true);
    try {
      await apiMutate<PickingBulkSaveResponse, PickingBulkSavePayload>(
        `/picking/${shopId}/save/`,
        'POST',
        buildPayload(),
      );
      await apiMutate<PickingDispatchResponse>(
        `/picking/${shopId}/dispatch/`,
        'POST',
        {},
      );
      navigate('/picking');
    } catch (err) {
      window.alert(`Не удалось отправить: ${(err as Error).message}`);
      setDispatching(false);
    }
  };

  const renderRemaining = (item: PickingItem) => {
    const picked = draft[item.id] ?? item.picked_quantity;
    const ordered = item.ordered_quantity;
    const status = deriveRowStatus(picked, ordered);
    if (status === 'picked') {
      return <PickStatusPill status="picked" />;
    }
    if (status === 'not_started') {
      return <PickStatusPill status="not_started" />;
    }
    return formatNumber(Math.max(0, ordered - picked));
  };

  if (loading && !data) {
    return (
      <div className="page">
        <div className={styles.headerRow}>
          <button
            type="button"
            className={styles.backButton}
            onClick={() => navigate(-1)}
          >
            ← Назад
          </button>
        </div>
        <div className={styles.card}>
          <div className={styles.skeleton} />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page">
        <div className={styles.headerRow}>
          <button
            type="button"
            className={styles.backButton}
            onClick={() => navigate('/picking')}
          >
            ← К списку
          </button>
        </div>
        <div className={styles.card}>
          <p className={styles.error}>
            {error
              ? 'Для этого магазина нет сборки на сегодня'
              : 'Данные не найдены'}
          </p>
        </div>
      </div>
    );
  }

  const busy = saving || dispatching;

  return (
    <div className="page">
      <div className={styles.headerRow}>
        <button
          type="button"
          className={styles.backButton}
          onClick={() => navigate(-1)}
        >
          ← Назад
        </button>
        <h2 className={styles.title}>{data.shop.name}</h2>
      </div>

      <div className={styles.card}>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.colNo}>№</th>
                <th className={styles.colProduct}>Товар</th>
                <th className={styles.colRight}>Заказано</th>
                <th className={styles.colCenter}>Собрано</th>
                <th className={styles.colRight}>Остаток</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={5} className={styles.error}>
                    Нет позиций к сборке
                  </td>
                </tr>
              ) : (
                items.map((item) => {
                  const picked = draft[item.id] ?? item.picked_quantity;
                  return (
                    <tr key={item.id}>
                      <td className={styles.colNo}>{item.position_no}</td>
                      <td className={styles.colProduct}>{item.product_name}</td>
                      <td className={styles.colRight}>
                        {formatNumber(item.ordered_quantity)}
                        {item.unit ? ` ${item.unit}` : ''}
                      </td>
                      <td className={styles.colCenter}>
                        <QuantityCounter
                          value={picked}
                          onChange={(next) =>
                            setDraft((prev) => ({ ...prev, [item.id]: next }))
                          }
                          disabled={busy}
                        />
                      </td>
                      <td className={styles.colRight}>{renderRemaining(item)}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className={styles.footerActions}>
          <span className={styles.footerSummary}>
            Итого собрано:{' '}
            <strong>
              {formatNumber(pickedTotal)} / {formatNumber(orderedTotal)}
            </strong>
          </span>
          <div className={styles.footerButtons}>
            <Button type="secondary" onClick={handleSave}>
              {saving ? 'Сохранение…' : 'Сохранить'}
            </Button>
            <Button type="primary" onClick={handleDispatch}>
              {dispatching ? 'Отправка…' : 'Отправить на выгрузку'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
