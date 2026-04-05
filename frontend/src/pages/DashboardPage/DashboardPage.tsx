import { useApi } from '../../api';
import type {
  DeviationResponse,
  RevenueResponse,
  ForecastAccuracyResponse,
  SalesChartResponse,
} from '../../api/types';
import { StatCard } from '../../components/features/StatCard';
import { SalesChart } from '../../components/features/SalesChart';
import { CriticalDeviationsCard } from '../../components/features/CriticalDeviationsCard';
import { ProblemProductsCard } from '../../components/features/ProblemProductsCard';
import { Divider } from '../../components/ui/Divider';
import styles from './DashboardPage.module.css';
import { ExclamationMark } from '../../components/icons/ExclamationMark';

export function DashboardPage() {
  const deficit = useApi<DeviationResponse>('/dashboard/deficit/');
  const surplus = useApi<DeviationResponse>('/dashboard/surplus/');
  const revenue = useApi<RevenueResponse>('/dashboard/revenue/');
  const forecast = useApi<ForecastAccuracyResponse>('/dashboard/forecast-accuracy/');
  const chart = useApi<SalesChartResponse>('/dashboard/sales-chart/');

  const anyError = deficit.error || surplus.error || revenue.error || forecast.error || chart.error;

  return (
    <div className="page">
      <h1 className="heading">Краткое состояние сети</h1>

      {anyError && (
        <div className={styles.error}>
          Не удалось загрузить данные: {anyError}
        </div>
      )}

      <div className={styles.cards}>
        <StatCard
          icon={<ExclamationMark color="var(--color-status-critical)" />}
          title="Дефицит товаров"
          title_additional={'за неделю'}
          value={deficit.data ? String(deficit.data.current_week.qty) : '—'}
          unit={deficit.data?.current_week.unit}
          changePct={deficit.data?.change_pct}
          footer_additional={'к прошлой неделе'}
          loading={deficit.loading}
        />
        <StatCard
          icon={<ExclamationMark color="var(--color-status-warning)" />}
          title="Избыток товаров"
          title_additional={'за неделю'}
          value={surplus.data ? String(surplus.data.current_week.qty) : '—'}
          unit={surplus.data?.current_week.unit}
          changePct={surplus.data?.change_pct}
          footer_additional={'к прошлой неделе'}
          loading={surplus.loading}
        />

        <StatCard
          icon={<ExclamationMark color="var(--color-status-info)" />}
          title="Точность прогноза"
          value={forecast.data ? String(forecast.data.accuracy_pct) : '—'}
          unit="%"
          loading={forecast.loading}
        />

        <StatCard
          icon={<ExclamationMark color="var(--color-status-positive)" />}
          title="Выручка"
          title_additional={'за неделю'}
          value={revenue.data ? String(revenue.data.revenue) : '—'}
          unit={revenue.data?.unit}
          loading={revenue.loading}
        />
      </div>

      <SalesChart data={chart.data} loading={chart.loading} />

      <div className={styles.deviationsBand}>
        <div className={styles.criticalWrap}>
          <CriticalDeviationsCard />
        </div>
        <Divider direction="vertical" className={styles.sepVertical} />
        <Divider direction="horizontal" className={styles.sepHorizontal} />
        <ProblemProductsCard />
      </div>
    </div>
  );
}
