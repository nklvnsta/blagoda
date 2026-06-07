import { useEffect, useState } from 'react';
import { useApi } from '../../../api';
import { apiMutate } from '../../../api/mutate';
import type { SupplyItem, SupplyItemPatchPayload, SupplyItemsResponse, SupplyRow } from '../../../api/types';
import styles from './SupplyEditModal.module.css';

interface SupplyEditModalProps {
  row: SupplyRow | null;
  onClose: () => void;
  onSaved: () => void;
}

function formatCurrency(value: string | number): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

export function SupplyEditModal({ row, onClose, onSaved }: SupplyEditModalProps) {
  const [quantities, setQuantities] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const itemsUrl = row
    ? `/supplies/items/?shop_id=${row.shop_id}&dispatch_date=${row.dispatch_date}`
    : null;

  const { data, loading } = useApi<SupplyItemsResponse>(itemsUrl ?? '');

  useEffect(() => {
    if (data) {
      const initial: Record<string, string> = {};
      data.results.forEach((item) => {
        initial[item.id] = String(item.quantity_shipped);
      });
      setQuantities(initial);
      setErrors({});
    }
  }, [data]);

  useEffect(() => {
    if (!row) return;
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [row, onClose]);

  if (!row) return null;

  const handleQuantityChange = (id: string, value: string) => {
    setQuantities((prev) => ({ ...prev, [id]: value }));
    setErrors((prev) => { const next = { ...prev }; delete next[id]; return next; });
  };

  const handleSave = async (item: SupplyItem) => {
    const raw = quantities[item.id] ?? '';
    const qty = parseInt(raw, 10);
    if (!raw || isNaN(qty) || qty < 1) {
      setErrors((prev) => ({ ...prev, [item.id]: 'Введите целое число ≥ 1' }));
      return;
    }
    if (qty === item.quantity_shipped) return;

    setSaving(item.id);
    try {
      await apiMutate<SupplyItem, SupplyItemPatchPayload>(
        `/supplies/items/${item.id}/`,
        'PATCH',
        { quantity_shipped: qty },
      );
      onSaved();
    } catch (err) {
      setErrors((prev) => ({ ...prev, [item.id]: (err as Error).message }));
    } finally {
      setSaving(null);
    }
  };

  const editableCount = data?.results.filter((i) => i.editable).length ?? 0;

  return (
    <div className={styles.overlay} onClick={onClose} role="presentation">
      <div
        className={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.modalHeader}>
          <div>
            <h2 id="edit-modal-title" className={styles.title}>
              Редактирование поставки
            </h2>
            <p className={styles.subtitle}>
              {row.shop_name} · {new Date(row.dispatch_date).toLocaleDateString('ru-RU')}
            </p>
          </div>
          <button type="button" className={styles.closeBtn} onClick={onClose} aria-label="Закрыть">
            ✕
          </button>
        </div>

        {loading && <div className={styles.loadingBar} />}

        {!loading && data && (
          <>
            {editableCount === 0 && (
              <p className={styles.notice}>
                Позиции этой поставки нельзя редактировать — статус не «запланирована».
              </p>
            )}

            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th className={styles.thProduct}>Товар</th>
                    <th className={styles.thNum}>Ед.</th>
                    <th className={styles.thNum}>Кол-во</th>
                    <th className={styles.thNum}>Цена</th>
                    <th className={styles.thNum}>Сумма</th>
                    <th className={styles.thAction} />
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((item) => {
                    const qtyStr = quantities[item.id] ?? String(item.quantity_shipped);
                    const isBusy = saving === item.id;
                    const err    = errors[item.id];
                    const isDirty = parseInt(qtyStr, 10) !== item.quantity_shipped;

                    return (
                      <tr key={item.id} className={item.editable ? '' : styles.rowReadonly}>
                        <td className={styles.tdProduct}>
                          <span className={styles.productName}>{item.product_name}</span>
                          <span className={styles.productSku}>{item.product_sku}</span>
                        </td>
                        <td className={styles.tdNum}>{item.unit}</td>
                        <td className={styles.tdNum}>
                          {item.editable ? (
                            <div className={styles.inputWrap}>
                              <input
                                className={`${styles.qtyInput} ${err ? styles.inputError : ''}`}
                                type="number"
                                min={1}
                                value={qtyStr}
                                onChange={(e) => handleQuantityChange(item.id, e.target.value)}
                                onKeyDown={(e) => { if (e.key === 'Enter') handleSave(item); }}
                                disabled={isBusy}
                              />
                              {err && <span className={styles.errorHint}>{err}</span>}
                            </div>
                          ) : (
                            <span>{item.quantity_shipped}</span>
                          )}
                        </td>
                        <td className={styles.tdNum}>{formatCurrency(item.price)}</td>
                        <td className={styles.tdNum}>
                          {formatCurrency(
                            item.editable && !isNaN(parseInt(qtyStr, 10))
                              ? parseFloat(item.price) * parseInt(qtyStr, 10)
                              : item.amount,
                          )}
                        </td>
                        <td className={styles.tdAction}>
                          {item.editable && (
                            <button
                              type="button"
                              className={`${styles.saveBtn} ${isDirty ? styles.saveBtnDirty : ''}`}
                              onClick={() => handleSave(item)}
                              disabled={isBusy || !isDirty}
                            >
                              {isBusy ? '…' : 'Сохранить'}
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}

        <div className={styles.footer}>
          <button type="button" className={styles.doneBtn} onClick={onClose}>
            Готово
          </button>
        </div>
      </div>
    </div>
  );
}
