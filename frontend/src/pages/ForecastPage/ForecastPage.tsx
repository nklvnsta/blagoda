import { useState } from 'react';
import { FiltersComponent } from '../../components/features/FiltersComponent';
import type { FilterValues } from '../../components/features/FiltersComponent';
import { StatCard } from '../../components/features/StatCard';
import { useApi } from '../../api';
import type {
  ForecastSummaryResponse,
  ForecastDemandChartResponse,
} from '../../api/types';
import { KPICardsRow } from '../../components/features/KPICardsRow';
import { ForecastDemandChart } from '../../components/features/ForecastDemandChart';
import { ForecastByProductsTable } from '../../components/features/ForecastByProductsTable';
import { Divider } from '../../components/ui/Divider';
import styles from './ForecastPage.module.css';

export function ForecastPage() {
  const [filters, setFilters] = useState<FilterValues>({
    shopId: undefined,
    categoryId: undefined,
    periodCode: undefined,
  });

  const summary = useApi<ForecastSummaryResponse>('/forecast/summary/', {
    shop: filters.shopId,
    category: filters.categoryId,
    period: filters.periodCode,
  });

  const chart = useApi<ForecastDemandChartResponse>('/forecast/demand-chart/', {
    shop: filters.shopId,
    category: filters.categoryId,
    period: filters.periodCode,
  });

  return (
    <div className="page">
      <h2 className="heading">Прогноз спроса</h2>
      <FiltersComponent onApply={setFilters} />

      <div className={styles.chartAndKpi}>
        <div className={styles.chartSlot}>
          <ForecastDemandChart data={chart.data} loading={chart.loading} />
        </div>

        <KPICardsRow>
          <StatCard
            title="Ожидаемые продажи"
            value={summary.data ? String(summary.data.expected_sales) : '—'}
            unit={summary.data?.expected_sales_unit}
            loading={summary.loading}
          />
          <StatCard
            title="Точность прогноза"
            value={summary.data ? `${summary.data.accuracy_pct}` : '—'}
            unit="%"
            loading={summary.loading}
          />
        </KPICardsRow>
      </div>

      <ForecastByProductsTable
        shopId={filters.shopId}
        categoryId={filters.categoryId}
        periodCode={filters.periodCode}
      />
    </div>
  );
}
