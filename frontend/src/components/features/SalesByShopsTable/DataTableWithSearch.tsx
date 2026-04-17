import { useMemo, useState, type ReactNode } from 'react';
import { ChevronDown, ChevronUp, SearchIcon } from '../../icons';
import { Input } from '../../ui/Input';
import styles from './DataTableWithSearch.module.css';

export type SortDirection = 'asc' | 'desc';

export interface DataTableColumn<T> {
  id: string;
  header: string;
  sortable?: boolean;
  sortValue?: (row: T) => number;
  cell: (row: T) => ReactNode;
  footerCell?: (row: T) => ReactNode;
  className?: string;
  headerClassName?: string;
}

export interface DataTableWithSearchProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  getRowKey: (row: T) => string;
  getSearchText?: (row: T) => string;
  searchPlaceholder?: string;
  leading?: ReactNode;
  footerRow?: T;
  initialSortField?: string;
  initialSortDirection?: SortDirection;
  toolbarClassName?: string;
  searchInputClassName?: string;
  hideSearch?: boolean;
  pagination?: ReactNode;
  /**
   * Controlled sort field. When provided together with onSortChange, internal
   * client-side sorting is disabled and the parent owns the sort state
   * (useful for server-side sorting).
   */
  sortField?: string;
  sortDirection?: SortDirection;
  onSortChange?: (field: string, direction: SortDirection) => void;
  /**
   * Controlled search value. When provided together with onSearchChange,
   * internal client-side filtering is disabled and the parent owns the
   * search state (useful for server-side search).
   */
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  /**
   * Message rendered inside the table body when there are no rows to show.
   * When set, keeps the toolbar (search/filters) and the thead visible
   * instead of unmounting the whole table.
   */
  emptyMessage?: string;
}

export function DataTableWithSearch<T>({
  columns,
  rows,
  getRowKey,
  getSearchText,
  searchPlaceholder = 'Поиск...',
  leading,
  footerRow,
  initialSortField = '',
  initialSortDirection = 'desc',
  toolbarClassName = styles.toolbar,
  searchInputClassName,
  hideSearch = false,
  pagination,
  sortField: controlledSortField,
  sortDirection: controlledSortDirection,
  onSortChange,
  searchValue: controlledSearchValue,
  onSearchChange,
  emptyMessage,
}: DataTableWithSearchProps<T>) {
  const isSortControlled = onSortChange !== undefined;
  const isSearchControlled = onSearchChange !== undefined;

  const [internalSortField, setInternalSortField] = useState<string>(initialSortField);
  const [internalSortDirection, setInternalSortDirection] =
    useState<SortDirection>(initialSortDirection);
  const [internalSearchQuery, setInternalSearchQuery] = useState('');

  const searchQuery = isSearchControlled
    ? (controlledSearchValue ?? '')
    : internalSearchQuery;
  const handleSearchChange = (value: string) => {
    if (isSearchControlled) {
      onSearchChange?.(value);
    } else {
      setInternalSearchQuery(value);
    }
  };

  const sortField = isSortControlled ? (controlledSortField ?? '') : internalSortField;
  const sortDirection = isSortControlled
    ? (controlledSortDirection ?? 'desc')
    : internalSortDirection;

  const sortableColumn = useMemo(
    () => columns.find((c) => c.id === sortField && c.sortable && c.sortValue),
    [columns, sortField]
  );

  const displayedRows = useMemo(() => {
    let list = rows;
    // In controlled search mode the server has already filtered rows.
    if (
      !isSearchControlled &&
      !hideSearch &&
      searchQuery.trim() &&
      getSearchText
    ) {
      const q = searchQuery.toLowerCase();
      list = rows.filter((row) => getSearchText(row).toLowerCase().includes(q));
    }
    // In controlled mode, rows are already sorted server-side — don't sort again.
    if (isSortControlled || !sortableColumn?.sortValue) {
      return list;
    }
    const sorted = [...list];
    const { sortValue } = sortableColumn;
    sorted.sort((a, b) => {
      const aVal = sortValue(a);
      const bVal = sortValue(b);
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });
    return sorted;
  }, [
    rows,
    searchQuery,
    sortableColumn,
    sortDirection,
    getSearchText,
    hideSearch,
    isSortControlled,
    isSearchControlled,
  ]);

  const handleSort = (field: string) => {
    const col = columns.find((c) => c.id === field && c.sortable);
    if (!col) return;
    const nextDirection: SortDirection =
      sortField === field ? (sortDirection === 'asc' ? 'desc' : 'asc') : 'desc';
    if (isSortControlled) {
      onSortChange?.(field, nextDirection);
      return;
    }
    if (sortField === field) {
      setInternalSortDirection(nextDirection);
    } else {
      setInternalSortField(field);
      setInternalSortDirection('desc');
    }
  };

  const getSortIcon = (field: string) => {
    if (sortField !== field) {
      return <ChevronDown size={16} />;
    }
    return sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
  };

  const renderCell = (col: DataTableColumn<T>, row: T, variant: 'body' | 'footer') => {
    if (variant === 'footer' && col.footerCell) {
      return col.footerCell(row);
    }
    return col.cell(row);
  };

  return (
    <>
      {(leading || !hideSearch) && (
        <div className={toolbarClassName}>
          {leading}
          {!hideSearch && (
            <Input
              type="text"
              placeholder={searchPlaceholder}
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              icon={<SearchIcon size={16} />}
              className={searchInputClassName}
            />
          )}
        </div>
      )}

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.id} className={col.headerClassName}>
                  {col.sortable && (col.sortValue || isSortControlled) ? (
                    <button
                      type="button"
                      className={styles.sortButton}
                      onClick={() => handleSort(col.id)}
                    >
                      <div className={styles.headerWithSort}>
                        {col.header}
                        <span
                          className={styles.sortIcon}
                          style={sortField === col.id ? { opacity: 1 } : { opacity: 0.4 }}
                        >
                          {getSortIcon(col.id)}
                        </span>
                      </div>
                    </button>
                  ) : (
                    col.header
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {displayedRows.length === 0 && emptyMessage ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className={styles.emptyCell}
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              displayedRows.map((row) => (
                <tr key={getRowKey(row)} className={styles.row}>
                  {columns.map((col) => (
                    <td key={col.id} className={col.className}>
                      {renderCell(col, row, 'body')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
          {footerRow !== undefined && (
            <tfoot>
              <tr className={styles.totalRow}>
                {columns.map((col) => (
                  <td key={col.id} className={col.className}>
                    {renderCell(col, footerRow, 'footer')}
                  </td>
                ))}
              </tr>
            </tfoot>
          )}
        </table>
      </div>

      {pagination && <div className={styles.pagination}>{pagination}</div>}
    </>
  );
}
