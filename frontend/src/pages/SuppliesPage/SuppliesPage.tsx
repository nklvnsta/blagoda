import { useState } from 'react';
import { useApi } from '../../api';
import type {
  SuppliesSummaryResponse,
  SuppliesTableResponse,
  SuppliesTableSort,
  SupplyStatus,
} from '../../api/types';
import type { SortDirection } from '../../components/features/SalesByShopsTable/DataTableWithSearch';
import { KPICardsRow } from '../../components/features/KPICardsRow';
import { StatCard } from '../../components/features/StatCard';
import {
  SuppliesFilters,
  type SuppliesFilterValues,
} from '../../components/features/SuppliesFilters';
import { ScheduledSuppliesPanel } from '../../components/features/ScheduledSuppliesPanel';
import { InTransitSuppliesPanel } from '../../components/features/InTransitSuppliesPanel';
import { SuppliesTable } from '../../components/features/SuppliesTable';
import styles from './SuppliesPage.module.css';

function toIsoDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function formatAmount(value: string | number | undefined): string {
  if (value === undefined) return '—';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (!Number.isFinite(num)) return '—';
  return new Intl.NumberFormat('ru-RU', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
}

function formatNumber(value: number | undefined): string {
  if (value === undefined) return '—';
  return new Intl.NumberFormat('ru-RU').format(value);
}

export function SuppliesPage() {
  const today = toIsoDate(new Date());
  const [filters, setFilters] = useState<SuppliesFilterValues>({
    shopId: undefined,
    date: today,
  });
  const [page, setPage] = useState<number>(1);
  const [sort, setSort] = useState<SuppliesTableSort | null>(null);
  const [order, setOrder] = useState<SortDirection>('desc');
  const [statusFilter, setStatusFilter] = useState<SupplyStatus | null>(null);

  const handleApply = (next: SuppliesFilterValues) => {
    setFilters(next);
    setPage(1);
  };

  const handleSortChange = (
    nextSort: SuppliesTableSort | null,
    nextOrder: SortDirection
  ) => {
    setSort(nextSort);
    setOrder(nextOrder);
    setPage(1);
  };

  const handleStatusChange = (next: SupplyStatus | null) => {
    setStatusFilter(next);
    setPage(1);
  };

  const summary = useApi<SuppliesSummaryResponse>('/supplies/summary/', {
    shop: filters.shopId,
    date: filters.date,
  });

  const table = useApi<SuppliesTableResponse>('/supplies/', {
    shop: filters.shopId,
    date: filters.date,
    page: String(page),
    status: statusFilter ?? undefined,
    sort: sort ?? undefined,
    order: sort ? order : undefined,
  });

  return (
    <div className="page">
      <h2 className="heading">Поставки</h2>
      <SuppliesFilters initialDate={filters.date} onApply={handleApply} />

      <KPICardsRow>
        <StatCard
          title="Отгружено сегодня"
          value={summary.data ? formatNumber(summary.data.shipped_qty_today) : '—'}
          unit={summary.data?.quantity_unit}
          loading={summary.loading}
        />
        <StatCard
          title="На сумму"
          value={summary.data ? formatAmount(summary.data.shipped_amount_today) : '—'}
          unit={summary.data?.currency ?? '₽'}
          loading={summary.loading}
        />
        <StatCard
          title="В пути"
          value={summary.data ? formatNumber(summary.data.in_transit_deliveries) : '—'}
          unit={summary.data && summary.data.in_transit_deliveries === 1 ? 'поставка' : 'поставок'}
          loading={summary.loading}
        />
        <StatCard
          title="К отгрузке завтра"
          value={summary.data ? formatNumber(summary.data.tomorrow_positions) : '—'}
          unit={summary.data?.quantity_unit}
          loading={summary.loading}
        />
      </KPICardsRow>

      <div className={styles.panelsRow}>
        <ScheduledSuppliesPanel shopId={filters.shopId} />
        <InTransitSuppliesPanel shopId={filters.shopId} />
      </div>

      <SuppliesTable
        data={table.data}
        loading={table.loading}
        page={page}
        onPageChange={setPage}
        sort={sort}
        order={order}
        onSortChange={handleSortChange}
        status={statusFilter}
        onStatusChange={handleStatusChange}
      />
    </div>
  );
}
