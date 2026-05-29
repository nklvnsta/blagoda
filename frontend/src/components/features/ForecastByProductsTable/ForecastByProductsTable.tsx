import { useState } from 'react';
import { buildFilterParams, useApi } from '../../../api';
import { useDebouncedValue } from '../../../hooks';
import type {
  ForecastProductRow,
  ForecastByProductsResponse,
} from '../../../api/types';
import styles from './ForecastByProductsTable.module.css';
import tableStyles from '../SalesByShopsTable/DataTableWithSearch.module.css';
import {
  DataTableWithSearch,
  type DataTableColumn,
  type SortDirection,
} from '../SalesByShopsTable/DataTableWithSearch';

interface ForecastByProductsTableProps {
  shopId?: string;
  categoryId?: string;
  periodCode?: string;
  dateFrom?: string;
  dateTo?: string;
}

type SortField = 'product_name' | 'forecast_qty' | 'previous_qty' | 'deviation_qty';

function formatNumber(value: number): string {
  return new Intl.NumberFormat('ru-RU').format(value);
}

function DeviationCell({ value }: { value: number }) {
  const cls =
    value > 0
      ? styles.deviationPositive
      : value < 0
        ? styles.deviationNegative
        : '';
  const prefix = value > 0 ? '+' : '';
  return <span className={cls}>{prefix}{formatNumber(value)}</span>;
}

const COLUMNS: DataTableColumn<ForecastProductRow>[] = [
  {
    id: 'product_name',
    header: 'Товар',
    className: tableStyles.tdShop,
    cell: (row) => row.product_name,
  },
  {
    id: 'forecast_qty',
    header: 'Прогноз продаж',
    className: tableStyles.tdRight,
    headerClassName: tableStyles.headerCellRight,
    sortable: true,
    cell: (row) => `${formatNumber(row.forecast_qty)} шт.`,
  },
  {
    id: 'previous_qty',
    header: 'Продажи (прошл.)',
    className: tableStyles.tdRight,
    headerClassName: tableStyles.headerCellRight,
    sortable: true,
    cell: (row) => `${formatNumber(row.previous_qty)} шт.`,
  },
  {
    id: 'deviation_qty',
    header: 'Отклонение',
    className: tableStyles.tdRight,
    headerClassName: tableStyles.headerCellRight,
    sortable: true,
    cell: (row) => <DeviationCell value={row.deviation_qty} />,
  },
];

export function ForecastByProductsTable({
  shopId,
  categoryId,
  periodCode,
  dateFrom,
  dateTo,
}: ForecastByProductsTableProps) {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortField>('forecast_qty');
  const [order, setOrder] = useState<SortDirection>('desc');

  const debouncedSearch = useDebouncedValue(search, 300);

  const { data, loading } = useApi<ForecastByProductsResponse>(
    '/forecast/by-products/',
    {
      ...buildFilterParams({ shopId, categoryId, periodCode, dateFrom, dateTo }),
      search: debouncedSearch || undefined,
      sort,
      order,
    }
  );

  const handleSortChange = (field: string, direction: SortDirection) => {
    if (
      field !== 'product_name' &&
      field !== 'forecast_qty' &&
      field !== 'previous_qty' &&
      field !== 'deviation_qty'
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
        columns={COLUMNS}
        rows={data?.rows ?? []}
        getRowKey={(row) => row.product_id}
        searchPlaceholder="Поиск по товару..."
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
            <h3 className={styles.title}>Прогноз по товарам</h3>
            <span className={styles.subtitle}>{data?.period_label ?? ''}</span>
          </div>
        }
      />
    </div>
  );
}
