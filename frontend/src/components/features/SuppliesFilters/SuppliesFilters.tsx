import { useState } from 'react';
import styles from './SuppliesFilters.module.css';

import { useApi } from '../../../api';
import { ChevronRight } from '../../icons';
import { FilterDropdown } from '../FilterDropdown';
import { Button } from '../../ui/Button';
import { Divider } from '../../ui/Divider';
import type { SuppliesFiltersResponse } from '../../../api/types';

export interface SuppliesFilterValues {
  shopId?: string;
  date: string;
}

interface SuppliesFiltersProps {
  initialDate?: string;
  onApply?: (filters: SuppliesFilterValues) => void;
}

const ALL_SHOPS_VALUE = 'all';

function toIsoDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function SuppliesFilters({ initialDate, onApply }: SuppliesFiltersProps) {
  const today = toIsoDate(new Date());
  const [selectedShop, setSelectedShop] = useState<string>(ALL_SHOPS_VALUE);
  const [selectedDate, setSelectedDate] = useState<string>(initialDate ?? today);

  const filters = useApi<SuppliesFiltersResponse>('/supplies/filters/');

  const shopOptions = filters.data
    ? [
        { label: 'Вся сеть', value: ALL_SHOPS_VALUE },
        ...filters.data.shops.map((s) => ({ label: s.name, value: s.id })),
      ]
    : [{ label: 'Вся сеть', value: ALL_SHOPS_VALUE }];

  const handleApply = () => {
    onApply?.({
      shopId: selectedShop !== ALL_SHOPS_VALUE ? selectedShop : undefined,
      date: selectedDate,
    });
  };

  const handleReset = () => {
    setSelectedShop(ALL_SHOPS_VALUE);
    setSelectedDate(today);
    onApply?.({ shopId: undefined, date: today });
  };

  return (
    <div className={styles.filters}>
      <div className={styles.options}>
        <FilterDropdown
          label="Магазин"
          options={shopOptions}
          value={selectedShop}
          onChange={setSelectedShop}
        />

        <label className={styles.dateControl}>
          <span className={styles.dateLabel}>Дата</span>
          <Divider direction="vertical" />
          <input
            type="date"
            className={styles.dateInput}
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            lang="ru"
          />
        </label>
      </div>

      <div className={styles.actions}>
        <Button type="secondary" onClick={handleReset}>
          Сбросить
        </Button>
        <Button onClick={handleApply} icon={<ChevronRight />}>
          Применить
        </Button>
      </div>
    </div>
  );
}
