import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import type { ForecastDemandChartResponse } from '../../../api/types';
import styles from '../SalesChart/SalesChart.module.css';

interface ForecastDemandChartProps {
  data: ForecastDemandChartResponse | null;
  loading?: boolean;
}

const ACTUAL_COLOR = '#8D271B';
const FORECAST_COLOR = '#536B8C';

function formatDay(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

export function ForecastDemandChart({ data, loading }: ForecastDemandChartProps) {
  if (loading) {
    return <div className={styles.skeleton} />;
  }

  if (!data || data.points.length === 0) {
    return (
      <div className={styles.wrapper}>
        <div className={styles.empty}>Нет данных для отображения</div>
      </div>
    );
  }

  const points = data.points.map((p) => ({
    day: formatDay(p.date),
    actual: p.actual,
    forecast: p.forecast,
  }));

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <div>
          <div className={styles.title}>Прогноз спроса</div>
          <div className={styles.subtitle}>за выбранный период, {data.unit}</div>
        </div>
        <div className={styles.legend}>
          <span className={styles.legendItem}>
            <span className={styles.dot} style={{ background: ACTUAL_COLOR }} />
            Факт
          </span>
          <span className={styles.legendItem}>
            <span className={styles.dot} style={{ background: FORECAST_COLOR }} />
            Прогноз
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={points} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="gradDemandActual" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={ACTUAL_COLOR} stopOpacity={0.15} />
              <stop offset="100%" stopColor={ACTUAL_COLOR} stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradDemandForecast" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={FORECAST_COLOR} stopOpacity={0.12} />
              <stop offset="100%" stopColor={FORECAST_COLOR} stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" vertical={false} />

          <XAxis
            dataKey="day"
            tick={{ fontSize: 12, fill: '#7e7e7e' }}
            tickLine={false}
            axisLine={{ stroke: '#e5e5e5' }}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 12, fill: '#7e7e7e' }}
            tickLine={false}
            axisLine={false}
            width={60}
            tickFormatter={(v: number) => `${v}`}
          />

          <Tooltip
            contentStyle={{
              borderRadius: '6px',
              border: '1px solid #e5e5e5',
              fontSize: '13px',
            }}
            formatter={(value, name) => {
              const n = typeof value === 'number' ? value : Number(value);
              const safe = Number.isFinite(n) ? n : 0;
              const label = name === 'actual' ? 'Факт' : 'Прогноз';
              return [`${safe} шт.`, label];
            }}
            labelFormatter={(label) => `Дата: ${String(label)}`}
          />

          <Area
            type="monotone"
            dataKey="actual"
            stroke={ACTUAL_COLOR}
            strokeWidth={2}
            fill="url(#gradDemandActual)"
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0, fill: ACTUAL_COLOR }}
            connectNulls
          />
          <Area
            type="monotone"
            dataKey="forecast"
            stroke={FORECAST_COLOR}
            strokeWidth={2}
            strokeDasharray="6 3"
            fill="url(#gradDemandForecast)"
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0, fill: FORECAST_COLOR }}
            connectNulls
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
