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
  getSearchText: (row: T) => string;
  searchPlaceholder?: string;
  leading?: ReactNode;
  footerRow?: T;
  initialSortField: string;
  initialSortDirection?: SortDirection;
  toolbarClassName?: string;
  searchInputClassName?: string;
}

export function DataTableWithSearch<T>({
  columns,
  rows,
  getRowKey,
  getSearchText,
  searchPlaceholder = 'Поиск...',
  leading,
  footerRow,
  initialSortField,
  initialSortDirection = 'desc',
  toolbarClassName = styles.toolbar,
  searchInputClassName,
}: DataTableWithSearchProps<T>) {
  const [sortField, setSortField] = useState<string>(initialSortField);
  const [sortDirection, setSortDirection] = useState<SortDirection>(initialSortDirection);
  const [searchQuery, setSearchQuery] = useState('');

  const sortableColumn = useMemo(
    () => columns.find((c) => c.id === sortField && c.sortable && c.sortValue),
    [columns, sortField]
  );

  const displayedRows = useMemo(() => {
    let list = rows;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = rows.filter((row) => getSearchText(row).toLowerCase().includes(q));
    }
    if (!sortableColumn?.sortValue) {
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
  }, [rows, searchQuery, sortableColumn, sortDirection, getSearchText]);

  const handleSort = (field: string) => {
    const col = columns.find((c) => c.id === field && c.sortable && c.sortValue);
    if (!col) return;
    if (sortField === field) {
      setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection('desc');
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
      <div className={toolbarClassName}>
        {leading}
        <Input
          type="text"
          placeholder={searchPlaceholder}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          icon={<SearchIcon size={16} />}
          className={searchInputClassName}
        />
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.id} className={col.headerClassName}>
                  {col.sortable && col.sortValue ? (
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
            {displayedRows.map((row) => (
              <tr key={getRowKey(row)} className={styles.row}>
                {columns.map((col) => (
                  <td key={col.id} className={col.className}>
                    {renderCell(col, row, 'body')}
                  </td>
                ))}
              </tr>
            ))}
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
    </>
  );
}
