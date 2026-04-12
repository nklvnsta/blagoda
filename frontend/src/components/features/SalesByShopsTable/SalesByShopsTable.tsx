import type { SalesByShopsResponse, ShopSalesRow } from '../../../api/types';
import styles from './SalesByShopsTable.module.css';
import tableStyles from './DataTableWithSearch.module.css';
import { DataTableWithSearch, type DataTableColumn } from './DataTableWithSearch';

interface SalesByShopsTableProps {
  data: SalesByShopsResponse | null;
  loading?: boolean;
}

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
    sortValue: (row) => parseFloat(row.revenue),
    cell: (row) => formatCurrency(row.revenue),
    footerCell: (row) => <strong>{formatCurrency(row.revenue)}</strong>,
  },
  {
    id: 'sold_qty',
    header: 'Продано, шт.',
    className: tableStyles.tdRight,
    sortable: true,
    sortValue: (row) => row.sold_qty,
    cell: (row) => formatNumber(row.sold_qty),
    footerCell: (row) => <strong>{formatNumber(row.sold_qty)}</strong>,
  },
  {
    id: 'receipt_count',
    header: 'Количество чеков',
    className: tableStyles.tdRight,
    sortable: true,
    sortValue: (row) => row.receipt_count,
    cell: (row) => formatNumber(row.receipt_count),
    footerCell: (row) => <strong>{formatNumber(row.receipt_count)}</strong>,
  },
];

export function SalesByShopsTable({ data, loading }: SalesByShopsTableProps) {
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
        columns={SHOP_COLUMNS}
        rows={data.rows}
        getRowKey={(row) => row.shop_id}
        getSearchText={(row) => row.shop_name}
        searchPlaceholder="Поиск по магазину..."
        footerRow={data.total}
        initialSortField="revenue"
        initialSortDirection="desc"
        toolbarClassName={styles.header}
        searchInputClassName={styles.searchInput}
        leading={
          <div>
            <h3 className={styles.title}>Продажи по магазинам</h3>
            <span className={styles.subtitle}>
              {data.period_label}
            </span>
          </div>
        }
      />
    </div>
  );
}
