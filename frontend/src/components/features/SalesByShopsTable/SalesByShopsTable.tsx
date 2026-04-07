import { useState } from 'react';
import type { SalesByShopsResponse, ShopSalesRow } from '../../../api/types';
import styles from './SalesByShopsTable.module.css';
import { ChevronDown, ChevronUp, SearchIcon } from '../../icons';
import { Input } from '../../ui/Input';

interface SalesByShopsTableProps {
  data: SalesByShopsResponse | null;
  loading?: boolean;
}

type SortField = 'revenue' | 'sold_qty' | 'receipt_count';
type SortDirection = 'asc' | 'desc';

export function SalesByShopsTable({ data, loading }: SalesByShopsTableProps) {
  const [sortField, setSortField] = useState<SortField>('revenue');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [searchQuery, setSearchQuery] = useState('');

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

  const formatCurrency = (value: string | number): string => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(num);
  };

  const formatNumber = (value: number): string => {
    return new Intl.NumberFormat('ru-RU').format(value);
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortRows = (rows: ShopSalesRow[]): ShopSalesRow[] => {
    const sorted = [...rows];
    sorted.sort((a, b) => {
      let aVal: number;
      let bVal: number;

      if (sortField === 'revenue') {
        aVal = parseFloat(a.revenue);
        bVal = parseFloat(b.revenue);
      } else if (sortField === 'sold_qty') {
        aVal = a.sold_qty;
        bVal = b.sold_qty;
      } else {
        aVal = a.receipt_count;
        bVal = b.receipt_count;
      }

      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    });

    return sorted;
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ChevronDown size={16} />;
    }
    return sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
  };

  const filterAndSortRows = (rows: ShopSalesRow[]): ShopSalesRow[] => {
    let filtered = rows;
    
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = rows.filter((row) =>
        row.shop_name.toLowerCase().includes(query)
      );
    }

    return sortRows(filtered);
  };

  const displayedRows = filterAndSortRows(data.rows);

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <div>
            <h3 className={styles.title}>Продажи по магазинам</h3>
            <span className={styles.subtitle}>
                {data.period_label}, {data.quantity_unit}
            </span>
        </div>
        <Input
          type="text"
          placeholder="Поиск по магазину..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          icon={<SearchIcon size={16} />}
          className={styles.searchInput}
        />
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Магазин</th>
              <th>
                <button
                  className={styles.sortButton}
                  onClick={() => handleSort('revenue')}
                >
                  <div className={styles.headerWithSort}>
                    Выручка
                    <span
                      className={styles.sortIcon}
                      style={sortField === 'revenue' ? { opacity: 1 } : { opacity: 0.4 }}
                    >
                      {getSortIcon('revenue')}
                    </span>
                  </div>
                </button>
              </th>
              <th>
                <button
                  className={styles.sortButton}
                  onClick={() => handleSort('sold_qty')}
                >
                  <div className={styles.headerWithSort}>
                    Продано, шт.
                    <span
                      className={styles.sortIcon}
                      style={sortField === 'sold_qty' ? { opacity: 1 } : { opacity: 0.4 }}
                    >
                      {getSortIcon('sold_qty')}
                    </span>
                  </div>
                </button>
              </th>
              <th>
                <button
                  className={styles.sortButton}
                  onClick={() => handleSort('receipt_count')}
                >
                  <div className={styles.headerWithSort}>
                    Количество чеков
                    <span
                      className={styles.sortIcon}
                      style={sortField === 'receipt_count' ? { opacity: 1 } : { opacity: 0.4 }}
                    >
                      {getSortIcon('receipt_count')}
                    </span>
                  </div>
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {displayedRows.map((row) => (
              <tr key={row.shop_id} className={styles.row}>
                <td className={styles.tdShop}>{row.shop_name}</td>
                <td className={styles.tdRight}>{formatCurrency(row.revenue)}</td>
                <td className={styles.tdRight}>{formatNumber(row.sold_qty)}</td>
                <td className={styles.tdRight}>{formatNumber(row.receipt_count)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className={styles.totalRow}>
              <td className={styles.tdShop}>{data.total.shop_name}</td>
              <td className={styles.tdRight}>
                <strong>{formatCurrency(data.total.revenue)}</strong>
              </td>
              <td className={styles.tdRight}>
                <strong>{formatNumber(data.total.sold_qty)}</strong>
              </td>
              <td className={styles.tdRight}>
                <strong>{formatNumber(data.total.receipt_count)}</strong>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
