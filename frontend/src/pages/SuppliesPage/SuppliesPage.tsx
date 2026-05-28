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
import { SuppliesTable } from '../../components/features/SuppliesTable';

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
  const [tableBump, setTableBump] = useState(0);

  const handleApply = (next: SuppliesFilterValues) => {
    setFilters(next);
    setPage(1);
  };

  const handleSortChange = (
    nextSort: SuppliesTableSort | null,
    nextOrder: SortDirection,
  ) => {
    setSort(nextSort);
    setOrder(nextOrder);
    setPage(1);
  };

  const handleStatusChange = (next: SupplyStatus | null) => {
    setStatusFilter(next);
    setPage(1);
  };

  const handleDispatched = () => {
    setTableBump((k) => k + 1);
  };

  const summary = useApi<SuppliesSummaryResponse>('/supplies/summary/', {
    shop: filters.shopId,
    date: filters.date,
    _: String(tableBump),
  });

  const table = useApi<SuppliesTableResponse>('/supplies/', {
    shop: filters.shopId,
    date: filters.date,
    page: String(page),
    status: statusFilter ?? undefined,
    sort: sort ?? undefined,
    order: sort ? order : undefined,
    _: String(tableBump),
  });

  return (
    <div className="page">
      <h2 className="heading">Поставки</h2>
      <SuppliesFilters initialDate={filters.date} onApply={handleApply} />

      <KPICardsRow>
        <StatCard
          title="К отгрузке"
          value={summary.data ? formatNumber(summary.data.to_dispatch_count) : '—'}
          unit="поставок"
          loading={summary.loading}
        />
        <StatCard
          title="На сумму"
          value={summary.data ? formatAmount(summary.data.to_dispatch_amount) : '—'}
          unit={summary.data?.currency ?? '₽'}
          loading={summary.loading}
        />
        <StatCard
          title="Отгружено"
          value={summary.data ? formatNumber(summary.data.shipped_count) : '—'}
          unit="поставок"
          loading={summary.loading}
        />
        <StatCard
          title="На сумму"
          value={summary.data ? formatAmount(summary.data.shipped_amount) : '—'}
          unit={summary.data?.currency ?? '₽'}
          loading={summary.loading}
        />
      </KPICardsRow>

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
        onDispatched={handleDispatched}
      />
    </div>
  );
}
