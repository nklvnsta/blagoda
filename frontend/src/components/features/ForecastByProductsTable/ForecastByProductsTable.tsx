import type { ForecastProductRow, ForecastByProductsResponse } from '../../../api/types';
import styles from './ForecastByProductsTable.module.css';
import tableStyles from '../SalesByShopsTable/DataTableWithSearch.module.css';
import {
  DataTableWithSearch,
  type DataTableColumn,
} from '../SalesByShopsTable/DataTableWithSearch';

interface ForecastByProductsTableProps {
  data: ForecastByProductsResponse | null;
  loading?: boolean;
}

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
    sortValue: (row) => row.forecast_qty,
    cell: (row) => `${formatNumber(row.forecast_qty)} шт.`,
  },
  {
    id: 'previous_qty',
    header: 'Продажи (прошл.)',
    className: tableStyles.tdRight,
    headerClassName: tableStyles.headerCellRight,
    sortable: true,
    sortValue: (row) => row.previous_qty,
    cell: (row) => `${formatNumber(row.previous_qty)} шт.`,
  },
  {
    id: 'deviation_qty',
    header: 'Отклонение',
    className: tableStyles.tdRight,
    headerClassName: tableStyles.headerCellRight,
    sortable: true,
    sortValue: (row) => row.deviation_qty,
    cell: (row) => <DeviationCell value={row.deviation_qty} />,
  },
];

export function ForecastByProductsTable({ data, loading }: ForecastByProductsTableProps) {
  if (loading) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.skeleton} />
      </div>
    );
  }

  if (!data || data.rows.length === 0) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.empty}>Нет данных для отображения</div>
      </div>
    );
  }

  return (
    <div className={styles.wrapper}>
      <DataTableWithSearch
        columns={COLUMNS}
        rows={data.rows}
        getRowKey={(row) => row.product_id}
        getSearchText={(row) => row.product_name}
        searchPlaceholder="Поиск по товару..."
        initialSortField="forecast_qty"
        initialSortDirection="desc"
        toolbarClassName={styles.header}
        searchInputClassName={styles.searchInput}
        leading={
          <div>
            <h3 className={styles.title}>Прогноз по товарам</h3>
            <span className={styles.subtitle}>
              {data.period_label}
            </span>
          </div>
        }
      />
    </div>
  );
}
