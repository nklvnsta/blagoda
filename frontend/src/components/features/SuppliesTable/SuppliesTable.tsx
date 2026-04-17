import type {
  SuppliesTableResponse,
  SuppliesTableSort,
  SupplyRow,
  SupplyStatus,
} from '../../../api/types';
import styles from './SuppliesTable.module.css';
import tableStyles from '../SalesByShopsTable/DataTableWithSearch.module.css';
import {
  DataTableWithSearch,
  type DataTableColumn,
  type SortDirection,
} from '../SalesByShopsTable/DataTableWithSearch';
import { FilterDropdown } from '../FilterDropdown';

interface SuppliesTableProps {
  data: SuppliesTableResponse | null;
  loading?: boolean;
  page: number;
  onPageChange: (next: number) => void;
  sort: SuppliesTableSort | null;
  order: SortDirection;
  onSortChange: (sort: SuppliesTableSort | null, order: SortDirection) => void;
  status: SupplyStatus | null;
  onStatusChange: (status: SupplyStatus | null) => void;
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

const STATUS_LABELS: Record<SupplyStatus, string> = {
  scheduled: 'запланирована',
  in_transit: 'в пути',
  delivered: 'доставлена',
  cancelled: 'отменена',
};

const ALL_STATUSES_VALUE = 'all';
const STATUS_FILTER_OPTIONS: { label: string; value: string }[] = [
  { label: 'Все статусы', value: ALL_STATUSES_VALUE },
  { label: 'Запланирована', value: 'scheduled' },
  { label: 'В пути', value: 'in_transit' },
  { label: 'Доставлена', value: 'delivered' },
];

function StatusPill({ status }: { status: SupplyStatus }) {
  const cls = [
    styles.pill,
    status === 'in_transit' && styles.pillInTransit,
    status === 'delivered' && styles.pillDelivered,
    status === 'scheduled' && styles.pillScheduled,
    status === 'cancelled' && styles.pillCancelled,
  ]
    .filter(Boolean)
    .join(' ');
  return <span className={cls}>{STATUS_LABELS[status]}</span>;
}

const COLUMNS: DataTableColumn<SupplyRow>[] = [
  {
    id: 'shop_name',
    header: 'Магазин',
    className: tableStyles.tdShop,
    cell: (row) => row.shop_name,
  },
  {
    id: 'positions_count',
    header: 'Позиций',
    className: tableStyles.tdRight,
    sortable: true,
    cell: (row) => formatNumber(row.positions_count),
  },
  {
    id: 'amount',
    header: 'Сумма',
    className: tableStyles.tdRight,
    sortable: true,
    cell: (row) => formatCurrency(row.amount),
  },
  {
    id: 'status',
    header: 'Статус',
    className: tableStyles.tdRight,
    cell: (row) => <StatusPill status={row.status} />,
  },
];

interface PaginationProps {
  page: number;
  hasPrev: boolean;
  hasNext: boolean;
  onPageChange: (next: number) => void;
}

function Pagination({ page, hasPrev, hasNext, onPageChange }: PaginationProps) {
  return (
    <div className={styles.paginator}>
      <button
        type="button"
        className={styles.pageButton}
        onClick={() => onPageChange(page - 1)}
        disabled={!hasPrev}
      >
        ‹ Назад
      </button>
      <span className={styles.pageNumber}>{page}</span>
      <button
        type="button"
        className={styles.pageButton}
        onClick={() => onPageChange(page + 1)}
        disabled={!hasNext}
      >
        Вперёд ›
      </button>
    </div>
  );
}

export function SuppliesTable({
  data,
  loading,
  page,
  onPageChange,
  sort,
  order,
  onSortChange,
  status,
  onStatusChange,
}: SuppliesTableProps) {
  const handleSortChange = (field: string, direction: SortDirection) => {
    if (field !== 'positions_count' && field !== 'amount') return;
    onSortChange(field, direction);
  };

  const handleStatusChange = (value: string) => {
    onStatusChange(value === ALL_STATUSES_VALUE ? null : (value as SupplyStatus));
  };

  const header = (
    <div className={styles.headerInner}>
      <div>
        <h3 className={styles.title}>Поставки</h3>
        {data && (
          <span className={styles.subtitle}>Всего: {formatNumber(data.count)}</span>
        )}
      </div>
      <FilterDropdown
        label="Статус"
        options={STATUS_FILTER_OPTIONS}
        value={status ?? ALL_STATUSES_VALUE}
        onChange={handleStatusChange}
      />
    </div>
  );

  if (loading && !data) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.header}>{header}</div>
        <div className={styles.skeleton} />
      </div>
    );
  }

  const rows = data?.results ?? [];
  const hasResults = rows.length > 0;

  return (
    <div className={styles.wrapper}>
      <DataTableWithSearch
        columns={COLUMNS}
        rows={rows}
        getRowKey={(row) => `${row.shop_id}-${row.dispatch_date}`}
        hideSearch
        toolbarClassName={styles.header}
        leading={header}
        sortField={sort ?? ''}
        sortDirection={order}
        onSortChange={handleSortChange}
        emptyMessage={
          status ? 'По выбранному статусу ничего не найдено' : 'Нет данных для отображения'
        }
        pagination={
          hasResults ? (
            <Pagination
              page={page}
              hasPrev={data?.previous !== null && data?.previous !== undefined}
              hasNext={data?.next !== null && data?.next !== undefined}
              onPageChange={onPageChange}
            />
          ) : undefined
        }
      />
    </div>
  );
}
