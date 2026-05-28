import { useState } from "react";
import { FiltersComponent } from "../../components/features/FiltersComponent";
import type { FilterValues } from "../../components/features/FiltersComponent";
import { StatCard } from "../../components/features/StatCard";
import { buildFilterParams, useApi } from "../../api";
import type {
  SalesData,
  SalesRevenueChartResponse,
} from "../../api/types";
import { KPICardsRow } from "../../components/features/KPICardsRow";
import { SalesRevenueChart } from "../../components/features/SalesRevenueChart";
import { SalesByShopsTable } from "../../components/features/SalesByShopsTable";
import { SalesByProductsTable } from "../../components/features/SalesByProductsTable";
import styles from "./SalesPage.module.css";

export function SalesPage() {

  const [filters, setFilters] = useState<FilterValues>({
    shopId: undefined,
    categoryId: undefined,
    periodCode: undefined,
  });

  const filterParams = buildFilterParams(filters);

  const salesData = useApi<SalesData>('/sales/summary', filterParams);

  const salesChart = useApi<SalesRevenueChartResponse>('/sales/sales-chart/', filterParams);

  return (
    <div className="page">
      <h2 className="heading">Продажи</h2>
      <FiltersComponent onApply={setFilters} />
      <KPICardsRow>
        <StatCard
          title="Выручка"
          value={salesData.data ? String(salesData.data.revenue) : '—'}
          unit="₽"
          loading={salesData.loading}
        />
        <StatCard
          title="Количество продаж"
          value={salesData.data ? String(salesData.data.sold_qty) : '—'}
          unit={salesData.data?.quantity_unit}
          loading={salesData.loading}
        />
        <StatCard
          title="Средний чек"
          value={salesData.data ? String(salesData.data.avg_ticket) : '—'}
          unit="₽"
          loading={salesData.loading}
        />
        <StatCard
          title="Средняя выручка за день"
          value={salesData.data ? String(salesData.data.avg_daily_revenue) : '—'}
          unit="₽"
          loading={salesData.loading}
        />
      </KPICardsRow>

      <SalesRevenueChart data={salesChart.data} loading={salesChart.loading} />

      <div className={styles.tablesRow}>
        <div className={styles.tableSlot}>
          <SalesByShopsTable
            categoryId={filters.categoryId}
            periodCode={filters.periodCode}
            dateFrom={filters.dateFrom}
            dateTo={filters.dateTo}
          />
        </div>
        <div className={styles.tableSlot}>
          <SalesByProductsTable
            shopId={filters.shopId}
            categoryId={filters.categoryId}
            periodCode={filters.periodCode}
            dateFrom={filters.dateFrom}
            dateTo={filters.dateTo}
          />
        </div>
      </div>
    </div>
  );
}