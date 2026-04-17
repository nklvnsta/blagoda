import { useState } from 'react';
import { useApi } from '../../../api';
import { useDebouncedValue } from '../../../hooks';
import type { ProductSalesRow, SalesByProductsResponse } from '../../../api/types';
import styles from './SalesByProductsTable.module.css';
import tableStyles from '../SalesByShopsTable/DataTableWithSearch.module.css';
import {
  DataTableWithSearch,
  type DataTableColumn,
  type SortDirection,
} from '../SalesByShopsTable/DataTableWithSearch';

interface SalesByProductsTableProps {
  shopId?: string;
  categoryId?: string;
  periodCode?: string;
}

type SortField = 'product_name' | 'sold_qty';

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

export function SalesByProductsTable({
  shopId,
  categoryId,
  periodCode,
}: SalesByProductsTableProps) {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortField>('sold_qty');
  const [order, setOrder] = useState<SortDirection>('desc');

  const debouncedSearch = useDebouncedValue(search, 300);

  const { data, loading } = useApi<SalesByProductsResponse>('/sales/by-products/', {
    shop: shopId,
    category: categoryId,
    period: periodCode,
    search: debouncedSearch || undefined,
    sort,
    order,
  });

  const handleSortChange = (field: string, direction: SortDirection) => {
    if (field !== 'product_name' && field !== 'sold_qty') return;
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
        columns={PRODUCT_COLUMNS}
        rows={data?.rows ?? []}
        getRowKey={(row) => row.product_id}
        searchPlaceholder="Поиск по товару..."
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
            <h3 className={styles.title}>Продажи по товарам</h3>
            <span className={styles.subtitle}>{data?.period_label ?? ''}</span>
          </div>
        }
      />
    </div>
  );
}
