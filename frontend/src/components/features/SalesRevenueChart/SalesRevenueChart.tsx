import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import type { SalesRevenueChartResponse } from '../../../api/types';
import styles from '../SalesChart/SalesChart.module.css';

interface SalesRevenueChartProps {
  data: SalesRevenueChartResponse | null;
  loading?: boolean;
}

const REVENUE_COLOR = '#8D271B';
const AVG_TICKET_COLOR = '#3E7E9E';

function formatDay(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

export function SalesRevenueChart({ data, loading }: SalesRevenueChartProps) {
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

  const points = data.points.map((point) => ({
    day: formatDay(point.date),
    revenue: parseFloat(point.revenue),
    avg_ticket: point.avg_ticket !== null ? parseFloat(point.avg_ticket) : null,
  }));

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <div>
          <div className={styles.title}>Выручка и средний чек</div>
          <div className={styles.subtitle}>за выбранный период, {data.unit}</div>
        </div>
        <div className={styles.legend}>
          <span className={styles.legendItem}>
            <span className={styles.dot} style={{ background: REVENUE_COLOR }} />
            Выручка
          </span>
          <span className={styles.legendItem}>
            <span className={styles.dot} style={{ background: AVG_TICKET_COLOR }} />
            Средний чек
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <ComposedChart data={points} margin={{ top: 4, right: 20, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="gradRevenue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={REVENUE_COLOR} stopOpacity={0.18} />
              <stop offset="100%" stopColor={REVENUE_COLOR} stopOpacity={0} />
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
            yAxisId="left"
            tick={{ fontSize: 12, fill: '#7e7e7e' }}
            tickLine={false}
            axisLine={false}
            width={60}
            tickFormatter={(value) => `${value}`}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 12, fill: '#7e7e7e' }}
            tickLine={false}
            axisLine={false}
            width={60}
            tickFormatter={(value) => `${value}`}
          />

          <Tooltip
            contentStyle={{
              borderRadius: '6px',
              border: '1px solid #e5e5e5',
              fontSize: '13px',
            }}
            formatter={(value, name) => {
              const numericValue = typeof value === 'number' ? value : Number(value);
              const safe = Number.isFinite(numericValue) ? numericValue : 0;
              const label = name === 'revenue' ? 'Выручка' : 'Средний чек';
              return [`${safe.toFixed(2)} ₽`, label];
            }}
            labelFormatter={(label) => `Дата: ${String(label)}`}
          />

          <Area
            yAxisId="left"
            type="monotone"
            dataKey="revenue"
            stroke={REVENUE_COLOR}
            fill="url(#gradRevenue)"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0, fill: REVENUE_COLOR }}
            connectNulls
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="avg_ticket"
            stroke={AVG_TICKET_COLOR}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, strokeWidth: 0, fill: AVG_TICKET_COLOR }}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
