import { useApi } from '../../api';
import type { PickingSummaryResponse } from '../../api/types';
import { KPICardsRow } from '../../components/features/KPICardsRow';
import { StatCard } from '../../components/features/StatCard';
import { PickingTodayTable } from '../../components/features/PickingTodayTable';

function formatNumber(value: number | undefined): string {
  if (value === undefined) return '—';
  return new Intl.NumberFormat('ru-RU').format(value);
}

export function PickingPage() {
  const summary = useApi<PickingSummaryResponse>('/picking/summary/');

  return (
    <div className="page">
      <h2 className="heading">Поставки на сегодня</h2>

      <KPICardsRow>
        <StatCard
          title="Всего магазинов"
          value={formatNumber(summary.data?.total_shops)}
          loading={summary.loading}
        />
        <StatCard
          title="Собрано полностью"
          value={formatNumber(summary.data?.picked_count)}
          loading={summary.loading}
        />
        <StatCard
          title="Собрано частично"
          value={formatNumber(summary.data?.partial_count)}
          loading={summary.loading}
        />
        <StatCard
          title="Не начато"
          value={formatNumber(summary.data?.not_started_count)}
          loading={summary.loading}
        />
      </KPICardsRow>

      <PickingTodayTable />
    </div>
  );
}
