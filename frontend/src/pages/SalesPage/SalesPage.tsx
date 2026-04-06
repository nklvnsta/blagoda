import { useEffect, useState } from "react";
import { FiltersComponent } from "../../components/features/FiltersComponent";
import type { FilterValues } from "../../components/features/FiltersComponent";
import { StatCard } from "../../components/features/StatCard";
import styles from "./SalesPage.module.css";
import { useApi } from "../../api";
import type { SalesData } from "../../api/types";
import { Divider } from "../../components/ui/Divider";
import { KPICardsRow } from "../../components/features/KPICardsRow";

export function SalesPage() {

  const [filters, setFilters] = useState<FilterValues>({
    shopId: undefined,
    categoryId: undefined,
    periodCode: undefined,
  });

  const salesData = useApi<SalesData>('/sales/summary', 
    {  
      shop: filters.shopId,
      category: filters.categoryId,
      period: filters.periodCode,
    }
  );
  
  return (
    <div className="page">
      <h1 className="heading">Продажи</h1>
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

    </div>
  );
}