import { useState } from 'react';
import { buildFilterParams, useApi } from '../../../api';
import { useDebouncedValue } from '../../../hooks';
import type { SalesByShopsResponse, ShopSalesRow } from '../../../api/types';
import styles from './SalesByShopsTable.module.css';
import tableStyles from './DataTableWithSearch.module.css';
import {
  DataTableWithSearch,
  type DataTableColumn,
  type SortDirection,
} from './DataTableWithSearch';

interface SalesByShopsTableProps {
  categoryId?: string;
  periodCode?: string;
  dateFrom?: string;
  dateTo?: string;
}

type SortField = 'shop_name' | 'revenue' | 'sold_qty' | 'receipt_count';

function formatCurrency(value: string | number): string {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('ru-RU').format(value);
}

const SHOP_COLUMNS: DataTableColumn<ShopSalesRow>[] = [
  {
    id: 'shop_name',
    header: 'Магазин',
    className: tableStyles.tdShop,
    cell: (row) => row.shop_name,
  },
  {
    id: 'revenue',
    header: 'Выручка',
    className: tableStyles.tdRight,
    sortable: true,
    cell: (row) => formatCurrency(row.revenue),
    footerCell: (row) => <strong>{formatCurrency(row.revenue)}</strong>,
  },
  {
    id: 'sold_qty',
    header: 'Продано, шт.',
    className: tableStyles.tdRight,
    sortable: true,
    cell: (row) => formatNumber(row.sold_qty),
    footerCell: (row) => <strong>{formatNumber(row.sold_qty)}</strong>,
  },
  {
    id: 'receipt_count',
    header: 'Количество чеков',
    className: tableStyles.tdRight,
    sortable: true,
    cell: (row) => formatNumber(row.receipt_count),
    footerCell: (row) => <strong>{formatNumber(row.receipt_count)}</strong>,
  },
];

export function SalesByShopsTable({ categoryId, periodCode, dateFrom, dateTo }: SalesByShopsTableProps) {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortField>('revenue');
  const [order, setOrder] = useState<SortDirection>('desc');

  const debouncedSearch = useDebouncedValue(search, 300);

  const { data, loading } = useApi<SalesByShopsResponse>('/sales/by-shops/', {
    ...buildFilterParams({ categoryId, periodCode, dateFrom, dateTo }),
    search: debouncedSearch || undefined,
    sort,
    order,
  });

  const handleSortChange = (field: string, direction: SortDirection) => {
    if (
      field !== 'shop_name' &&
      field !== 'revenue' &&
      field !== 'sold_qty' &&
      field !== 'receipt_count'
    )
      return;
    setSort(field);
    setOrder(direction);
  };

  if (loading && !data) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.skeleton} />
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      <DataTableWithSearch
        columns={SHOP_COLUMNS}
        rows={data?.rows ?? []}
        getRowKey={(row) => row.shop_id}
        searchPlaceholder="Поиск по магазину..."
        footerRow={data && data.rows.length > 0 ? data.total : undefined}
        toolbarClassName={styles.header}
        searchInputClassName={styles.searchInput}
        searchValue={search}
        onSearchChange={setSearch}
        sortField={sort}
        sortDirection={order}
        onSortChange={handleSortChange}
        emptyMessage={
          debouncedSearch
            ? 'Ничего не найдено по запросу'
            : 'Нет данных для отображения'
        }
        leading={
          <div>
            <h3 className={styles.title}>Продажи по магазинам</h3>
            <span className={styles.subtitle}>{data?.period_label ?? ''}</span>
          </div>
        }
      />
    </div>
  );
}
