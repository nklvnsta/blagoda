import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../../../api';
import { useDebouncedValue } from '../../../hooks';
import type {
  GroupPickStatus,
  PickingShopRow,
  PickingTodayResponse,
  PickingTodaySort,
} from '../../../api/types';
import {
  DataTableWithSearch,
  type DataTableColumn,
  type SortDirection,
} from '../SalesByShopsTable/DataTableWithSearch';
import tableStyles from '../SalesByShopsTable/DataTableWithSearch.module.css';
import { FilterDropdown } from '../FilterDropdown';
import { PickStatusPill } from '../PickStatusPill';
import styles from './PickingTodayTable.module.css';

const ALL_STATUSES_VALUE = 'all';
const STATUS_FILTER_OPTIONS: { label: string; value: string }[] = [
  { label: 'Все статусы', value: ALL_STATUSES_VALUE },
  { label: 'Не начато', value: 'not_started' },
  { label: 'В сборке', value: 'in_progress' },
  { label: 'Частично', value: 'partial' },
  { label: 'Собрано', value: 'picked' },
];

const SORT_FIELDS: PickingTodaySort[] = [
  'shop_name',
  'positions_count',
  'ordered_units',
  'picked_units',
];

function isPickingSort(field: string): field is PickingTodaySort {
  return (SORT_FIELDS as string[]).includes(field);
}

function isGroupPickStatus(value: string): value is GroupPickStatus {
  return (
    value === 'not_started' ||
    value === 'in_progress' ||
    value === 'partial' ||
    value === 'picked'
  );
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat('ru-RU').format(value);
}

export function PickingTodayTable() {
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<PickingTodaySort>('shop_name');
  const [order, setOrder] = useState<SortDirection>('asc');
  const [statusFilter, setStatusFilter] = useState<GroupPickStatus | null>(null);
  const [page, setPage] = useState<number>(1);

  const debouncedSearch = useDebouncedValue(search, 300);

  const { data, loading } = useApi<PickingTodayResponse>('/picking/today/', {
    search: debouncedSearch || undefined,
    sort,
    order,
    status: statusFilter ?? undefined,
    page: String(page),
  });

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  const handleSortChange = (field: string, direction: SortDirection) => {
    if (!isPickingSort(field)) return;
    setSort(field);
    setOrder(direction);
    setPage(1);
  };

  const handleStatusChange = (value: string) => {
    const next = value === ALL_STATUSES_VALUE || !isGroupPickStatus(value) ? null : value;
    setStatusFilter(next);
    setPage(1);
  };

  const COLUMNS: DataTableColumn<PickingShopRow>[] = [
    {
      id: 'shop_name',
      header: 'Магазин',
      className: tableStyles.tdShop,
      sortable: true,
      cell: (row) => row.shop_name,
    },
    {
      id: 'positions_count',
      header: 'Позиции',
      className: tableStyles.tdRight,
      sortable: true,
      cell: (row) => formatNumber(row.positions_count),
    },
    {
      id: 'ordered_units',
      header: 'Ед. в заказе',
      className: tableStyles.tdRight,
      sortable: true,
      cell: (row) => formatNumber(row.ordered_units),
    },
    {
      id: 'pick_status',
      header: 'Статус',
      className: tableStyles.tdRight,
      cell: (row) => <PickStatusPill status={row.pick_status} />,
    },
    {
      id: 'action',
      header: '',
      className: tableStyles.tdRight,
      cell: (row) => {
        const isStart = row.pick_status === 'not_started';
        const cls = [
          styles.actionButton,
          !isStart && styles.actionButtonSecondary,
        ]
          .filter(Boolean)
          .join(' ');
        return (
          <button
            type="button"
            className={cls}
            onClick={() => navigate(`/picking/${row.shop_id}`)}
          >
            {isStart ? 'Начать сборку' : 'Открыть сборку'}
          </button>
        );
      },
    },
  ];

  const header = (
    <div className={styles.headerInner}>
      <div className={styles.headerLeft}>
        <h3 className={styles.title}>Поставки на сегодня</h3>
      </div>
      <div className={styles.headerRight}>
        <FilterDropdown
          label="Статус"
          options={STATUS_FILTER_OPTIONS}
          value={statusFilter ?? ALL_STATUSES_VALUE}
          onChange={handleStatusChange}
        />
      </div>
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
  const hasPrev = data?.previous !== null && data?.previous !== undefined;
  const hasNext = data?.next !== null && data?.next !== undefined;

  let emptyMessage = 'Сегодня нет магазинов к сборке';
  if (debouncedSearch) {
    emptyMessage = 'Ничего не найдено по запросу';
  } else if (statusFilter) {
    emptyMessage = 'По выбранному статусу ничего не найдено';
  }

  return (
    <div className={styles.wrapper}>
      <DataTableWithSearch
        columns={COLUMNS}
        rows={rows}
        getRowKey={(row) => row.shop_id}
        searchPlaceholder="Поиск по магазину..."
        searchValue={search}
        onSearchChange={handleSearchChange}
        searchInputClassName={styles.searchInput}
        toolbarClassName={styles.header}
        leading={header}
        sortField={sort}
        sortDirection={order}
        onSortChange={handleSortChange}
        emptyMessage={emptyMessage}
        pagination={
          hasResults && (hasPrev || hasNext) ? (
            <div className={styles.paginator}>
              <button
                type="button"
                className={styles.pageButton}
                onClick={() => setPage(page - 1)}
                disabled={!hasPrev}
              >
                ‹ Назад
              </button>
              <span className={styles.pageNumber}>{page}</span>
              <button
                type="button"
                className={styles.pageButton}
                onClick={() => setPage(page + 1)}
                disabled={!hasNext}
              >
                Вперёд ›
              </button>
            </div>
          ) : undefined
        }
      />
    </div>
  );
}
