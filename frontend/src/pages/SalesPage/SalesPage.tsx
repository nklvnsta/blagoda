import { useState } from "react";
import { FiltersComponent } from "../../components/features/FiltersComponent";
import type { FilterValues } from "../../components/features/FiltersComponent";
import { StatCard } from "../../components/features/StatCard";
import { useApi } from "../../api";
import type {
  SalesData,
  SalesRevenueChartResponse,
  SalesByShopsResponse,
  SalesByProductsResponse,
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

  const salesData = useApi<SalesData>('/sales/summary', {
    shop: filters.shopId,
    category: filters.categoryId,
    period: filters.periodCode,
  });

  const salesChart = useApi<SalesRevenueChartResponse>('/sales/sales-chart/', {
    shop: filters.shopId,
    category: filters.categoryId,
    period: filters.periodCode,
  });

  const shopsTable = useApi<SalesByShopsResponse>('/sales/by-shops/', {
    category: filters.categoryId,
    period: filters.periodCode,
  });

  const productsTable = useApi<SalesByProductsResponse>('/sales/by-products/', {
    shop: filters.shopId,
    category: filters.categoryId,
    period: filters.periodCode,
  });

  return (
    <div className="page">
      <h2 className="heading">Продажи</h2>
      <FiltersComponent onApply={setFilters} />
      <KPICardsRow>
        <StatCard
          title="Выручка"
          value={salesData.data ? String(salesData.data.revenue) : '—'}
          unit={salesData.data?.quantity_unit}
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
          <SalesByShopsTable data={shopsTable.data} loading={shopsTable.loading} />
        </div>
        <div className={styles.tableSlot}>
          <SalesByProductsTable data={productsTable.data} loading={productsTable.loading} />
        </div>
      </div>
    </div>
  );
}