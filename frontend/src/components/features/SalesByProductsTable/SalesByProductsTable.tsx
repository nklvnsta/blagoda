import type { ProductSalesRow, SalesByProductsResponse } from '../../../api/types';
import styles from './SalesByProductsTable.module.css';
import tableStyles from '../SalesByShopsTable/DataTableWithSearch.module.css';
import {
  DataTableWithSearch,
  type DataTableColumn,
} from '../SalesByShopsTable/DataTableWithSearch';

interface SalesByProductsTableProps {
  data: SalesByProductsResponse | null;
  loading?: boolean;
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('ru-RU').format(value);
}

const PRODUCT_COLUMNS: DataTableColumn<ProductSalesRow>[] = [
  {
    id: 'product_name',
    header: 'Товар',
    className: tableStyles.tdShop,
    cell: (row) => row.product_name,
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
    id: 'category_name',
    header: 'Категория',
    headerClassName: tableStyles.headerCellRight,
    className: tableStyles.tdRight,
    cell: (row) => row.category_name,
  },
];

export function SalesByProductsTable({ data, loading }: SalesByProductsTableProps) {
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
        columns={PRODUCT_COLUMNS}
        rows={data.rows}
        getRowKey={(row) => row.product_id}
        getSearchText={(row) => row.product_name}
        searchPlaceholder="Поиск по товару..."
        footerRow={data.total}
        initialSortField="sold_qty"
        initialSortDirection="desc"
        toolbarClassName={styles.header}
        searchInputClassName={styles.searchInput}
        leading={
          <div>
            <h3 className={styles.title}>Продажи по товарам</h3>
            <span className={styles.subtitle}>
              {data.period_label}
            </span>
          </div>
        }
      />
    </div>
  );
}
